#!/usr/bin/env python3
"""Retired compatibility entry point; fails locally without subprocesses."""
import json
import sys


def main():
    print(json.dumps({"status":"remote_transport_disabled",
        "reason":"out-of-host proof transport is prohibited; use the managed local compiler from an exact bound workspace. GitHub-hosted CI remains allowed."},sort_keys=True))
    return 9


if __name__ == "__main__":
    raise SystemExit(main())
