#!/bin/sh
# Hermetic tests for the per-invocation FREE-ONLY Antonina allowlist wrapper.
# No live agent is dispatched; global model config is never touched.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
wrap=government/knowledge-free-dispatch.sh
[ -s "$wrap" ]
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/state/economy" "$d/town/government" "$d/bin"
cp government/knowledge-practical-bounds.py "$d/town/government/"
python3 - "$d/state/economy/model-policy.json" <<'PY'
import json,sys
json.dump({"prefer":["opencode/tidepool-alpha-free","opencode-go/hy4-flash-free"],"exclude":[]},open(sys.argv[1],"w"))
PY
# Stub antonina records the env and args instead of dispatching.
cat > "$d/bin/antonina" <<'EOF'
#!/bin/sh
printf 'XDG=%s ARGS=%s\n' "${XDG_CONFIG_HOME:-}" "$*" > "$CAPTURE"
EOF
chmod +x "$d/bin/antonina"
fail=0

# The wrapper builds a free-only config from policy and pins XDG on `run`.
CAPTURE="$d/capture" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach
grep -q "XDG=$d/state/knowledge/free-allowlist ARGS=agent run --id fake --cwd /tmp --prompt hi --detach" "$d/capture" ||
  { echo 'FAIL: XDG not pinned / args changed' >&2; fail=1; }
python3 - "$d/state/knowledge/free-allowlist/config.json" <<'PY'
import json,sys
c=json.load(open(sys.argv[1]))
assert [e['model'] for e in c['models']]==['opencode/tidepool-alpha-free','opencode-go/hy4-flash-free']
assert all('-free' in e['model'] for e in c['models'])
PY

# Global ladder is untouched (wrapper works from a temp state root only).
grep -q 'muse-spark-1.3-contributor' /home/lubko/.config/antonina/config.json ||
  { echo 'FAIL: global config changed' >&2; fail=1; }

# A disguised paid id containing -free mid-string must be refused.
python3 - "$d/state/economy/model-policy.json" <<'PYMASK'
import json,sys
json.dump({"prefer":["provider/paid-free-trial"],"exclude":[]},open(sys.argv[1],"w"))
PYMASK
if CAPTURE="$d/capture3" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
   PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
 echo 'FAIL: disguised paid id admitted' >&2; fail=1
fi

# A non-free id in policy prefer is refused (fail closed).
python3 - "$d/state/economy/model-policy.json" <<'PY'
import json,sys
json.dump({"prefer":["openai/gpt-6-luna"],"exclude":[]},open(sys.argv[1],"w"))
PY
if CAPTURE="$d/capture2" VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$wrap" run --id fake --cwd /tmp --prompt hi --detach >/dev/null 2>&1; then
  echo 'FAIL: non-free id admitted' >&2; fail=1
fi

[ "$fail" -eq 0 ] || { echo 'knowledge free dispatch smoke: FAILED' >&2; exit 1; }
echo 'knowledge free dispatch smoke: OK (XDG pinned, free-only allowlist, global untouched, fail-closed)'
