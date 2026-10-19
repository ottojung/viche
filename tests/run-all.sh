#!/bin/sh
# Run every Viche test from one local or CI command.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"

echo 'Checking shell syntax and constitutional roster'
/bin/sh -n constitution/*.sh government/*.sh tests/*.sh deploy/s6/viche/run deploy/s6/viche-intake/run
dash -n constitution/*.sh government/*.sh tests/*.sh deploy/s6/viche/run
grep -Fq 'opencode-go/longcat-2.5-preview-free' constitution/CONSTITUTION.md
test -s government/seats.tsv
awk -F '\t' 'NF != 3 || $1 !~ /^[0-9a-f]+$/ { exit 1 }' government/seats.tsv
test "$(cut -f1 government/seats.tsv | sort -u | wc -l)" -eq "$(wc -l < government/seats.tsv)"

for script in tests/*-smoke.sh tests/ballot-integrity.sh; do
    printf '\nRunning %s\n' "$script"
    dash "$script"
done
echo 'All Viche tests passed'
