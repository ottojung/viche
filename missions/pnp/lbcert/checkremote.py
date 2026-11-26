"""Retired remote checker compatibility API; refuses locally and spawns nothing."""
import json
import sys

try:
    from .. import host_boundary
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from missions.pnp import host_boundary


def check(path, module, timeout=900):
    return host_boundary.EXIT, host_boundary.refusal("checkremote")


def main():
    host_boundary.print_refusal("checkremote")
    return host_boundary.EXIT


if __name__ == "__main__":
    raise SystemExit(main())
