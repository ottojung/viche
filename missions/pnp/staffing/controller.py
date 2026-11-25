"""Single-writer, independently supervised desired-state reconciliation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
import time

from .. import staff
from . import backend, plan, policy, reconcile, store


def tick():
    now=time.time()
    p=policy.load()
    # The lock also fences legacy helpers during the migration.
    with staff.staffing_lock():
        running=backend.running()
        issues=[]
        slots=plan.desired(p,running,issues)
        # Known positions do not wait for the historical registry scan.
        # Cold/ambiguous identities need complete history before creating.
        warm=[];cold=[]
        for s in slots:
            if store.get(s.key).get("agent") or any(backend.same(a,s.path) for a in running):
                warm.append(s)
            else:
                cold.append(s)
        rows=[]
        def finish(s,f):
            try:
                row=f.result()
            except Exception as exc:
                row={"phase":"unknown","reason":"slot error "+type(exc).__name__}
            rows.append({"key":s.key,"label":s.label,"gap":s.gap,
                         **{k:row.get(k) for k in ("phase","reason","agent","vacant_since","next_at","failures","started","activity","model")}})
        def history_scan():
            try:
                return staff.roster()
            except reconcile.ERRORS:
                return None
        with ThreadPoolExecutor(max_workers=1) as scan:
            history_future=scan.submit(history_scan) if cold and not p["paused"] else None
            with ThreadPoolExecutor(max_workers=p["parallel"]) as pool:
                jobs=[(s,pool.submit(reconcile.reconcile,s,p,running,None))
                      for s in sorted(warm,key=lambda s:s.priority)]
                # Known positions already reconcile while the scan is underway.
                history=history_future.result() if history_future else None
                jobs.extend((s,pool.submit(reconcile.reconcile,s,p,running,history))
                            for s in sorted(cold,key=lambda s:s.priority))
                for s,f in jobs:
                    finish(s,f)
        # Retire exact obsolete agents independently, never arbitrary processes.
        retired=[]
        if not p["paused"]:
            for a in running:
                try:
                    if plan.obsolete(a,slots):
                        fresh=backend.status(a["id"])
                        if backend.live(fresh) and plan.obsolete(fresh,slots):
                            backend.stop(a["id"])
                            retired.append(a["id"])
                except reconcile.ERRORS:
                    pass
        t=time.time()
        store.sample(rows,t)
        out={"at":t,"last_good_at":t,"state":"paused" if p["paused"] else "degraded" if issues or any(r["phase"]=="unknown" for r in rows) else "healthy" if all(r["phase"] in ("running","completed") for r in rows) else "reconciling","issues":issues,
             "duration":round(t-now,3),"slots":rows,"retired":retired,
             "desired":len(rows),"running":sum(r["phase"]=="running" for r in rows),
             "unknown":sum(r["phase"]=="unknown" for r in rows)}
        store.health(out)
        return out


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command",choices=("tick","status","metrics","policy","set-policy","pause","resume"),default="status",nargs="?")
    ap.add_argument("--hours",type=float,default=1)
    ap.add_argument("--json",help="JSON object of policy fields to update")
    args=ap.parse_args()
    if args.command=="status":
        print(json.dumps(store.read_health(),indent=2));return 0
    if args.command=="metrics":
        if not 0<args.hours<=168:
            ap.error("metrics window must be within 0–168 hours")
        print(json.dumps(store.metrics(args.hours),indent=2));return 0
    if args.command=="policy":
        print(json.dumps(policy.load(),indent=2));return 0
    if args.command in ("set-policy","pause","resume"):
        if Path(__file__).resolve().parents[3]!=Path("/var/lib/lubko/wd/viche") or policy.root()!=Path("/var/lib/lubko/wd/viche-state/pnp/staffing"):
            ap.error("policy edits require canonical deployment")
        try:
            patch=json.loads(args.json or "{}") if args.command=="set-policy" else {"paused":args.command=="pause"}
            if not isinstance(patch,dict) or not patch:
                raise ValueError("nonempty policy object required")
            print(json.dumps(policy.change(lambda p:{**p,**patch}),indent=2))
            return 0
        except (OSError,ValueError,TypeError) as exc:
            ap.error(str(exc))
    # Only the canonical launcher can mutate live state. Hermetic tests call
    # the pure tick with an isolated state root and mocked backend.
    if (Path(__file__).resolve().parents[3]!=Path("/var/lib/lubko/wd/viche")
            or os.environ.get("PNP_STAFFING_DAEMON")!="1"
            or policy.root()!=Path("/var/lib/lubko/wd/viche-state/pnp/staffing")):
        ap.error("live ticks belong to canonical staffing daemon")
    try:
        result=tick()
        print(json.dumps({k:v for k,v in result.items() if k!="slots"}),flush=True)
        return 0
    except Exception as exc:
        # Preserve previous evidence while making uncertainty explicit.
        previous=store.read_health()
        t=time.time()
        rows=[{**r,"phase":"unknown"} for r in previous.get("slots",[])]
        if rows:
            try:store.sample(rows,t)
            except Exception:pass
        store.health({**previous,"at":t,"state":"unknown","slots":rows,
                      "running":None,"unknown":len(rows),
                      "reason":type(exc).__name__,"last_good_at":previous.get("last_good_at",previous.get("at"))})
        print("staffing tick deferred: "+type(exc).__name__,file=sys.stderr,flush=True)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
