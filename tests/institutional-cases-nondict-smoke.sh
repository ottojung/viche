#!/bin/sh
# Regression: institutional-cases.py must not crash on stray non-case files in
# the shared cases store. A JSON list or a zero-byte file previously made
# `report` raise AttributeError, which made sitting.sh exit 1 and silently
# halted every seat dispatch in the Town (a Town-wide outage).
set -eu
town=${1:-$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
store=$tmp/institutional-cases
mkdir -p "$store"

# A legitimate open case (dict).
printf '%s\n' '{"id":"real:1","state":"open","signal":"real","first_seen":1,"last_seen":1}' > "$store/real.json"
# Hostile stray files that must be ignored, not crash on.
printf '%s\n' '[{"not":"a case"}, 1, 2]' > "$store/addendum-list.json"
: > "$store/zero-byte.json"
printf '%s\n' 'not json at all' > "$store/garbage.json"

out=$(VICHE_STATE_ROOT=$tmp python3 "$town/government/institutional-cases.py" report 2>&1) || {
    echo "report crashed/failed on non-dict store:" >&2
    printf '%s\n' "$out" >&2
    exit 1
}
# The real open case is still reported; the unhappy files are simply ignored.
printf '%s' "$out" | grep -q 'real:1' || { echo "real case missing from report" >&2; exit 1; }
printf '%s' "$out" | grep -q 'not.*a case' && { echo "non-dict leaked into report" >&2; exit 1; }

# Reconcile must likewise tolerate the same store (it shares read()).
VICHE_STATE_ROOT=$tmp python3 "$town/government/institutional-cases.py" reconcile >/dev/null 2>&1 || {
    echo "reconcile crashed/failed on non-dict store" >&2
    exit 1
}

echo 'institutional-cases tolerates non-dict/unparseable store files'
