#!/bin/sh
# Check parliamentary ballot tally under POSIX sh (no agent or network needed).
set -eu
root=$(git rev-parse --show-toplevel)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' 0
mkdir -p "$scratch/government" "$scratch/records/bills" "$scratch/records/ballots"
cp "$root/government/seats.tsv" "$scratch/government/seats.tsv"
cp "$root/government/voting.conf" "$scratch/government/voting.conf"
cp "$root/government/predict-gate.sh" "$scratch/government/predict-gate.sh"
mkdir -p "$scratch/records/predictions"
printf '# no pilot bills in this fixture\n' > "$scratch/records/predictions/pilot.tsv"
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
# The tally cannot silently bypass Act 22 when the gate executable is absent.
mv "$scratch/government/predict-gate.sh" "$scratch/government/predict-gate.missing"
if /bin/sh "$root/government/tally.sh" test-1 >/dev/null 2>&1; then
    echo "Missing Act 22 gate executable bypassed the gate" >&2
    exit 1
fi
mv "$scratch/government/predict-gate.missing" "$scratch/government/predict-gate.sh"
# With the pilot registry missing, tally must invoke the gate and fail closed.
rm "$scratch/records/predictions/pilot.tsv"
if /bin/sh "$root/government/tally.sh" test-1 >/dev/null 2>&1; then
    echo "Missing Act 22 pilot registry bypassed the gate" >&2
    exit 1
fi
printf '# no pilot bills in this fixture\n' > "$scratch/records/predictions/pilot.tsv"
# The exact bill hash is binding: a revision must invalidate every old ballot.
printf '%s\n' "Unapproved new text" >> "$scratch/records/bills/test-1.md"
if /bin/sh "$root/government/tally.sh" test-1 >/dev/null 2>&1; then
    echo "Old ballots incorrectly passed a changed bill" >&2
    exit 1
fi
printf '%s\n' "Viche: votes for the original bill pass; stale ballots rejected"
