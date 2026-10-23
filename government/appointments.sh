#!/bin/sh
# Map durable logical seat/office keys to disposable Antonina agent IDs.
set -eu
[ "$#" -eq 2 ] || { echo 'Usage: appointments.sh ensure|resolve|replace KEY' >&2; exit 2; }
action=$1 key=$2
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
  if meta=$(antonina agent status --id "$old" --json 2>/dev/null); then
    status=$(printf '%s\n' "$meta" | jq -er '.state') || exit 1
    case "$status" in running|idle|succeeded) live=true;; failed|stopped|killed) :;; *) echo "unknown status $status" >&2; exit 1;; esac
  fi
fi
if [ "$action" = resolve ]; then
  [ "$live" = true ] || { echo "no live appointment for $key" >&2; exit 1; }
  printf '%s\n' "$old"
  exit 0
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
# A new agent has no model history until it runs; Antonina owns model choice.
tmp=$(mktemp "$root/roster.XXXXXXXX")
if [ -f "$registry" ]; then awk -F '\t' -v k="$key" '$1!=k {print}' "$registry" > "$tmp"; fi
printf '%s\t%s\n' "$key" "$new" >> "$tmp"
mv -f "$tmp" "$registry"
printf '%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$key" "${old:--}" "$new" >> "$root/appointments.log"
printf '%s\n' "$new"
