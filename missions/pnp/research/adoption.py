"""Measure prompt delivery and actual agent tool use without collecting proof text."""
import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from .. import config, assignment

def db():
    p=Path(config.STATE_ROOT)/"research"
    p.mkdir(parents=True,exist_ok=True,mode=0o700)
    c=sqlite3.connect(p/"adoption.sqlite",timeout=1)
    c.row_factory=sqlite3.Row
    c.executescript("""
    CREATE TABLE IF NOT EXISTS dispatch(
      id TEXT PRIMARY KEY, agent TEXT, cwd TEXT, role TEXT, prompt_hash TEXT,
      started REAL, confirmed INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS dispatch_agent ON dispatch(agent,started);
    CREATE TABLE IF NOT EXISTS use_event(
      id TEXT PRIMARY KEY, dispatch TEXT, agent TEXT, invocation TEXT,
      role TEXT, command TEXT, started REAL, elapsed REAL, exit INTEGER
    );
    CREATE INDEX IF NOT EXISTS use_dispatch ON use_event(dispatch,started);
    """)
    return c

def planned(agent,cwd,role,prompt):
    """Before invoking Antonina; evidence does not gate dispatch."""
    import hashlib
    did=uuid.uuid4().hex
    try:
        with closing(db()) as c,c:
            c.execute("INSERT INTO dispatch VALUES(?,?,?,?,?,?,0)",
                      (did,agent,str(Path(cwd).resolve()),role,
                       hashlib.sha256(prompt.encode()).hexdigest(),time.time()))
        return did
    except (OSError,sqlite3.Error):return None

def confirmed(did):
    if not did:return
    try:
        with closing(db()) as c,c:c.execute("UPDATE dispatch SET confirmed=1 WHERE id=?",(did,))
    except (OSError,sqlite3.Error):pass

def lookup(c,agent,cwd,at):
    return c.execute("SELECT * FROM dispatch WHERE agent=? AND started<=? ORDER BY started DESC LIMIT 1",
                     (agent,at)).fetchone()

def current_role():
    agent=os.environ.get("ANTONINA_AGENT_ID")
    if not agent:return None
    try:
        with closing(db()) as c:
            row=lookup(c,agent,Path.cwd(),time.time())
            return row["role"] if row else None
    except (OSError,sqlite3.Error):return None

def record(command,started,code):
    agent=os.environ.get("ANTONINA_AGENT_ID")
    # Operator smoke tests are not agent adoption. No command args, source,
    # credentials or prompt content are stored.
    if not agent:return
    try:
        with closing(db()) as c,c:
            row=lookup(c,agent,Path.cwd(),started)
            c.execute("INSERT INTO use_event VALUES(?,?,?,?,?,?,?,?,?)",
              (uuid.uuid4().hex,row["id"] if row else None,agent,
               os.environ.get("ANTONINA_INVOCATION_ID"),row["role"] if row else None,
               command,started,max(0,time.time()-started),code))
    except (OSError,sqlite3.Error):pass

def command_name(argv):
    if len(argv)<2:return "help"
    group=argv[1]
    if "--help" in argv or "-h" in argv:return group+" help"
    if group in ("knowledge","obligations"):
        return group+" "+(argv[2] if len(argv)>2 else "help")
    return group if group in ("start","guide","star","yield","adoption","dispatch","certificate") else "unknown"

def meaningful(command):
    return command not in {"start","guide","help","adoption","dispatch","knowledge stats"} and not command.endswith(" help")

def report(hours=24):
    now=time.time()
    with closing(db()) as c:
        launches=[dict(r) for r in c.execute("SELECT * FROM dispatch WHERE confirmed=1 AND started>=? ORDER BY started DESC",(now-hours*3600,))]
        uses=[dict(r) for r in c.execute("SELECT * FROM use_event WHERE started>=?",(now-hours*3600,))]
    by={}
    for d in launches:
        events=[u for u in uses if u["dispatch"]==d["id"]]
        actual=[u for u in events if meaningful(u["command"])]
        d["discovered"]=any(u["command"]=="start" for u in events)
        d["used"]=bool(actual)
        d["successful_use"]=any(u["exit"]==0 for u in actual)
        d["first_use_seconds"]=round(min(u["started"] for u in actual)-d["started"],2) if actual else None
        d["commands"]=sorted(set(u["command"] for u in events))
        role=by.setdefault(d["role"],{"launches":0,"discovered":0,"used":0,"successful_use":0})
        role["launches"]+=1
        for key in ("discovered","used","successful_use"):role[key]+=int(d[key])
        del d["cwd"]
    commands={}
    for u in uses:
        row=commands.setdefault(u["command"],{"calls":0,"successful":0})
        row["calls"]+=1;row["successful"]+=int(u["exit"]==0)
    return {"hours":hours,"roles":by,"commands":commands,"launches":launches[:40],
            "unmatched_agent_calls":sum(u["dispatch"] is None for u in uses),
            "note":"Agent environment attribution; successful command is not a proof or credited contribution."}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--hours",type=float,default=24)
    a=p.parse_args();print(json.dumps(report(a.hours),indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
