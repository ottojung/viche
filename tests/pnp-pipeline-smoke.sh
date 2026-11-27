#!/bin/sh
# Offline acceptance tests for the P vs NP publisher; no external side effects.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' 0
trap 'exit 130' 1 2 3 15
export PNP_STATE_ROOT="$scratch/pnp"
mkdir -p "$PNP_STATE_ROOT"
/bin/sh -n missions/pnp/git-auth.sh
python3 tests/pnp-research.py
python3 tests/pnp-pipeline.py
python3 tests/pnp-generator-process.py
python3 tests/pnp-generator-fairness.py
python3 tests/pnp-circwit-outwire.py
python3 tests/pnp-production-ready.py
python3 tests/pnp-rectcover.py
python3 tests/pnp-edgecover.py
python3 tests/pnp-promise.py
python3 tests/pnp-promise-batch.py
python3 tests/pnp-posting.py
python3 tests/pnp-private-prelease.py
python3 tests/pnp-private-promotion.py
python3 tests/pnp-host-boundary.py
python3 tests/pnp-real-smoke.py
python3 tests/pnp-watchdog-smoke.py
python3 tests/pnp-retention.py
python3 tests/pnp-proof-tools.py
python3 tests/pnp-bench.py

python3 tests/pnp-support.py

python3 tests/pnp-allocator.py

# tests/pnp-runtime-isolation-smoke.sh is also a tests/*-smoke.sh script and
# therefore runs in the canonical tests/run-all.sh loop. Invoking it here ran
# the same hermetic isolation test twice per exact candidate; the single loop
# execution is retained with all of its assertions.
python3 tests/pnp-continuity.py
python3 tests/pnp-staffing.py
python3 tests/pnp-sparse-workspace.py

python3 tests/pnp-brief.py
python3 tests/pnp-tool-discovery.py

python3 tests/pnp-adapter.py

python3 tests/pnp-rows.py

python3 tests/pnp-metrics.py
python3 tests/pnp-race-metrics.py
python3 tests/pnp-competition.py
python3 tests/pnp-catalog-observer.py
python3 tests/pnp-status-pacing.py

python3 tests/pnp-remote-protocol.py
