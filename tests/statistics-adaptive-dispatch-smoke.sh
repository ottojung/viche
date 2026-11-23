#!/bin/sh
# Hermetic dynamic inquiry dispatch under APPROVED activation/budget stubs.
# No real agent, provider, or model called here.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
t="$d/town"
s="$d/state"
seat="$d/seats"
mkdir -p "$t/government" "$t/records/knowledge" "$t/records/statistics/inquiries" \
         "$seat/branches/statistics" "$d/bin" "$s"
: > "$seat/branches/statistics/.git"
cp "$repo/government/knowledge-office-cycle.sh" "$repo/government/statistics-inquiry.py" \
   "$t/government/"
printf '## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)\n' \
  > "$t/government/LAWS.md"
printf 'One authorized scientific office, not a fixed metrics script.\n' \
  > "$t/government/KNOWLEDGE-OFFICES.md"
printf '{}\n' > "$t/records/knowledge/baseline-20261119.json"
printf 'The institution must use evidence, not fake achievements.\n' > "$d/constitution"
cat > "$t/records/statistics/inquiries/unexpected-recovery-debt.json" <<'JSON'
{"schema":"viche-statistics-inquiry-v1",
 "id":"unexpected-recovery-debt","stage":"candidate",
 "question":"Which dormant services incur hidden recovery debt?",
 "why_now":"A service recently recovered but the next failure mode is unknown",
 "decision_use":"Decide whether to fund additional randomized disaster recovery observations"}
JSON
cat > "$t/government/knowledge-activation-verify.sh" <<'STUB'
#!/bin/sh
test "$1" = statistics && test "$ALLOW_ACTIVATION" = yes
STUB
cat > "$t/government/knowledge-budget.sh" <<'STUB'
#!/bin/sh
case "$1" in guard|reserve|mark-dispatched|start) exit 0;; *) exit 1;; esac
STUB
cat > "$t/government/statistics-preflight.sh" <<'STUB'
#!/bin/sh
[ "$1" = statistics ]
STUB
cat > "$t/government/branch-bootstrap.sh" <<'STUB'
#!/bin/sh
exit 0
STUB
cat > "$t/government/appointments.sh" <<'STUB'
#!/bin/sh
test "$1" = ensure && test "$2" = statistics || exit 1
echo test-science-agent
STUB
cat > "$t/government/terminal-continuity.sh" <<'STUB'
#!/bin/sh
echo 'Continue the most decision-relevant unsolved inquiry.'
STUB
cat > "$d/bin/antonina" <<'STUB'
#!/bin/sh
test "$1" = agent || exit 99
case "$2" in
  status) printf '%s\n' '{"state":"idle"}' ;;
  run)
    while [ $# -gt 1 ]; do
      if [ "$1" = --prompt ]; then
        printf '%s\n' "$2" > "$DISPATCH_CAPTURE"
        exit 0
      fi
      shift
    done
    exit 98 ;;
  *) exit 97 ;;
esac
STUB
chmod +x "$d/bin/antonina"
export PATH="$d/bin:$PATH" DISPATCH_CAPTURE="$d/prompt"
export VICHE_TOWN_ROOT="$t" VICHE_STATE_ROOT="$s" VICHE_SEATS_ROOT="$seat"
export VICHE_CONSTITUTION="$d/constitution" ALLOW_ACTIVATION=yes
sh "$t/government/knowledge-office-cycle.sh" statistics
test -s "$DISPATCH_CAPTURE"
grep -q 'Which dormant services incur hidden recovery debt?' "$DISPATCH_CAPTURE"
grep -q 'YOU must choose what matters to measure NOW' "$DISPATCH_CAPTURE"
grep -q 'Unmerged worktree:' "$DISPATCH_CAPTURE"
grep -q 'The institution must use evidence' "$DISPATCH_CAPTURE"
! grep -q 'run statistics-report.py daily' "$DISPATCH_CAPTURE"
test ! -e "$s/knowledge/statistics/snapshot-$(date -u +%Y-%m-%d).json"
# Denied activation must block dispatch despite successful stubs elsewhere.
rm -f "$DISPATCH_CAPTURE" "$s/knowledge/offices/statistics/last-dispatch"
ALLOW_ACTIVATION=no sh "$t/government/knowledge-office-cycle.sh" statistics >/dev/null 2>&1 || :
test ! -e "$DISPATCH_CAPTURE"
echo 'Statistics dynamic agent prompt receives novel inquiry and respects denied activation'
