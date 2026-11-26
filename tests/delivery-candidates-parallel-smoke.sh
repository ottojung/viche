#!/bin/sh
# Bounded parallel worktree inspection keeps the Executive delivery inventory
# inside its 300s cycle budget without changing queries, classification or output.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/town" "$scratch/seats/branches"
for i in 1 2 3 4 5 6 7 8; do mkdir -p "$scratch/seats/branches/w$i"; done

cat > "$scratch/bin/git" <<'MOCK'
#!/bin/sh
set -eu
s=${MOCK_STATE:?}
[ "$1" = '-C' ] || { echo "unexpected git args: $*" >&2; exit 9; }
path=$2
shift 2
cmd=$1
shift || true
case "$cmd" in
  rev-parse)
    if [ "$1" = 'refs/remotes/origin/main' ]; then
      echo 1111111111111111111111111111111111111111; exit 0
    fi
    case "$1" in --verify*) echo 2222222222222222222222222222222222222222; exit 0 ;; esac
    echo 3333333333333333333333333333333333333333; exit 0 ;;
  worktree)
    for i in 1 2 3 4 5 6 7 8; do
      echo "worktree $s/seats/branches/w$i"
      echo "branch refs/heads/b$i"
      echo ''
    done
    exit 0 ;;
  symbolic-ref)
    bn=$(basename "$path")
    echo "b${bn#w}"
    exit 0 ;;
  rev-list)
    if [ "${1:-}" = '--left-right' ]; then echo '1 2'; else echo 0; fi
    exit 0 ;;
  diff) echo 'records/x.md'; exit 0 ;;
  status)
    # Count concurrent inspections with an atomic high-water mark.
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
    exit 0 ;;
  *) echo "unexpected git command: $cmd $*" >&2; exit 9 ;;
esac
MOCK
chmod +x "$scratch/bin/git"

PATH="$scratch/bin:$PATH"
MOCK_STATE="$scratch"
VICHE_DELIVERY_WORKERS=4
export PATH MOCK_STATE VICHE_DELIVERY_WORKERS

python3 "$repo/government/delivery-candidates.py" \
  --repo "$scratch/town" --seats "$scratch/seats" > "$scratch/out4.json" 2> "$scratch/err4.txt"

max=$(cat "$scratch/max")
test "$max" -ge 2 || { echo 'FAIL: no concurrent inspections observed' >&2; exit 1; }
test "$max" -le 4 || { echo "FAIL: concurrency $max exceeded bound 4" >&2; exit 1; }
active=$(cat "$scratch/active")
test "$active" -eq 0 || { echo 'FAIL: leaked active inspections' >&2; exit 1; }
jq -e '.candidate_count == 8 and (.candidates | length) == 8' "$scratch/out4.json" >/dev/null

# Bound of 1 reproduces the historical serial behaviour and identical output.
rm -f "$scratch/max" "$scratch/active"
VICHE_DELIVERY_WORKERS=1
export VICHE_DELIVERY_WORKERS
python3 "$repo/government/delivery-candidates.py" \
  --repo "$scratch/town" --seats "$scratch/seats" > "$scratch/out1.json" 2> "$scratch/err1.txt"
test "$(cat "$scratch/max")" -eq 1 || { echo 'FAIL: bound=1 must be serial' >&2; exit 1; }
jq -S 'del(.generated_at)' "$scratch/out1.json" > "$scratch/n1.json"
jq -S 'del(.generated_at)' "$scratch/out4.json" > "$scratch/n4.json"
cmp "$scratch/n1.json" "$scratch/n4.json" || { echo 'FAIL: parallel output differs from serial' >&2; exit 1; }

# Hostile worker values cannot create unbounded parallelism.
VICHE_DELIVERY_WORKERS=99999
python3 -c 'import importlib.util; spec=importlib.util.spec_from_file_location("dc","'"$repo"'/government/delivery-candidates.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); assert m.WORKERS == 16'

echo 'Delivery-candidates bounded parallel inspection smoke passed'
