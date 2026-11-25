#!/usr/bin/env python3
"""Read-only Act 12.4 preflight/postcheck for the 21 Executive-authorized PnP dirs.

Never moves or deletes. Writes only beneath OUT_DIR. The Janitor performs the
quarantine; this tool verifies exact scope, state, references, mounts and result.
"""
import argparse
import datetime as dt
import glob
import json
import os
import subprocess
import sys
import time

BASE = "/var/lib/lubko/wd/viche-state"
GAPS = BASE + "/pnp/gaps"
QUARANTINE = BASE + "/quarantine"
OUT_DIR = "/tmp/opencode/economy-pnp-quarantine-21-20261125"
AUTH = "P-1795598940-b3b2"
NAMES = [
    "L-meta-5012", "L-meta-4305", "L-meta-3566", "L-meta-2976",
    "L-meta-2583", "L-meta-4478", "L-meta-2223", "L-meta-4215",
    "L-meta-4199", "L-meta-1692", "L-meta-2585", "L-meta-3646",
    "L-meta-1782", "L-meta-4707", "L-meta-2625", "L-meta-1967",
    "L-meta-2270", "L-meta-2872", "L-meta-3774", "L-meta-1745",
    "L-meta-5760",
]
PRESERVE = {
    "L-meta-3321", "L-meta-2149", "L-meta-2382", "L-meta-2341",
    "L-meta-2373", "L-meta-2232",
}


def utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def df():
    out = subprocess.check_output(["df", "-Pk", BASE], text=True).splitlines()[1].split()
    return {"device": out[0], "size_kb": int(out[1]), "used_kb": int(out[2]),
            "avail_kb": int(out[3]), "used_pct": int(out[4].rstrip("%"))}


def du(path):
    p = subprocess.run(["du", "-s", "-k", path], text=True, capture_output=True, timeout=90)
    if p.returncode:
        raise RuntimeError("du failed for %s: %s" % (path, p.stderr.strip()))
    return int(p.stdout.split()[0])


def refs_for(paths):
    """One procfs/mount scan. Any unreadable entry is conservatively noted."""
    wanted = [(name, os.fsencode(path)) for name, path in paths.items()]
    refs = []
    scan_errors = 0
    for proc in glob.glob("/proc/[0-9]*"):
        links = [proc + "/cwd", proc + "/root"]
        links.extend(glob.glob(proc + "/fd/*"))
        for link in links:
            try:
                target = os.readlink(link)
            except OSError:
                continue
            target = os.fsencode(target)
            if target.endswith(b" (deleted)"):
                target = target[:-10]
            for name, path in wanted:
                if target == path or target.startswith(path + b"/"):
                    refs.append({"name": name, "kind": link.split("/")[-1]
                                 if link.rsplit("/", 1)[-1].isdigit() else link.rsplit("/", 1)[-1],
                                 "source": link, "target": os.fsdecode(target)})
        try:
            with open(proc + "/maps", "rb") as f:
                for line in f:
                    for name, path in wanted:
                        if path + b"/" in line or (path + b" ") in line:
                            refs.append({"name": name, "kind": "maps", "source": proc + "/maps",
                                         "target": os.fsdecode(path)})
        except FileNotFoundError:
            pass
        except OSError:
            scan_errors += 1
    try:
        with open("/proc/mounts", "rb") as f:
            for line in f:
                fields = line.split()
                if len(fields) < 2:
                    continue
                target = fields[1].replace(b"\\040", b" ")
                for name, path in wanted:
                    if target == path or target.startswith(path + b"/"):
                        refs.append({"name": name, "kind": "mount", "source": "/proc/mounts",
                                     "target": os.fsdecode(target)})
    except OSError:
        scan_errors += 1
    return refs, scan_errors


def worktree_refs(paths):
    p = subprocess.run(["git", "-C", "/var/lib/lubko/wd/viche", "worktree", "list", "--porcelain"],
                       text=True, capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError("git worktree list failed")
    return [{"name": name, "source": "git-worktree-list"} for name, path in paths.items()
            if path in p.stdout]


def current_owner_refs():
    """Current allocator/agent state only; historical records are not live leases."""
    found = {}
    for rel in ["pnp/allocator.json", "pnp/swarm/agents.json"]:
        path = BASE + "/" + rel
        try:
            text = open(path, errors="replace").read()
        except OSError:
            continue
        for name in NAMES:
            if name in text:
                found.setdefault(name, []).append(rel)
    return found


def preflight(quick=False):
    now = time.time()
    paths = {name: GAPS + "/" + name for name in NAMES}
    errors, rows = [], []
    prior_sizes = {}
    if quick:
        try:
            with open(OUT_DIR + "/evidence-pre.json") as f:
                prior_sizes = {r["name"]: int(r["size_kb"]) for r in json.load(f)["rows"]}
        except Exception as e:
            errors.append("cannot reuse preflight sizes: " + repr(e))
    if set(NAMES) & PRESERVE:
        errors.append("authorized/preserve overlap")
    for name, path in paths.items():
        row = {"name": name, "src": path}
        try:
            if os.path.realpath(path) != path or os.path.islink(path) or not os.path.isdir(path):
                errors.append(name + ": missing/symlink/noncanonical")
                row["size_kb"] = 0
                rows.append(row)
                continue
            with open(path + "/state.json") as f:
                state = json.load(f)
            required_null = ["pr_number", "pending_pr_number", "queued_lease", "publisher_retry_at", "worktree"]
            checks = {
                "state_released_or_stale": state.get("state") in ("RELEASED", "STALE"),
                "lease_expired": isinstance(state.get("lease_expires_at"), (int, float))
                                 and state["lease_expires_at"] <= now,
                "no_pr_queue_retry_worktree": all(state.get(k) is None for k in required_null),
                "no_release_pending": state.get("release_pending") is False,
                "no_researchers": state.get("researchers") in ([], None),
                "gap_id_matches": state.get("gap_id") == name,
            }
            row["state_checks"] = checks
            row["state"] = state.get("state")
            row["lease_expires_at"] = state.get("lease_expires_at")
            row["failure_reason"] = state.get("failure_reason")
            row["updated_at"] = state.get("updated_at")
            if not all(checks.values()):
                errors.append(name + ": state check failed")
            row["has_dot_git"] = os.path.lexists(path + "/.git")
            if row["has_dot_git"]:
                errors.append(name + ": .git present")
            row["size_kb"] = prior_sizes.get(name, 0) if quick else du(path)
        except Exception as e:
            errors.append(name + ": " + repr(e))
            row["size_kb"] = 0
        rows.append(row)
    proc_refs, scan_errors = refs_for(paths)
    wt_refs = worktree_refs(paths)
    owner_refs = current_owner_refs()
    if proc_refs:
        errors.append("live process/mount references")
    if wt_refs:
        errors.append("git worktree references")
    if owner_refs:
        errors.append("current allocator/agent references")
    if scan_errors:
        errors.append("proc/mount scan had unreadable entries")
    ev = {
        "at": utc(), "phase": "pre", "quick": quick, "authority": AUTH,
        "authorized_count": len(NAMES), "authorized_names": NAMES,
        "preserve_names": sorted(PRESERVE), "preserve_overlap": sorted(set(NAMES) & PRESERVE),
        "df_before": df(), "rows": rows, "total_kb": sum(r["size_kb"] for r in rows),
        "proc_mount_refs": proc_refs, "git_worktree_refs": wt_refs,
        "current_allocator_agent_refs": owner_refs, "scan_errors": scan_errors,
        "recoverability": "same-filesystem move to live quarantine; normal 604800-second grace; no deletion",
        "errors": errors,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    suffix = "quick" if quick else "pre"
    with open(OUT_DIR + "/evidence-%s.json" % suffix, "w") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
        f.write("\n")
    if not quick:
        jdir = OUT_DIR + "/state/janitor"
        os.makedirs(jdir + "/tmp", exist_ok=True)
        with open(jdir + "/inventory.tsv", "w") as f:
            f.write("ts\thost\tpath\tsize_kb\tmtime\tage_days\tis_git\tuncommitted\tunpushed\tclass\n")
            for row in rows:
                path = row["src"]
                mtime = int(os.stat(path).st_mtime) if os.path.isdir(path) else 0
                age = max(0, int((now - mtime) // 86400))
                f.write("%s\t%s\t%s\t%s\t%s\t%s\t0\t0\t0\tquarantine-candidate\n" %
                        (ev["at"], os.uname().nodename, path, row["size_kb"], mtime, age))
    print(json.dumps({k: v for k, v in ev.items() if k not in ("rows", "authorized_names", "preserve_names")}, indent=2))
    return 1 if errors else 0


def postcheck():
    qlog = OUT_DIR + "/state/janitor/quarantined.tsv"
    rows = []
    errors = []
    if not os.path.isfile(qlog):
        print("missing scoped quarantine ledger", file=sys.stderr)
        return 1
    with open(qlog) as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 5:
                rows.append(dict(zip(header, p)))
    names = [os.path.basename(r["src"]) for r in rows]
    if len(rows) != 21 or set(names) != set(NAMES) or len(set(names)) != 21:
        errors.append("ledger scope mismatch")
    for r in rows:
        name = os.path.basename(r["src"])
        src = GAPS + "/" + name
        dest = r["dest"]
        if r["src"] != src:
            errors.append(name + ": wrong src")
        if os.path.exists(src):
            errors.append(name + ": src still exists")
        if os.path.realpath(dest) != dest or os.path.islink(dest) or not os.path.isdir(dest):
            errors.append(name + ": dest missing/symlink/noncanonical")
        if os.path.dirname(dest) != QUARANTINE:
            errors.append(name + ": dest escaped quarantine")
        if name in PRESERVE:
            errors.append(name + ": preserve overlap")
    ev = {"at": utc(), "phase": "post", "authority": AUTH, "rows": rows,
          "df_after": df(), "moved_count": len(rows),
          "moved_kb": sum(int(r["size_kb"]) for r in rows), "errors": errors}
    with open(OUT_DIR + "/evidence-post.json", "w") as f:
        json.dump(ev, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: v for k, v in ev.items() if k != "rows"}, indent=2))
    return 1 if errors else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["pre", "quick", "post"])
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.phase == "post":
        return postcheck()
    return preflight(args.quick or args.phase == "quick")


if __name__ == "__main__":
    sys.exit(main())
