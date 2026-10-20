#!/bin/sh
# Independent durable government offices, never parliamentary voting seats.
set -eu
[ "$#" -eq 1 ] || exit 2
branch=$1
case "$branch" in
  executive) id=c1e00002; title=Executive ;;
  judiciary) id=c1e00008; title=Judiciary ;;
  innovation-centre) id=c1e00011; title="Legislative Innovation Centre" ;;
  *) exit 2 ;;
esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
cwd=$seats/branches/$branch
. "$town/government/office-recovery.sh"
if cut -f 1 "$town/government/seats.tsv" | grep -Fxq "$id"; then
  echo "Office $branch must never share a parliamentary voting seat" >&2
  exit 1
fi
if [ ! -f "$cwd/.git" ] && [ ! -d "$cwd/.git" ]; then
  if [ -d "$cwd" ] && [ -n "$(ls -A "$cwd")" ]; then
    echo "Refusing to replace occupied office worktree: $cwd" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$cwd")"
  git -C "$town" worktree add --detach "$cwd" HEAD
fi
if ! meta=$(antonina agent status --id "$id" --json 2>/dev/null); then
  antonina agent new --id "$id" --cwd "$cwd" --title "Viche: $title"
  meta=$(antonina agent status --id "$id" --json)
fi
mode=$(printf '%s\n' "$meta" | jq -r '.state')
reason=$(printf '%s\n' "$meta" | jq -r '.backend_error.classification // ""')
# Act 19 §3.1: record every failure; the reset decision is decidable from the
# failure record (count + window + cooldown + progress guard), not the state.
if [ "$mode" = failed ]; then
  or_record "$branch" "$reason" || true
  # permanent failures are surfaced, never silently reset
  if [ "$(or_classify "$reason")" = permanent ]; then
    echo "Office $branch permanent failure ($reason); surfaced, not reset" >&2
  fi
  if or_should_reset "$branch" "$cwd"; then
    echo "Office $branch reached failure threshold; resetting" >&2
    or_reset "$branch" "$id" "$title" "$cwd" >/dev/null
    meta=$(antonina agent status --id "$id" --json)
  fi
fi
model=$(printf '%s\n' "$meta" | jq -r '.model // empty')
variant=$(printf '%s\n' "$meta" | jq -r '.variant // empty')
if [ "$model" != opencode-go/longcat-2.5-preview-free ] || [ "$variant" != low ]; then
  echo "Office $branch has unauthorized model; refusing dispatch" >&2
  exit 1
fi
