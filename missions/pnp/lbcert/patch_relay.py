#!/usr/bin/env python3
"""Retired relay patcher.

Out-of-host proof transport is prohibited; this script must never inject a
worker handler or operation back into a relay service. It is a fail-closed
compatibility stub that edits no file and spawns no process.
"""
import json
import sys

print(json.dumps({"status": "remote_transport_disabled",
                  "reason": "the relay patcher is retired; no relay operation or worker is installed"}, sort_keys=True))
raise SystemExit(9)
