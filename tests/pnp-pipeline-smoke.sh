#!/bin/sh
# Offline acceptance tests for the P vs NP publisher; no external side effects.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
/bin/sh -n missions/pnp/git-auth.sh
python3 tests/pnp-pipeline.py
python3 tests/pnp-real-smoke.py
python3 tests/pnp-watchdog-smoke.py
python3 tests/pnp-proof-tools.py
python3 tests/pnp-bench.py

python3 tests/pnp-support.py

python3 tests/pnp-allocator.py

/bin/sh tests/pnp-runtime-isolation-smoke.sh

python3 tests/pnp-continuity.py

python3 tests/pnp-brief.py
