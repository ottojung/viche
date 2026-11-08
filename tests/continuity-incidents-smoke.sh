#!/bin/sh
# Repeated observations must not duplicate permanent incident reports.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
. "$repo/government/office-continuity.sh"
mkdir -p "$tmp/liveness"
oc_surface_permanent "$tmp/liveness" agent-1 ""
oc_surface_permanent "$tmp/liveness" agent-1 ""
grep -Fq 'unclassified_failure classification=missing_backend_classification' \
 "$tmp/liveness/permanent-incidents.log"
if grep -Fq 'permanent_failure classification=missing_backend_classification' "$tmp/liveness/permanent-incidents.log"; then
 echo 'Missing classification was fabricated as permanent' >&2; exit 1
fi
[ "$(wc -l < "$tmp/liveness/permanent-incidents.log")" -eq 1 ]
oc_surface_permanent "$tmp/liveness" agent-2 invalid_api_key
oc_surface_permanent "$tmp/liveness" agent-2 invalid_api_key
[ "$(wc -l < "$tmp/liveness/permanent-incidents.log")" -eq 2 ]
grep -Fq 'permanent_failure classification=invalid_api_key' \
 "$tmp/liveness/permanent-incidents.log"
# If the append-only incident log is lost before durable publication, no
# stale auxiliary marker may prevent a later observation from reporting it.
cp "$tmp/liveness/permanent-incidents.log" "$tmp/previous-log"
: > "$tmp/liveness/permanent-incidents.log"
oc_surface_permanent "$tmp/liveness" agent-2 invalid_api_key
[ "$(wc -l < "$tmp/liveness/permanent-incidents.log")" -eq 1 ]
echo 'Honest incident classification and idempotency smoke passed'
