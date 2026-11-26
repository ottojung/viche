#!/bin/sh
# Act 21 gate machinery invariant: the default suite bound must accommodate a
# red-rerun under host load while staying bounded below the outer wrapper.
set -eu
here=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
exec python3 "$here/integrator-suite-bound-default.py"
