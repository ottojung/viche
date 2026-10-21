#!/bin/sh
# Act 21 §3 — suite-status generator smoke test (hermetic; POSIX /bin/sh).
# Proves: a green suite records green; two consecutive reds record red; a
# red-then-green (flaky) run records green (the §1 flaky-red policy); and the
# recorded commit/tree match. No board or network access.
set -eu

repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT

town=$scratch/town
mkdir -p "$town/government" "$town/records" "$town/tests"
cp "$repo/government/suite-status.sh" "$town/government/"

git -C "$town" init -q
git -C "$town" -c user.email=t@t -c user.name=t add -A
git -C "$town" -c user.email=t@t -c user.name=t commit -qm init

printf '#!/bin/sh\nexit 0\n' > "$town/tests/green.sh"
printf '#!/bin/sh\necho boom; exit 1\n' > "$town/tests/red.sh"
cat > "$town/tests/flaky.sh" <<'EOF'
#!/bin/sh
n=$(cat tests/flaky.count 2>/dev/null || echo 0)
n=$((n + 1))
echo "$n" > tests/flaky.count
[ "$n" -ge 2 ] && exit 0
exit 1
EOF

run() {
    VICHE_TOWN_ROOT=$town /bin/sh "$town/government/suite-status.sh" "$@"
}
result() {
    sed -n 's/.*"result": "\([a-z]*\)".*/\1/p' "$town/records/suite-status.json"
}

# green -> green, commit/tree recorded
run --suite tests/green.sh >/dev/null
[ "$(result)" = green ] || { echo "FAIL: expected green"; exit 1; }
grep -q "\"commit\": \"$(git -C "$town" rev-parse HEAD)\"" "$town/records/suite-status.json" || { echo "FAIL: commit"; exit 1; }
grep -q "\"tree\": \"$(git -C "$town" rev-parse HEAD^{tree})\"" "$town/records/suite-status.json" || { echo "FAIL: tree"; exit 1; }

# two consecutive reds -> red (exit 1), incident true
if run --suite tests/red.sh >/dev/null 2>&1; then echo "FAIL: red must exit non-zero"; exit 1; fi
[ "$(result)" = red ] || { echo "FAIL: expected red"; exit 1; }
grep -q '"incident": true' "$town/records/suite-status.json" || { echo "FAIL: incident"; exit 1; }

# flaky (red then green) -> green (flaky-red policy: not a permanent block)
rm -f "$town/tests/flaky.count"
run --suite tests/flaky.sh >/dev/null
[ "$(result)" = green ] || { echo "FAIL: expected green (flaky)"; exit 1; }
grep -q '"run":1,"result":"red"' "$town/records/suite-status.json" || { echo "FAIL: run1 red"; exit 1; }
grep -q '"run":2,"result":"green"' "$town/records/suite-status.json" || { echo "FAIL: run2 green"; exit 1; }

# CI reconciliation: disagree -> incident
run --suite tests/green.sh --ci red >/dev/null
grep -q '"ci_reconciliation": "disagree"' "$town/records/suite-status.json" || { echo "FAIL: ci disagree"; exit 1; }

echo "suite-status smoke passed"
