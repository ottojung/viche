#!/bin/sh
# Regression: the documented `cli.py status` operator command must tolerate a
# dangling gap directory with no state.json (e.g. an archived test fixture that
# left only lock files). Such a directory is not a gap and must be skipped, not
# crash the diagnostic with AttributeError on a None state record.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"

python3 - <<'PY'
import io
import json
import tempfile
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from missions.pnp import cli, config, state

class FakeDesk:
    def docs(self, refresh=False):
        return "desk docs"

    def status(self):
        return {"open_gaps": 1, "held_now": 1}

with tempfile.TemporaryDirectory() as root:
    gaps = Path(root) / "gaps"
    gaps.mkdir()
    # Keep this smoke test independent of any shared/suite state root.
    with patch.object(config, "GAPS_DIR", str(gaps)):
        # A leftover fixture directory with lock files but no state.json.
        stale = gaps / "L-meta-582"
        stale.mkdir()
        (stale / ".lock").touch()
        # A normal gap with a real state record must still be reported.
        state.save({"gap_id": "L-meta-999", "state": "LEASED",
                    "lease": "lease-x", "lease_expires_at": 1})

        with patch.object(cli.desk_mod, "Desk", FakeDesk):
            buf = io.StringIO()
            with redirect_stdout(buf):
                cli.cmd_status(Namespace())

data = json.loads(buf.getvalue())
gap_ids = [row.get("gap_id") for row in data["gaps"]]
assert "L-meta-999" in gap_ids, gap_ids
assert "L-meta-582" not in gap_ids, gap_ids
assert all(row.get("gap_id") for row in data["gaps"]), data["gaps"]
print("pnp-cli-status-smoke: ok")
PY
