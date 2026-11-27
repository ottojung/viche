"""First-sighting evidence from complete, timely public frontier observations."""
import fcntl
import json
import os
import time

from . import freshness, ledger, state

MAX_GAP = freshness.OBSERVATION_MAX_GAP


def record(snapshot, now=None):
    now = time.time() if now is None else now
    try:
        at = float(snapshot["observed"])
        gaps = snapshot["gaps"]
        if not snapshot.get("complete") or not isinstance(gaps, dict) or not 0 <= now - at <= 45:
            return
        path = freshness.observation_path()
        root = os.path.dirname(path)
        os.makedirs(root, exist_ok=True)
        with open(path + ".lock", "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                with open(path) as f:
                    previous = json.load(f)
                old = set(previous["ids"])
                last = float(previous["at"])
                prior = previous.get("recent", {})
                if not isinstance(prior, dict):
                    prior = {}
            except (OSError, ValueError, KeyError, TypeError):
                old, last, prior = set(), 0, {}
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
            # First sightings and their recent index commit in one atomic write.
            # A bootstrap, clock jump, or observation outage is not freshness.
            continuous = bool(last and at - last <= MAX_GAP)
            recent = {}
            if continuous:
                recent = {g: t for g, t in prior.items()
                          if g in old and type(t) in (int, float)
                          and t <= last and 0 <= at - t <= freshness.WINDOW}
                recent.update({g: at for g in new})
            state.atomic_write(path, json.dumps({"ids": sorted(old | set(gaps)),
                                                "at": at, "recent": recent}) + "\n")
            if continuous:
                for gid in sorted(new):
                    ledger.mark("seen", gid)
    except (OSError, ValueError, KeyError, TypeError):
        # Observation must never block allocation/publication on local disk failure.
        return
