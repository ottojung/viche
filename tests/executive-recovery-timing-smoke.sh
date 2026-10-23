#!/bin/sh
# Exact supervisor/appointment timing regressions (distinct invocation IDs).
# The retired fixture changed observed failed/running state without changing
# invocation identity and wrongly counted the same failure three times.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
/bin/sh "$repo/tests/appointment-recovery-integration-smoke.sh"
echo 'Executive recovery timing checks passed (distinct invocation evidence)'
