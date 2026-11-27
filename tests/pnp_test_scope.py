"""Hermetic PnP fixtures even when unittest imported production modules first."""
from contextlib import ExitStack
import os
from pathlib import Path
import sys
from unittest.mock import patch


def enter(root):
    from missions.pnp import config, gitctl
    root = str(Path(root).resolve())
    # All fixture callers use a private temporary directory.
    if not Path(root).parent.name.startswith(("pnp-tests-", "pnp-real-smoke-")):
        raise ValueError("not a private PnP test root")
    stack = ExitStack()
    cache = os.path.join(root, "cache")
    stack.enter_context(patch.dict(os.environ, {"PNP_STATE_ROOT": root}))
    stack.enter_context(patch.multiple(config, STATE_ROOT=root,
        GAPS_DIR=os.path.join(root, "gaps"),
        WORKTREES_DIR=os.path.join(root, "worktrees"), CACHE_DIR=cache,
        DOCS_CACHE=os.path.join(cache, "join.txt")))
    stack.enter_context(patch.object(gitctl, "MIRROR", os.path.join(cache, "fork.git")))
    # Cached constants in modules which other unittest suites may have loaded.
    work = os.path.join(root, "lbcert")
    for name, values in (
        ("missions.pnp.fastlane", {"WORK": work, "CANDS": os.path.join(work, "cands")}),
        ("missions.pnp.lbcert.live", {"STATE": root, "CACHE": os.path.join(work, "live.json"),
            "STATUS_CACHE": os.path.join(work, "status-cache.json"),
            "GAPS_CACHE": os.path.join(work, "gaps-cache.json")}),
        ("live", {"STATE": root, "CACHE": os.path.join(work, "live.json"),
            "STATUS_CACHE": os.path.join(work, "status-cache.json"),
            "GAPS_CACHE": os.path.join(work, "gaps-cache.json")}),
    ):
        module = sys.modules.get(name)
        if module:
            stack.enter_context(patch.multiple(module, **values))
    return stack
