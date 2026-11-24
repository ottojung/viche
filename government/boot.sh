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
while IFS="$tab" read -r seat_id title focus; do
    [ -n "$seat_id" ] || continue
    case "$seat_id" in
        *[!0123456789abcdef]*|'') echo "Invalid seat ID: $seat_id" >&2; exit 1 ;;
    esac
    [ -n "$title" ] && [ -n "$focus" ] || {
        echo "Incomplete seat: $seat_id" >&2; exit 1;
    }
    printf '%s\n' "$seat_id" >> "$ids"
done < "$town/government/seats.tsv"

[ -s "$ids" ] || { echo "No parliamentary seats" >&2; exit 1; }
unique=$(sort -u "$ids" | wc -l)
total=$(wc -l < "$ids")
[ "$unique" -eq "$total" ] || { echo "Duplicate seat IDs" >&2; exit 1; }

while IFS="$tab" read -r seat_id title focus; do
    [ -n "$seat_id" ] || continue
    seat_dir=$seats/$seat_id
    if [ ! -f "$seat_dir/.git" ] && [ ! -d "$seat_dir/.git" ]; then
        if [ -d "$seat_dir" ] && [ -n "$(ls -A "$seat_dir")" ]; then
            echo "Refusing to replace seat directory: $seat_dir" >&2
            exit 1
        fi
        git -C "$town" worktree add --detach "$seat_dir" HEAD
    fi
    # All seats have durable, independently recoverable sessions; don't let a
    # failed provider continuation permanently remove a future voter.
    if [ -f "$town/government/seat-liveness.sh" ]; then
        /bin/sh "$town/government/seat-liveness.sh" "$seat_id" ||
            echo "Viche: seat $seat_id recovery failed" >&2
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
    # A whole-box inventory can take minutes. It has its own exclusive lock;
    # never block legislative, executive or judicial dispatch behind it.
    janitor_state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/janitor
    mkdir -p "$janitor_state"
    (
        /bin/sh "$town/government/janitor.sh" cycle ||
            echo "Viche: janitor cycle failed; see janitor action log" >&2
    ) >> "$janitor_state/boot-cycle.log" 2>&1 < /dev/null &
fi

# Founder directive 2026-11-16 (Act 30): obligations expire unless renewed with a
# reason; deadline-bound requests become "due"; Parliament sits once a day.
# Deterministic, no model call, none of it can block an office.
if [ -f "$town/government/obligation-expiry.py" ]; then
    python3 "$town/government/obligation-expiry.py" sweep > /dev/null ||
        echo "Viche: obligation expiry sweep failed" >&2
fi
if [ -f "$town/government/proceed-by-default.sh" ]; then
    /bin/sh "$town/government/proceed-by-default.sh" sweep "$town" ||
        echo "Viche: proceed-by-default sweep failed" >&2
fi
if [ -f "$town/government/daily-sitting.py" ]; then
    python3 "$town/government/daily-sitting.py" run ||
        echo "Viche: daily plenary convening failed" >&2
fi

# Act 31: the integration queue lands proposed work on main. It runs the test
# suite, so it is backgrounded under its own lock and never blocks an office.
if grep -Eq '^## Act [0-9]+ — Integration Queue Act ' "$town/government/LAWS.md" &&
   [ -f "$town/government/integrator.py" ]; then
    integration_state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/delivery/integrator
    mkdir -p "$integration_state"
    (
        flock -n 9 || exit 0
        timeout 7200 nice python3 "$town/government/integrator.py" run ||
            echo "Viche: integration queue pass failed" >&2
    ) 9>"$integration_state/run.lock" >> "$integration_state/run.log" 2>&1 < /dev/null &
fi

# Non-parliamentary work must not be on the constitutional sitting critical
# path. A failed/hung Executive, Judiciary, Innovation, Economy or collector
# must not keep summoned voting seats from receiving their prompts.
# Each task has a separate nonblocking lock, deadline and isolated log.
nonblocking_office() {
    key=$1
    deadline=$2
    shift 2
    dir=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/boot-independent
    mkdir -p "$dir" || { echo "Viche: cannot create independent task state for $key" >&2; return 0; }
    (
        flock -n 9 || exit 0
        timeout "$deadline" "$@" || echo "Viche: independent $key task failed or timed out (deadline $deadline seconds)" >&2
    ) 9>"$dir/$key.lock" >>"$dir/$key.log" 2>&1 < /dev/null &
}

# Independent Executive: no parliamentary summons required.
if [ -f "$town/government/branch-liveness.sh" ]; then
    nonblocking_office executive 300 /bin/sh "$town/government/branch-liveness.sh" executive
fi

# Task-independent lifecycle hooks. One failed mission cannot block the Town.
if [ -s "$town/government/mission-cycle.sh" ]; then
    nonblocking_office missions 180 /bin/sh "$town/government/mission-cycle.sh"
fi

# The innovation office is an Executive unit ONLY after parliamentary enactment.
if grep -Eq '^## Act [0-9]+ — Executive Innovation Office Act \((re-)?enacted ' "$town/government/LAWS.md"; then
    nonblocking_office executive-innovation 300 /bin/sh "$town/government/executive-innovation-cycle.sh"
fi

# The Ministry of Economy is an Executive unit ONLY after enactment of Act 29. Its
# funding refresh is deterministic and backgrounded; its agent is gated.
if grep -Eq '^## Act [0-9]+ — Ministry of Economy Act ' "$town/government/LAWS.md"; then
    if [ -f "$town/government/executive-economy-cycle.sh" ]; then
        nonblocking_office economy 300 /bin/sh "$town/government/executive-economy-cycle.sh"
    fi
fi

# Source-code deployment alone does not create an institution. Parliament must
# enact the Institutional Knowledge Act first. Offices run under independent
# locks so they cannot block Parliament or Judiciary or each other.
if grep -Eq '^## Act [0-9]+ — Institutional Knowledge and Communications Act \(enacted ' "$town/government/LAWS.md" &&
   [ -s "$town/government/knowledge-office-cycle.sh" ]; then
    # Act 32 H: after a crash or box restart, reconcile in-flight reservations
    # before any new dispatch. Deterministic, bounded and fail-closed.
    if [ -s "$town/government/knowledge-budget.sh" ]; then
        /bin/sh "$town/government/knowledge-budget.sh" reconcile ||
            echo "Viche: knowledge budget reconciliation failed" >&2
    fi
    knowledge_root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/knowledge/offices
    for office in statistics foresight strategy spying; do
        # Same fail-closed verifier as appointments and the office cycle: a
        # forged, wrong-Act, wrong-office or expired activation dispatches nothing.
        /bin/sh "$town/government/knowledge-activation-verify.sh" "$office" || continue
        mkdir -p "$knowledge_root/$office"
        (
            flock -n 9 || exit 0
            timeout 900 /bin/sh "$town/government/knowledge-office-cycle.sh" "$office" ||
                echo "Viche: $office knowledge office failed; see its log" >&2
        ) 9>"$knowledge_root/$office/cycle.lock" >> "$knowledge_root/$office/cycle.log" 2>&1 < /dev/null &
    done
fi

# The Statistics Bureau is an adaptive, staffed scientific office; its agent
# alone selects current questions under the independently reviewed budget and
# phase gates above. Legacy deterministic snapshots are diagnostic inputs,
# never an alternative office and NEVER evidence of institutional activation.
# Do not auto-publish a fixed metrics bundle as a surrogate for its work.

# Act 34: first-use observations, not efficacy certification. No model is
# invoked. Judiciary reviews actual operation within 48 hours, and a failed
# collector never obstructs Legislature, Judiciary or Executive.
# Inert unless Act 34 ENACTED and an Executive Git-reviewed permit
# explicitly enables this office under the same Economy resource budget.
if grep -Eq '^## Act 34 — Minimum Viable Knowledge Institutions Pilot Act \(enacted ' \
     "$town/government/LAWS.md" &&
   [ -s "$town/government/knowledge-minimal-pilot.py" ]; then
    min_root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/knowledge/pilot
    for office in statistics foresight strategy spying; do
        jq -e --arg office "$office" '
          .offices[$office].enabled == true and
          .offices[$office].trial_mode == "deterministic-v1" and
          .offices[$office].authorized_by == ("act:34:"+$office)
        ' "$town/records/knowledge/activation.json" >/dev/null 2>&1 || continue
        mkdir -p "$min_root/$office"
        (
            flock -n 9 || exit 0
            timeout -k 2 38 python3 "$town/government/knowledge-minimal-pilot.py" \
                "$office" --run ||
              echo "Viche Act34 $office: model-free sample held; core town continues" >&2
        ) 9>"$min_root/$office/lock" >>"$min_root/$office/log" 2>&1 < /dev/null &
    done
fi

# Act 32 PUBLIC Post archive redaction scan: independent, bounded and
# strictly nonblocking. Scanner failures are reported without silencing
# constitutional, legislative or judicial duties.
if grep -Eq '^## Act [0-9]+ — Institutional Knowledge and Communications Act \(enacted ' "$town/government/LAWS.md" &&
   [ -f "$town/government/post.py" ]; then
    guard_state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/post
    mkdir -p "$guard_state"
    (
        flock -n 9 || exit 0
        now=$(date +%s)
        last=0
        [ ! -s "$guard_state/last-archive-scan" ] ||
            last=$(cat "$guard_state/last-archive-scan")
        case "$last" in ''|*[!0-9]*) last=0;; esac
        [ $((now-last)) -ge 21600 ] || exit 0
        if timeout 90 python3 "$town/government/post.py" archive-scan; then
            printf '%s\n' "$now" > "$guard_state/last-archive-scan"
        else
            echo "Viche Post: public archive scan failed; retry next boot" >&2
        fi
    ) 9>"$guard_state/guard.lock" >> "$guard_state/guard.log" 2>&1 < /dev/null &
fi

# Deterministic oversight continues even when every AI session is unavailable.
# Failure of telemetry/auditing must not prevent unrelated reconciliation.
if [ -f "$town/government/oversight-watch.sh" ]; then
    nonblocking_office oversight 180 /bin/sh "$town/government/oversight-watch.sh"
fi
# Independent feedback never holds up legislature, executive, or judiciary.
# Serialize collectors, bound their runtime, and timestamp their evidence.
if [ -f "$town/government/outcome-metrics.py" ]; then
    metrics_state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/institutional-outcomes
    mkdir -p "$metrics_state"
    (
        flock -n 9 || exit 0
        timeout 150 python3 "$town/government/outcome-metrics.py" ||
            echo "Viche: outcome feedback unavailable; do not infer success" >&2
    ) 9>"$metrics_state/collector.lock"       >>"$metrics_state/collector.log" 2>&1 < /dev/null &
fi

# Independent Judiciary: evidence and adjudication, not executive delivery,
# proposing bills, or modifying its own measurement rules.
if [ -f "$town/government/branch-liveness.sh" ]; then
    nonblocking_office judiciary 300 /bin/sh "$town/government/branch-liveness.sh" judiciary
fi
# Run the historic legislative Centre ONLY until lawful transfer.
if ! grep -Eq '^## Act [0-9]+ — Executive Innovation Office Act \((re-)?enacted ' "$town/government/LAWS.md"; then
    if [ -f "$town/government/innovation-centre-cycle.sh" ]; then
        nonblocking_office innovation-centre 300 /bin/sh "$town/government/innovation-centre-cycle.sh"
    fi
fi
if [ -f "$town/government/branch-health.sh" ]; then
    nonblocking_office branch-health 180 /bin/sh "$town/government/branch-health.sh"
fi
# Durable independent case routing persists even if every branch model fails.
if [ -f "$town/government/institutional-cases.py" ]; then
    nonblocking_office institutional-cases 180 python3 "$town/government/institutional-cases.py" reconcile
fi
# Act 18 §7: the Executive maintains the generated board-trail index; refresh it
# each measurement window (throttled, non-fatal) so the Founder-visible status
# map cannot silently go stale. Runs before the §5 lens that consumes it.
if [ -f "$town/government/board-trail-refresh.sh" ]; then
    nonblocking_office board-trail 180 /bin/sh "$town/government/board-trail-refresh.sh"
fi
if [ -f "$town/government/judiciary-measurements.py" ]; then
    nonblocking_office judiciary-measurements 180 python3 "$town/government/judiciary-measurements.py"
fi

# Founder directive 2026-11-16: ten-line daily digest on Town Hall, once per
# UTC day after VICHE_DIGEST_HOUR. No model call; serialized; never blocks.
if [ -f "$town/government/daily-digest.py" ] && [ -n "${VICHE_TOWNHALL_ID:-}" ]; then
    digest_state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/digest
    mkdir -p "$digest_state"
    (
        flock -n 9 || exit 0
        timeout 600 nice python3 "$town/government/daily-digest.py" --post ||
            echo "Viche: daily digest failed; retried next cycle" >&2
    ) 9>"$digest_state/digest.lock" >>"$digest_state/digest.log" 2>&1 < /dev/null &
fi

# Government setup completed; not proof of delivery.
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/health
mkdir -p "$state"
date +%s > "$state/government-setup.last"
