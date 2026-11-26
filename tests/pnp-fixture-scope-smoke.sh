#!/bin/sh
# Multi-module unittest import order must not mutate the preloaded root.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
outer=$(mktemp -d)
trap 'rm -rf "$outer"' 0
trap 'exit 130' 1 2 3 15
export PNP_STATE_ROOT="$outer/preloaded"
mkdir -p "$PNP_STATE_ROOT/gaps/L-meta-582"
printf 'sentinel\n' > "$PNP_STATE_ROOT/gaps/L-meta-582/state.json"
python3 - <<'PY'
import os
from pathlib import Path
import unittest
from missions.pnp import config, cli, fastlane, gitctl
root=config.STATE_ROOT
mirror=gitctl.MIRROR
work=fastlane.WORK
suite=unittest.defaultTestLoader.loadTestsFromNames([
    'tests.pnp-pipeline.TestState.test_transitions_events_and_intent',
    'tests.pnp-pipeline.TestCli.test_submit_snapshots_and_launches_without_agent_git',
])
assert unittest.TextTestRunner().run(suite).wasSuccessful()
assert config.STATE_ROOT==root==os.environ['PNP_STATE_ROOT']
assert gitctl.MIRROR==mirror and fastlane.WORK==work
assert Path(root,'gaps/L-meta-582/state.json').read_text()=='sentinel\n'
print('Preloaded production-shaped PnP root preserved')
PY
