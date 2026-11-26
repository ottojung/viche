#!/bin/sh
# The boot wrapper caps the whole daily digest at 600 s. When the serial
# antonina/git readers are slower than the shared budget, the digest must still
# post its ten lines, degrading the slow sources to honest "unavailable" lines
# instead of exceeding the wrapper cap and posting nothing at all.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/bin" "$d/town/government" "$d/town/records" "$d/state/institutional-cases" \
  "$d/xdg-config/antonina" "$d/home"
cp "$repo/government/daily-digest.py" "$d/town/government/"
git -C "$d/town" init -q -b main
git -C "$d/town" -c user.name=t -c user.email=t@example.test commit -q --allow-empty -m baseline
printf '{"models":[{"model":"p/free","comment":""}]}\n' > "$d/xdg-config/antonina/config.json"
printf '{"observed_at":0,"active":[],"count":0,"auto_closed":[]}\n' > "$d/state/institutional-cases/index.json"

# Each paged reader sleeps, so a small budget expires mid-pagination.
cat > "$d/bin/antonina" <<MOCK
#!/bin/sh
sleep 0.2
case "\$1 \$2" in
  'agent list') printf '{"agents":[%s],"unreadable":[]}\n' "\$(python3 -c 'import json;print(",".join(json.dumps({"id":str(i),"state":"idle"}) for i in range(100)))')" ;;
  'board list') python3 -c 'import json;print(json.dumps([{"number":str(i),"title":"t","updatedAt":"2026-11-26T00:00:00Z"} for i in range(10)]))' ;;
  'board show') python3 -c 'import datetime,json,time;n=int(time.time());iso=datetime.datetime.fromtimestamp(n,datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ");print(json.dumps({"messages":[{"id":str(i),"author":"clerk","createdAt":iso,"body":"notes"} for i in range(50)]}))' ;;
  'board comment') printf '%s\n' "\$*" >> "$d/comments" ;;
  *) echo "unexpected: \$*" >&2; exit 9 ;;
esac
MOCK
chmod +x "$d/bin/antonina"

cat > "$d/drive.py" <<'PY'
import importlib.util, os, time
spec = importlib.util.spec_from_file_location("dd", os.environ["DIGEST_PATH"])
dd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dd)
start = time.monotonic()
out = dd.build(int(time.time()))
print("BUILD_SECONDS=%.2f" % (time.monotonic() - start))
print(out, end="")
PY

PATH="$d/bin:$PATH" DIGEST_PATH="$d/town/government/daily-digest.py" \
  VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" HOME="$d/home" \
  XDG_CONFIG_HOME="$d/xdg-config" VICHE_DIGEST_REPOS= VICHE_TOWNHALL_ID=302 \
  VICHE_DIGEST_READ_BUDGET=0.5 python3 "$d/drive.py" > "$d/out"

# Bounded: the build returns promptly rather than running past the wrapper cap.
seconds=$(sed -n 's/^BUILD_SECONDS=//p' "$d/out")
python3 -c 'import sys; raise SystemExit(0 if float(sys.argv[1]) < 10 else 1)' "$seconds"

# Exactly ten lines, with the slow sources named as unavailable, never as zero.
sed '1d' "$d/out" > "$d/digest"
test "$(wc -l < "$d/digest")" -eq 10
grep -Fq 'Shipped (Viche main): unavailable (read budget exhausted)' "$d/digest"
grep -Fq 'Shipped (elsewhere): unavailable (read budget exhausted)' "$d/digest"
grep -Fq 'Agent runs: unavailable (read budget exhausted)' "$d/digest"
grep -Fq 'Town Hall unreadable, so requests may be missing' "$d/digest"
echo 'Daily digest read-budget smoke passed'
