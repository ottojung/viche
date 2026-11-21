#!/usr/bin/env python3
"""Read-only Act 22 due-prediction agenda for independent resolution.

Not a scorer, not a verdict, not permission to backfill outcomes. Missing
evidence is a documented unresolved result, not a fabricated false/true event.
Runs during already authorized Clerk/Audit sessions, never wakes agents.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def iso(epoch):
    return datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).isoformat()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--now",type=int,default=int(time.time()))
    ap.add_argument("--limit",type=int,default=50)
    ap.add_argument("--offset",type=int,default=0)
    ap.add_argument("--resolver",choices=("all","c1a00001","c1a0000b"),
                    default="all")
    args=ap.parse_args()
    if args.offset < 0:
        raise SystemExit("predict-due: offset cannot be negative")
    if not 1 <= args.limit <= 50:
        raise SystemExit("predict-due: limit must be between 1 and 50")
    town=Path(os.environ.get("VICHE_TOWN_ROOT","/var/lib/lubko/wd/viche"))
    ledger=Path(os.environ.get("VICHE_PREDICT_LEDGER",
                             str(town/"records/predictions/ledger.json")))
    check=subprocess.run([sys.executable,str(town/"government/predict-ledger.py"),
                          "verify"],text=True,capture_output=True,timeout=15)
    if check.returncode:
        print(json.dumps({"integrity":"failed","alert":"Do not score a compromised ledger."}))
        return 1
    try:
        data=json.loads(ledger.read_text())
        if data.get("schema")!="act22-ledger-v1":
            raise ValueError("unsupported ledger schema")
        entries=data["entries"]
        resolutions={r["id"]:r for r in data["resolutions"]}
        day=datetime.datetime.fromtimestamp(args.now,datetime.timezone.utc).date()
        future=[];due=[];pending=[]
        for r in entries:
            if r.get("kind")!="registration":
                continue
            target=datetime.date.fromisoformat(r["resolution_date"])
            if target>day:
                future.append(target)
                continue
            due.append(r)
            if r["id"] not in resolutions:
                pending.append(r)
        pending.sort(key=lambda r:(r["resolution_date"],r["id"]))
        def resolver(r):
            return "c1a0000b" if r["author"]=="c1a00001" else "c1a00001"
        assigned=[r for r in pending if args.resolver=="all" or
                  resolver(r)==args.resolver]
        page=assigned[args.offset:args.offset+args.limit]
        items=[]
        for r in page:
            bill=town/"records/bills"/(r["bill_id"]+".md")
            withdrawn=False
            if bill.is_file() and not bill.is_symlink():
                withdrawn="WITHDRAWN" in bill.read_text(errors="replace")[:200]
            items.append({
                "id":r["id"],"author":r["author"],
                "required_resolver":resolver(r),
                "due_utc":r["resolution_date"],
                "days_past_due":(day-datetime.date.fromisoformat(r["resolution_date"])).days,
                "proposition":r["proposition"][:240],
                "evidence_source":r["evidence_source"][:180],
                "full_evidence_must_be_read_from_ledger":(
                    len(r["proposition"])>240 or len(r["evidence_source"])>180),
                "conditional_withdrawn_bill":withdrawn,
                "caution":"Examine exact primary evidence. If unavailable or counterfactual, resolve UNRESOLVED with reason, not an invented Brier score."
            })
        scored=sum(1 for r in due if r["id"] in resolutions and
                   resolutions[r["id"]].get("outcome") in ("true","false"))
        unable=sum(1 for r in due if r["id"] in resolutions and
                   resolutions[r["id"]].get("outcome")=="unresolved")
        print(json.dumps({
            "as_of_utc":iso(args.now),"integrity":"clean",
            "due":len(due),"scored":scored,"unresolved":unable,
            "awaiting_independent_resolution":len(pending),
            "awaiting_assigned_resolution":len(assigned),
            "resolver_filter":args.resolver,"offset":args.offset,
            "future_registered":len(future),
            "next_due_utc":min(future).isoformat() if future else None,
            "items":items,"truncated":args.offset+len(items)<len(assigned),
            "next_offset":args.offset+len(items)
                if args.offset+len(items)<len(assigned) else None,
            "no_auto_resolution":True,
            "review_note":"Clerk is Act 22 resolver except its own predictions; those require independent Audit c1a0000b. Report calibration coverage even when all cases are unresolved."
        },ensure_ascii=False,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(json.dumps({"integrity":"unreadable",
                          "alert":"Cannot interpret due ledger; no automatic scoring",
                          "error_type":type(exc).__name__}))
        return 1


if __name__=="__main__":
    sys.exit(main())
