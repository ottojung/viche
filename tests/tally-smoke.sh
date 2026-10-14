#!/bin/sh
# Check parliamentary ballot tally under POSIX sh (no agent or network needed).
set -eu
root=$(git rev-parse --show-toplevel)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' 0
mkdir -p "$scratch/government" "$scratch/records/bills" "$scratch/records/ballots"
cp "$root/government/seats.tsv" "$scratch/government/seats.tsv"
cp "$root/government/voting.conf" "$scratch/government/voting.conf"
printf '%s\n' "A proposed statute" > "$scratch/records/bills/test-1.md"
digest=$(sha256sum "$scratch/records/bills/test-1.md" | cut -d ' ' -f1)
tab=$(printf '\t')
# Take an explicit ballot from every current seat, irrespective of seat count.
while IFS="$tab" read -r seat title focus; do
    [ -n "$seat" ] || continue
    printf '%s\tyes\t%s\n' "$seat" "$digest"
done < "$scratch/government/seats.tsv" > "$scratch/records/ballots/test-1.tsv"
VICHE_TOWN_ROOT=$scratch; export VICHE_TOWN_ROOT
/bin/sh "$root/government/tally.sh" test-1 | grep -Fx 'PASSED'
# The exact bill hash is binding: a revision must invalidate every old ballot.
printf '%s\n' "Unapproved new text" >> "$scratch/records/bills/test-1.md"
if /bin/sh "$root/government/tally.sh" test-1 >/dev/null 2>&1; then
    echo "Old ballots incorrectly passed a changed bill" >&2
    exit 1
fi
printf '%s\n' "Viche: votes for the original bill pass; stale ballots rejected"
