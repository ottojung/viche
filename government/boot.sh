#!/bin/sh
# Parliament-editable seat reconciliation; invoked by the protected S6 boot.
# No separate scheduler or direct model calls.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
[ -s "$town/government/LAWS.md" ] || exit 1
[ -s "$town/government/seats.tsv" ] || exit 1
command -v antonina >/dev/null 2>&1
mkdir -p "$seats"
git -C "$town" rev-parse --is-inside-work-tree >/dev/null

ids=$(mktemp)
trap 'rm -f "$ids"' EXIT HUP INT TERM
tab=$(printf '\t')
while IFS="$tab" read -r agent_id title focus; do
    [ -n "$agent_id" ] || continue
    case "$agent_id" in
        *[!0123456789abcdef]*|'') echo "Invalid seat ID: $agent_id" >&2; exit 1 ;;
    esac
    [ -n "$title" ] && [ -n "$focus" ] || {
        echo "Incomplete seat: $agent_id" >&2; exit 1;
    }
    printf '%s\n' "$agent_id" >> "$ids"
done < "$town/government/seats.tsv"

[ -s "$ids" ] || { echo "No parliamentary seats" >&2; exit 1; }
unique=$(sort -u "$ids" | wc -l)
total=$(wc -l < "$ids")
[ "$unique" -eq "$total" ] || { echo "Duplicate seat IDs" >&2; exit 1; }

while IFS="$tab" read -r agent_id title focus; do
    [ -n "$agent_id" ] || continue
    seat_dir=$seats/$agent_id
    if [ ! -f "$seat_dir/.git" ] && [ ! -d "$seat_dir/.git" ]; then
        if [ -d "$seat_dir" ] && [ -n "$(ls -A "$seat_dir")" ]; then
            echo "Refusing to replace seat directory: $seat_dir" >&2
            exit 1
        fi
        git -C "$town" worktree add --detach "$seat_dir" HEAD
    fi
    if ! antonina agent status --id "$agent_id" --json >/dev/null 2>&1; then
        antonina agent new --id "$agent_id" --cwd "$seat_dir" --title "Viche: $title"
    fi
done < "$town/government/seats.tsv"

# Restore a failed Clerk's independent Antonina session only after a cooldown.
# Ordinary government owns this recovery; constitutional boot/model are unchanged.
if [ -f "$town/government/clerk-liveness.sh" ]; then
    /bin/sh "$town/government/clerk-liveness.sh" || echo "Viche: Clerk liveness reconciliation failed" >&2
fi

# Janitor Office: observe disk health each cycle; safe reclamation is self-throttled and
# non-fatal so it can never block seat reconciliation. Authority and safeguards:
# records/bills/janitor-office-act.md (Act 12); observation is within Act 4.2.
if [ -f "$town/government/janitor.sh" ]; then
    /bin/sh "$town/government/janitor.sh" cycle || echo "Viche: janitor cycle failed" >&2
fi
