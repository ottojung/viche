"""Immutable, content-addressed Lean fragments for parallel formalization."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from .. import assignment, config, state, support


def share(file, message, cwd=None):
    cwd = Path(cwd or Path.cwd())
    bound = assignment.binding(cwd)
    found = assignment.workspace(cwd)
    if not bound or not found:
        raise ValueError("run in a bound research workspace")
    if not isinstance(message,str) or not message.strip() or len(message)>3500:
        raise ValueError("describe the fragment's theorem and status")
    gap, lease = bound
    file = Path(file).resolve()
    if file.suffix != ".lean" or not file.is_relative_to(found[1].resolve()) or not file.is_file():
        raise ValueError("share a Lean source in your own workspace")
    with file.open("rb") as f:
        data = f.read(config.MAX_FILE_BYTES+1)
    if len(data)>config.MAX_FILE_BYTES or not data:
        raise ValueError("fragment is empty or exceeds the proof size limit")
    source = data.decode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    try:
        base = subprocess.check_output(["git","-C",str(found[1]),"rev-parse","HEAD"],
                                       text=True,timeout=5).strip()
    except (OSError,subprocess.SubprocessError):
        base = None
    with state.lock(gap):
        rec = state.load(gap)
        if not support.active(rec) or rec["lease"] != lease:
            raise ValueError("assignment ended")
        folder = support.directory(rec)/"fragments"
        path = folder/(digest+".lean")
        info = {"digest":digest,"attempt":support.attempt(rec),"worker":assignment.worker_label(cwd),
                "source":file.name,"base":base,"bytes":len(data),"message":message,
                "verified_by_tool":False,"at":time.time()}
        if not path.exists():
            state.atomic_write(str(path),source)
        meta = folder/(digest+".json")
        if not meta.exists():
            state.atomic_write(str(meta),json.dumps(info,ensure_ascii=False)+"\n")
    # Reuse the existing peer evidence channel, not a new approval process.
    try:
        support.finding(str(path),message,cwd)
    except ValueError:
        pass
    return {**info,"path":str(path)}


def inventory(all_attempts=False,cwd=None):
    bound=assignment.binding(Path(cwd or Path.cwd()))
    if not bound:
        raise ValueError("run in a bound research workspace")
    gap,lease=bound
    rec=state.load(gap)
    if not support.active(rec) or rec["lease"]!=lease:
        raise ValueError("assignment ended")
    root=Path(state.gap_dir(gap),"support")
    dirs=list(root.glob("*/fragments")) if all_attempts else [support.directory(rec)/"fragments"]
    result=[]
    for folder in dirs:
        for meta in sorted(folder.glob("*.json")):
            if not re.fullmatch(r"[0-9a-f]{64}",meta.stem):
                continue
            try:
                obj=json.loads(meta.read_text())
                file=meta.with_suffix(".lean")
                if file.stat().st_size>config.MAX_FILE_BYTES or hashlib.sha256(file.read_bytes()).hexdigest()!=meta.stem or obj.get("digest")!=meta.stem:
                    continue
                result.append({**obj,"path":str(file),"current_attempt":obj.get("attempt")==support.attempt(rec)})
            except (OSError,ValueError,AttributeError):
                continue
    return result
