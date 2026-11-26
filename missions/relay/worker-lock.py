#!/usr/bin/env python3
"""Retired relay worker launcher. Fails closed without spawning anything."""
import json
import sys

print(json.dumps({"status": "remote_transport_disabled",
                  "reason": "the relay worker is retired; no process is started"}, sort_keys=True))
raise SystemExit(9)
