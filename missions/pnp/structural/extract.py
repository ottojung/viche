"""Read-only extraction of reusable finite lemmas from the public merged mirror.

The mirror is the authoritative public source (git objects under the PnP cache).
This module only reads objects; it never fetches, writes state, compiles Lean,
claims a lease, or publishes.  Extracted text carries the upstream Apache-2.0
attribution and the exact blob/revision it came from.
"""
import hashlib
import os
import re
import subprocess

from .. import config, gitctl

SOURCE_PATH = "lean/PEqualNP/Outside/L_meta_17487.lean"
# Exact revision used for this research pass; pinned so the evidence is
# reproducible even though the production mirror is fetched continuously.
PINNED_REVISION = "54000fdbe91c846adb213e5acde692ef02bec05f"
PINNED_BLOB = "1052b76494a2972ca5ee978fd4dfa6e60b9bd302"
LICENSE = "Apache-2.0"

# Verbatim generic block from the pinned blob: pack .. anyEq (no n/diffs).
_START = "def pack (xs : List Bool) := xs.foldr Nat.bit 0"
_END = "def input (rs : List (Bool × List Bool))"


def blob(mirror=None, revision=PINNED_REVISION, path=SOURCE_PATH):
    """Return (text, blob_sha) from the public mirror, read-only."""
    mirror = mirror or gitctl.MIRROR
    gd = "--git-dir=" + mirror
    sha = subprocess.check_output(
        ["git", gd, "rev-parse", revision + ":" + path], timeout=30).decode().strip()
    text = subprocess.check_output(
        ["git", gd, "cat-file", "blob", sha], timeout=30).decode("utf-8", "replace")
    if hashlib.sha1(b"blob %d\0" % len(text.encode()) + text.encode()).hexdigest() != sha:
        raise ValueError("mirror blob does not match its object id")
    return text, sha


def generic_block(text):
    """Slice the generic finite lemmas out of an exact upstream source."""
    i = text.find(_START)
    j = text.find(_END)
    if i < 0 or j <= i:
        raise ValueError("upstream source lacks the generic lemma block")
    return text[i:j].rstrip() + "\n"


def attribution(path=SOURCE_PATH, blob_sha=PINNED_BLOB,
                revision=PINNED_REVISION):
    return (
        "-- Reuses the finite bit-reflection lemmas from the public merged proof\n"
        "-- %s\n" % path +
        "-- upstream revision %s, blob %s\n" % (revision, blob_sha) +
        "-- Upstream project is licensed %s; those lemma statements and proof\n" % LICENSE +
        "-- skeletons are attributed to that source.  Parameterisation, assembly\n"
        "-- and the independent oracle are original research tooling.\n"
    )


def extract(mirror=None, revision=PINNED_REVISION):
    """Return an attributed generic lemma block from the exact public source."""
    text, sha = blob(mirror, revision)
    return {"path": SOURCE_PATH, "revision": revision, "blob": sha,
            "license": LICENSE, "block": generic_block(text),
            "header": attribution(SOURCE_PATH, sha, revision)}
