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

TREE=Path("/home/lubko/pnp-verify-2171/up2")      # kept at origin/main, Defs rebuilt (sib-handler)
TREE_LOCK=Path.home()/".local/state/sibling/tree.lock"


def seed_from_tree(directory, seeds):
    """A definitions change upstream (2026-11-26: Defs/BranchingProgram, Defs/Represents) left no
    seed for any recent base, so every exact-base check answered "no pinned cache" for hours.
    When main's dependency tree has no seed, copy the sibling tree's already-built Defs into a
    new immutable cache directory and write its manifest, modelled on an existing seed (same
    packages, toolchain, image and runner).  The alias pass then covers the other bases."""
    import fcntl,shutil,stat
    head_fp=fingerprint("main")
    if head_fp in seeds or not seeds:
        return None
    template_manifest,template_provenance=next(iter(seeds.values()))
    TREE_LOCK.parent.mkdir(parents=True,exist_ok=True)
    with open(TREE_LOCK,"w") as lk:
        fcntl.flock(lk,fcntl.LOCK_SH)          # the tree does not move while we read it
        base=subprocess.check_output(["git","-C",str(TREE),"rev-parse","HEAD"],text=True,timeout=10).strip()
        if not SHA.fullmatch(base) or fingerprint(base)!=head_fp:
            return None                         # tree not at this dependency tree yet: next pass
        if subprocess.run(["git","-C",str(TREE),"status","--porcelain","--","lean/PEqualNP/Defs","lean/PEqualNP/Defs.lean"],
                          capture_output=True,text=True,timeout=30).stdout.strip():
            return None
        env=dict(os.environ,PATH=str(Path.home()/".elan/bin")+":"+os.environ.get("PATH",""))
        if subprocess.run(["lake","build","--no-build","PEqualNP.Defs"],cwd=str(TREE/"lean"),env=env,
                          capture_output=True,timeout=300).returncode!=0:
            return None                         # Defs build not current
        src=TREE/"lean/.lake/build/lib/lean/PEqualNP"
        dest=ROOT/"cache"/base/"lean"/"PEqualNP"
        if (ROOT/"cache"/base).exists():
            return None
        tmp=Path(tempfile.mkdtemp(dir=ROOT/"cache"))
        (tmp/"lean"/"PEqualNP").mkdir(parents=True)
        for p in src.iterdir():
            if p.name=="Defs" or p.name.startswith("Defs."):
                (shutil.copytree if p.is_dir() else shutil.copy2)(p,tmp/"lean"/"PEqualNP"/p.name)
    for p in sorted(tmp.rglob("*"),reverse=True):
        p.chmod(p.stat().st_mode&~(stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH))
    tmp.chmod(0o755)
    os.replace(tmp,ROOT/"cache"/base)
    manifest=dict(template_manifest,base=base,
                  libraries=[l for l in template_manifest["libraries"] if "/pnp-remote/cache/" not in l]
                  +[str(dest.parent)])
    provenance={k:v for k,v in template_provenance.items() if k not in ("equivalent_to","dependency_tree")}
    provenance.update(base=base,source="Defs build of the sibling tree at this base, seeded by refresh-cache.py")
    for name,value in ((base+".provenance.json",provenance),(base+".json",manifest)):
        atomic(directory/name,value)
        (directory/name).chmod(0o600)
    return base


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
    try:
        new=seed_from_tree(directory,seeds)
    except (OSError,ValueError,subprocess.SubprocessError) as exc:
        new=None
        print("remote cache seed deferred:",type(exc).__name__,str(exc)[:200],flush=True)
    if new:
        print("remote cache seeded:",new,flush=True)
        seeds[fingerprint(new)]=(json.loads((directory/(new+".json")).read_text()),
                                 json.loads((directory/(new+".provenance.json")).read_text()))
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
