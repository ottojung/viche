"""Disabled-by-default, private, offline verification of canonical promise proofs.

No lease/PR operations, no production receipt writes, no network requests.
The Executive configures a private sparse checkout and separately enables
this service after the reviewed activation gate. Receipt promotion is NOT
part of this service. All Lean jobs use the canonical shared admission queue.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time

from .. import config, frontier, freshness, gitctl, host_boundary, research_workspace, state, validate
from ..research.obligations import axiom_guard, verify_report
from . import ready
from .generators.promise import gen

TOWN = Path("/var/lib/lubko/wd/viche")
PRODUCTION = Path("/var/lib/lubko/wd/viche-state/pnp")
PRIVATE = Path("/var/lib/lubko/wd/viche-state/pnp-prelease")
DECISION = "records/investigations/executive-sanctioned-prelease-proof-check-decision-20261126T2238Z.md"
CHECK_BUDGET = 120
BUILD_BUDGET = 300
SHA = re.compile(r"[0-9a-f]{40}")
DIGEST = re.compile(r"[0-9a-f]{64}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def deployment():
    return (socket.gethostname() == host_boundary.ALLOWED_HOST
            and Path(__file__).resolve().parents[3] == TOWN
            and Path(config.STATE_ROOT).resolve() == PRODUCTION
            and (TOWN / DECISION).is_file())


def private_dir():
    st = PRIVATE.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ValueError("private state must be an owner-only directory")
    if PRIVATE.resolve() != PRIVATE or PRIVATE == PRODUCTION:
        raise ValueError("unsafe private state root")
    return PRIVATE


def private_json(name):
    p = private_dir() / name
    st = p.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ValueError("not an owner-only private file: " + name)
    return json.loads(p.read_text())


def enablement():
    from missions.pnp import pause
    if not deployment() or pause.paused(PRODUCTION):
        return None
    try:
        cfg = private_json("enable.json")
        if (not isinstance(cfg, dict) or set(cfg) != {"base", "authorization"}
                or not isinstance(cfg["base"], str) or not SHA.fullmatch(cfg["base"])
                or not isinstance(cfg["authorization"], str) or not cfg["authorization"].strip()):
            return None
        pin = private_json("workspace.json")
        if pin != {"base": cfg["base"], "toolchain": config.LEAN_TOOLCHAIN}:
            return None
        return cfg
    except (OSError, ValueError, KeyError, TypeError):
        return None


def lock():
    fd = os.open(private_dir() / "checker.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BaseException:
        os.close(fd)
        raise


def git(*args, cwd):
    # Local object reads only, never fetch or mutate refs in a check.
    env={k:v for k,v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_NO_LAZY_FETCH="1",GIT_OPTIONAL_LOCKS="0")
    p = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args],
                       cwd=cwd, capture_output=True, text=True, timeout=10,
                       env=env)
    if p.returncode:
        raise ValueError("local git validation failed")
    return p.stdout.strip()


def public_base(base):
    if not isinstance(base, str) or not SHA.fullmatch(base):
        raise ValueError("invalid pinned public commit")
    if git("--git-dir="+gitctl.MIRROR, "rev-parse", base+"^{commit}", cwd=TOWN) != base:
        raise ValueError("pin is not a commit")
    git("--git-dir="+gitctl.MIRROR, "merge-base", "--is-ancestor",
        base, "refs/remotes/upstream/main", cwd=TOWN)


def workspace(base, scratch=None):
    public_base(base)
    w = private_dir() / "worktree"
    if not w.is_dir() or w.resolve() != w:
        raise ValueError("missing private pinned checkout")
    if git("rev-parse", "HEAD", cwd=w) != base:
        raise ValueError("workspace base changed")
    if Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=w)).resolve() != Path(gitctl.MIRROR).resolve():
        raise ValueError("workspace is not from the public mirror")
    if git("config", "--bool", "core.sparseCheckout", cwd=w) != "true":
        raise ValueError("workspace not sparse")
    expected = "" if scratch is None else "?? lean/" + scratch
    if git("status", "--porcelain=v1", "--untracked-files=all", cwd=w) != expected:
        raise ValueError("workspace is not clean")
    lean = w / "lean"
    if (lean / "lean-toolchain").read_text().strip() != config.LEAN_TOOLCHAIN:
        raise ValueError("toolchain mismatch")
    # Check the shared pinned dependency seed, never use a researcher override.
    seed = Path("/home/lubko/pequalnp-research-20261123/lean")
    if (lean / "lake-manifest.json").read_bytes() != (seed / "lake-manifest.json").read_bytes():
        raise ValueError("dependency pin mismatch")
    if lean.resolve()!=lean or (lean/".lake").is_symlink():
        raise ValueError("unexpected private build path")
    packages = lean / ".lake/packages"
    if packages.resolve() != (seed / ".lake/packages").resolve() or not packages.is_dir():
        raise ValueError("untrusted package cache")
    for item in json.loads((lean/"lake-manifest.json").read_text())["packages"]:
        if (item.get("type")!="git" or not re.fullmatch(r"[A-Za-z0-9_-]+",item.get("name",""))
                or not SHA.fullmatch(item.get("rev",""))):
            raise ValueError("unsupported dependency pin")
        dep=packages/item["name"]
        if git("rev-parse","HEAD",cwd=dep)!=item["rev"] or git("status","--porcelain=v1","--untracked-files=no",cwd=dep):
            raise ValueError("shared dependency differs from pin")
    return lean


def prepare(base):
    """Explicit operator setup: no compilation, no enabling, no network fetch."""
    if not deployment():
        raise ValueError("not canonical authorized deployment")
    public_base(base)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    fd = lock()
    try:
        if (PRIVATE / "enable.json").exists() or (PRIVATE / "worktree").exists():
            raise ValueError("refuse to replace an existing or enabled workspace")
        if os.environ.get("PNP_SHARED_LAKE"):
            raise ValueError("custom dependency cache forbidden")
        research_workspace.create(gitctl.MIRROR, PRIVATE / "worktree", base, ["PEqualNP.Defs"])
        gitctl.prepare_build_cache(str(PRIVATE / "worktree"))
        workspace(base)
        state.atomic_write(str(PRIVATE / "workspace.json"),
                           json.dumps({"base": base, "toolchain": config.LEAN_TOOLCHAIN}))
    finally:
        os.close(fd)


def metadata(gid):
    if not isinstance(gid, str) or not config.GAP_ID_RE.fullmatch(gid):
        raise ValueError("invalid gap id")
    cache = PRODUCTION / "lbcert/gaps-cache.json"
    meta = json.loads(Path(str(cache)+".meta").read_text())
    if not 0 <= time.time()-meta["at"] <= 120:
        raise ValueError("public catalog observation unavailable or stale")
    rows = [q for q in json.loads(cache.read_text())["gaps"] if q.get("id") == gid]
    if len(rows) != 1:
        raise ValueError("gap missing or ambiguous")
    return rows[0]


def audited(q, raw):
    """Admit only exact bytes reproduced by our literal-circuit emitter."""
    if len(raw) > config.MAX_FILE_BYTES or not raw:
        raise ValueError("candidate byte bound")
    try:
        validate.validate(q, raw)
    except validate.InvalidCandidate as e:
        raise ValueError("invalid candidate: "+str(e)) from e
    p = gen.parse(q["statement"])
    if p is None:
        raise ValueError("unsupported proof family")
    source = raw.decode("utf-8")
    sol = gen.lean_witness(p, source)
    if sol is None or not gen.valid(p, sol):
        raise ValueError("independent circuit audit failed")
    n, _, _ = gen.domain(p)
    if not 0 <= sol[1] < n+len(sol[0]):
        raise ValueError("output wire outside witness")
    if gen.emit(q["id"], q["statement"], p, sol).encode() != raw:
        raise ValueError("noncanonical proof bytes")
    return raw + axiom_guard(q["module"]).encode()


def artifact_digest():
    """Fingerprint the private import cache, not shared dependency packages."""
    root=PRIVATE/"worktree/lean/.lake/build/lib/lean"
    if root.resolve()!=root or not root.is_dir():
        raise ValueError("private artifact cache unavailable")
    h=hashlib.sha256()
    paths=sorted(root.rglob("*.olean"))
    if not paths:
        raise ValueError("private artifact cache empty")
    for p in paths:
        if p.is_symlink() or p.resolve()!=p or not p.is_file():
            raise ValueError("unexpected artifact path")
        digest=hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024),b""):
                digest.update(chunk)
        h.update(str(p.relative_to(root)).encode()+b"\0"+digest.digest())
    return h.hexdigest()


def build_ready(base):
    try:
        b = private_json("build.json")
        return (b == {"base": base, "toolchain": config.LEAN_TOOLCHAIN,"artifacts":artifact_digest()}
                and (PRIVATE / "worktree/lean/.lake/build/lib/lean/PEqualNP/Defs.olean").is_file())
    except (OSError, ValueError, TypeError):
        return False


def compiler_context(args, cwd):
    """Called by the canonical compiler before admission for this scoped mode."""
    cfg = enablement()
    if not cfg:
        raise ValueError("pre-lease checker disabled")
    job = private_json("job.json")
    if job.get("base") != cfg["base"] or job.get("authorization") != cfg["authorization"]:
        raise ValueError("job authorization changed")
    if os.readlink("/proc/self/ns/net") == job.get("host_net") or not job.get("host_net"):
        raise ValueError("job not in isolated network namespace")
    if args == ["lake", "build", "+PEqualNP.Defs"] and job.get("kind") == "build":
        scratch, budget = None, BUILD_BUDGET
    elif (len(args) == 4 and args[:3] == ["lake", "env", "lean"]
          and job.get("kind") == "check" and args[3] == job.get("file")
          and re.fullmatch(r"Prelease_[0-9a-f]{64}\.lean", args[3])):
        scratch, budget = args[3], CHECK_BUDGET
        if not build_ready(cfg["base"]):
            raise ValueError("pinned import cache not initialized")
    else:
        raise ValueError("not a pre-lease compiler operation")
    lean = workspace(cfg["base"], scratch)
    if Path(cwd).resolve() != lean:
        raise ValueError("compiler not in private checkout")
    if scratch:
        src = lean / scratch
        if src.is_symlink() or not src.is_file():
            raise ValueError("invalid temporary proof path")
        data = src.read_bytes()
        q = metadata(job["gap"])
        guard = axiom_guard(q["module"]).encode()
        if not data.endswith(guard):
            raise ValueError("missing trusted axiom guard")
        raw = data[:-len(guard)]
        if sha(raw) != job.get("sha256") or audited(q, raw) != data:
            raise ValueError("exact candidate changed")
    return cfg, budget


def managed(args, lean, cfg, job, budget):
    """Namespace kills every descendant on timeout, even a detached child."""
    if enablement() != cfg:
        return 75, "authorization changed"
    job = {**job, **cfg, "host_net": os.readlink("/proc/self/ns/net")}
    state.atomic_write(str(PRIVATE / "job.json"), json.dumps(job))
    cmd = ["/run/current-system/profile/bin/unshare", "--user", "--map-root-user",
           "--net", "--pid", "--fork", "--kill-child=SIGKILL", "--",
           *host_boundary.managed_compile_command(args)]
    cmd.insert(len(cmd)-len(args)-1, "--prelease")
    env = host_boundary.managed_compile_env()
    # No ambient assignment context, custom toolchain or cache overrides.
    for k in list(env):
        if k.startswith(("PNP_PUBLISH_", "LEAN_", "LAKE_", "ELAN_")) or k in ("PNP_POSTCHECK_SHA", "PNP_SHARED_LAKE"):
            env.pop(k, None)
    with tempfile.TemporaryFile(dir=PRIVATE) as out:
        try:
            p = subprocess.run(cmd, cwd=lean, env=env, stdout=out,
                               stderr=subprocess.STDOUT, timeout=budget+40)
            out.seek(max(0, out.tell()-32768))
            return p.returncode, out.read().decode("utf-8", "replace")
        except subprocess.TimeoutExpired:
            return 75, "bounded compiler timeout"
        finally:
            (PRIVATE / "job.json").unlink(missing_ok=True)


def initialize():
    cfg = enablement()
    if not cfg:
        return "disabled"
    fd = lock()
    try:
        lean = workspace(cfg["base"])
        rc, log = managed(["lake","build","+PEqualNP.Defs"], lean, cfg,
                          {"kind":"build"}, BUILD_BUDGET)
        if rc or enablement() != cfg:
            return "deferred"
        workspace(cfg["base"])
        if not (lean / ".lake/build/lib/lean/PEqualNP/Defs.olean").is_file():
            return "unavailable"
        state.atomic_write(str(PRIVATE/"build.json"),
                           json.dumps({"base":cfg["base"],"toolchain":config.LEAN_TOOLCHAIN,"artifacts":artifact_digest()}))
        return "initialized"
    finally:
        os.close(fd)


def check(gid, path):
    cfg = enablement()
    if not cfg:
        return {"status":"disabled"}
    fd = lock()
    try:
        if not build_ready(cfg["base"]):
            return {"status":"deferred","reason":"initialize pinned import cache first"}
        q = metadata(gid)
        with open(path,"rb") as f:
            raw = f.read(config.MAX_FILE_BYTES+1)
        guarded = audited(q, raw)
        digest = sha(raw)
        lean = workspace(cfg["base"])
        name = "Prelease_"+digest+".lean"
        scratch = lean/name
        with scratch.open("xb") as f:
            f.write(guarded)
        try:
            rc, log = managed(["lake","env","lean",name], lean, cfg,
                {"kind":"check","gap":gid,"sha256":digest,"file":name},CHECK_BUDGET)
            unchanged = scratch.read_bytes() == guarded
        finally:
            scratch.unlink(missing_ok=True)
        workspace(cfg["base"])
        if rc or not unchanged or enablement()!=cfg:
            return {"status":"deferred" if rc==75 or enablement()!=cfg else "unavailable",
                    "reason":"no exact successful check"}
        if not verify_report(log,q["module"]):
            return {"status":"unavailable","reason":"no trusted allowed-axiom report"}
        if not build_ready(cfg["base"]):
            return {"status":"deferred","reason":"private import cache changed"}
        if metadata(gid)["statement"] != q["statement"]:
            return {"status":"deferred","reason":"public statement changed"}
        receipt={"status":"ok","compiled":True,"sha256":digest,
                 "checked_base":cfg["base"],"gap":gid,"module":q["module"],
                 "statement_sha256":sha(q["statement"].encode()),
                 "guarded_sha256":sha(guarded),"toolchain":config.LEAN_TOOLCHAIN,
                 "axiom_report":log.strip().splitlines()[-1].strip(),
                 "compiler_log":log,"compiler_log_sha256":sha(log.encode()),
                 "authorization":cfg["authorization"],"at":time.time()}
        if not ready.exact_receipt(receipt,raw):
            raise ValueError("receipt identity mismatch")
        out = PRIVATE/"receipts"/cfg["base"]
        for parent in (PRIVATE/"receipts",out):
            parent.mkdir(mode=0o700,exist_ok=True)
            st=parent.lstat()
            if not stat.S_ISDIR(st.st_mode) or parent.resolve()!=parent or st.st_uid!=os.getuid() or st.st_mode&0o077:
                raise ValueError("unsafe private receipt directory")
        state.atomic_write(str(out/(gid+"-"+digest+".lean")), raw.decode())
        state.atomic_write(str(out/(gid+"-"+digest+".json")),json.dumps(receipt,sort_keys=True))
        return receipt
    finally:
        os.close(fd)


def staged_candidates(cfg, now=None):
    """Read-only intake of staged local bytes. No stock promotion or claims."""
    now=time.time() if now is None else now
    cache=PRODUCTION/"lbcert/gaps-cache.json"
    meta=json.loads(Path(str(cache)+".meta").read_text())
    if not 0<=now-meta["at"]<=120:
        return []
    snap=frontier.load(now)
    if not snap.get("complete"):
        return []
    rows=snap["gaps"]; seen=freshness.recent(now)
    eligible={}
    for q in json.loads(cache.read_text())["gaps"]:
        gid=q.get("id"); row=rows.get(gid,{})
        if not isinstance(gid,str) or not config.GAP_ID_RE.fullmatch(gid):
            continue
        if (not row or q.get("pr_open")!=0
                or type(row.get("held")) is not int or type(row.get("parallel")) is not int
                or row["held"]>=row["parallel"] or row["held"]!=0):
            continue
        if not gen.parse(q.get("statement") or ""):
            continue
        r=state.load(gid)
        if r and (r.get("pr_number") or r.get("state") not in ("RELEASED","STALE")):
            continue
        if ready.verified(gid):
            continue
        eligible[gid]=q
    options={}
    def add(gid, raw, observed):
        q=eligible.get(gid)
        if not q or not raw or len(raw)>config.MAX_FILE_BYTES:
            return
        digest=sha(raw);key=(gid,digest)
        receipt=PRIVATE/"receipts"/cfg["base"]/(gid+"-"+digest+".json")
        attempt=PRIVATE/"attempts"/(gid+"-"+digest+".json")
        if receipt.is_file():
            return
        try:
            a=json.loads(attempt.read_text())
            if a.get("base")==cfg["base"] and now<a["retry"]:
                return
        except (OSError,ValueError,KeyError,TypeError):
            pass
        try:audited(q,raw)
        except (ValueError,KeyError,TypeError):
            return
        rank=(gid not in seen, -seen.get(gid,0), -observed,
              -(rows[gid].get("points") or 0), gid)
        options[key]=(rank,gid,raw)
    db=PRODUCTION/"lbcert/promise-batch.sqlite"
    try:
        with contextlib.closing(sqlite3.connect(f"file:{db}?mode=ro",uri=True,timeout=2)) as conn:
            for gid,source,observed in conn.execute(
                    "SELECT gap,source,observed FROM attempt WHERE status='staged' AND source IS NOT NULL ORDER BY observed DESC LIMIT 128"):
                if isinstance(source,str):add(gid,source.encode(),observed)
    except sqlite3.Error:
        pass
    # Canonical generator output files are read only, never edited by intake.
    cands=PRODUCTION/"lbcert/cands"
    candidates=[]
    for gid in eligible:
        p=cands/(gid+".lean")
        try:
            st=p.stat()
            if st.st_size<=config.MAX_FILE_BYTES and p.is_file():
                candidates.append((st.st_mtime,gid,p))
        except OSError:
            pass
    for observed,gid,p in sorted(candidates,reverse=True)[:128]:
        try:add(gid,p.read_bytes(),observed)
        except OSError:pass
    return sorted(options.values(),key=lambda x:x[0])


def once():
    cfg=enablement()
    if not cfg:
        return {"status":"disabled"}
    if not build_ready(cfg["base"]):
        return {"status":"deferred","reason":"initialize first"}
    options=staged_candidates(cfg)
    if not options:
        return {"status":"idle"}
    _,gid,raw=options[0]
    with tempfile.NamedTemporaryFile(dir=PRIVATE,suffix=".lean") as f:
        f.write(raw);f.flush()
        result=check(gid,f.name)
    # Private retry evidence; deferral preserves the staged source.
    folder=PRIVATE/"attempts"
    folder.mkdir(mode=0o700,exist_ok=True)
    st=folder.lstat()
    if not stat.S_ISDIR(st.st_mode) or folder.resolve()!=folder or st.st_uid!=os.getuid() or st.st_mode&0o077:
        raise ValueError("unsafe private attempt directory")
    if result.get("status")!="ok":
        state.atomic_write(str(folder/(gid+"-"+sha(raw)+".json")),
            json.dumps({"base":cfg["base"],"retry":time.time()+60,
                        "status":result.get("status")}))
    return result


def serve():
    """Explicit Executive-launched single service, no production supervisor effects."""
    cfg=enablement()
    if not cfg:
        return "disabled"
    fd=os.open(private_dir()/"service.lock",os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        while enablement()==cfg:
            try:
                result=once()
                print(json.dumps({k:result[k] for k in ("status","gap","sha256") if k in result}),flush=True)
            except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as exc:
                print(json.dumps({"status":"deferred","reason":str(exc)[:150]}),flush=True)
            time.sleep(10)
        return "authorization ended"
    finally:
        os.close(fd)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode",required=True)
    sub.add_parser("status")
    sub.add_parser("initialize")
    sub.add_parser("once")
    sub.add_parser("serve")
    p = sub.add_parser("prepare");p.add_argument("base")
    p = sub.add_parser("check");p.add_argument("gap");p.add_argument("candidate")
    a = ap.parse_args()
    try:
        if a.mode=="status":
            cfg=enablement()
            result={"enabled":bool(cfg),"base":cfg["base"] if cfg else None,
                    "initialized":bool(cfg and build_ready(cfg["base"]))}
        elif a.mode=="prepare":
            prepare(a.base);result={"status":"prepared, not enabled"}
        elif a.mode=="initialize":result={"status":initialize()}
        elif a.mode=="once":result=once()
        elif a.mode=="serve":result={"status":serve()}
        else:result=check(a.gap,a.candidate)
        print(json.dumps(result,sort_keys=True))
        return 0
    except (OSError,ValueError,TypeError,KeyError,gitctl.GitError,subprocess.SubprocessError) as e:
        print(json.dumps({"status":"unavailable","reason":str(e)[:250]}))
        return 75


if __name__=="__main__":
    sys.exit(main())
