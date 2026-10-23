#!/usr/bin/env python3
"""Act 22 (Pre-Registered Prediction and Calibration Act) — ledger operations.

The Executive implements the mechanism (Acts 2/6); the Clerk exercises the
gatekeeper (§2), resolver (§3) and publisher (§5) duties. This file is the
deterministic, append-only ledger writer/reader. It records registrations,
rejections (no named evidence source), independent resolutions, and runs the
per-entry content-hash integrity check the Judiciary can run each window (§3.5,
§12). It performs no policy: it applies the recorded rules verbatim.

Ledger: records/predictions/ledger.json — an append-only list of immutable
entries. A correction is a NEW entry citing the original (§3.5); an entry is
never edited or deleted. The file is rewritten only to append.

Content hash (§3.5): sha256 over the canonical JSON of the registered
prediction's immutable content — bill id, proposition, probability, resolution
date, evidence source, author — computed at registration and committed before
the outcome-establishing evidence exists. Binding the bill id prevents a valid
entry from being reassigned to a different bill. Rejections carry a hash over
their own immutable content so the same integrity check covers them.

Usage:
  predict-ledger.py register --bill ID --proposition TEXT --probability P \
      --resolution-date DATE --evidence SOURCE --author SEAT [--cites ENTRY_ID]
  predict-ledger.py reject   --bill ID --proposition TEXT --author SEAT --reason TEXT
  predict-ledger.py resolve  --id ENTRY_ID --outcome true|false|unresolved \
      --resolver SEAT --evidence CITATION [--reason TEXT]
  predict-ledger.py verify
  predict-ledger.py show

Exit: register/resolve 0 ok, 1 rejected/refused; verify 0 clean, 1 defect(s).
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

SCHEMA = "act22-ledger-v1"
FALLBACK_RESOLVER = "c1a0000b"


def town_root() -> Path:
    return Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))


def ledger_path() -> Path:
    return Path(os.environ.get(
        "VICHE_PREDICT_LEDGER", str(town_root() / "records/predictions/ledger.json")))


def now_epoch() -> int:
    env = os.environ.get("VICHE_PREDICT_NOW")
    if env is not None:
        try:
            return int(env)
        except ValueError:
            pass
    return int(time.time())


def iso(epoch: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def load(path: Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "entries": [], "resolutions": []}
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise SystemExit("predict-ledger: ledger is not an object")
    data.setdefault("schema", SCHEMA)
    data.setdefault("entries", [])
    data.setdefault("resolutions", [])
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    tmp.replace(path)


def content_hash(entry: dict) -> str:
    """Canonical content hash over the immutable prediction fields (§3.5)."""
    if entry.get("kind") == "rejection":
        canon = {"kind": "rejection", "bill_id": entry.get("bill_id", ""),
                 "proposition": entry.get("proposition", ""),
                 "author": entry.get("author", ""), "reason": entry.get("reason", "")}
    else:
        canon = {"bill_id": entry.get("bill_id", ""),
                 "proposition": entry.get("proposition", ""),
                 "probability": entry.get("probability"),
                 "resolution_date": entry.get("resolution_date", ""),
                 "evidence_source": entry.get("evidence_source", ""),
                 "author": entry.get("author", "")}
    blob = json.dumps(canon, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def next_id(data: dict, bill_id: str, kind: str) -> str:
    n = 1 + sum(1 for e in data["entries"]
                if e.get("bill_id") == bill_id and e.get("kind") == kind)
    return "%s-%s-%d" % (bill_id, kind, n)


def cmd_register(a) -> int:
    path = ledger_path()
    data = load(path)
    if not (a.evidence or "").strip():
        # §3.1: a prediction lacking a named evidence source is rejected and the
        # rejection recorded (anti-vagueness signal, §3.6).
        entry = {"id": next_id(data, a.bill, "rejection"), "kind": "rejection",
                 "bill_id": a.bill, "proposition": a.proposition, "author": a.author,
                 "reason": "no named evidence source", "status": "rejected",
                 "registered_at": now_epoch(), "registered_iso": iso(now_epoch())}
        entry["content_hash"] = content_hash(entry)
        data["entries"].append(entry)
        save(path, data)
        print("predict-ledger: REJECTED (no named evidence source) %s" % entry["id"])
        return 1
    try:
        p = float(a.probability)
    except (TypeError, ValueError):
        print("predict-ledger: probability must be a number in (0,1)", file=sys.stderr)
        return 2
    if not (0.0 < p < 1.0):
        print("predict-ledger: probability must be in (0,1)", file=sys.stderr)
        return 2
    entry = {"id": next_id(data, a.bill, "registration"), "kind": "registration",
             "bill_id": a.bill, "proposition": a.proposition, "probability": p,
             "resolution_date": a.resolution_date, "evidence_source": a.evidence,
             "author": a.author, "self_reference": bool(a.self_reference),
             "status": "registered", "registered_at": now_epoch(),
             "registered_iso": iso(now_epoch())}
    if a.cites:
        entry["cites"] = a.cites
    entry["content_hash"] = content_hash(entry)
    data["entries"].append(entry)
    save(path, data)
    print("predict-ledger: registered %s (hash %s)" % (entry["id"], entry["content_hash"]))
    return 0


def cmd_resolve(a) -> int:
    path = ledger_path()
    data = load(path)
    target = next((e for e in data["entries"] if e.get("id") == a.id), None)
    if target is None:
        print("predict-ledger: no such entry: %s" % a.id, file=sys.stderr)
        return 2
    if target.get("kind") != "registration":
        print("predict-ledger: entry is not a registration: %s" % a.id, file=sys.stderr)
        return 2
    # §3.2: the author may not resolve their own prediction.
    if a.resolver == target.get("author"):
        print("predict-ledger: REFUSED — resolver %s is the author of %s "
              "(fallback resolver is %s)" % (a.resolver, a.id, FALLBACK_RESOLVER),
              file=sys.stderr)
        return 1
    if any(r.get("id") == a.id for r in data["resolutions"]):
        print("predict-ledger: already resolved: %s" % a.id, file=sys.stderr)
        return 1
    if a.outcome == "unresolved" and not (a.reason or "").strip():
        print("predict-ledger: unresolved requires a reason", file=sys.stderr)
        return 2
    if a.outcome in ("true", "false") and not (a.evidence or "").strip():
        print("predict-ledger: a scored resolution requires an evidence citation",
              file=sys.stderr)
        return 2
    resolved_at = now_epoch()
    res = {"id": a.id, "outcome": a.outcome, "resolver": a.resolver,
           "evidence_citation": a.evidence or "", "resolved_at": now_epoch(),
           "resolved_iso": iso(resolved_at)}
    if a.reason:
        res["reason"] = a.reason
    if res["resolved_at"] < int(target.get("registered_at", 0)):
        res["defect"] = "resolution_timestamp_precedes_registration"
    data["resolutions"].append(res)
    save(path, data)
    print("predict-ledger: resolved %s -> %s by %s" % (a.id, a.outcome, a.resolver))
    return 0


def cmd_verify(a) -> int:
    path = ledger_path()
    data = load(path)
    defects = []
    seen = set()
    for e in data["entries"]:
        eid = e.get("id")
        if eid in seen:
            defects.append({"id": eid, "defect": "duplicate_entry_id"})
        seen.add(eid)
        want = content_hash(e)
        if e.get("content_hash") != want:
            defects.append({"id": eid, "defect": "content_hash_mismatch",
                            "recorded": e.get("content_hash"), "recomputed": want})
    known = {e.get("id"): e for e in data["entries"] if e.get("kind") == "registration"}
    for r in data["resolutions"]:
        if r.get("defect"):
            defects.append({"id": r.get("id"), "defect": r["defect"]})
        target = known.get(r.get("id"))
        if target is None:
            defects.append({"id": r.get("id"), "defect": "resolution_without_registration"})
        elif r.get("resolver") == target.get("author"):
            defects.append({"id": r.get("id"), "defect": "author_self_resolved"})
        elif int(r.get("resolved_at", 0)) < int(target.get("registered_at", 0)):
            defects.append({"id": r.get("id"), "defect": "resolution_timestamp_precedes_registration"})
    resolution_ids = [r.get("id") for r in data["resolutions"]]
    for eid in set(resolution_ids):
        if resolution_ids.count(eid) > 1:
            defects.append({"id": eid, "defect": "duplicate_resolution"})
    out = {"schema": SCHEMA, "entries": len(data["entries"]),
           "resolutions": len(data["resolutions"]), "defects": defects}
    print(json.dumps(out, sort_keys=True))
    if defects:
        print("predict-ledger: INTEGRITY DEFECTS: %d" % len(defects), file=sys.stderr)
        return 1
    print("predict-ledger: integrity clean (%d entries, %d resolutions)"
          % (len(data["entries"]), len(data["resolutions"])))
    return 0


def cmd_show(a) -> int:
    print(json.dumps(load(ledger_path()), sort_keys=True, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Act 22 prediction ledger")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("register")
    r.add_argument("--bill", required=True)
    r.add_argument("--proposition", required=True)
    r.add_argument("--probability", required=True)
    r.add_argument("--resolution-date", required=True)
    r.add_argument("--evidence", default="")
    r.add_argument("--author", required=True)
    r.add_argument("--self-reference", action="store_true")
    r.add_argument("--cites", default="")
    r.set_defaults(fn=cmd_register)

    j = sub.add_parser("reject")
    j.add_argument("--bill", required=True)
    j.add_argument("--proposition", required=True)
    j.add_argument("--author", required=True)
    j.add_argument("--reason", required=True)
    j.set_defaults(fn=lambda a: _reject(a))

    s = sub.add_parser("resolve")
    s.add_argument("--id", required=True)
    s.add_argument("--outcome", required=True, choices=["true", "false", "unresolved"])
    s.add_argument("--resolver", required=True)
    s.add_argument("--evidence", default="")
    s.add_argument("--reason", default="")
    s.set_defaults(fn=cmd_resolve)

    sub.add_parser("verify").set_defaults(fn=cmd_verify)
    sub.add_parser("show").set_defaults(fn=cmd_show)

    a = ap.parse_args()
    return a.fn(a)


def _reject(a) -> int:
    path = ledger_path()
    data = load(path)
    entry = {"id": next_id(data, a.bill, "rejection"), "kind": "rejection",
             "bill_id": a.bill, "proposition": a.proposition, "author": a.author,
             "reason": a.reason, "status": "rejected",
             "registered_at": now_epoch(), "registered_iso": iso(now_epoch())}
    entry["content_hash"] = content_hash(entry)
    data["entries"].append(entry)
    save(path, data)
    print("predict-ledger: REJECTED %s (%s)" % (entry["id"], a.reason))
    return 0


if __name__ == "__main__":
    sys.exit(main())
