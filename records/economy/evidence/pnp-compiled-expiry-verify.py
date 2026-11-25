#!/usr/bin/env python3
"""Read-only Act 12.4 preflight / quick / post verifier for the authorized
compiled-artifact-only expiry in the 44 named stale PnP gap dirs.

Owner: P-1795618764-9ded (Act 12.7, approved 2026-11-25T15:12:36Z).
Evidence basis: state/economy/research/2026-11-25-1400z-second-reclaim-candidates.json
and .../2026-11-25-1425z-gap-content-and-growth-evidence.md.

Usage: python3 2026-11-25-compiled-artifact-verify.py <pre|quick|post> [evidence.json]
  pre   full verification + compiled-artifact inventory + df, writes evidence JSON
  quick fresh liveness recheck only (immediately before any execution)
  post  confirm preserve files intact + df after
Never mutates state. Never touches records/, government/, credentials or live procs.
"""
import json, os, sys, time, subprocess, datetime

STATE = "/var/lib/lubko/wd/viche-state"
GAPS = os.path.join(STATE, "pnp", "gaps")
CAND = os.path.join(STATE, "economy", "research", "2026-11-25-1400z-second-reclaim-candidates.json")
# 21 dirs already authorized/reclaimed under P-1795613709-0545
RECLAIMED_21 = set("5012 4305 3566 2976 2583 4478 2223 4215 4199 1692 2585 3646 1782 4707 2625 1967 2270 2872 3774 1745 5760".split())
COMPILED_EXT = (".olean", ".ilean", ".c", ".cnf", ".trace", ".hash", ".lake")


def iso(ts=None):
    return datetime.datetime.utcfromtimestamp(ts or time.time()).strftime("%Y-%m-%dT%H:%M:%SZ")


def df_probe(path=STATE):
    out = subprocess.check_output(["df", "-Pk", path], text=True).splitlines()[1].split()
    return {"device": out[0], "size_kb": int(out[1]), "used_kb": int(out[2]),
            "avail_kb": int(out[3]), "used_pct": int(out[4].rstrip("%"))}


def proc_refs(paths):
    """Return (refs, errors): live /proc cwd/root/fd/maps references to any path."""
    refs, errors = [], []
    needles = [p.rstrip("/") for p in paths if p and p != "/"]
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        base = "/proc/" + pid
        try:
            for link in ("cwd", "root"):
                try:
                    val = os.readlink(os.path.join(base, link))
                except OSError:
                    continue
                for n in needles:
                    if val.startswith(n):
                        refs.append({"pid": pid, "kind": link, "path": val})
        except Exception as e:
            errors.append(str(e))
        fd_dir = os.path.join(base, "fd")
        try:
            for fd in os.listdir(fd_dir):
                try:
                    val = os.readlink(os.path.join(fd_dir, fd))
                except OSError:
                    continue
                for n in needles:
                    if val.startswith(n):
                        refs.append({"pid": pid, "kind": "fd:" + fd, "path": val})
        except Exception:
            pass  # permission-denied fd dirs are normal, not scan errors
        try:
            with open(os.path.join(base, "maps"), "r", errors="ignore") as fh:
                for line in fh:
                    for n in needles:
                        if n in line:
                            refs.append({"pid": pid, "kind": "maps"})
                            break
        except Exception:
            pass  # unreadable maps are normal, not scan errors
    return refs, errors


def git_worktree_refs(paths):
    out = subprocess.run(["git", "-C", "/var/lib/lubko/wd/viche", "worktree", "list", "--porcelain"],
                         capture_output=True, text=True)
    text = out.stdout or ""
    return [p for p in paths if p and p.rstrip("/") in text]


def mount_refs(paths):
    refs = []
    try:
        with open("/proc/mounts", "r", errors="ignore") as fh:
            text = fh.read()
        for p in paths:
            if p and p.rstrip("/") and p.rstrip("/") in text:
                refs.append(p)
    except Exception:
        pass
    return refs


def load_rows():
    d = json.load(open(CAND))
    rows = d["rows"]
    names = [r["gap"] for r in rows]
    preserve = list(d.get("preserve_excluded", []))
    focus = list(d.get("allocator_focus_excluded", []))
    return d, rows, names, preserve, focus


def compiled_inventory(gapdir):
    """Return (list_of_relative_paths, total_kb, files_count) for compiled artifacts."""
    found, total, count = [], 0, 0
    for root, dirs, files in os.walk(gapdir):
        for f in files:
            if f.endswith(COMPILED_EXT):
                fp = os.path.join(root, f)
                try:
                    kb = os.path.getsize(fp) // 1024
                except OSError:
                    kb = 0
                found.append(os.path.relpath(fp, gapdir))
                total += kb
                count += 1
        # build/ dirs count fully (regenerable compiled output)
        for d in list(dirs):
            if d == "build":
                bp = os.path.join(root, d)
                for r2, d2, f2 in os.walk(bp):
                    for f in f2:
                        fp = os.path.join(r2, f)
                        try:
                            total += os.path.getsize(fp) // 1024
                        except OSError:
                            pass
                        count += 1
                found.append(os.path.relpath(bp, gapdir) + "/")
                dirs.remove(d)
    return found, total, count


def state_ok(gapdir, n, now):
    sp = os.path.join(gapdir, "state.json")
    if not os.path.isfile(sp):
        return False, "no-state.json", None
    try:
        st = json.load(open(sp))
    except Exception as e:
        return False, "bad-state.json:%s" % e, None
    state = str(st.get("state", ""))
    if state not in ("RELEASED", "STALE"):
        return False, "state=%s" % state, st
    lease = st.get("lease_expires_at")
    if lease is not None and float(lease) > now:
        return False, "lease-active", st
    for key in ("pr", "pr_url", "pr_open", "queued", "queued_lease", "publisher_retry",
                "researchers", "release_pending", "worktree"):
        v = st.get(key)
        if v not in (None, "", [], False, 0):
            return False, "bound:%s=%r" % (key, v), st
    return True, "", st


def scan(path_list):
    refs, errors = proc_refs(path_list)
    return {"proc_refs": refs, "proc_scan_errors": errors,
            "git_refs": git_worktree_refs(path_list), "mount_refs": mount_refs(path_list)}


def do_pre():
    now = time.time()
    d, rows, names, preserve, focus = load_rows()
    overlap21 = sorted(set(names) & RECLAIMED_21)
    dirs = []
    for r in rows:
        gp = os.path.join(GAPS, r["gap"])
        if os.path.isdir(gp):
            dirs.append(gp)
    live = scan(dirs)
    detail, compiled_total, compiled_files, missing = [], 0, 0, []
    for r in rows:
        gp = os.path.join(GAPS, r["gap"])
        n = r["gap"].split("-")[-1]
        ok, why, _ = state_ok(gp, n, now) if os.path.isdir(gp) else (False, "missing", None)
        inv, kb, cnt = compiled_inventory(gp) if os.path.isdir(gp) else ([], 0, 0)
        compiled_total += kb
        compiled_files += cnt
        detail.append({"gap": r["gap"], "state_ok": ok, "why": why,
                       "compiled_kb": kb, "compiled_files": cnt,
                       "compiled_sample": inv[:4]})
        if not ok:
            missing.append(r["gap"])
    preserve_present = {}
    for n in preserve:
        preserve_present[n] = os.path.isdir(os.path.join(GAPS, "L-meta-" + n))
    focus_present = {n: os.path.isdir(os.path.join(GAPS, "L-meta-" + n)) for n in focus}
    ev = {"at": iso(), "phase": "pre", "authority": "P-1795618764-9ded",
          "authorized_count": len(rows), "reclaimed_21_overlap": overlap21,
          "df_before": df_probe(), "candidate_dir_kb": d.get("candidate_total_kb"),
          "compiled_total_kb": compiled_total, "compiled_files": compiled_files,
          "state_failures": missing, "preserve_present": preserve_present,
          "allocator_focus_present": focus_present,
          "liveness": live, "rows": detail}
    return ev


def do_quick():
    d, rows, names, preserve, focus = load_rows()
    dirs = [os.path.join(GAPS, r["gap"]) for r in rows if os.path.isdir(os.path.join(GAPS, r["gap"]))]
    now = time.time()
    state_fail, present = [], 0
    for r in rows:
        gp = os.path.join(GAPS, r["gap"])
        if not os.path.isdir(gp):
            state_fail.append(r["gap"])
            continue
        present += 1
        ok, why, _ = state_ok(gp, r["gap"].split("-")[-1], now)
        if not ok:
            state_fail.append(r["gap"] + ":" + why)
    return {"at": iso(), "phase": "quick", "dirs_present": present,
            "state_failures": state_fail, "liveness": scan(dirs), "df": df_probe()}


def do_post():
    d, rows, names, preserve, focus = load_rows()
    preserve_present = {n: os.path.isdir(os.path.join(GAPS, "L-meta-" + n)) for n in preserve}
    focus_present = {n: os.path.isdir(os.path.join(GAPS, "L-meta-" + n)) for n in focus}
    return {"at": iso(), "phase": "post", "preserve_present": preserve_present,
            "allocator_focus_present": focus_present, "df_after": df_probe()}


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    fn = sys.argv[2] if len(sys.argv) > 2 else None
    ev = {"pre": do_pre, "quick": do_quick, "post": do_post}[mode]()
    text = json.dumps(ev, indent=1, sort_keys=True)
    print(text)
    if fn:
        with open(fn, "w") as fh:
            fh.write(text + "\n")
