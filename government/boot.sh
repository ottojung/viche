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
    # All seats have durable, independently recoverable sessions; don't let a
    # failed provider continuation permanently remove a future voter.
    if [ -f "$town/government/seat-liveness.sh" ]; then
        /bin/sh "$town/government/seat-liveness.sh" "$agent_id" ||
            echo "Viche: seat $agent_id recovery failed" >&2
    fi
done < "$town/government/seats.tsv"

# Three independent branches: readiness is checked separately and durably.
# The protected constitutional boot still owns parliamentary sittings.
# A branch failure never suppresses another branch's reconciliation.
if [ -f "$town/government/branch-liveness.sh" ]; then
    /bin/sh "$town/government/branch-liveness.sh" legislature ||
        echo "Viche: Legislature liveness investigation required" >&2
fi

# Janitor Office: observe disk health each cycle; safe reclamation is self-throttled and
# non-fatal so it can never block seat reconciliation. Authority and safeguards:
# records/bills/janitor-office-act.md (Act 12); observation is within Act 4.2.
if [ -f "$town/government/janitor.sh" ]; then
    /bin/sh "$town/government/janitor.sh" cycle || echo "Viche: janitor cycle failed" >&2
fi

# SoringP1 (#301) research-pool oversight: read-only measurement of the live
# phoebe-dev research pool each cycle (standing Executive duty). Never
# fabricates or auto-launches research; replenishment is operator-registry
# gated. Non-fatal so it can never block reconciliation.
if [ -f "$town/government/soringp1-oversight.sh" ]; then
    /bin/sh "$town/government/soringp1-oversight.sh" report >/dev/null 2>&1 ||
        echo "Viche: SoringP1 pool oversight report failed" >&2
fi

# Independent Executive: no parliamentary summons required.
if [ -f "$town/government/branch-liveness.sh" ]; then
    /bin/sh "$town/government/branch-liveness.sh" executive ||
        echo "Viche: Executive liveness investigation required" >&2
fi

# Deterministic oversight continues even when every AI session is unavailable.
# Failure of telemetry/auditing must not prevent unrelated reconciliation.
if [ -f "$town/government/oversight-watch.sh" ]; then
    /bin/sh "$town/government/oversight-watch.sh" ||
        echo "Viche: watchdog cycle failed; investigate monitoring coverage" >&2
fi
# Independent Judiciary: evidence and adjudication, not executive delivery,
# proposing bills, or modifying its own measurement rules.
if [ -f "$town/government/branch-liveness.sh" ]; then
    /bin/sh "$town/government/branch-liveness.sh" judiciary ||
        echo "Viche: Judiciary liveness investigation required" >&2
fi
# Autonomous legislative Innovation Centre (not a fourth branch or voting seat).
# Its dispatch and recovery do not depend on the Clerk or parliamentary summons.
if [ -f "$town/government/innovation-centre-cycle.sh" ]; then
    /bin/sh "$town/government/innovation-centre-cycle.sh" ||
        echo "Viche: legislative Innovation Centre failed; investigate" >&2
fi
if [ -f "$town/government/branch-health.sh" ]; then
    /bin/sh "$town/government/branch-health.sh" ||
        echo "Viche: independent branch readiness incident recorded" >&2
fi
if [ -f "$town/government/judiciary-measurements.py" ]; then
    python3 "$town/government/judiciary-measurements.py" ||
        echo "Viche: Judiciary self-measurement unavailable" >&2
fi

# Government setup completed; not proof of delivery.
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/health
mkdir -p "$state"
date +%s > "$state/government-setup.last"
