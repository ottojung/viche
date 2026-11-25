"""Bounded Antonina operations. Prompt files avoid ARG_MAX and secret argv."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import fcntl

from .. import assignment, config, gitctl, staff, state, support
from ..research import adoption, playbook
from . import plan


class Uncertain(RuntimeError):
    pass


class MissingAgent(Uncertain):
    pass


def wire(*args, timeout=12):
    p = subprocess.run(["antonina","agent",*args],capture_output=True,text=True,
                       timeout=timeout,check=True)
    return p.stdout.strip()


def object_row(text):
    row=json.loads(text)
    if not isinstance(row,dict):
        raise Uncertain("invalid backend response")
    return row


def running():
    # No destructive operations from partial/unreadable observations.
    rows={}
    for page in range(1,65):
        data=object_row(wire("list","--running","--page",str(page),"--limit","100","--json"))
        agents=data.get("agents")
        if not isinstance(agents,list) or data.get("unreadable"):
            raise Uncertain("running roster unavailable")
        for a in agents:
            if not isinstance(a,dict) or not isinstance(a.get("id"),str) or a["id"] in rows:
                raise Uncertain("unstable running roster")
            rows[a["id"]]=a
        if len(agents)<100:
            return list(rows.values())
    raise Uncertain("running roster exceeds bounded scan")


def status(aid):
    try:
        row=object_row(wire("status","--id",aid,"--json"))
    except subprocess.CalledProcessError as exc:
        if exc.returncode==3 and (exc.stderr or "").strip()=="antonina: unknown agent: "+aid:
            raise MissingAgent("agent deleted") from exc
        raise
    if row.get("id")!=aid or not isinstance(row.get("state"),str) or type(row.get("alive")) is not bool:
        raise Uncertain("agent identity unavailable")
    return row


def same(row,path):
    return (row.get("invocation_cwd") or row.get("cwd"))==path


def live(row):
    return row.get("state")=="running" and row.get("alive") is True


def known_terminal(row):
    return row.get("state") in staff._REUSABLE and row.get("alive") is False


def prepare(slot):
    if not slot.gap:
        Path(slot.path).mkdir(parents=True,exist_ok=True)
        return
    rec=state.load(slot.gap)
    if not plan.current(slot):
        raise Uncertain("assignment changed")
    path=Path(slot.path)
    base=slot.base or None
    if not (path/".git").exists() and not base:
        general=Path(state.gap_dir(slot.gap),"attempts",assignment.attempt_id(rec["lease"]),"workers/general/path")
        if slot.label!="general" and (general/".git").exists():
            base=subprocess.check_output(["git","-C",str(general),"rev-parse","HEAD"],text=True,timeout=5).strip()
        else:
            # Staffing never waits for a network fetch when a local public
            # mirror is available. The independent mirror refresh owns freshness.
            try:
                base=gitctl.run(["git","--git-dir="+gitctl.MIRROR,"rev-parse","refs/remotes/upstream/main"]).stdout.strip()
            except gitctl.GitError:
                # Bootstrap only if the local mirror/ref is absent. Serialize
                # the repair; other slots retry rather than race a clone.
                root=Path(config.CACHE_DIR);root.mkdir(parents=True,exist_ok=True)
                with (root/"staffing-mirror.lock").open("a+") as lock:
                    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    base=gitctl.ensure_mirror()
    result=assignment.prepare(slot.gap,worker=slot.label,base=base,expected=rec["lease"])
    if result["cwd"]!=slot.path or not plan.current(slot):
        raise Uncertain("assignment changed during preparation")


def new(slot):
    title=("Viche P vs NP research: "+slot.gap+" "+slot.label if slot.gap
           else support.PREFIX+" "+slot.label)
    aid=wire("new","--cwd",slot.path,"--title",title)
    if not re.fullmatch(r"[A-Za-z0-9_-]+",aid):
        raise Uncertain("unreadable created agent identity")
    return aid


def resource_ready():
    # Use the existing town memory safety policy, not a private worker cap.
    root=Path(__file__).resolve().parents[3]
    p=subprocess.run(["/bin/sh",str(root/"government/resource-safety.sh"),"pnp-staffing"],
                     capture_output=True,text=True,timeout=5)
    return p.returncode==0


def run(slot,aid):
    role=playbook.role_for(slot.label,slot.label=="general") if slot.gap else slot.label
    if slot.gap:
        rec=state.load(slot.gap)
        text=staff.prompt(rec,slot.task,slot.label=="general",slot.label)
        text+="\nContinue the durable mathematical work from this workspace. Do not end a pass after only reporting status. If no route remains, preserve exact exhaustion evidence for the evaluator."
    else:
        text=("Continue the durable support work in this workspace. Read current assignments and prior findings. "
              "Deliver concrete results and preserve them. No agent launches, lease acquisition or direct publication. "
              "Do not repeat identical work without new evidence.\n"+slot.task)
    text=playbook.guide(role)+"\n\n"+text
    did=adoption.planned(aid,Path(slot.path),role,text)
    with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",prefix="pnp-staff-",delete=True) as f:
        f.write(text);f.flush()
        if not plan.current(slot):
            raise Uncertain("assignment changed before run")
        row=object_row(wire("run","--id",aid,"--cwd",slot.path,"--prompt-file",f.name,
                           "--detach","--json",timeout=30))
    if row.get("id")!=aid or row.get("state")!="running":
        raise Uncertain("launch acknowledgement not confirmed")
    adoption.confirmed(did)
    if slot.gap and slot.label.startswith("ob-"):
        # Advisory assignment record; dispatch already happened.
        try:
            from contextlib import closing
            from ..research import knowledge
            import time
            with closing(knowledge.db()) as c,c:
                c.execute("INSERT OR REPLACE INTO assignment VALUES(?,?,?,?)",
                          (slot.label[3:],slot.attempt,slot.label,time.time()))
        except Exception:
            pass


def stop(aid):
    wire("stop","--id",aid,timeout=15)
