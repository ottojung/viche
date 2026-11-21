#!/bin/sh
# The audit --prompt must stay under the kernel per-argument limit even when
# the deterministic incident evidence is very large. The full evidence is
# preserved in a durable file that the agent reads, not inlined into argv.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/town/government" "$d/state/oversight/random" "$d/seats/branches/judiciary" "$d/bin"
cp "$repo/government/audit-cycle.sh" "$d/town/government/audit-cycle.sh"
cp "$repo/government/agent-state.sh" "$d/town/government/agent-state.sh"
cp "$repo/government/AGENT-REPORTING-POLICY.md" "$d/town/government/AGENT-REPORTING-POLICY.md"
printf 'Charter\n' > "$d/charter"
printf 'observation\n' > "$d/state/oversight/observations.tsv"
printf 'incident\n' > "$d/state/oversight/incident.json"
cat > "$d/town/government/appointments.sh" <<'APPOINT'
#!/bin/sh
printf 'judicial-fixture-agent\n'
APPOINT
cat > "$d/town/government/audit-selection.py" <<'SAMPLE'
import json,os,pathlib
now=int(os.environ['VICHE_OVERSIGHT_NOW'])
r=pathlib.Path(os.environ['VICHE_STATE_ROOT'])/'oversight/random'
v={'at':now,'seed_after_snapshot':'b'*64,
   'cases':[{'case_id':'0123456789abcdef01'}]}
(r/'latest.json').write_text(json.dumps(v)+'\n')
print(json.dumps(v))
SAMPLE
# A large frozen incident report with a distinctive inline marker.
python3 - "$d/state/oversight/random/incident.json" <<'PY'
import json,sys
marker='E2BIG_INLINE_MARKER_9f3c'
obj={'at':1,'cases_total':464,
     'signals':[{'case_id':'x','blob':marker + 'z'*200000}]}
open(sys.argv[1],'w').write(json.dumps(obj))
PY
# Mock Antonina: emulate the E2BIG argv ceiling and detect leaked evidence.
cat > "$d/bin/antonina" <<'ANTONINA'
#!/bin/sh
case "$1 $2" in
 'agent status') printf '{"state":"idle"}\n' ;;
 'agent run')
    prompt=
    prev=
    for a in "$@"; do
      [ "$prev" = '--prompt' ] && prompt=$a
      prev=$a
    done
    plen=${#prompt}
    if [ "$plen" -gt 120000 ]; then
      echo "mock E2BIG: prompt length $plen exceeds argv budget" >&2
      exit 7
    fi
    case "$prompt" in
      *E2BIG_INLINE_MARKER_9f3c*)
        echo 'full incident evidence leaked inline into prompt' >&2
        exit 8 ;;
      *audit-evidence.txt*) : ;;
      *) echo 'prompt missing durable evidence pointer' >&2; exit 9 ;;
    esac
    printf '%s\n' "$plen" >> "$MOCK_PROMPT_SIZES"
    printf 'run\n' >> "$MOCK_RUNS" ;;
 *) echo "Unexpected Antonina: $*" >&2; exit 2 ;;
esac
ANTONINA
chmod +x "$d/town/government/appointments.sh" "$d/bin/antonina"
base=2000000000
export VICHE_STATE_ROOT="$d/state" VICHE_TOWN_ROOT="$d/town" \
 VICHE_SEATS_ROOT="$d/seats" VICHE_CONSTITUTION="$d/charter" \
 VICHE_OVERSIGHT_NOW="$base" VICHE_AUDIT_CHECKS=0 VICHE_AUDIT_SELECTION=1 \
 MOCK_RUNS="$d/runs" MOCK_PROMPT_SIZES="$d/sizes" PATH="$d/bin:$PATH"

/bin/sh "$d/town/government/audit-cycle.sh"

[ "$(wc -l < "$MOCK_RUNS")" -eq 1 ] || { echo 'audit dispatch did not launch' >&2; exit 1; }
# The bounded --prompt stays well below the ceiling.
[ "$(cat "$MOCK_PROMPT_SIZES")" -le 120000 ] || exit 1
# Full evidence is preserved durably, not dropped.
grep -q 'E2BIG_INLINE_MARKER_9f3c' "$d/state/oversight/audit-evidence.txt" ||
  { echo 'durable evidence file lost the incident report' >&2; exit 1; }
# The frozen sampled cohort is preserved too.
cycle=$(cat "$d/state/oversight/current-audit-cycle")
[ -s "$d/state/oversight/audit-selection-$cycle.json" ] ||
  { echo 'sampled cohort not preserved' >&2; exit 1; }
echo 'Audit prompt argv budget and durable evidence pointer passed'
