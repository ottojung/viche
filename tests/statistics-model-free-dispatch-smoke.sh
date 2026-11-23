#!/bin/sh
# Founder changed design: deterministic-v1 NEVER authorizes the Statistics
# Bureau. A fixed report is a diagnostic input, not an agent/scientific office.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
t="$d/town"
mkdir -p "$t/government" "$t/records/knowledge"
cp "$repo/government/knowledge-activation-verify.sh" "$t/government/"
cat > "$t/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22)
EOF
now=$(date +%s)
jq -n --argjson nb "$((now-30))" --argjson ex "$((now+3600))" '{
 schema:"viche-knowledge-activation-v1",
 offices:{statistics:{enabled:true,authorized_by:"act:32:statistics",
 not_before:$nb,expires_at:$ex,trial_mode:"deterministic-v1"}}
}' > "$t/records/knowledge/activation.json"
# Give BOTH modes the same test-phase independently green result; this
# isolates the deterministic-v1 prohibition from generic missing phase data.
mkdir -p "$t/records/knowledge/phases"
cat > "$t/records/knowledge/phases/statistics-initial.json" <<'JSON'
{"schema":"viche-knowledge-phase-gate-v1","office":"statistics",
 "act":32,"decision":"proceed"}
JSON
cat > "$t/government/knowledge-phase-gate.sh" <<'STUB'
#!/bin/sh
[ "$1" = verify ] && [ "$2" = records/knowledge/phases/statistics-initial.json ]
STUB
jq '.offices.statistics.phase_gate_record="records/knowledge/phases/statistics-initial.json"'   "$t/records/knowledge/activation.json" > "$d/new"
mv "$d/new" "$t/records/knowledge/activation.json"
export VICHE_TOWN_ROOT="$t"
if /bin/sh "$t/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
 echo 'FAIL: deterministic diagnostic authorized Bureau even with a phase PROCEED' >&2
 exit 1
fi
jq '.offices.statistics.trial_mode="adaptive-v1"' "$t/records/knowledge/activation.json" > "$d/new"
mv "$d/new" "$t/records/knowledge/activation.json"
if ! /bin/sh "$t/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
 echo 'FAIL: phase-approved adaptive agent mode incorrectly rejected' >&2
 exit 1
fi
# The independently corroborated phase gate is still mandatory.
jq '.decision="hold"' "$t/records/knowledge/phases/statistics-initial.json" > "$d/new"
mv "$d/new" "$t/records/knowledge/phases/statistics-initial.json"
if /bin/sh "$t/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
 echo 'FAIL: adaptive mode bypassed the independent Judiciary HOLD' >&2
 exit 1
fi
! grep -q 'statistics-bounded-trial.py' "$repo/government/boot.sh"
! grep -q 'statistics-report.py' "$repo/government/boot.sh"
grep -q 'antonina agent run' "$repo/government/knowledge-office-cycle.sh"
echo 'Statistics Bureau requires an independent adaptive agent; no telemetry-only activation'
