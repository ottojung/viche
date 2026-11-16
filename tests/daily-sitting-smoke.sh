#!/bin/sh
# Act 30 §6: Parliament sits once per UTC day so a six-seat quorum can form;
# the sitting adds seats to SUMMONED.txt, never touches the Clerk's own
# summonses, and releases the seats it added once they have sat.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/town/government" "$d/town/records/bills" "$d/town/records/ballots" "$d/state"
for n in 1 2 3 4 5 6 7 8 9 10; do
  printf 'c1a%05d\tSeat %s\tx\n' "$n" "$n"
done > "$d/town/government/seats.tsv"
export VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state"
no() { if grep -q "$@"; then echo "unexpected match: $*" >&2; exit 1; fi; }
ds() { python3 "$repo/government/daily-sitting.py" "$@"; }
at() { # ISO -> epoch
  date -u -d "$1" +%s
}
summoned=$d/town/records/SUMMONED.txt

# Before inauguration nothing happens.
VICHE_DAILY_NOW=$(at 2026-11-16T18:00:00Z) ds run 2>/dev/null
test ! -e "$summoned"
touch "$d/state/inaugurated"

# Before the sitting hour: nothing.
VICHE_DAILY_NOW=$(at 2026-11-16T16:59:00Z) ds run 2>/dev/null
test ! -e "$summoned"

# Business: one fresh bill without ballots, one with ballots, one stale.
printf '# B1\n' > "$d/town/records/bills/B1.md"
printf '# B2\n' > "$d/town/records/bills/B2.md"; printf 'c1a00002\tyes\n' > "$d/town/records/ballots/B2.tsv"
printf '# B3\n' > "$d/town/records/bills/B3.md"; touch -d '2026-09-01' "$d/town/records/bills/B3.md"
# The Clerk had already summoned seat 3 for specific work.
printf 'c1a00003\n' > "$summoned"
mkdir -p "$d/town/records/summons"
printf 'Specific assignment from the Clerk.\n' > "$d/town/records/summons/c1a00003.md"

# Sitting: the nine non-Clerk seats are summoned, the Clerk is not.
VICHE_DAILY_NOW=$(at 2026-11-16T17:00:00Z) ds run 2>/dev/null
test "$(wc -l < "$summoned")" -eq 9
no '^c1a00001$' "$summoned"
for n in 2 3 4 5 6 7 8 9 10; do grep -q "^c1a0000$n\$\|^c1a000$n\$" "$summoned" || { echo "seat $n missing" >&2; exit 1; }; done
agenda=$d/state/parliament/daily/plenary-agenda.md
grep -q 'B1' "$agenda"
no '(records/bills/B2.md)' "$agenda"
no '(records/bills/B3.md)' "$agenda"
# Generated summons for seats without one; the Clerk's own is preserved.
grep -q 'daily-plenary' "$d/town/records/summons/c1a00002.md"
grep -q "$agenda" "$d/town/records/summons/c1a00002.md"
grep -q '^Specific assignment from the Clerk.$' "$d/town/records/summons/c1a00003.md"
jq -e '.day == "2026-11-16" and (.added | length) == 8 and .clerk == "c1a00001"' "$d/state/parliament/daily/2026-11-16.json" >/dev/null

# Once per day: running again adds nothing and does not re-add released seats.
VICHE_DAILY_NOW=$(at 2026-11-16T17:05:00Z) ds run 2>/dev/null
test "$(wc -l < "$summoned")" -eq 9

# Seats dispatched by the constitutional sitting are reported and then released;
# seat 3 (the Clerk's own summons) is not ours to release.
for n in 02 04 05; do VICHE_DAILY_NOW=$(at 2026-11-16T17:10:00Z) ds dispatched c1a000$n; done
VICHE_DAILY_NOW=$(at 2026-11-16T17:10:00Z) ds dispatched c1a00003     # not in "added": ignored
VICHE_DAILY_NOW=$(at 2026-11-16T17:12:00Z) ds run 2>/dev/null
no '^c1a00002$' "$summoned"
no '^c1a00004$' "$summoned"
grep -q '^c1a00003$' "$summoned"
grep -q '^c1a00006$' "$summoned"
test "$(wc -l < "$summoned")" -eq 6
jq -e '(.dispatched | length) == 3 and (.released | length) == 3' "$d/state/parliament/daily/2026-11-16.json" >/dev/null

# Seats that never sat are released after six hours (no wedged summonses).
VICHE_DAILY_NOW=$(at 2026-11-16T23:30:00Z) ds run 2>/dev/null
test "$(cat "$summoned")" = c1a00003

# The next day convenes again, honouring the seat limit and the hour.
VICHE_PARLIAMENT_SEATS=5 VICHE_DAILY_NOW=$(at 2026-11-17T17:30:00Z) ds run 2>/dev/null
test "$(wc -l < "$summoned")" -eq 5                 # seat 3 plus generated seats 2, 4, 5, 6
test "$(jq -r '.added | length' "$d/state/parliament/daily/2026-11-17.json")" -eq 4
VICHE_DAILY_NOW=$(at 2026-11-17T17:31:00Z) ds status | jq -e '.day == "2026-11-17"' >/dev/null

# The switch turns it off.
rm -f "$summoned"
VICHE_DAILY_SITTING=off VICHE_DAILY_NOW=$(at 2026-11-18T18:00:00Z) ds run 2>/dev/null
test ! -e "$summoned"
test ! -e "$d/state/parliament/daily/2026-11-18.json"

echo 'daily sitting smoke passed'
