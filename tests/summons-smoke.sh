#!/bin/sh
# A summoned seat must receive concrete current work, not just a generic agenda.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/government" "$scratch/records/summons"
printf 'c1a00001\tClerk\tintake\nc1a00002\tExecutive\tdelivery\nc1a00004\tResearch\tmetrics\nc1a00005\tResource\taudit\n' > "$scratch/government/seats.tsv"
printf '%s\n' 'UNIQUE ACT 10 CGROUP ASSIGNMENT' > "$scratch/records/summons/c1a00004.md"
VICHE_TOWN_ROOT=$scratch
VICHE_TOWNHALL_ID=297
export VICHE_TOWN_ROOT VICHE_TOWNHALL_ID

printf '%s\n' 'UNIQUE LIVE KAWUN EXECUTIVE ASSIGNMENT' > "$scratch/records/summons/c1a00002.md"
/bin/sh "$repo/government/sitting.sh" c1a00002 > "$scratch/executive.txt"
grep -Fq 'UNIQUE LIVE KAWUN EXECUTIVE ASSIGNMENT' "$scratch/executive.txt"
grep -Fq 'You are a voting parliamentarian' "$scratch/executive.txt"
if grep -Fq 'Your ongoing job is to' "$scratch/executive.txt"; then exit 1; fi

/bin/sh "$repo/government/sitting.sh" c1a00004 > "$scratch/seat4.txt"
grep -Fq 'UNIQUE ACT 10 CGROUP ASSIGNMENT' "$scratch/seat4.txt"
grep -Fq 'Prioritize your latest specific' "$scratch/seat4.txt"
grep -Fq 'Act on this assignment' "$scratch/seat4.txt"

/bin/sh "$repo/government/sitting.sh" c1a00005 > "$scratch/seat5.txt"
grep -Fq 'No seat-specific summons file exists' "$scratch/seat5.txt"
if grep -Fq 'UNIQUE ACT 10 CGROUP ASSIGNMENT' "$scratch/seat5.txt"; then
    echo 'Leaked seat-specific task to another seat' >&2
    exit 1
fi

/bin/sh "$repo/government/sitting.sh" c1a00001 > "$scratch/clerk.txt"
grep -Fq 'records/summons/SEAT_ID.md' "$scratch/clerk.txt"
grep -Fq 'records/SUMMONED.txt' "$scratch/clerk.txt"
grep -Fq 'Executive discovery, issue prioritization' "$scratch/clerk.txt"
if grep -Fq 'At EVERY sitting inspect' "$scratch/clerk.txt"; then exit 1; fi
echo 'Summons smoke checks passed'
