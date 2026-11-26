#!/bin/sh
# Act 21 gate machinery regression: a hung suite must be bounded and fail
# closed, and a completing suite must be unaffected. Hermetic; no writers.
set -eu
here=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
exec python3 "$here/integrator-suite-timeout.py"
