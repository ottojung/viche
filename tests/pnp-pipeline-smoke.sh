#!/bin/sh
# Offline acceptance tests for the P vs NP publisher; no external side effects.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
/bin/sh -n government/pnp/git-auth.sh
python3 tests/pnp-pipeline.py
