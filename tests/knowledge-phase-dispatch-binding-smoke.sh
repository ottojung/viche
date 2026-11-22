#!/bin/sh
# Hermetic Act33 runtime gate; no live activation or agent state changed.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
t="$d/town"
mkdir -p "$t/government" "$t/records/knowledge/phases"
cp "$repo/government/knowledge-activation-verify.sh" "$t/government/"
cat > "$t/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22)
EOF
now=$(date +%s)
a="$t/records/knowledge/activation.json"
jq -n --argjson nb "$((now-5))" --argjson ex "$((now+3600))" '{
schema:"viche-knowledge-activation-v1",
offices:{statistics:{enabled:true,authorized_by:"act:32:statistics",not_before:$nb,expires_at:$ex}}
}' > "$a"
verify() { VICHE_TOWN_ROOT="$t" /bin/sh "$t/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; }
deny() { if verify; then echo "FAIL: $1" >&2; exit 1; fi; }
deny "bare enabled/authorized label"
jq '.offices.statistics.phase_gate_record="records/knowledge/phases/statistics-initial.json"' "$a" > "$d/new"
mv "$d/new" "$a"
deny "missing gate record"
r="$t/records/knowledge/phases/statistics-initial.json"
printf '%s\n' '{"schema":"viche-knowledge-phase-gate-v1","act":32,"office":"statistics","decision":"hold"}' > "$r"
printf '#!/bin/sh\nexit 0\n' > "$t/government/knowledge-phase-gate.sh"
deny "independent hold even when helper exits success"
jq '.decision="proceed" | .office="spying"' "$r" > "$d/new"
mv "$d/new" "$r"
deny "wrong-office replay"
jq '.office="statistics" | .act=31' "$r" > "$d/new"
mv "$d/new" "$r"
deny "wrong-Act replay"
jq '.act=32' "$r" > "$d/new"
mv "$d/new" "$r"
verify || { echo 'FAIL: structure + successful helper did not permit' >&2; exit 1; }
printf '#!/bin/sh\nexit 1\n' > "$t/government/knowledge-phase-gate.sh"
deny "independent actual verification failure"
jq '.offices.statistics.phase_gate_record="records/knowledge/phases/../other.json"' "$a" > "$d/new"
mv "$d/new" "$a"
deny "path traversal"
echo 'knowledge phase dispatch gate: correct structural binding and fail-closed independent review'
