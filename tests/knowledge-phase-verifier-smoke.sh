#!/bin/sh
# Smoke test: the production phase-gate record must FAIL CLOSED, all offices
# stay disabled, and the POSIX wrapper must work. No real sign-off is forged.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
town=$repo
ver=$town/government/knowledge-phase-verifier.py
rec=records/knowledge/phases/statistics-initial.json

[ -s "$ver" ]
[ -s "$town/$rec" ]
[ -s "$town/records/knowledge/PHASE-GATE-SCHEMA.md" ]
/bin/sh -n "$town/government/knowledge-phase-gate.sh"

# verify: non-zero and a hold disposition (draft, no Git-anchored review).
set +e
out=$(python3 "$ver" --town "$town" verify "$rec")
rc=$?
set -e
[ "$rc" -ne 0 ] || { echo 'phase verifier failed open' >&2; exit 1; }
printf '%s\n' "$out" | grep -q '"decision": "hold"'

# check: prints the same disposition but always exits 0.
out2=$(python3 "$ver" --town "$town" check "$rec")
printf '%s\n' "$out2" | grep -q '"decision": "hold"'

# audit: no dispatch ledger yet -> no violations, no new invocation after expiry.
audit=$(python3 "$ver" --town "$town" audit)
printf '%s\n' "$audit" | grep -q '"ok": true'
printf '%s\n' "$audit" | grep -q '"new_invocation_after_expiry": \[\]'

# Verify the legacy draft independently of the later Act34 activation record.
# Disabled activation and cross-office forgery are exercised in isolated
# knowledge-activation-binding-smoke fixtures, not by assuming live inactivity.
jq -e '.offices | keys == ["foresight","spying","statistics","strategy"]' "$town/records/knowledge/activation.json" >/dev/null

# Wrapper carries no authority but locates the verifier deterministically.
set +e
VICHE_TOWN_ROOT=$town /bin/sh "$town/government/knowledge-phase-gate.sh" verify "$rec" >/dev/null 2>&1
wrc=$?
set -e
[ "$wrc" -ne 0 ] || { echo 'wrapper failed open' >&2; exit 1; }

echo 'knowledge phase-gate verifier smoke: OK (fail-closed legacy draft)'
