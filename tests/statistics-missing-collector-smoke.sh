#!/bin/sh
# A missing collector yields a correctly attributed MISSINGNESS publication,
# not a permanently stalled publishing loop or invented zero.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/town/government" "$d/state"
cp "$repo/government/statistics-report.py" "$repo/government/post.py" \
  "$repo/government/post_guard.py" "$d/town/government/"
printf '%s\n' '## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)' > "$d/town/government/LAWS.md"
export VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state"
python3 "$d/town/government/statistics-report.py" > "$d/result"
python3 "$d/town/government/post.py" health | jq -e '.messages==2 and .publications==2 and .healthy==true' >/dev/null
python3 - "$d/state" <<'PY'
import sys,sqlite3
from pathlib import Path
root=Path(sys.argv[1])
db=sqlite3.connect(root/"post/post.sqlite3")
data=db.execute("select topic,body,sources from messages order by topic").fetchall()
assert len(data)==2
for topic,body,sources in data:
 assert topic in ("statistics/outcomes","statistics/resources")
 assert "UNAVAILABLE (not zero and not healthy)" in body,body
 assert "derived missingness evidence only" in body
 assert "snapshot-" in sources
PY
python3 "$d/town/government/statistics-report.py" > "$d/result2"
python3 "$d/town/government/post.py" health | jq -e '.messages==2' >/dev/null
echo 'Stats missing collectors: publish immutable UNAVAILABLE evidence, no zero imputation'
