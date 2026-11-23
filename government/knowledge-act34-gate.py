#!/usr/bin/env python3
"""Act34 broad adaptive office authorization, no first-sample or value gate.

Enactment + reviewed written Executive permit + actual Economy config must be
valid before a model-using office dispatches. Judiciary inspects real work
WITHIN 48h after start, and any HOLD/STOP blocks immediately. The gate itself
is pure: no model, bills, file writes or mutable session side-effects.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

OFFICES = ("statistics", "foresight", "strategy", "spying")
TITLE = "## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act (enacted "
WINDOW = 45 * 86400
REVIEW = 48 * 3600


def fail(reason):
    print("Act34 %s: HOLD: %s" % (sys.argv[1] if len(sys.argv) > 1 else "?", reason),
          file=sys.stderr)
    return 1


def load(path):
    return json.loads(path.read_text())


def on_main(root, path):
    rel = path.relative_to(root).as_posix()
    actual = path.read_bytes()
    committed = subprocess.run(["git", "-C", str(root), "show", "HEAD:" + rel],
                               check=True, capture_output=True, timeout=8).stdout
    if hashlib.sha256(actual).digest() != hashlib.sha256(committed).digest():
        raise ValueError("unreviewed canonical bytes: " + rel)
    return hashlib.sha256(actual).hexdigest()


def check(office, root):
    if office not in OFFICES:
        raise ValueError("unknown office")
    laws = (root / "government/LAWS.md").read_text()
    if sum(line.startswith(TITLE) for line in laws.splitlines()) != 1:
        raise ValueError("exactly one enacted Act34 required")
    on_main(root, root / "government/LAWS.md")
    activation = root / "records/knowledge/activation.json"
    budget = root / "government/knowledge-budget.conf"
    on_main(root, activation)
    budget_hash = on_main(root, budget)
    record = load(activation)
    if record.get("schema") != "viche-knowledge-activation-v1":
        raise ValueError("malformed activation schema")
    a = record.get("offices", {}).get(office, {})
    now = int(time.time())
    values = (a.get("not_before"), a.get("expires_at"))
    if (a.get("enabled") is not True or a.get("authorized_by") != "act:34:" + office
            or a.get("trial_mode") != "adaptive-v1" or a.get("signer") != "c1e00002"
            or any(type(x) is not int for x in values)
            or not values[0] <= now < values[1]
            or not 0 < values[1] - values[0] <= WINDOW):
        raise ValueError("missing/expired Executive adaptive office permit")
    ref = a.get("permit_ref")
    if not isinstance(ref, str) or not re.fullmatch(
            r"records/knowledge/permits/(statistics|foresight|strategy|spying)[.]json", ref):
        raise ValueError("operating permit ref missing or malformed")
    if ref != "records/knowledge/permits/" + office + ".json":
        raise ValueError("permit belongs to another office")
    permit_path = root / ref
    permit_hash = on_main(root, permit_path)
    if a.get("permit_sha256") != permit_hash:
        raise ValueError("written Executive permit digest mismatch")
    permit = load(permit_path)
    cfg = load(budget)
    caps = cfg.get("offices", {}).get(office, {})
    if (caps.get("enabled") is not True
            or permit.get("schema") != "viche-act34-operating-permit-v1"
            or permit.get("office") != office
            or permit.get("signer") != "c1e00002"
            or permit.get("authorized_by") != "act:34:" + office
            or permit.get("not_before") != values[0]
            or permit.get("expires_at") != values[1]
            or permit.get("budget_sha256") != budget_hash
            or permit.get("caps") != caps.get("caps")
            or permit.get("provider_budget_mode") != "measured-stop-on-detection"
            or permit.get("inflight_overrun_risk_disclosed") is not True
            or permit.get("cancellation") != "stop-agent-and-hold-budget"
            or permit.get("reboot_recovery") != "reconcile-held-liability"):
        raise ValueError("Executive permit is not bound to real active Economy budget")
    review_path = root / ("records/knowledge/pilot-reviews/" + office + ".json")
    # An early adverse Judiciary decision is immediately binding.
    if review_path.exists():
        on_main(root, review_path)
        rev = load(review_path)
        reviewed = rev.get("reviewed_at")
        if (rev.get("schema") != "viche-act34-judiciary-review-v1"
                or rev.get("office") != office or rev.get("reviewer") != "c1e00008"
                or rev.get("permit_sha256") != permit_hash
                or type(reviewed) is not int
                or not values[0] <= reviewed < values[0] + REVIEW
                or reviewed > now):
            raise ValueError("uncorroborated or stale Judiciary disposition")
        if rev.get("decision") != "proceed":
            raise ValueError("Judiciary HOLD/STOP")
    elif now >= values[0] + REVIEW:
        raise ValueError("Judiciary review missing 48h after initial start")
    if office == "spying":
        # The caller separately runs the source-bundle preflight. A missing
        # bundle is never made a green result by this authorization gate.
        if not (root / "records/knowledge/spying-source-scope.json").is_file():
            raise ValueError("Spying permitted source-scope bundle absent")


def main():
    if len(sys.argv) != 3:
        return fail("usage: knowledge-act34-gate.py OFFICE TOWN_ROOT")
    try:
        check(sys.argv[1], Path(sys.argv[2]).resolve())
        return 0
    except (OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        return fail(str(exc)[:300])


if __name__ == "__main__":
    raise SystemExit(main())
