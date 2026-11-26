"""First-sighting evidence from complete, timely public frontier observations."""
import fcntl
import json
import os
import time

from . import config, ledger, state

MAX_GAP = 120


def record(snapshot, now=None):
    now = time.time() if now is None else now
    try:
        at = float(snapshot["observed"])
        gaps = snapshot["gaps"]
        if not snapshot.get("complete") or not isinstance(gaps, dict) or not 0 <= now - at <= 45:
            return
        root = os.path.join(config.STATE_ROOT, "lbcert")
        os.makedirs(root, exist_ok=True)
        path = os.path.join(root, "seen-observation.json")
        with open(path + ".lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                with open(path) as f:
                    previous = json.load(f)
                old = set(previous["ids"])
                last = float(previous["at"])
            except (OSError, ValueError, KeyError, TypeError):
                old, last = set(), 0
                # Carry historical first sightings across migration, but never
                # consider the first new observation itself a fresh release.
                try:
                    with open(os.path.join(root, "seen.json")) as f:
                        old = set(json.load(f))
                except (OSError, ValueError, TypeError):
                    pass
            if at <= last:
                return
            new = set(gaps) - old
            # A bootstrap or observation outage is not evidence of a fresh release.
            state.atomic_write(path, json.dumps({"ids": sorted(old | set(gaps)), "at": at}) + "\n")
            if last and at - last <= MAX_GAP:
                for gid in sorted(new):
                    ledger.mark("seen", gid)
    except (OSError, ValueError, KeyError, TypeError):
        # Observation must never block allocation/publication on local disk failure.
        return
