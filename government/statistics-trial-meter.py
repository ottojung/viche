#!/usr/bin/env python3
"""Prospective, source-attested Act 32 business-as-usual resource snapshots.

Does NOT assert any verified OUTCOME or authorize activation. It provides the
previously missing reproducible resource-denominator methodology for a matched
pre/post comparison, to be interpreted by Economy and independently by Judiciary.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import time
import urllib.parse

SCHEMA = "viche-statistics-resource-snapshot-v1"
FIELDS = ("tokens_input","tokens_output","tokens_reasoning",
          "tokens_cache_read","tokens_cache_write")
VICHE_PREFIX="/var/lib/lubko/wd/viche-seats/"
VICHE_ROOT="/var/lib/lubko/wd/viche"
DEFAULT_DB="/home/lubko/.local/state/antonina/opencode-service/opencode.db"


def host_cpu():
    # Same monotone whole-host upper-bound method as the Act 32 budget patch,
    # kept independent so the preactivation baseline can be captured first.
    import re
    boot=Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}",boot):
        raise ValueError("host boot identifier invalid")
    with Path("/proc/stat").open() as file:
        fields=file.readline().split()
    if len(fields)<9 or fields[0]!="cpu":
        raise ValueError("host CPU counters unavailable")
    ticks=[int(x) for x in fields[1:9]]
    if any(x<0 for x in ticks):
        raise ValueError("host CPU counter is invalid")
    hz=os.sysconf("SC_CLK_TCK")
    if not isinstance(hz,int) or hz<=0:
        raise ValueError("invalid host CPU tick rate")
    return {"cpu_seconds":sum(ticks[i] for i in (0,1,2,5,6,7))/hz,
            "cpu_boot_id":boot,"cpu_available":True,
            "cpu_source":"proc-stat-host-busy-upper-bound-v1",
            "cpu_attribution":"conservative-whole-host-upper-bound"}


def sessions(db):
    if not Path(db).is_file():
        raise ValueError("OpenCode authoritative SQLite meter is missing")
    uri="file:"+urllib.parse.quote(str(db),safe="/")+"?mode=ro"
    with sqlite3.connect(uri,uri=True,timeout=10) as con:
        con.execute("PRAGMA query_only=ON")
        con.execute("BEGIN")
        fields=",".join(("id","directory","time_created","time_updated")+FIELDS)
        columns={r[1] for r in con.execute("PRAGMA table_info(session_v2)")}
        if not set(("id","directory","time_created","time_updated")+FIELDS)<=columns:
            raise ValueError("OpenCode meter schema lacks required fields")
        rows=con.execute("SELECT "+fields+" FROM session_v2").fetchall()
    result={}
    for row in rows:
        sid,directory,created,updated,*tokens=row
        if not isinstance(sid,str) or not sid:
            raise ValueError("OpenCode meter has malformed session identifier")
        if not isinstance(directory,str):
            raise ValueError("OpenCode meter directory cannot be classified")
        if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in tokens):
            raise ValueError("OpenCode token counters unavailable or invalid")
        if (not isinstance(created,int) or not isinstance(updated,int)
                or updated<created):
            raise ValueError("OpenCode session timestamps invalid")
        if directory!=VICHE_ROOT and not directory.startswith(VICHE_PREFIX):
            continue
        result[sid]={"directory":directory,"time_created_ms":created,
                     "time_updated_ms":updated,
                     "tokens":dict(zip(FIELDS,tokens))}
    return result,len(rows)


def snapshot(db):
    cpu=host_cpu()
    session_data,all_rows=sessions(db)
    return {"schema":SCHEMA,"created_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "time_epoch_ms":int(time.time()*1000),"cpu":cpu,
            "token_meter":{"source":"opencode-service-session-v2",
                           "viche_coverage":"exact directory /var/lib/lubko/wd/viche or prefix /var/lib/lubko/wd/viche-seats/",
                           "sessions_in_viche_directory":len(session_data),
                           "all_host_sessions":all_rows},
            "sessions":session_data,
            "caveat":"Host CPU is an UPPER BOUND, not per-office actual. Directory selection may include Viche-related development rather than official office work."}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def write_new(path,obj):
    path=Path(path)
    if path.is_symlink():
        raise ValueError("refusing symlinked snapshot")
    path.parent.mkdir(parents=True,mode=0o700,exist_ok=True)
    if path.parent.is_symlink():
        raise ValueError("refusing symlinked snapshot directory")
    raw=(json.dumps(obj,sort_keys=True,indent=2)+"\n").encode()
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,"wb") as dest:
            dest.write(raw)
            dest.flush()
            os.fsync(dest.fileno())
        folder=os.open(str(path.parent),os.O_RDONLY|os.O_DIRECTORY)
        try: os.fsync(folder)
        finally: os.close(folder)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return hashlib.sha256(raw).hexdigest()


def compare(before,after):
    if before.get("schema")!=SCHEMA or after.get("schema")!=SCHEMA:
        raise ValueError("snapshot schema mismatch")
    a=before["cpu"];b=after["cpu"]
    if a.get("cpu_boot_id")!=b.get("cpu_boot_id"):
        raise ValueError("host reboot during window; split windows by boot")
    if a.get("cpu_source")!="proc-stat-host-busy-upper-bound-v1" or b.get("cpu_source")!=a.get("cpu_source"):
        raise ValueError("host CPU meter method changed")
    start=before["time_epoch_ms"];end=after["time_epoch_ms"]
    if not all(isinstance(x,int) for x in (start,end)) or end<=start:
        raise ValueError("window duration invalid")
    c1=a["cpu_seconds"];c2=b["cpu_seconds"]
    if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (c1,c2)) or c2<c1:
        raise ValueError("host CPU counter reset")
    prev=before["sessions"];curr=after["sessions"]
    if not isinstance(prev,dict) or not isinstance(curr,dict):
        raise ValueError("session source missing")
    if set(prev)-set(curr):
        raise ValueError("OpenCode sessions vanished; no complete token denominator")
    totals=dict.fromkeys(FIELDS,0)
    by_directory={}
    new_count=0
    for sid,item in curr.items():
        old=prev.get(sid)
        if old is not None and item["directory"]!=old["directory"]:
            raise ValueError("OpenCode session directory changed")
        if old is None:
            new_count+=1
            if item["time_created_ms"]<start:
                raise ValueError("newly observed session predates baseline; source incomplete")
        delta={}
        for key in FIELDS:
            current=item["tokens"][key]
            previous=old["tokens"][key] if old else 0
            if (isinstance(current,bool) or not isinstance(current,int) or current<previous
                    or not isinstance(previous,int) or isinstance(previous,bool)):
                raise ValueError("OpenCode token counter reset or unavailable")
            delta[key]=current-previous
            totals[key]+=delta[key]
        d=by_directory.setdefault(item["directory"],dict.fromkeys(FIELDS,0))
        for key in FIELDS: d[key]+=delta[key]
    return {
        "schema":"viche-statistics-resource-window-v1",
        "start":before["created_at_utc"],"end":after["created_at_utc"],
        "duration_seconds":(end-start)/1000,
        "viche_directory_tokens":sum(totals.values()),
        "tokens_by_category":totals,
        "sessions_begin":len(prev),"sessions_end":len(curr),"new_sessions":new_count,
        "host_cpu_upper_bound_seconds":round(c2-c1,3),
        "host_cpu_attribution":"all-host-busy-upper-bound",
        "by_directory":by_directory,
        "source_snapshot_sha256":{"start":digest(before),"end":digest(after)},
        "outcome_numerator":None,
        "independent_factual_verdict":None,
        "honest_limit":"Token directory matching includes Viche development, not necessarily only government offices; CPU includes other projects. No verified outcome benefit is asserted."
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest="cmd",required=True)
    take=subs.add_parser("capture");take.add_argument("--out",required=True)
    take.add_argument("--db",default=DEFAULT_DB)
    diff=subs.add_parser("compare");diff.add_argument("--before",required=True)
    diff.add_argument("--after",required=True)
    args=parser.parse_args()
    try:
        if args.cmd=="capture":
            obj=snapshot(args.db)
            sha=write_new(args.out,obj)
            print(json.dumps({"captured":args.out,"sha256":sha,
                              "viche_session_count":len(obj["sessions"]),
                              "verified_outcome":False},sort_keys=True))
        else:
            a=json.loads(Path(args.before).read_text())
            b=json.loads(Path(args.after).read_text())
            print(json.dumps(compare(a,b),sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError,sqlite3.Error) as exc:
        print("statistics-trial-meter: "+str(exc),file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    sys.exit(main())
