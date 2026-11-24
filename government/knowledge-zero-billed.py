#!/usr/bin/env python3
"""Exact-ID zero-billed model policy shared by the Act34 wrapper and gate.

A model name containing ``-free`` is never billing evidence.  This module admits
only exact provider/model IDs recorded in a reviewed policy whose published
input, output and cache-read costs are all zero.  The policy expires so a
limited-time free offer cannot silently outlive its evidence.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA = "viche-zero-billed-model-policy-v1"
MODEL_ID = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
REQUIRED_COST = ("input", "output", "cache_read")
ALLOWED_COST = set(REQUIRED_COST + ("cache_write",))


def _zero(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and value == 0)


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("review_after must be a UTC timestamp")
    parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("review_after must include a timezone")
    return parsed


def load_verified(path, now=None):
    """Load a fresh policy and validate every exact-ID cost record."""
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("zero-billed policy schema invalid")
    source = data.get("source")
    if (not isinstance(source, dict) or source.get("url") != "https://opencode.ai/inference/v1/models"
            or not isinstance(source.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"])):
        raise ValueError("zero-billed provider-cost source invalid")
    review_after = _timestamp(data.get("review_after"))
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)
    if now >= review_after:
        raise ValueError("zero-billed provider-cost evidence expired")
    models = data.get("models")
    if not isinstance(models, dict) or not models:
        raise ValueError("zero-billed exact-ID policy empty")
    for mid, row in models.items():
        if not isinstance(mid, str) or not MODEL_ID.fullmatch(mid):
            raise ValueError("malformed zero-billed model id")
        provider, provider_model = mid.split("/", 1)
        if (not isinstance(row, dict) or row.get("provider") != provider
                or row.get("provider_model") != provider_model):
            raise ValueError("zero-billed provider/model identity mismatch: " + mid)
        cost = row.get("cost")
        if not isinstance(cost, dict) or any(k not in cost for k in REQUIRED_COST):
            raise ValueError("zero-billed cost dimensions missing: " + mid)
        if any(k not in ALLOWED_COST for k in cost):
            raise ValueError("unknown billing dimension: " + mid)
        if any(not _zero(cost[k]) for k in cost):
            raise ValueError("nonzero provider cost: " + mid)
    return data


def verified_subset(policy_path, ids, catalogue_models=None):
    """Return the exact, fresh, zero-cost subset in caller order.

    IDs absent from provider-cost evidence are omitted, not admitted. An empty
    result fails closed. This lets the general free rotation retain secondary-
    only offers while the Act34 path uses the primary-confirmed subset.
    """
    data = load_verified(policy_path)
    if not isinstance(ids, list):
        raise ValueError("model allowlist missing")
    selected = []
    for mid in ids:
        if not isinstance(mid, str):
            raise ValueError("malformed model id")
        if mid not in data["models"]:
            continue
        if catalogue_models is not None:
            if not isinstance(catalogue_models, dict) or catalogue_models.get(mid, {}).get("tier") != "free":
                raise ValueError("model not catalogued in Economy rotation: " + mid)
        selected.append(mid)
    if not selected:
        raise ValueError("no primary-confirmed zero-cost model in active policy")
    return selected


def negative_acceptance_digest(paths):
    """Digest the exact rejected-ID vector and control bytes.

    The vector includes a paid-looking ID that a name-derived catalogue marks
    free.  Passing the smoke test therefore proves the exact-ID cost policy,
    not the old suffix/tier inference, made the rejection decision.
    """
    names = (
        "provider/paid-free-trial",
        "provider/paid-free",
        "openai/gpt-6-luna",
        "opencode/hy4-flash-free:nonzero-cost",
        "opencode/hy4-flash-free:expired-evidence",
        "opencode-go/hy4-flash-free:gateway-only-omitted")
    payload = {"rejected_ids": names,
               "controls": {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                            for name, path in sorted(paths.items())}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def build_allowlist(policy_path, prefer_path, catalogue_path, output_path):
    """Build Antonina's per-invocation config from exact verified IDs."""
    policy = json.loads(Path(prefer_path).read_text(encoding="utf-8"))
    catalogue = json.loads(Path(catalogue_path).read_text(encoding="utf-8"))
    if not isinstance(catalogue, dict) or not isinstance(catalogue.get("models"), dict):
        raise ValueError("Economy catalogue missing/invalid")
    ids = verified_subset(policy_path, policy.get("prefer"), catalogue.get("models"))
    entries = [{"model": mid,
                "comment": "Economy exact-ID zero-cost policy; source-attested provider metadata"}
               for mid in ids]
    output = Path(output_path)
    output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output.parent, 0o700)
    fd, tmp = tempfile.mkstemp(prefix=".free-allow-", dir=str(output.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"models": entries}, handle, indent=2)
            handle.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, output)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return ids
