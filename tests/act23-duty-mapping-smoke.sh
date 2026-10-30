#!/bin/sh
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
for n in 15 17 18 19 21 23; do
    grep -Fq "Act $n" "$repo/records/agentic-operations-duty-map.md"
done
grep -Fq 'continuity_unverified_executive' "$repo/records/agentic-cutover-open-cases.md"
grep -Fq 'continuity_unverified_judiciary' "$repo/records/agentic-cutover-open-cases.md"
grep -Fq 'office-blockers/$seat' "$repo/government/sitting.sh"
grep -Fq 'office-blockers/$office' "$repo/government/agentic-office.sh"
echo 'Act 23 mapping and blocked-appointment gate passed'
