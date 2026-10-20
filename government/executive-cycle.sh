#!/bin/sh
# Continuously reconcile executive delivery without parliamentary summons.
# Called by ordinary government boot; does not modify protected constitution.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
charter=${VICHE_CONSTITUTION:?founder-owned charter required}
[ -f "$state/inaugurated" ] || exit 0
id=c1e00002
[ -n "$id" ] || { echo "Viche: missing executive seat" >&2; exit 1; }
# Act 19 §3.2: read the handoff queue FIRST. A read failure aborts the cycle
# (no generic dispatch). Open handoffs suppress the generic prompt entirely.
open_handoffs=$(/bin/sh "$town/government/handoff-queue.sh" open executive) || {
  echo "Viche: handoff queue read failed; no dispatch this cycle" >&2
  exit 1
}
status=$(antonina agent status --id "$id" --json)
current=$(printf "%s\n" "$status" | jq -r ".state")
case "$current" in
  running) exit 0 ;;
  failed) echo "Independent Executive failed; branch recovery required" >&2; exit 1 ;;
  idle|succeeded) : ;;
  *) echo "Viche: unexpected executive state $current" >&2; exit 1 ;;
esac
model=$(printf "%s\n" "$status" | jq -r ".model // empty")
variant=$(printf "%s\n" "$status" | jq -r ".variant // empty")
if [ "$model" != opencode-go/longcat-2.5-preview-free ] || [ "$variant" != low ]; then
  echo "Viche: unauthorized executive model; refusing dispatch" >&2
  exit 1
fi
cwd=$seats/branches/executive
[ -d "$cwd" ] && [ -s "$charter" ] || exit 1
promptfile=$(mktemp)
cat "$town/government/prompts/exec-head.txt" >> "$promptfile"
cat "$charter" >> "$promptfile"
if [ -n "$open_handoffs" ]; then
  # Act 19 §3.2.3: open handoffs only; the generic prompt is NOT run.
  cat "$town/government/prompts/exec-handoff-tail.txt" >> "$promptfile"
  printf '%s\n' "$open_handoffs" >> "$promptfile"
  printf 'Use only the constitutionally approved model with Antonina.\n' >> "$promptfile"
  printf 'Your worktree is %s.\n' "$cwd" >> "$promptfile"
else
  eligible=$(python3 "$town/government/eligible-work.py") || exit 1
  cat "$town/government/prompts/exec-generic-tail.txt" >> "$promptfile"
  printf '%s\n' "$eligible" >> "$promptfile"
  cat "$town/government/prompts/exec-generic-static.txt" >> "$promptfile"
  printf 'Your worktree is %s.\n' "$cwd" >> "$promptfile"
fi
prompt=$(cat "$promptfile")
rm -f "$promptfile"
antonina agent run --id "$id" --cwd "$cwd" --prompt "$prompt" --detach
mkdir -p "$state/branches"
date +%s > "$state/branches/executive-last-dispatch"
