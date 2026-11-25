"""Bulk lane: publish ready machine-generated proofs for open desk steps the town does not hold.

Why (evidence, 2026-11-25): families are posted in batches of hundreds and are cleared within an hour
by agents that open one PR every few seconds for every instance they can prove (78 PRs in 18 minutes
by one agent); the desk credits the first accepted PR (join.txt: "the pull request is what counts").
Founder decision 2026-11-25: Viche does the same for proofs its generators produce.

Rules: only steps with pr_open == 0 on a fresh desk read and no PR from us; candidates come from
PNP_STATE_ROOT/lbcert/cands (status ok: lb_cert certificates, compile-gated monotone and sibling
proofs); every file passes missions.pnp.validate first; same fork, signed identity, branch scheme and
PR shape as the publisher (gitctl/github). Rate-limited. Held steps stay with the fast lane.

run: python3 -m missions.pnp.bulk   (allocator.sh keeps one running)   stop: touch PNP_STATE_ROOT/bulk/STOP
"""
import fcntl
import json
import os
import sys
import time
import urllib.request

from . import cli, config, gitctl as git, github as gh, validate

WORK = os.path.join(config.STATE_ROOT, "bulk")
CANDS = os.path.join(config.STATE_ROOT, "lbcert", "cands")
DESK = "https://data.pequalnp.com/data/desk/gaps.json"
GAP_SECONDS = 6          # between PRs
MAX_PER_HOUR = 300
os.makedirs(WORK, exist_ok=True)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def desk():
    r = urllib.request.Request(DESK, headers={"User-Agent": "viche-town"})
    return {g["id"]: g for g in json.loads(urllib.request.urlopen(r, timeout=40).read())["gaps"]}


def ready():
    out = []
    for f in os.listdir(CANDS):
        if not f.endswith(".status"):
            continue
        gid = f[:-7]
        try:
            ok = open(os.path.join(CANDS, f)).read().startswith("ok")
        except OSError:
            continue
        if ok and os.path.exists(os.path.join(CANDS, gid + ".lean")):
            out.append(gid)
    return out


def done_path(gid):
    return os.path.join(WORK, gid + ".json")


def publish(g, data, base):
    branch = config.branch_for(g["id"])
    meta = {"id": g["id"], "file": g["file"], "module": g["module"], "statement": g["statement"],
            "imports": g["imports"]}
    digest = validate.validate(meta, data)
    existing = gh.pr_exists_for(branch, g["id"])
    if existing:
        return int(existing), digest, "existing"
    wt = git.fresh_worktree(g["id"], base, branch)
    git.prepare_unpublished(wt, branch, base, None)
    git.pin_candidate(wt, g["file"], data)
    sha = git.signed_commit(wt, base, g["id"])
    if git.push_branch(branch) != sha:
        raise RuntimeError("pushed sha differs")
    for _ in range(20):
        ver = gh.commit_verification(sha)
        if ver.get("verified") is True:
            break
        time.sleep(3)
    if ver.get("verified") is not True:
        raise RuntimeError("signature not verified")
    num = int(gh.create_pr(branch, g["id"]))
    git.run(["git", "--git-dir=" + git.MIRROR, "worktree", "remove", "--force", wt], check=False)
    return num, digest, sha


def main():
    lock = open(os.path.join(WORK, "bulk.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    stamps = []
    while not os.path.exists(os.path.join(WORK, "STOP")):
        try:
            todo = [gid for gid in ready() if not os.path.exists(done_path(gid))]
            held = {r["gap_id"] for r in cli.held_records()}
            todo = [gid for gid in todo if gid not in held]   # the fast lane owns held steps
            if todo:
                D = desk()
                base = git.ensure_mirror()                    # one upstream fetch per batch
                for gid in sorted(todo, key=lambda x: -int(x.rsplit("-", 1)[1])):   # newest first
                    if os.path.exists(os.path.join(WORK, "STOP")):
                        break
                    g = D.get(gid)
                    if not g:
                        json.dump({"gap": gid, "outcome": "not_open"}, open(done_path(gid), "w"))
                        continue
                    if g.get("pr_open", 0) != 0:
                        continue                              # someone is on it; maybe later
                    stamps = [t for t in stamps if time.time() - t < 3600]
                    if len(stamps) >= MAX_PER_HOUR:
                        log("hourly cap reached"); break
                    data = open(os.path.join(CANDS, gid + ".lean"), "rb").read()
                    try:
                        num, digest, how = publish(g, data, base)
                        stamps.append(time.time())
                        json.dump({"gap": gid, "pr": num, "digest": digest, "how": how, "at": time.time(),
                                   "status": open(os.path.join(CANDS, gid + ".status")).read().strip()},
                                  open(done_path(gid), "w"))
                        log("PR", gid, num, how)
                    except validate.InvalidCandidate as e:
                        json.dump({"gap": gid, "outcome": "invalid", "error": str(e)[:300]}, open(done_path(gid), "w"))
                        log("invalid", gid, str(e)[:150])
                    except Exception as e:
                        log("publish failed", gid, type(e).__name__, str(e)[:200])
                    time.sleep(GAP_SECONDS)
        except Exception as e:
            log("bulk cycle error", type(e).__name__, str(e)[:200])
        time.sleep(30)
    log("STOP")
    return 0


if __name__ == "__main__":
    sys.exit(main())
