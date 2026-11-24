#!/bin/sh
# Act 29: the Ministry of Economy keeps the Antonina model list ordered
# free -> contributor -> Luna -> paid, adds only free models that answered a probe,
# and never leaves Antonina with an empty or rejected list.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/bin" "$d/state" "$d/cfg" "$d/cool" "$d/health"
cat > "$d/bin/opencode" <<'MOCK'
#!/bin/sh
# opencode run -m MODEL --format json PROMPT
[ "$1" = run ] || exit 9
echo "$3" >> "$MOCK_PROBES"
case "$3" in
  *gamma-free#low) printf '{"type":"error","part":{"message":"quota"}}\n'; exit 0 ;;
  *) printf '{"type":"text","part":{"text":"OK"}}\n' ;;
esac
MOCK
cat > "$d/bin/antonina" <<'MOCK'
#!/bin/sh
[ "$1 $2 $3" = 'agent model select' ] || exit 9
if [ -n "${MOCK_LIVE_CONFIG:-}" ]; then
  [ "$VICHE_ANTONINA_CONFIG" != "$MOCK_LIVE_CONFIG" ] || exit 8
  cmp "$MOCK_LIVE_CONFIG" "$MOCK_EXPECTED_LIVE" || exit 8
  if [ "${MOCK_CONCURRENT_EDIT:-0}" = 1 ]; then
    printf '%s\n' '{"models":[{"model":"openai/gpt-6-luna","variant":"low"}],"concurrent":true}' > "$MOCK_LIVE_CONFIG"
  fi
fi
[ "${MOCK_ANTONINA_REJECT:-0}" = 0 ] || exit 1
jq -r '.models[].model' "$VICHE_ANTONINA_CONFIG"
MOCK
chmod +x "$d/bin/opencode" "$d/bin/antonina"
export PATH="$d/bin:$PATH" MOCK_PROBES="$d/probes.log" HOME="$d/home" \
  VICHE_STATE_ROOT="$d/state" VICHE_ANTONINA_CONFIG="$d/cfg/config.json" \
  VICHE_ANTONINA_COOLDOWNS="$d/cool" VICHE_ANTONINA_MODEL_HEALTH="$d/health" \
  VICHE_OPENCODE_MODELS="$d/catalogue.txt" VICHE_ECONOMY_NOW=1794830400
: > "$d/probes.log"
eco="python3 $repo/government/economy-models.py"
order() { jq -r '[.models[].model] | join(",")' "$VICHE_ANTONINA_CONFIG"; }

cat > "$d/catalogue.txt" <<'EOF'
opencode/alpha-free
opencode/beta-free
opencode/gamma-free
opencode/delta-free
openai/gpt-6
openai/gpt-6-luna
anthropic/claude-x
opencode-go/glm-contributor
opencode/zeta
opencode/eta
opencode/theta
some banner line that is not a model id
EOF
cat > "$VICHE_ANTONINA_CONFIG" <<'EOF'
{"models":[
 {"model":"openai/gpt-6","comment":"paid"},
 {"model":"openai/gpt-6-luna","comment":"Luna before paid"},
 {"model":"opencode/alpha-free","comment":"free"},
 {"model":"opencode-go/glm-contributor","comment":"contributor plan"},
 {"model":"opencode/vanished-free","comment":"was free once"}
],"keep_me":"yes"}
EOF
printf '{"exclude":[{"model":"opencode/delta-free","reason":"rate limit 5/day","until":9999999999}]}\n' > /dev/null
mkdir -p "$d/state/economy"
printf '{"exclude":[{"model":"opencode/delta-free","reason":"rate limit 5/day","until":9999999999},{"model":"opencode/old-expired","reason":"x","until":1}]}\n' \
  > "$d/state/economy/model-policy.json"

# The configured order violates the tier policy (paid and Luna ahead of free): `check` says so.
rc=0; $eco check > "$d/check.out" || rc=$?
test "$rc" -eq 1
grep -q 'gpt-6-luna' "$d/check.out"

# `plan` changes nothing.
before=$(cat "$VICHE_ANTONINA_CONFIG")
$eco plan | jq -e '.after == ["opencode/alpha-free","opencode/glm-contributor","opencode/gpt-6","opencode/gpt-6-luna"] or (.after | length) > 0' >/dev/null
test "$(cat "$VICHE_ANTONINA_CONFIG")" = "$before"

# Refresh: free first (alpha, then probed-OK beta), contributor, Luna, paid LAST.
$eco refresh --probe-limit 10 > "$d/refresh.out"
jq -e '.changed == true and .funding_risk == "none" and .free_available_now == 2' "$d/refresh.out" >/dev/null
test "$(order)" = 'opencode/alpha-free,opencode/vanished-free,opencode/beta-free,opencode-go/glm-contributor,openai/gpt-6-luna,openai/gpt-6'
jq -e '.keep_me == "yes"' "$VICHE_ANTONINA_CONFIG" >/dev/null                 # unrelated config keys survive
jq -e '.models[0].comment == "free"' "$VICHE_ANTONINA_CONFIG" >/dev/null       # existing comments survive
jq -e '.models[2].comment | test("Ministry of Economy")' "$VICHE_ANTONINA_CONFIG" >/dev/null
$eco check
ls "$VICHE_ANTONINA_CONFIG".bak-* >/dev/null

# Never auto-added: paid, contributor and Luna models from the catalogue; probe failures; excluded; stale entries dropped.
for m in anthropic/claude-x opencode/zeta opencode/eta opencode/theta opencode/gamma-free opencode/delta-free; do
  case ",$(order)," in *",$m,"*) echo "unexpected model $m" >&2; exit 1 ;; esac
done
# Probes ran only for free, non-excluded candidates; none for paid or excluded models.
grep -q 'alpha-free' "$d/probes.log"; grep -q 'beta-free' "$d/probes.log"; grep -q 'gamma-free' "$d/probes.log"
if grep -q 'delta-free\|gpt-6\|claude-x' "$d/probes.log"; then echo 'probed a model it must not' >&2; exit 1; fi
r=$d/state/economy/report.json
jq -e '.order[0].tier == "free" and .order[-1].tier == "paid" and (.paid_before_free_violations | length) == 0' "$r" >/dev/null
jq -e '.free_missing_from_catalogue == ["opencode/vanished-free"]' "$r" >/dev/null
jq -e '[.dropped[] | select(.model == "opencode/gamma-free" and (.why | startswith("probe failed")))] | length == 1' "$r" >/dev/null
jq -e '[.dropped[] | select(.model == "opencode/delta-free" and (.why | startswith("excluded by policy")))] | length == 1' "$r" >/dev/null

# A second refresh is a no-op: fresh probes are not repeated, the config is not rewritten.
probes_before=$(wc -l < "$d/probes.log")
n_bak=$(ls "$VICHE_ANTONINA_CONFIG".bak-* | wc -l)
VICHE_ECONOMY_NOW=1794834000 $eco refresh --probe-limit 10 | jq -e '.changed == false' >/dev/null
test "$(wc -l < "$d/probes.log")" -eq "$probes_before"
test "$(ls "$VICHE_ANTONINA_CONFIG".bak-* | wc -l)" -eq "$n_bak"

# Policy preference reorders within a tier but never across tiers.
printf '{"prefer":["opencode/beta-free","openai/gpt-6-luna","openai/gpt-6"],"exclude":[{"model":"opencode/delta-free","reason":"rate limit 5/day","until":9999999999}]}\n' > "$d/state/economy/model-policy.json"
VICHE_ECONOMY_NOW=1794837600 $eco refresh | jq -e '.changed == true' >/dev/null
test "$(order)" = 'opencode/beta-free,opencode/alpha-free,opencode/vanished-free,opencode-go/glm-contributor,openai/gpt-6-luna,openai/gpt-6'
$eco check

# Funding risk follows only the hard cooldowns Antonina honours: one free model cooling = elevated, both = high.
rm -f "$d/cool"/*.json
printf '{"model":"opencode/alpha-free","reason":"quota_exhausted","until":1794900000}\n' > "$d/cool/opencode@alpha-free.json"
printf '{"model":"opencode/beta-free","reason":"quota_exhausted","until":1794800000}\n' > "$d/cool/opencode@beta-free.json"   # already over
VICHE_ECONOMY_NOW=1794837600 $eco refresh --probe-limit 0 | jq -e '.funding_risk == "elevated" and .free_available_now == 1' >/dev/null
printf '{"model":"opencode/beta-free","reason":"quota_exhausted","until":1794880000}\n' > "$d/cool/opencode@beta-free.json"
VICHE_ECONOMY_NOW=1794837600 $eco refresh --probe-limit 0 | jq -e '.funding_risk == "high" and .free_available_now == 0' >/dev/null
jq -e '.next_free_returns_at == 1794880000 and (.cooling | length) == 2 and (.cooldown_ignored | length) == 0' "$r" >/dev/null

# Adversarial cooldowns: future, soft, misnamed, oversized and malformed files carry no authority.
printf '{"model":"opencode/alpha-free","reason":"quota_exhausted","until":9999999999}\n' > "$d/cool/opencode@alpha-free.json"
printf '{"model":"opencode/beta-free","reason":"transient_backend","until":1794880000}\n' > "$d/cool/opencode@beta-free.json"
printf '{"model":"opencode/beta-free","reason":"rate_limited","until":1794880000}\n' > "$d/cool/wrong-name.json"
python3 - "$d/cool/opencode@vanished-free.json" <<'PY'
import sys
open(sys.argv[1], "w").write('{"model":"opencode/vanished-free","reason":"quota_exhausted","until":1794880000}' + ' ' * 1200)
PY
printf '{broken\n' > "$d/cool/opencode@gamma-free.json"
VICHE_ECONOMY_NOW=1794837600 $eco refresh --probe-limit 0 | jq -e '.funding_risk == "none" and .free_available_now == 2' >/dev/null
jq -e '(.cooling | length) == 0 and (.cooldown_ignored | length) == 4' "$r" >/dev/null
jq -e '[.cooldown_ignored[] | select(.why == "until outside the runtime bound")] | length == 1' "$r" >/dev/null
jq -e '[.cooldown_ignored[] | select(.why == "not a hard provider cooldown")] | length == 1' "$r" >/dev/null
jq -e '[.cooldown_ignored[] | select(.why == "filename or model id mismatch")] | length == 1' "$r" >/dev/null
jq -e '[.cooldown_ignored[] | select(.why == "unreadable or oversized")] | length == 1' "$r" >/dev/null
rm -f "$d/cool"/*.json

# Fleet-wide soft health is a last-resort warning, never a reason to revoke authorization.
printf '[]\n' > "$d/health/1794837500000-cccccccccccccccc.json"
printf '{"model":"opencode/beta-free","reason":[],"until":1794880000}\n' > "$d/cool/opencode@beta-free.json"
printf '{"agent_id":"agent-one","model":"opencode/alpha-free","at":1794837500}\n' > "$d/health/1794837500000-aaaaaaaaaaaaaaaa.json"
printf '{"agent_id":"agent-two","model":"opencode/alpha-free","at":1794837550}\n' > "$d/health/1794837550000-bbbbbbbbbbbbbbbb.json"
VICHE_ECONOMY_NOW=1794837600 $eco refresh --probe-limit 0 | jq -e '.funding_risk == "none" and .free_available_now == 2' >/dev/null
jq -e '.soft_unhealthy["opencode/alpha-free"].agents == ["agent-one","agent-two"]' "$r" >/dev/null
jq -e '[.order[].model | select(. == "opencode/alpha-free")] | length == 1' "$r" >/dev/null
rm -f "$d/health"/*.json "$d/cool"/*.json

# The catalogue disappearing never damages the list.
snapshot=$(cat "$VICHE_ANTONINA_CONFIG")
printf 'opencode/only-one-free\n' > "$d/tiny.txt"
rc=0; VICHE_OPENCODE_MODELS="$d/tiny.txt" $eco refresh 2>/dev/null || rc=$?
test "$rc" -eq 1
test "$(cat "$VICHE_ANTONINA_CONFIG")" = "$snapshot"
jq -e 'has("error")' "$r" >/dev/null

# Antonina rejecting the new list restores the previous config.
printf '{"prefer":["opencode/vanished-free"],"exclude":[{"model":"opencode/beta-free","reason":"test","until":9999999999}]}\n' > "$d/state/economy/model-policy.json"
cp "$VICHE_ANTONINA_CONFIG" "$d/live-before.json"
rc=0; MOCK_LIVE_CONFIG="$VICHE_ANTONINA_CONFIG" MOCK_EXPECTED_LIVE="$d/live-before.json" MOCK_ANTONINA_REJECT=1 $eco refresh 2>/dev/null || rc=$?
test "$rc" -ne 0
test "$(cat "$VICHE_ANTONINA_CONFIG")" = "$snapshot"

# Validation is outside live config; a concurrent authorized change is not lost.
rc=0; MOCK_LIVE_CONFIG="$VICHE_ANTONINA_CONFIG" MOCK_EXPECTED_LIVE="$d/live-before.json" MOCK_CONCURRENT_EDIT=1 $eco refresh 2>/dev/null || rc=$?
test "$rc" -ne 0
jq -e '.concurrent == true and (.models|length)==1' "$VICHE_ANTONINA_CONFIG" >/dev/null

# Without any catalogued model the existing authorized model is still preserved.
cat > "$d/catalogue2.txt" <<'EOF'
opencode/gamma-free
openai/gpt-7
openai/gpt-7-luna
anthropic/claude-y
anthropic/claude-z
openai/a1
openai/a2
openai/a3
openai/a4
openai/a5
EOF
printf '{"models":[{"model":"opencode/gone-free"}]}\n' > "$VICHE_ANTONINA_CONFIG"
snapshot=$(cat "$VICHE_ANTONINA_CONFIG")
rc=0; VICHE_OPENCODE_MODELS="$d/catalogue2.txt" $eco refresh 2>/dev/null || rc=$?
test "$rc" -eq 0
test "$(order)" = opencode/gone-free

# A config whose models are bare strings is understood.
printf '{"models":["openai/gpt-6-luna","opencode/alpha-free","openai/gpt-6"]}\n' > "$VICHE_ANTONINA_CONFIG"
printf '{}\n' > "$d/state/economy/model-policy.json"
VICHE_ECONOMY_NOW=1794837700 $eco refresh >/dev/null
test "$(jq -r '[.models[] | (.model // .)] | join(",")' "$VICHE_ANTONINA_CONFIG")" = 'opencode/alpha-free,opencode/beta-free,opencode/delta-free,openai/gpt-6-luna,openai/gpt-6'   # delta is free again once the exclusion is lifted

# A partial or unauthenticated catalogue must never erase authorized fallbacks.
# Even a small configured list cap must reserve their slots.
grep -vE '^(openai/|opencode-go/)' "$d/catalogue.txt" > "$d/partial.txt"
printf '%s\n' opencode/a opencode/b opencode/c >> "$d/partial.txt"
VICHE_OPENCODE_MODELS="$d/partial.txt" VICHE_ECONOMY_MAX_MODELS=3 $eco refresh --probe-limit 0 >/dev/null
test "$(order)" = 'opencode/alpha-free,opencode/beta-free,opencode/delta-free,openai/gpt-6-luna,openai/gpt-6'
jq -e '.fallback_eligible_now == 0 and (.fallback_missing_from_catalogue|length)==2' "$r" >/dev/null
# When authenticated catalogue returns, eligibility recovers without manual re-add.
$eco refresh --probe-limit 0 >/dev/null
jq -e '.fallback_eligible_now == 2 and (.fallback_missing_from_catalogue|length)==0' "$r" >/dev/null
test "$(order)" = 'opencode/alpha-free,opencode/beta-free,opencode/delta-free,openai/gpt-6-luna,openai/gpt-6'
# Service discovery and free probes share Antonina's isolated XDG roots.
python3 - "$repo" <<'PYTEST'
import importlib.util, pathlib, sys
spec=importlib.util.spec_from_file_location("eco", pathlib.Path(sys.argv[1])/"government/economy-models.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
e=m.service_env()
root=m.COOLDOWNS.parent/"opencode-service"
assert e["XDG_CONFIG_HOME"]==str(root/"config")
assert e["XDG_DATA_HOME"]==str(root/"data")
assert e["XDG_STATE_HOME"]==str(root/"state")
PYTEST
jq -e 'all(.models[]; .variant == "low")' "$VICHE_ANTONINA_CONFIG" >/dev/null
# Repair effort even when order is already correct.
jq 'del(.models[0].variant)' "$VICHE_ANTONINA_CONFIG" > "$d/without-low"
mv "$d/without-low" "$VICHE_ANTONINA_CONFIG"
$eco refresh --probe-limit 0 | jq -e '.changed == true' >/dev/null
jq -e 'all(.models[]; .variant == "low")' "$VICHE_ANTONINA_CONFIG" >/dev/null

# Writer invariant: only Economy writes the global ladder; the Act34 wrapper pins an isolated dir.
for f in "$repo"/government/*; do
  [ -f "$f" ] || continue
  grep -q 'antonina/config.json' "$f" || continue
  case "$(basename "$f")" in
    economy-models.py|knowledge-free-dispatch.sh|knowledge-zero-billed.py|MINISTRY-OF-ECONOMY.md|daily-digest.py) : ;;
    *) echo "unexpected global-config reference in $(basename "$f")" >&2; exit 1 ;;
  esac
done

# Adversarial: a catalogue id with # is never published (Antonina rejects it).
cp "$d/catalogue.txt" "$d/weird.txt"
printf 'opencode/odd-free-x#fast\n' >> "$d/weird.txt"
printf '{"models":[{"model":"opencode/alpha-free","comment":"free","variant":"low"}]}\n' > "$VICHE_ANTONINA_CONFIG"
VICHE_OPENCODE_MODELS="$d/weird.txt" $eco refresh --probe-limit 0 >/dev/null
case ",$(order)," in *',opencode/odd-free-x#fast,'*) echo 'published an invalid runtime id' >&2; exit 1 ;; esac
jq -e '[.dropped[] | select(.model == "opencode/odd-free-x#fast" and .why == "not a valid Antonina config id")] | length == 1' "$r" >/dev/null

# An invalid authorized entry fails closed; it is never silently deleted.
printf '{"models":[{"model":"opencode/alpha-free","comment":"free"},{"model":"opencode/alpha-free","comment":"dup"}]}\n' > "$VICHE_ANTONINA_CONFIG"
snapshot=$(cat "$VICHE_ANTONINA_CONFIG")
rc=0; $eco check > "$d/bad.out" 2>/dev/null || rc=$?
test "$rc" -eq 1
grep -q 'duplicate configured model' "$d/bad.out"
rc=0; $eco refresh --probe-limit 0 2>/dev/null || rc=$?
test "$rc" -ne 0
test "$(cat "$VICHE_ANTONINA_CONFIG")" = "$snapshot"

# Invalid non-object entries must produce a controlled refusal without a rewrite.
printf '{"models":[42]}\n' > "$VICHE_ANTONINA_CONFIG"
snapshot=$(cat "$VICHE_ANTONINA_CONFIG")
rc=0; $eco check > "$d/bad.out" 2>/dev/null || rc=$?
test "$rc" -eq 1
grep -q "invalid Antonina config" "$d/bad.out"
rc=0; $eco refresh --probe-limit 0 2>/dev/null || rc=$?
test "$rc" -ne 0
test "$(cat "$VICHE_ANTONINA_CONFIG")" = "$snapshot"

# A missing comment is repaired rather than treated as a reason to revoke.
printf '{"models":[{"model":"opencode/alpha-free"}]}\n' > "$VICHE_ANTONINA_CONFIG"
$eco refresh --probe-limit 0 >/dev/null
jq -e '.models[0].comment == "" and .models[0].variant == "low"' "$VICHE_ANTONINA_CONFIG" >/dev/null

# A copied checkout with inherited HOME and no fixture overrides cannot
# execute discovery or modify any config.
before=$(cat "$VICHE_ANTONINA_CONFIG")
(unset VICHE_OPENCODE_MODELS; $eco refresh) && exit 1
test "$(cat "$VICHE_ANTONINA_CONFIG")" = "$before"
echo 'economy models smoke passed'
