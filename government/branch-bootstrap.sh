#!/bin/sh
# Two independent durable branch agents not present in the parliamentary roster.
set -eu
[ "$#" -eq 1 ] || exit 2
branch=$1
case "$branch" in
  executive) id=c1e00002; title=Executive ;;
  judiciary) id=c1e00008; title=Judiciary ;;
  *) exit 2 ;;
esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
cwd=$seats/branches/$branch
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
if [ "$mode" = failed ]; then
  reason=$(printf '%s\n' "$meta" | jq -r '.backend_error.classification // ""')
  if [ "$reason" = upstream_endpoint_unavailable ]; then
    dir=$state/liveness
    mkdir -p "$dir"
    now=$(date +%s)
    stamp=$dir/last-reset-$id
    last=0
    [ ! -s "$stamp" ] || last=$(cat "$stamp")
    case "$last" in ''|*[!0-9]*) last=0 ;; esac
    if [ $((now-last)) -ge 1800 ]; then
      snapshot=$(mktemp -d "$dir/branch-$id-recovery-XXXXXX")
      printf '%s\n' "$meta" > "$snapshot/status.json"
      antonina agent log --id "$id" --lines 200 > "$snapshot/log.txt" 2>&1 || :
      git -C "$cwd" status --short > "$snapshot/worktree.txt"
      printf '%s\n' "$now" > "$stamp"
      antonina agent delete --id "$id"
      antonina agent new --id "$id" --cwd "$cwd" --title "Viche: $title"
      meta=$(antonina agent status --id "$id" --json)
    fi
  fi
fi
model=$(printf '%s\n' "$meta" | jq -r '.model // empty')
variant=$(printf '%s\n' "$meta" | jq -r '.variant // empty')
if [ "$model" != opencode-go/longcat-2.5-preview-free ] || [ "$variant" != low ]; then
  echo "Office $branch has unauthorized model; refusing dispatch" >&2
  exit 1
fi
