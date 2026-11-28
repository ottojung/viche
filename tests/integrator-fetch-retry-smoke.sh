#!/bin/sh
# Bounded retry of the checked integrator fetch: transient faults recover,
# exhaustion fails closed. Hermetic; no live writers or git fetches.
set -eu
here=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
exec python3 "$here/integrator-fetch-retry.py"
