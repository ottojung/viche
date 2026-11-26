#!/usr/bin/env python3
"""Retired exact-base cache refresher.

Negotiating or refreshing out-of-host compiler bases is prohibited.
This file is a fail-closed compatibility stub: it executes no subprocess,
opens no network socket and reads no credential. See relay/README.md.
"""
import json
import sys

REFUSAL = {
    "status": "remote_transport_disabled",
    "reason": "out-of-host base negotiation is prohibited; compile only from an exact bound workspace with the managed local compiler.",
}


def main():
    print(json.dumps(REFUSAL, sort_keys=True))
    return 9


if __name__ == "__main__":
    raise SystemExit(main())
