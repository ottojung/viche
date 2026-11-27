#!/usr/bin/env python3
"""Retired relay `lb-cert` worker handler.

Lower-bound candidate generation is local and bounded on billy-dev only.
This file is a fail-closed compatibility stub: it executes no subprocess,
opens no network socket and reads no credential. See relay/README.md.
"""
import json
import sys

REFUSAL = {
    "status": "remote_transport_disabled",
    "reason": "out-of-host proof transport is prohibited; use bounded local generation and the managed local compiler from an exact bound workspace.",
}


def main():
    print(json.dumps(REFUSAL, sort_keys=True))
    return 9


if __name__ == "__main__":
    raise SystemExit(main())
