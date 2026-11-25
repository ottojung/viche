#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from missions.pnp.metrics import replay

def e(second, kind, **detail):
    return {"at":f"2026-11-24T00:00:{second:02d}Z","kind":kind,"detail":detail}

from missions.pnp.metrics import timestamp
now=timestamp("2026-11-24T00:01:00Z")
a,p,c,m=replay([
    e(0,"acquired"),e(2,"state",to="CANDIDATE_READY"),
    e(3,"state",to="CANDIDATE_READY"),e(5,"published",pr=7,sha="a"),
    e(6,"published",pr=7,sha="b"),e(7,"postcheck",local_check_status="failed"),
    e(9,"postcheck"),e(10,"state",to="ACCEPTED",sha="b"),
    e(12,"acquired"),e(20,"state",to="STALE"),
    e(22,"acquired"),e(23,"acquired"),e(25,"portfolio_release"),e(26,"acquired"),{"bad":True}
],now)
assert [x["outcome"] for x in a]==["submitted","stale","superseded","released","active"]
assert [x["slot_seconds"] for x in a]==[5,8,1,2,34]
assert a[0]["candidate"]-a[0]["start"]==2
assert len(p)==1 and p[7]["accepted"]-p[7]["first"]==5
assert c=={"failed":1,"deferred_or_unspecified":1} and m==1
print("metrics replay: OK")
