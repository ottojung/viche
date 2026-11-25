#!/bin/sh
# Hermetic certified Act34 parity-v3 verifier smoke suite.
# Every town, board, appointment and codification below is synthetic and lives
# in a temp directory. No live law, permit, attestation, board action or
# activation is touched. Mock antonina is read-only, as in the legacy smoke.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/bin"
FIXTURE_NOW=$(date +%s)
export ACT34_FIXTURE_NOW="$FIXTURE_NOW"

cat > "$d/bin/antonina" <<'EOF'
#!/bin/sh
set -eu
case "$1 $2" in
  'board show')
    shift 2
    [ "$1" = --id ] || exit 2
    cat "$VICHE_STATE_ROOT/board/$2.json"
    ;;
  'agent status')
    shift 2
    [ "$1" = --id ] || exit 2
    printf '{"id":"%s","state":"idle"}\n' "$2"
    ;;
  *) exit 2;;
esac
EOF
chmod +x "$d/bin/antonina"

# The legacy gate, its test, wrapper and eight bound controls must be untouched.
legacy_files='government/knowledge-act34-gate.py tests/knowledge-act34-adaptive-smoke.sh government/knowledge-free-dispatch.sh tests/knowledge-free-dispatch-smoke.sh government/knowledge-practical-bounds.py government/knowledge-zero-billed-policy.json government/knowledge-zero-billed.py government/knowledge-office-cycle.sh records/economy/evidence/2026-11-24-provider-models.json records/economy/evidence/2026-11-24-go-provider-models.json'
(cd "$repo" && sha256sum $legacy_files) > "$d/legacy-before"

check_case() {
  variant=$1; expect=$2; marker=$3
  case_dir="$d/case-$variant"
  mkdir -p "$case_dir"
  python3 "$repo/tests/knowledge-act34-parity-v3-fixture.py" \
    "$repo" "$case_dir/town" "$case_dir/state" "$variant" > "$case_dir/facts.json"
  for office in statistics foresight strategy spying; do
    log="$case_dir/$office.log"
    if VICHE_TOWN_ROOT="$case_dir/town" VICHE_STATE_ROOT="$case_dir/state" \
       PATH="$d/bin:$PATH" XDG_CONFIG_HOME="$case_dir/global" \
       /bin/sh "$case_dir/town/government/knowledge-activation-verify.sh" "$office" \
       > "$log" 2>&1; then rc=0; else rc=$?; fi
    if [ "$expect" = pass ]; then
      [ "$rc" -eq 0 ] || { echo "FAIL $variant/$office expected PASS: $(cat "$log")" >&2; exit 1; }
    else
      [ "$rc" -ne 0 ] || { echo "FAIL $variant/$office expected fail-closed" >&2; exit 1; }
      if [ -n "$marker" ] && ! grep -q "$marker" "$log"; then
        echo "FAIL $variant/$office wrong refusal reason: $(cat "$log")" >&2; exit 1
      fi
    fi
  done
  echo "PASS: $variant ($expect)"
}

# Before any genuine codification, even a fully formed certified permit dies.
check_case pre-enactment fail ''
# All four offices, independent board/appointment corroboration and both snapshots.
check_case valid pass ''
check_case canonical-evidence pass ''
check_case conflicting-evidence fail 'conflicting shared certification evidence'
# One comment-only control repair: one Economy refresh, no permit byte changes.
check_case repair pass ''
python3 - "$d/case-valid/facts.json" "$d/case-repair/facts.json" <<'PY'
import json,sys
a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2]))
assert a['permits']==b['permits'], 'permit SHA256 changed across comment-only control refresh'
assert a['legacy_evidence']==b['legacy_evidence'], 'legacy Economy evidence was modified'
print('PASS: four permit SHA256 values and legacy Economy evidence unchanged across one refresh')
PY
# Policy binding: a committed policy byte change and a rebind attempt both die.
check_case policy-bytes fail 'control'
check_case policy-digest fail 'policy digest'
# Certification authenticity, freshness and identity.
check_case missing-cert fail ''
check_case stale-cert fail 'validity window'
check_case wrong-cert-schema fail 'validity window'
check_case forged-board fail 'unverified economy'
# Authority and old safeguards are not relaxed by the amendment.
check_case wrong-identity fail 'wrong-identity'
check_case wrong-signer fail 'budget/authority'
check_case wrong-caps fail 'budget/authority'
check_case wrong-per-run-caps fail 'budget/authority'
check_case wrong-host fail 'budget/authority'
check_case wrong-mission fail 'budget/authority'
check_case hold fail 'HOLD'
check_case hold-local-missing fail 'committed Judiciary disposition or attestation missing'
check_case hold-committed-deletion fail 'same-permit Judiciary disposition was deleted'
check_case no-review-48h fail '48h'

(cd "$repo" && /bin/sh tests/knowledge-act34-adaptive-smoke.sh)
(cd "$repo" && sha256sum $legacy_files) > "$d/legacy-after"
cmp "$d/legacy-before" "$d/legacy-after" || { echo 'FAIL: legacy bound bytes changed' >&2; exit 1; }
echo 'PASS: legacy gate, test, wrapper and eight controls byte-identical'
echo 'PASS: certified parity-v3 hermetic suite'
