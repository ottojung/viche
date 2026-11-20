#!/bin/sh
# POSIX sh wrapper for the independent Act 32 phase-gate verifier.
# This wrapper carries NO authority: it only locates canonical code and data.
# Activation decisions remain fail-closed inside knowledge-phase-verifier.py.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
[ -s "$town/government/knowledge-phase-verifier.py" ] || {
  echo "phase verifier missing in canonical town" >&2
  exit 1
}
exec python3 "$town/government/knowledge-phase-verifier.py" --town "$town" "$@"
