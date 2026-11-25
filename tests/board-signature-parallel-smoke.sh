#!/bin/sh
# Bounded parallel board-signature fetch: identical input-order output, any
# lookup failure still fails open, and concurrency never exceeds the knob.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin"

cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
[ "$1 $2" = 'board show' ] || exit 9
id=$4
case "$id" in
  bad*) exit 3 ;;
esac
s=${MOCK_STATE:?}
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
printf '{"updatedAt":"2026-11-25T10:00:00Z","messages":[{"id":"sha256:%s"}]}\n' "$id"
MOCK
chmod +x "$scratch/bin/antonina"

PATH="$scratch/bin:$PATH"
MOCK_STATE="$scratch"
VICHE_BOARD_SIGNATURE_WORKERS=4
export PATH MOCK_STATE VICHE_BOARD_SIGNATURE_WORKERS

out=$(python3 "$repo/government/board-signature.py" 302 301 303 304 305 306 307 308)
expected='302 2026-11-25T10:00:00Z sha256:302
301 2026-11-25T10:00:00Z sha256:301
303 2026-11-25T10:00:00Z sha256:303
304 2026-11-25T10:00:00Z sha256:304
305 2026-11-25T10:00:00Z sha256:305
306 2026-11-25T10:00:00Z sha256:306
307 2026-11-25T10:00:00Z sha256:307
308 2026-11-25T10:00:00Z sha256:308'
test "$out" = "$expected" || { echo 'FAIL: signature output or order changed' >&2; exit 1; }
max=$(cat "$scratch/max")
test "$max" -ge 2 || { echo 'FAIL: no concurrent fetches observed' >&2; exit 1; }
test "$max" -le 4 || { echo "FAIL: concurrency $max exceeded bound 4" >&2; exit 1; }
active=$(cat "$scratch/active")
test "$active" -eq 0 || { echo 'FAIL: leaked active fetches' >&2; exit 1; }

# A failed lookup still exits non-zero so the gate fails open.
rc=0
python3 "$repo/government/board-signature.py" 302 bad1 >/dev/null 2>&1 || rc=$?
test "$rc" -eq 1 || { echo 'FAIL: failed lookup must exit 1' >&2; exit 1; }

# Bad issue id is a usage error (2), never a silent empty signature.
rc=0
python3 "$repo/government/board-signature.py" 'a b' >/dev/null 2>&1 || rc=$?
test "$rc" -eq 2 || { echo 'FAIL: bad issue id must exit 2' >&2; exit 1; }

# Bound of 1 reproduces the historical serial behaviour.
rm -f "$scratch/max" "$scratch/active"
VICHE_BOARD_SIGNATURE_WORKERS=1
python3 "$repo/government/board-signature.py" 302 301 >/dev/null 2>&1
test "$(cat "$scratch/max")" -eq 1 || { echo 'FAIL: bound=1 must be serial' >&2; exit 1; }

# Hostile worker values cannot create unbounded parallelism.
VICHE_BOARD_SIGNATURE_WORKERS=99999
python3 -c 'import importlib.util; spec=importlib.util.spec_from_file_location("bs","'"$repo"'/government/board-signature.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); assert m.WORKERS == 16'

echo 'Board-signature bounded parallel fetch smoke passed'
