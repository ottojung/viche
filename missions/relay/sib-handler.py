#!/usr/bin/env python3
"""Retired relay `sibling` worker handler.

Sibling indexing is local; sibling adaptation is not automatically checked.
This file is a fail-closed compatibility stub: it executes no subprocess,
opens no network socket and reads no credential. See relay/README.md.
"""
import json
import sys

REFUSAL = {
    "status": "remote_transport_disabled",
    "reason": "out-of-host proof transport is prohibited; siblings are indexed locally and checked only by the managed local compiler from an exact bound workspace.",
}


def main():
    print(json.dumps(REFUSAL, sort_keys=True))
    return 9


if __name__ == "__main__":
    raise SystemExit(main())
