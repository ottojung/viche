"""Single-controller durable intents, bounded observations and health."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import time

from .. import state
from . import policy


def connect():
    root = policy.root()
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    c = sqlite3.connect(root/"controller.sqlite", timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=FULL")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS slots(key TEXT PRIMARY KEY, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(at REAL, slot TEXT, kind TEXT, detail TEXT);
        CREATE INDEX IF NOT EXISTS events_at ON events(at);
        CREATE TABLE IF NOT EXISTS coverage(at REAL PRIMARY KEY, desired INTEGER,
             running INTEGER, unknown INTEGER, general_desired INTEGER, general_running INTEGER);
    """)
    return c


@contextmanager
def db():
    c = connect()
    try:
        with c:
            yield c
    finally:
        c.close()


def get(key):
    with db() as c:
        r = c.execute("SELECT data FROM slots WHERE key=?",(key,)).fetchone()
    return json.loads(r[0]) if r else {}


def put(key, data, event=None):
    with db() as c:
        c.execute("INSERT OR REPLACE INTO slots VALUES(?,?)",(key,json.dumps(data,sort_keys=True)))
        if event:
            c.execute("INSERT INTO events VALUES(?,?,?,?)",
                      (time.time(),key,event,json.dumps({k:data.get(k) for k in
                        ("agent","phase","reason","failures","next_at")})))


def health(data):
    p = policy.root()/"health.json"
    state.atomic_write(str(p),json.dumps(data,sort_keys=True,indent=2)+"\n")


def read_health():
    try:
        x=json.loads((policy.root()/"health.json").read_text())
        x["age_seconds"]=round(max(0,time.time()-x["at"]),1)
        x["stale"]=x["age_seconds"]>60
        if x["stale"]:
            x["state"]="stale"
        return x
    except (OSError,ValueError,KeyError,TypeError):
        return {"state":"unknown"}


def sample(rows, now):
    general=[r for r in rows if r["label"]=="general"]
    with db() as c:
        c.execute("INSERT OR REPLACE INTO coverage VALUES(?,?,?,?,?,?)",
                  (now,len(rows),sum(r["phase"]=="running" for r in rows),
                   sum(r["phase"]=="unknown" for r in rows),len(general),
                   sum(r["phase"]=="running" for r in general)))
        # Bounded history; slot/intent identity is not discarded.
        c.execute("DELETE FROM coverage WHERE at<?",(now-7*86400,))
        c.execute("DELETE FROM events WHERE at<?",(now-30*86400,))


def metrics(hours=1):
    with db() as c:
        rows=c.execute("SELECT * FROM coverage WHERE at>=? ORDER BY at",(time.time()-hours*3600,)).fetchall()
        events=dict(c.execute("SELECT kind,count(*) FROM events WHERE at>=? GROUP BY kind",
                              (time.time()-hours*3600,)).fetchall())
    # Integrate observed samples; do not fill outages with invented coverage.
    desired=covered=unknown=unobserved=0.0
    for a,b in zip(rows,rows[1:]):
        span=max(0,b["at"]-a["at"])
        dt=min(60,span)
        unobserved+=span-dt
        desired+=dt*a["general_desired"]
        covered+=dt*a["general_running"]
        unknown+=dt*a["unknown"]
    return {"hours":hours,"samples":len(rows),"general_slot_seconds":desired,
            "general_covered_seconds":covered,"unknown_slot_seconds":unknown,
            "general_coverage":covered/desired if desired else None,"unobserved_seconds":unobserved,"events":events}
