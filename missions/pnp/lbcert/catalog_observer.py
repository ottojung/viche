"""Refresh only public status/catalog data, without proof or desk mutations."""
from .. import frontier
from . import live


def refresh():
    try:
        frontier.refresh()
    finally:
        live.gaps_bytes(timeout=20)


if __name__ == "__main__":
    try:
        refresh()
    except Exception as exc:
        print("PnP catalog observation unavailable:", exc, flush=True)
