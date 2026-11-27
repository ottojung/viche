#!/bin/sh
# Hermetic wrapper: the Act 31 descendant-priority test uses only a temp git repo.
set -eu
here=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
exec python3 "$here/integrator-descendant-priority.py"
