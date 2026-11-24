#!/bin/sh
# Pre-enactment certified permits must fail closed; legacy permits still use
# the unchanged Act34 gate. This fixture never creates approval or certification.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town=$d/town
mkdir -p "$town/government" "$town/records/knowledge/permits"
cp "$repo/government/knowledge-activation-verify.sh" "$town/government/"
cp "$repo/government/knowledge-act34-gate.py" "$town/government/"
cp "$repo/government/knowledge-act34-certified-gate.py" "$town/government/"
cat > "$town/government/LAWS.md" <<'EOF'
## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act (enacted 2026-11-23)
EOF
cat > "$town/records/knowledge/activation.json" <<'EOF'
{"offices":{"statistics":{"permit_ref":"records/knowledge/permits/statistics.json"}}}
EOF
cat > "$town/records/knowledge/permits/statistics.json" <<'EOF'
{"control_certification":{"certification_id":"act34-common-zero-billed-controls-v1"}}
EOF
if VICHE_TOWN_ROOT="$town" /bin/sh "$town/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
  echo 'FAIL: certified path accepted before Act 35 enactment' >&2; exit 1
fi
echo 'PASS: certified permit refused before enactment'
# A permit without the opt-in key reaches precisely the old verifier invocation.
cat > "$town/records/knowledge/permits/statistics.json" <<'EOF'
{}
EOF
cat > "$town/government/knowledge-act34-gate.py" <<'EOF'
import sys
assert sys.argv[1] == 'statistics'
assert sys.argv[2].endswith('/town')
EOF
chmod +x "$town/government/knowledge-act34-gate.py"
if ! VICHE_TOWN_ROOT="$town" /bin/sh "$town/government/knowledge-activation-verify.sh" statistics >/dev/null 2>&1; then
  echo 'FAIL: legacy route changed' >&2; exit 1
fi
echo 'PASS: legacy permit remains on prior gate route'
