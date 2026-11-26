#!/usr/bin/env python3
"""Retired relay client. Use local lbgen/lbassemble for generation."""
import json
import sys

try:
    from .. import host_boundary
except ImportError:
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
    from missions.pnp import host_boundary


def main():
    host_boundary.print_refusal("lbremote")
    return host_boundary.EXIT


if __name__ == '__main__':
    sys.exit(main())
