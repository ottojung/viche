"""Fixed, non-overridable configuration for the PnP contribution workflow.

Nothing in this module may be set from a research worker's prompt or candidate
file.  Only the operator CLI may choose a gap id and a local candidate path.
"""
import os
import re

# Numeric GitHub identities are immutable across account/repository renames.
UPSTREAM_ID = 1468025030
FORK_ID = 1469318535
CONTRIBUTOR_ID = 121908118
# Preserve the historical human checker identity. The official intake GitHub
# App began publishing verdicts on 2026-11-24. Both its numeric bot account
# and performed_via_github_app identity must match (never just a login).
CHECKER_ID = 275416420
CHECKER_INTAKE_BOT_ID = 360790873
CHECKER_INTAKE_APP_ID = 5908013
BASE_REF = "main"

# The external desk and public scoreboard identify participants by handle,
# not GitHub numeric ID. This is the authorized mission's credit target.
DESK_HANDLE = "ottojung"

AUTHOR_NAME = "Otto Jung"
AUTHOR_EMAIL = "otto.jung@vauplace.com"
SIGNING_KEY = "08AF2726387BD4A4C87DF1821BEDDF96D7B1BA2B!"

DESK_BASE = "https://pequalnp.com/desk"
JOIN_URL = "https://pequalnp.com/join.txt"
HEADER = "https://pequalnp.com/a/" + DESK_HANDLE

STATE_ROOT = os.environ.get(
    "PNP_STATE_ROOT", "/var/lib/lubko/wd/viche-state/pnp"
)
GAPS_DIR = os.path.join(STATE_ROOT, "gaps")
WORKTREES_DIR = os.path.join(STATE_ROOT, "worktrees")
CACHE_DIR = os.path.join(STATE_ROOT, "cache")
DOCS_CACHE = os.path.join(CACHE_DIR, "join.txt")

GH_CLI = "/home/lubko/.local/bin/gh-pequalnp"
TOKEN_FILE = os.path.expanduser("~/.config/viche-pequalnp/pr-token")
TOKEN_FINE = os.path.expanduser("~/.config/viche-pequalnp/token")
GIT_AUTH_HELPER = os.path.join(os.path.dirname(__file__), "git-auth.sh")

LEAN_TOOLCHAIN = "leanprover/lean4:v4.36.0"
MAX_FILE_BYTES = 512 * 1024
MAX_LEASES = 5
BEAT_INTERVAL_SECONDS = 9 * 60       # live docs: renew every 10 minutes
LEASE_TTL_SECONDS = 20 * 60          # live docs: 20 min after last renewal
REQUEST_MIN_INTERVAL = 3.0           # be gentle with the desk

# Desk gap ids are opaque but constrained (e.g. L-meta-582, L-gct-086).
GAP_ID_RE = re.compile(r"^L-[a-z0-9]+(?:-[a-z0-9]+)*$")
BRANCH_RE = re.compile(r"^pnp/[a-z0-9][a-z0-9_/-]{0,80}$")
RELEASE_REASONS = {
    "missing_lemma", "hypothesis_too_weak", "statement_seems_false",
    "does_not_elaborate", "out_of_time", "other", "exhausted", "submitted",
}

STATES = (
    "DISCOVERED", "LEASED", "RESEARCHING", "CANDIDATE_READY",
    "LOCAL_CHECKED", "SIGNED", "PUSHED", "PR_OPEN", "ACCEPTED",
    "REJECTED", "FAULT", "RELEASED", "STALE",
)
ALLOWED = {
    "DISCOVERED": {"LEASED", "RELEASED", "FAULT"},
    "LEASED": {"RESEARCHING", "RELEASED", "STALE", "FAULT"},
    "RESEARCHING": {"CANDIDATE_READY", "RELEASED", "STALE", "FAULT"},
    "CANDIDATE_READY": {"LOCAL_CHECKED", "SIGNED", "RESEARCHING", "RELEASED",
                        "STALE", "FAULT"},
    "LOCAL_CHECKED": {"SIGNED", "RESEARCHING", "RELEASED", "STALE", "FAULT"},
    "SIGNED": {"PUSHED", "FAULT"},
    "PUSHED": {"PR_OPEN", "FAULT"},
    "PR_OPEN": {"ACCEPTED", "REJECTED", "STALE", "FAULT"},
    "REJECTED": {"RESEARCHING", "SIGNED", "FAULT", "STALE"},
    "FAULT": {"RESEARCHING", "RELEASED", "PR_OPEN"},
}


def branch_for(gap_id):
    """A fresh, deterministic branch name unique to the leased gap."""
    if not GAP_ID_RE.match(gap_id):
        raise ValueError("bad gap id")
    return "pnp/" + gap_id.lower().replace("-", "_")
