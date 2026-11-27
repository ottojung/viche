#!/bin/sh
# Keep an appointee's instruction file consistent with canonical Viche policy.
# Never touch unrelated work or silently overwrite the agent's own edits.
set -eu
usage() { echo 'Usage: policy-sync.sh WORKTREE [--contributor "Name <email>"]' >&2; exit 2; }
contributor=
cwd=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --contributor) [ "$#" -ge 2 ] || usage; contributor=$2; shift 2 ;;
        -*) usage ;;
        *) [ -z "$cwd" ] || usage; cwd=$1; shift ;;
    esac
done
[ -n "$cwd" ] || usage
verifier_dir=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
case "$cwd" in /*) : ;; *) echo 'Worktree must have an absolute path' >&2; exit 2 ;; esac
[ -s "$town/AGENTS.md" ] && [ -d "$cwd" ] || exit 1

# No Git operations in the already-consistent fast path.
if cmp -s "$town/AGENTS.md" "$cwd/AGENTS.md"; then exit 0; fi

# Prevent mutations of unrelated paths and unmanaged clones.
git -C "$town" worktree list --porcelain |
    grep -Fxq "worktree $cwd" ||
    { echo "Unregistered Viche worktree: $cwd" >&2; exit 1; }
[ -f "$cwd/AGENTS.md" ] ||
    { echo "Missing tracked AGENTS.md in $cwd" >&2; exit 1; }
[ -z "$(git -C "$cwd" status --porcelain -- AGENTS.md)" ] ||
    { echo "Locally modified AGENTS.md in $cwd; refuse overwrite" >&2; exit 1; }

# Signed commit on Billy: the linked worktree can be arbitrarily old, but
# no other source change, index entry or branch history may be discarded.
umask 077
tmp=$(mktemp "$cwd/.viche-policy.XXXXXXXX")
trap 'rm -f "$tmp"' EXIT HUP INT TERM
cat "$town/AGENTS.md" > "$tmp"
chmod 0644 "$tmp"
mv -f "$tmp" "$cwd/AGENTS.md"
set -- commit --repo "$cwd" --subject 'Sync current Viche operating instructions'
[ -z "$contributor" ] || set -- "$@" --contributor "$contributor"
set -- "$@" -- --only -- AGENTS.md
if ! python3 "$verifier_dir/commit-identity.py" "$@"; then
    git -C "$cwd" restore --source=HEAD --staged --worktree -- AGENTS.md
    echo "Policy update could not be committed in $cwd" >&2
    exit 1
fi
mkdir -p "$state"
printf '%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$cwd" \
    "$(git -C "$cwd" rev-parse --short HEAD)" >> "$state/policy-sync.log"
