"""Load public checked-corpus metadata for graph-circuit-construction rows.

Only public corpus metadata is read. The loader uses the upstream proof-corpus
index built by missions.pnp.proofs.corpus and filters rows whose statements
match the finite graph-circuit construction shape recognized by
missions.pnp.proofs.synthesis.parse.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
import re
import sqlite3
from pathlib import Path

from missions.pnp import config
from missions.pnp.proofs import synthesis


DEFAULT_DB = Path(config.CACHE_DIR) / "proof-corpus.sqlite"


def _open_ro(path):
    path = Path(path)
    uri = f"file:{path}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=15)


def checked_timestamps(export):
    """Use official public checked-step times, never PR creation or module order."""
    entries = export.get("contributors", export.get("entries"))
    if not isinstance(entries, list):
        raise ValueError("missing public contributor entries")
    times = {}
    for entry in entries:
        for lemma in entry.get("lemmas", []):
            gid, at = lemma.get("id"), lemma.get("at")
            if not isinstance(gid, str) or not re.fullmatch(r"L-[a-z]+-[0-9]+", gid):
                continue
            try:
                dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    continue
                canonical = dt.astimezone(timezone.utc).isoformat(timespec="microseconds")
            except (AttributeError, TypeError, ValueError):
                continue
            # Keep the earliest recorded checked event if there are duplicates.
            times[gid] = min(times.get(gid, canonical), canonical)
    return times


def load_graph_circuits(db_path=DEFAULT_DB, limit=None, timestamps=None):
    """Return checked-corpus graph-circuit construction metadata rows.

    Each row contains only public metadata derived from the checked corpus:
    path, module, blob, n, bound, edges, edge_count, imports, statement. The
    statement is included because it is public checked proof metadata and is
    needed for independent evaluation; callers should not treat it as private.
    """
    db = _open_ro(db_path)
    try:
        rows = db.execute(
            "select path, blob, statement, imports from proof order by path"
        ).fetchall()
    finally:
        db.close()

    out = []
    for path, blob, statement, imports_json in rows:
        parsed = synthesis.parse(statement)
        if not parsed:
            continue
        n, bound, edges = parsed
        module = path.removeprefix("lean/").removesuffix(".lean").replace("/", ".")
        out.append(
            {
                "path": path,
                "module": module,
                "blob": blob,
                "n": n,
                "bound": bound,
                "edges": [list(e) for e in sorted(edges)],
                "edge_count": len(edges),
                "imports": json.loads(imports_json),
                "statement": statement,
            }
        )
        if timestamps is not None:
            gid = module.split(".")[-1].replace("_", "-")
            out[-1]["checked_at"] = timestamps.get(gid)
        if limit is not None and len(out) >= limit:
            break
    return out


def family_key(row):
    """Stable family label for holdouts.

    Family is based on the public structural shape: input count and edge count.
    This keeps holdouts coarse and avoids memorizing individual instances.
    """
    return f"n{row['n']}-e{row['edge_count']}"


def time_key(row):
    """Stable chronological-ish key for time-based holdouts.

    Uses the numeric suffix in the module name when present; falls back to path.
    This is a public metadata ordering, not a private timestamp.
    """
    module = row.get("module", "")
    digits = "".join(ch if ch.isdigit() else " " for ch in module).split()
    if digits:
        return (0, int(digits[-1]), module)
    return (1, 0, row.get("path", ""))
