#!/bin/sh
# Preserve terminal appointment evidence BEFORE an Antonina ID is superseded.
# This is read-only with respect to the old agent and Git worktree; it does NOT
# claim that replacing an appointee satisfies Act 19's 3-failure reset policy.
set -eu
[ "$#" -eq 3 ] || { echo 'Usage: terminal-appointment-evidence.sh KEY ID CWD' >&2; exit 2; }
key=$1 id=$2 cwd=$3
case "$key:$id" in *[!a-zA-Z0-9_:-]*|'') echo 'Invalid terminal appointment key' >&2; exit 2;; esac
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/appointments
dest=$root/terminal-evidence/$id
[ ! -d "$dest" ] || exit 0
mkdir -p "$root/terminal-evidence"
umask 077
tmp=$(mktemp -d "$root/.terminal-XXXXXXXX") || exit 1
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
cat > "$tmp/status.json"
jq -e 'type=="object" and (.state | type=="string")' "$tmp/status.json" >/dev/null ||
  { echo 'Malformed terminal appointment evidence' >&2; exit 1; }
state=$(jq -r '.state' "$tmp/status.json")
case "$state" in
  failed|killed|stopped|unreadable) : ;;
  *) echo "Refusing to log nonterminal state: $state" >&2; exit 1 ;;
esac
antonina agent log --id "$id" --lines 80 > "$tmp/log-tail.txt" 2>&1 || :
git -C "$cwd" rev-parse HEAD > "$tmp/worktree-head.txt" 2>/dev/null || printf 'unavailable\n' > "$tmp/worktree-head.txt"
git -C "$cwd" status --short > "$tmp/worktree-status.txt" 2>/dev/null || :
jq -cn --arg key "$key" --arg id "$id" --arg cwd "$cwd" \
  --arg at "$(date -u +%FT%TZ)" --slurpfile m "$tmp/status.json" \
  '{at:$at, office:$key, agent_id:$id, cwd:$cwd, state:$m[0].state,
    finished_at:($m[0].finished_at//null), prompts:($m[0].prompts//null),
    failure_class:($m[0].backend_error.classification//null),
    transient:($m[0].backend_error.transient),
    automatic_retry_safe:($m[0].backend_error.automatic_retry_safe),
    evidence:("terminal-evidence/" + $id)}' > "$tmp/event.json"
mv "$tmp" "$dest"
trap - EXIT HUP INT TERM
cat "$dest/event.json" >> "$root/terminal-events.jsonl"
echo "Viche: retained terminal appointment $id ($state) before replacement" >&2
