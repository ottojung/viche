#!/bin/sh
# Offline acceptance tests for the P vs NP publisher; no external side effects.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
/bin/sh -n missions/pnp/git-auth.sh
python3 tests/pnp-research.py
python3 tests/pnp-pipeline.py
python3 tests/pnp-generator-process.py
python3 tests/pnp-real-smoke.py
python3 tests/pnp-watchdog-smoke.py
python3 tests/pnp-retention.py
python3 tests/pnp-proof-tools.py
python3 tests/pnp-bench.py

python3 tests/pnp-support.py

python3 tests/pnp-allocator.py

/bin/sh tests/pnp-runtime-isolation-smoke.sh

python3 tests/pnp-continuity.py
python3 tests/pnp-staffing.py
python3 tests/pnp-sparse-workspace.py

python3 tests/pnp-brief.py
python3 tests/pnp-tool-discovery.py

python3 tests/pnp-adapter.py

python3 tests/pnp-rows.py

python3 tests/pnp-metrics.py

python3 tests/pnp-remote-protocol.py
