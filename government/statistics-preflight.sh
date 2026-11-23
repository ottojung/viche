#!/bin/sh
# Fail-closed readiness gates for the Act 32 / enacted Act 33 Statistics trial.
#
# Two narrowly scoped modes (second argument, default "legacy"):
#
#   legacy       The original Act 32 comparator gate. Requires a historically
#                verified outcome numerator AND a measured resource denominator.
#                This remains the ONLY gate for any efficacy claim, renewal or
#                successor office (Act 33 §§5-6). Unchanged behaviour; existing
#                tests and attestations are preserved verbatim.
#
#   first-trial  The enacted Act 33 exception, for the FIRST reversible Statistics
#                measurement trial only. Historical numerator and actual
#                per-office CPU must be explicitly UNAVAILABLE (never zero, never
#                "verified"); instead the mode strictly requires a preregistered
#                prospective design, frozen primary sources with reliable
#                same-boot observations, an independently measured and genuinely
#                ENFORCED hard cap, an explicit <=14-day Executive order and an
#                independently corroborated Judiciary proceed bound to the exact
#                frozen source bytes. See government/statistics-first-trial.py.
#
# Both modes only WITHHOLD readiness; neither enables an office or spends money.
# An absent, tampered, forged or uncorroborated artifact fails closed. POSIX sh.
set -eu

office=${1:-}
[ "$office" = "statistics" ] || exit 0
mode=${2:-legacy}
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}

case "$mode" in
  legacy)
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
    ;;
  first-trial)
    # Enacted Act 33 narrow exception. The verifier checks the enacted Act in
    # canonical LAWS.md (old law / no Act 33 fails closed), corroborates every
    # gate against an officer registry + Git-anchored artifact + separate
    # institutional review export, and enforces the UNAVAILABLE/hard-cap/order/
    # expiry/source-integrity rules. No single all-green JSON is authority.
    att=$town/records/knowledge/statistics-first-trial-preflight-20261122.json
    helper=$town/government/statistics-first-trial.py
    [ -s "$att" ] || exit 1
    [ -s "$helper" ] || exit 1
    at=${VICHE_AT:-}
    if [ -n "$at" ]; then
      # A fabricated future/past wall clock could make an expired or not-yet-
      # valid Executive order appear active. Synthetic dates are allowed ONLY
      # for an explicitly selected, isolated /tmp trial fixture, never the
      # canonical billy-dev state or an arbitrary Git seat worktree.
      real_town=$(cd "$town" && pwd -P) || exit 1
      case "$real_town" in
        /tmp/*) : ;;
        *) echo 'Act33 preflight: synthetic time refused on live town' >&2; exit 1 ;;
      esac
      python3 "$helper" verify "$town" "$att" "$at" >/dev/null 2>&1 || exit 1
    else
      python3 "$helper" verify "$town" "$att" >/dev/null 2>&1 || exit 1
    fi
    ;;
  *)
    exit 1
    ;;
esac

exit 0
