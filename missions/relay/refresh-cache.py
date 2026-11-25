#!/usr/bin/env python3
"""Refresh small exact-base aliases for identical upstream Lean definition trees."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

ROOT=Path.home()/".local/share/viche/pnp-remote"
PATHS=("lean/PEqualNP/Defs","lean/PEqualNP/Defs.lean","lean/lean-toolchain",
       "lean/lake-manifest.json","lean/lakefile.toml")
SHA=re.compile(r"[0-9a-f]{40}")
UPSTREAM="https://github.com/open-goat/pequalnp-proofs.git"

def git(*args):
    return subprocess.check_output(["git","--git-dir="+str(ROOT/"upstream.git"),*args],
                                   text=True,timeout=90,stderr=subprocess.DEVNULL).strip()

def atomic(p,value):
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,"w") as f:
            json.dump(value,f,sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def fingerprint(rev):
    value=git("ls-tree",rev,"--",*PATHS)
    if len(value.splitlines())!=len(PATHS):
        raise ValueError("incomplete dependency tree")
    return value

def refresh():
    directory=ROOT/"manifests"
    if git("remote","get-url","origin")!=UPSTREAM:
        raise ValueError("unexpected upstream")
    git("fetch","--no-tags","origin","+refs/heads/main:refs/heads/main")
    seeds={}
    for p in directory.glob("*.provenance.json"):
        data=json.loads(p.read_text())
        base=data["base"]
        if data.get("equivalent_to") or not SHA.fullmatch(base):
            continue
        imports=git("grep","-h","^import PEqualNP\\.",base,"--",PATHS[0],PATHS[1])
        if any(not line.startswith("import PEqualNP.Defs.") for line in imports.splitlines()):
            continue
        seeds[fingerprint(base)]=(json.loads((directory/(base+".json")).read_text()),data)
    if not seeds:raise ValueError("no verified seed caches")
    recent=git("rev-list","--first-parent","--max-count=160","main").splitlines()
    count=0
    for base in recent:
        m=directory/(base+".json")
        p=directory/(base+".provenance.json")
        if m.is_file() and p.is_file():continue
        seed=seeds.get(fingerprint(base))
        if seed is None:continue
        manifest,provenance=seed
        atomic(p,dict(provenance,base=base,equivalent_to=manifest["base"],dependency_tree=fingerprint(base)))
        atomic(m,dict(manifest,base=base))
        count+=1
    # Keep older aliases for still-running assignments, with a bounded history.
    aliases=[]
    for p in directory.glob("*.provenance.json"):
        data=json.loads(p.read_text())
        if data.get("equivalent_to") and data["base"] not in recent:
            aliases.append((p.stat().st_mtime,p,data["base"]))
    for _,p,base in sorted(aliases,reverse=True)[512:]:
        (directory/(base+".json")).unlink(missing_ok=True)
        p.unlink(missing_ok=True)
    return count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--loop",action="store_true")
    args=p.parse_args()
    while True:
        try:
            n=refresh()
            if n:print("remote cache aliases added:",n,flush=True)
        except Exception as exc:
            print("remote cache refresh deferred:",type(exc).__name__,flush=True)
            if not args.loop:return 1
        if not args.loop:return 0
        time.sleep(120)

if __name__=="__main__":
    raise SystemExit(main())
