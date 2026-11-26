#!/usr/bin/env python3
"""Retired relay `lean-check` worker handler.

Out-of-host proof checking is prohibited under the current host assignment.
This file is a fail-closed compatibility stub: it executes no subprocess,
opens no network socket and reads no credential. See relay/README.md.
"""
import json
import sys

REFUSAL = {
    "status": "remote_transport_disabled",
    "reason": "out-of-host proof transport is prohibited; use the managed local compiler from an exact bound workspace. GitHub-hosted CI remains allowed.",
}


def main():
    print(json.dumps(REFUSAL, sort_keys=True))
    return 9


if __name__ == "__main__":
    raise SystemExit(main())
