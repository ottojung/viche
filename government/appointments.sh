#!/bin/sh
# Map durable logical seat/office keys to disposable Antonina agent IDs.
set -eu
{ [ "$#" -eq 2 ] || { [ "$#" -eq 3 ] && [ "$1" = replace ]; }; } ||
  { echo 'Usage: appointments.sh ensure|resolve|replace KEY [EXPECTED_ID]' >&2; exit 2; }
action=$1 key=$2
expected=${3:-}
case "$expected" in ''|*[!a-zA-Z0-9_-]*) [ -z "$expected" ] || exit 2;; esac
case "$action" in ensure|resolve|replace) :;; *) exit 2;; esac
case "$key" in ''|*[!a-zA-Z0-9_-]*) exit 2;; esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/appointments
mkdir -p "$root"
umask 077
tab=$(printf '\t')
title=
cwd=
while IFS="$tab" read -r seat_id seat_title focus; do
  if [ "$key" = "$seat_id" ]; then title=$seat_title; cwd=$seats/$key; break; fi
done < "$town/government/seats.tsv"
if [ -z "$cwd" ]; then
  case "$key" in
    executive) title=Executive;;
    judiciary) title=Judiciary;;
    innovation-centre) title='Legislative Innovation Centre';;
    *) echo "unknown seat or office $key" >&2; exit 2;;
  esac
  cwd=$seats/branches/$key
fi
[ -d "$cwd" ] || { echo "missing worktree $cwd" >&2; exit 1; }
registry=$root/appointments.tsv
if [ "$action" != resolve ]; then
  tries=0
  until mkdir "$root/lock" 2>/dev/null; do
    tries=$((tries+1))
    [ "$tries" -lt 20 ] || { echo 'appointment lock busy' >&2; exit 1; }
    sleep 1
  done
  trap 'rmdir "$root/lock"' EXIT HUP INT TERM
fi
old=
if [ -f "$registry" ]; then
  old=$(awk -F '\t' -v k="$key" '$1==k {n++; print $2} END {if(n>1) exit 9}' "$registry") ||
    { echo 'duplicate appointment record' >&2; exit 1; }
fi
live=false
if [ -n "$old" ]; then
  case "$old" in *[!a-zA-Z0-9_-]*|'') echo 'invalid stored ID' >&2; exit 1;; esac
  if ! meta=$(antonina agent status --id "$old" --json 2>/dev/null); then
    # A transient status-query failure is NOT evidence of a dead agent.
    # Replacing it could create a second live agent on the same worktree.
    echo "Viche: status of appointed agent $old is unreadable; refuse replacement until a terminal status is proven" >&2
    exit 1
  fi
  status=$(printf '%s\n' "$meta" | jq -er '.state') || exit 1
  case "$status" in running|idle|succeeded) live=true;; failed|stopped|killed) :;; *) echo "unknown status $status" >&2; exit 1;; esac
fi
if [ "$action" = replace ] && [ -n "$expected" ] && [ "$old" != "$expected" ]; then
  echo "Viche: stale recovery appointment $expected for $key; actual is $old" >&2
  exit 1
fi
if [ "$action" = resolve ]; then
  [ -n "$old" ] || { echo "no appointment for $key" >&2; exit 1; }
  printf '%s\n' "$old"
  exit 0
fi
if [ "$action" = ensure ] && [ -n "$old" ]; then
  # Terminal agents remain assigned until per-office supervisor records the
  # failure and explicitly replaces at the legally required threshold.
  printf '%s\n' "$old"
  exit 0
fi
# The Act 19 supervisors need evidence of real failed invocations. Historically
# 'ensure' replaced a failed appointee BEFORE they could observe it. Capture
# exact terminal status, last log and worktree identity BEFORE replacement.
# Record at most once per disposable agent ID, even across repeated cycles.
# This does not authorize replay of an unsafe failed prompt or claim that a
# first-failure replacement met Act 19's reset threshold.
if [ -n "$old" ] && [ "$live" != true ]; then
  observed=${meta:-'{"state":"unreadable"}'}
  printf '%s\n' "$observed" |
    /bin/sh "$(CDPATH= cd "$(dirname "$0")" && pwd -P)/terminal-appointment-evidence.sh" "$key" "$old" "$cwd" ||
      { echo "Cannot preserve evidence of departing agent $old" >&2; exit 1; }
fi
# An old Git branch may carry a retired model or scope restriction.
# Refresh only idle appointees, not worktrees of currently running agents.
if [ -s "$town/AGENTS.md" ] && { [ -f "$cwd/.git" ] || [ -d "$cwd/.git" ]; } &&
   { [ "$live" != true ] || [ "$status" != running ]; }; then
  /bin/sh "$town/government/policy-sync.sh" "$cwd" ||
    { echo "Cannot dispatch $key: stale instructions could not be repaired" >&2; exit 1; }
fi
if [ "$live" = true ] && [ "$action" = ensure ]; then
  printf '%s\n' "$old"
  exit 0
fi
new=$(antonina agent new --cwd "$cwd" --title "Viche: $title") || exit 1
case "$new" in ''|*[!a-zA-Z0-9_-]*) echo 'malformed new agent ID' >&2; exit 1;; esac
[ "$new" != "$old" ] || { echo 'new agent reused old ID' >&2; exit 1; }
meta=$(antonina agent status --id "$new" --json) || exit 1
[ "$(printf '%s\n' "$meta" | jq -r '.state')" = idle ] || exit 1
tmp=$(mktemp "$root/roster.XXXXXXXX")
if [ -f "$registry" ]; then awk -F '\t' -v k="$key" '$1!=k {print}' "$registry" > "$tmp"; fi
printf '%s\t%s\n' "$key" "$new" >> "$tmp"
mv -f "$tmp" "$registry"
printf '%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$key" "${old:--}" "$new" >> "$root/appointments.log"
printf '%s\n' "$new"
