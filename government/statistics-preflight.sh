#!/bin/sh
# Fail-closed readiness gate for the Act 32 Statistics-only trial.
#
# Exits 0 ONLY for the statistics office when a source-attested preflight record
# exists, every pinned snapshot is byte-identical, the design is honestly
# recorded (unavailable is not zero), and every preactivation gate is green:
#   - verified outcome numerator (Act 23 5.2),
#   - frozen Economy resource denominator with metered units and a hard cap,
#   - signed reversible Executive activation order,
#   - independent Judiciary factual determination.
# No artifact, tampered artifact, missing measure or unmet gate fails closed.
# This script never enables an office; it only withholds readiness. POSIX sh.
set -eu

office=${1:-}
[ "$office" = "statistics" ] || exit 0

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
att=$town/records/knowledge/statistics-trial-preflight-20261120.json
src=$town/records/knowledge/statistics-preflight-20261120-sources
helper=$town/government/statistics-evidence.py

[ -s "$att" ] || exit 1
[ -d "$src" ] || exit 1
[ -s "$helper" ] || exit 1

# Tamper detection + missingness: pinned bytes must match and unmetered values
# must be declared unavailable rather than silently converted to zero.
python3 "$helper" verify "$att" "$src" >/dev/null 2>&1 || exit 1
python3 "$helper" missingness "$att" >/dev/null 2>&1 || exit 1

# Every gate green, readiness explicitly ready, and a real metered denominator.
jq -e '
    .schema == "viche-statistics-trial-preflight-1" and
    .office == "statistics" and
    .readiness == "ready" and
    (.gates | type == "object") and
    ([.gates[] | .status] | all(. == "green")) and
    (.denominator_resource.meter_available == true) and
    (.denominator_resource.units != "unavailable") and
    (.denominator_resource.units != null)
  ' "$att" >/dev/null 2>&1 || exit 1

exit 0
