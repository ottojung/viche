#!/bin/sh
# Bounded concurrent issue fetching keeps the executive discovery inside its
# 300s cycle budget without changing eligibility decisions or output order.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/state"

cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
s=${MOCK_STATE:?}
if [ "$1 $2" = "board list" ]; then
    printf '%s\n' '[{"number":"1","title":"one"},{"number":"2","title":"two"},{"number":"3","title":"three"},{"number":"4","title":"four"},{"number":"5","title":"five"},{"number":"6","title":"six"},{"number":"7","title":"seven"},{"number":"8","title":"eight"}]'
    exit 0
fi
if [ "$1 $2" = "board show" ]; then
    # Atomically track active concurrent board-show calls and the high-water mark.
    exec 9>"$s/lock"
    flock 9
    cur=0
    [ ! -f "$s/active" ] || cur=$(cat "$s/active")
    cur=$((cur + 1))
    printf '%s\n' "$cur" > "$s/active"
    max=0
    [ ! -f "$s/max" ] || max=$(cat "$s/max")
    if [ "$cur" -gt "$max" ]; then printf '%s\n' "$cur" > "$s/max"; fi
    flock -u 9
    sleep 0.3
    flock 9
    cur=$(cat "$s/active")
    cur=$((cur - 1))
    printf '%s\n' "$cur" > "$s/active"
    flock -u 9
    echo '{"body":"All agent execution and development work must happen on billy-dev.","messages":[]}'
    exit 0
fi
echo "unexpected antonina invocation: $*" >&2
exit 9
MOCK
chmod +x "$scratch/bin/antonina"

PATH="$scratch/bin:$PATH"
VICHE_STATE_ROOT="$scratch/state"
VICHE_BOARD_FETCH_WORKERS=4
MOCK_STATE="$scratch"
export PATH VICHE_STATE_ROOT VICHE_BOARD_FETCH_WORKERS MOCK_STATE

# Four workers over eight issues: several fetches must overlap, but never more
# than the configured bound. Eligibility and emitted order stay identical.
python3 "$repo/government/eligible-work.py" > "$scratch/out.json" 2> "$scratch/err.txt"
max=$(cat "$scratch/max")
test "$max" -ge 2 || { echo 'FAIL: no concurrent fetches observed' >&2; exit 1; }
test "$max" -le 4 || { echo "FAIL: concurrency $max exceeded bound 4" >&2; exit 1; }
active=$(cat "$scratch/active")
test "$active" -eq 0 || { echo 'FAIL: leaked active fetches' >&2; exit 1; }
jq -e '.complete == true and .count == 8 and
        (.eligible | map(.number) == ["1","2","3","4","5","6","7","8"])' \
    "$scratch/state/branches/eligible-issues.json" >/dev/null

# A bound of 1 reproduces the historical serial behaviour exactly.
rm -f "$scratch/max" "$scratch/active"
VICHE_BOARD_FETCH_WORKERS=1
export VICHE_BOARD_FETCH_WORKERS
python3 "$repo/government/eligible-work.py" > "$scratch/out2.json" 2> "$scratch/err2.txt"
test "$(cat "$scratch/max")" -eq 1 || { echo 'FAIL: bound=1 must be serial' >&2; exit 1; }
jq -e '.count == 8' "$scratch/state/branches/eligible-issues.json" >/dev/null

# Hostile worker values cannot create unbounded parallelism.
VICHE_BOARD_FETCH_WORKERS=99999
python3 -c 'import importlib.util,sys; spec=importlib.util.spec_from_file_location("ew","'"$repo"'/government/eligible-work.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); assert m.FETCH_WORKERS == 16'

echo 'Eligible-work bounded parallel fetch smoke passed'
