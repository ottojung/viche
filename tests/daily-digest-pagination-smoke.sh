#!/bin/sh
# The NEEDS-FOUNDER line must be collected from every Town Hall page inside
# WINDOW, deduplicated by message id, not only from page 1. A high-rate external
# scheduler can push a single substantive ask onto page 2 while it is still
# current; stale asks and the Founder's own lines must not be echoed back.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/bin" "$d/town/government" "$d/xdg-config/antonina" "$d/state"

# Page-aware antonina stub: page 1 is 50 scheduler records, page 2 carries the
# open ask, page 3 repeats it and adds an out-of-window ask and a Vitalik line.
cat > "$d/bin/antonina" <<'MOCK'
#!/bin/sh
case "$1 $2" in
  'board show')
    page=1
    while [ "$#" -gt 0 ]; do
      if [ "$1" = "--page" ]; then shift; page=$1; fi
      shift
    done
    exec python3 - "$page" <<'PY'
import datetime, json, sys, time
page = int(sys.argv[1])
now = int(time.time())
def iso(age):
    return datetime.datetime.fromtimestamp(now - age, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def msg(mid, body, author="antonina-scheduler", age=0):
    return {"id": mid, "author": author, "createdAt": iso(age), "body": body}
chatter = lambda p, n: [msg("%s-chatter-%d" % (p, i), "[scheduler-turn 2026-11-26 marceline-dev] 0 launches; 0 steers", age=i * 10) for i in range(n)]
ask = "status ok\nNEEDS-FOUNDER: free disk space or approve removing a named directory"
if page == 1:
    out = chatter("p1", 50)
elif page == 2:
    out = chatter("p2", 49) + [msg("disk", ask, author="economy", age=600)]
elif page == 3:
    out = [msg("disk", ask, author="economy", age=610),
           msg("stale", "NEEDS-FOUNDER: stale request from last week", author="economy", age=3 * 86400),
           msg("founder", "NEEDS-FOUNDER: ignored, from the Founder", author="Vitalik", age=620),
           msg("sched-noise", "[scheduler-turn 2026-11-26 marceline-dev] 0 launches; 0 steers\n\nNEEDS-FOUNDER: scheduler noise must be ignored", age=615)]
else:
    out = []
print(json.dumps({"messages": out}))
PY
    ;;
  *) echo "unexpected: $*" >&2; exit 9 ;;
esac
MOCK
chmod +x "$d/bin/antonina"

printf '{"models":[{"model":"p/free","comment":""}]}\n' > "$d/xdg-config/antonina/config.json"

cat > "$d/drive.py" <<'PY'
import importlib.util, os, time
path = os.environ["DIGEST_PATH"]
spec = importlib.util.spec_from_file_location("daily_digest", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.line_needs(int(time.time()), True))
PY

PATH="$d/bin:$PATH" DIGEST_PATH="$repo/government/daily-digest.py" \
  VICHE_TOWNHALL_ID=302 VICHE_STATE_ROOT="$d/state" XDG_CONFIG_HOME="$d/xdg-config" \
  python3 "$d/drive.py" > "$d/out"
cat "$d/out"

grep -Fq 'Needs you: free disk space or approve removing a named directory' "$d/out"
# The page-2 ask was repeated verbatim on page 3 with the same id: count once.
test "$(grep -o 'free disk space or approve removing a named directory' "$d/out" | wc -l)" -eq 1
# Out-of-window and Founder-authored lines must never become requests to us.
if grep -Fq 'stale request from last week' "$d/out"; then
  echo 'out-of-window NEEDS-FOUNDER leaked into digest' >&2; exit 1
fi
if grep -Fq 'ignored, from the Founder' "$d/out"; then
  echo 'Founder line echoed as a request' >&2; exit 1
fi
if grep -Fq 'scheduler noise must be ignored' "$d/out"; then
  echo 'scheduler-turn body echoed as a request' >&2; exit 1
fi
echo 'Daily digest pagination smoke passed'
