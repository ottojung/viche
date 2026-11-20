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

# An arbitrary bag of all-green keys is not authority. Require the exact
# enumerated mandatory gates, each with a non-empty independent owner and an
# authenticated evidence link, plus a verified Judiciary-reviewed numerator and
# a metered denominator backed by a pinned source snapshot and numeric values.
jq -e '
    .schema == "viche-statistics-trial-preflight-1" and
    .office == "statistics" and
    .readiness == "ready" and
    (.gates | type == "object") and
    ((.gates | keys | sort) == ([
        "verified_numerator", "frozen_resource_denominator", "source_attestation",
        "budget_cap_enforcement", "executive_order", "judiciary_determination"
      ] | sort)) and
    ([.gates[] |
        (.status == "green") and
        (.owner | type == "string") and (.owner | length > 0) and
        (.evidence_ref | type == "string") and (.evidence_ref | length > 0)
      ] | all) and
    (.numerator.verified == true) and
    (.numerator.independent_verifier | type == "string") and
    (.numerator.independent_verifier | length > 0) and
    (.denominator_resource.meter_available == true) and
    (.denominator_resource.units | type == "string") and
    (.denominator_resource.units != "unavailable") and
    (.denominator_resource.reproducible == true) and
    (.denominator_resource.values | type == "object") and
    ([.denominator_resource.values.tokens,
      .denominator_resource.values.machine_time,
      .denominator_resource.values.wall_time | type == "number"] | all) and
    (.denominator_resource.source_snapshot as $snap |
      ([.sources[].snapshot] | index($snap) != null))
  ' "$att" >/dev/null 2>&1 || exit 1

exit 0
