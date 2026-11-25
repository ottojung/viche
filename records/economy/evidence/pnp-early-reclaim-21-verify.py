#!/usr/bin/env python3
"""Read-only Act 12.4 verification for the 21 owner-authorized EARLY RECLAIM rows.

Modes:
  pre   - verify the 21 live quarantine destinations are safe; write evidence-pre.json
          and build a filtered scratch ledger containing EXACTLY those 21 rows.
  quick - re-verify proc/mount liveness immediately before the destructive run;
          write evidence-quick.json. Refuses on any reference or scan error.
  post  - verify the 21 destinations are gone, preserve set intact, and record
          the after df; write evidence-post.json. Never mutates live state.

Never deletes. The only writes are beneath SCRATCH.
"""
import datetime as dt
import glob
import json
import os
import subprocess
import sys

BASE = "/var/lib/lubko/wd/viche-state"
QLIVE = BASE + "/janitor/quarantined.tsv"
QDIR = BASE + "/quarantine"
GAPS = BASE + "/pnp/gaps"
SCRATCH = "/tmp/opencode/economy-early-reclaim-21-20261125"
AUTH = "P-1795613709-0545"
QAT = "1795608788"
NAMES = [
    "L-meta-5012", "L-meta-4305", "L-meta-3566", "L-meta-2976",
    "L-meta-2583", "L-meta-4478", "L-meta-2223", "L-meta-4215",
    "L-meta-4199", "L-meta-1692", "L-meta-2585", "L-meta-3646",
    "L-meta-1782", "L-meta-4707", "L-meta-2625", "L-meta-1967",
    "L-meta-2270", "L-meta-2872", "L-meta-3774", "L-meta-1745",
    "L-meta-5760",
]
PRESERVE = [
    "L-meta-3321", "L-meta-2149", "L-meta-2382", "L-meta-2341",
    "L-meta-2373", "L-meta-2232",
]
HDR = "ts\tsrc\tdest\tsize_kb\tquarantined_at"


def utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def df():
    out = subprocess.check_output(["df", "-Pk", BASE], text=True).splitlines()[1].split()
    return {"device": out[0], "size_kb": int(out[1]), "used_kb": int(out[2]),
            "avail_kb": int(out[3]), "used_pct": int(out[4].rstrip("%"))}


def du(path):
    p = subprocess.run(["du", "-s", "-k", path], text=True, capture_output=True, timeout=120)
    if p.returncode:
        raise RuntimeError("du failed for %s: %s" % (path, p.stderr.strip()))
    return int(p.stdout.split()[0])


def live_rows():
    rows = []
    with open(QLIVE) as f:
        header = f.readline().rstrip("\n")
        if header != HDR:
            raise RuntimeError("live ledger header unexpected: %r" % header)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) == 5:
                rows.append(p)
    return rows


def auth_rows():
    """Exactly the authorized 21 rows: those whose dest carries the 20261125121315 tag."""
    out = []
    for r in live_rows():
        dest = r[2]
        base = os.path.basename(dest)
        name = base[:-len("-20261125121315")] if base.endswith("-20261125121315") else None
        if name in NAMES:
            out.append({"name": name, "row": r})
    return out


def refs_for(paths):
    wanted = [(name, os.fsencode(path)) for name, path in paths.items()]
    refs, scan_errors = [], 0
    for proc in glob.glob("/proc/[0-9]*"):
        links = [proc + "/cwd", proc + "/root"] + glob.glob(proc + "/fd/*")
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
                    refs.append({"name": name, "kind": "proc-link", "source": link,
                                 "target": os.fsdecode(target)})
        try:
            with open(proc + "/maps", "rb") as f:
                for line in f:
                    for name, path in wanted:
                        if path + b"/" in line or path + b" " in line:
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


def path_map(arows):
    return {a["name"]: a["row"][2] for a in arows}


def write_json(name, obj):
    os.makedirs(SCRATCH, exist_ok=True)
    with open(SCRATCH + "/" + name, "w") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps(obj, indent=2, sort_keys=True))


def pre():
    errors = []
    arows = auth_rows()
    names = [a["name"] for a in arows]
    if set(NAMES) != set(names) or len(names) != 21 or len(set(names)) != 21:
        errors.append("authorized/ledger scope mismatch: %d rows, %r" % (len(names), names))
    if set(NAMES) & set(PRESERVE):
        errors.append("authorized/preserve overlap")
    rows = []
    total_kb = 0
    for a in arows:
        name, r = a["name"], a["row"]
        dest = r[2]
        src = r[1]
        rec = {"name": name, "src": src, "dest": dest, "size_kb": int(r[3]), "qat": r[4]}
        if r[4] != QAT:
            errors.append("%s: unexpected quarantine timestamp %s" % (name, r[4]))
        if os.path.realpath(dest) != dest or os.path.islink(dest) or not os.path.isdir(dest):
            errors.append("%s: dest missing/symlink/noncanonical" % name)
        if os.path.dirname(dest) != QDIR:
            errors.append("%s: dest escaped quarantine" % name)
        if os.path.exists(src):
            errors.append("%s: source still present" % name)
        if name in PRESERVE:
            errors.append("%s: preserve overlap" % name)
        rec["du_kb"] = du(dest) if os.path.isdir(dest) else 0
        total_kb += rec["du_kb"]
        rows.append(rec)
    preserve_present = {}
    for name in PRESERVE:
        p = GAPS + "/" + name
        preserve_present[name] = os.path.isdir(p) and not os.path.islink(p)
        if not preserve_present[name]:
            errors.append("preserve dir missing: " + name)
    pmap = path_map(arows)
    proc_refs, scan_errors = refs_for(pmap)
    if proc_refs:
        errors.append("live proc/mount references: %r" % proc_refs[:5])
    if scan_errors:
        errors.append("proc/mount scan errors: %d" % scan_errors)
    ev = {"at": utc(), "phase": "pre", "authority": AUTH,
          "authorized_count": 21, "ledger_rows": len(names),
          "authorized_names": NAMES, "preserve_names": PRESERVE,
          "preserve_present": preserve_present,
          "df_before": df(), "rows": rows, "du_total_kb": total_kb,
          "ledger_size_total_kb": sum(int(a["row"][3]) for a in arows),
          "proc_mount_refs": proc_refs, "scan_errors": scan_errors,
          "recoverability": "reversible move already complete; recovery only from quarantine copy until reclaimed",
          "errors": errors}
    write_json("evidence-pre.json", ev)
    # Build the filtered scratch ledger: header + exactly the 21 authorized rows.
    jdir = SCRATCH + "/state/janitor"
    os.makedirs(jdir + "/tmp", exist_ok=True)
    with open(jdir + "/quarantined.tsv", "w") as f:
        f.write(HDR + "\n")
        for a in arows:
            f.write("\t".join(a["row"]) + "\n")
    return 1 if errors else 0


def quick():
    errors = []
    arows = auth_rows()
    if len(arows) != 21:
        errors.append("ledger scope changed: %d rows" % len(arows))
    pmap = path_map(arows)
    present = {}
    for name, dest in pmap.items():
        present[name] = os.path.isdir(dest) and not os.path.islink(dest) and os.path.realpath(dest) == dest
        if not present[name]:
            errors.append("dest not present/canonical: " + name)
    proc_refs, scan_errors = refs_for(pmap)
    if proc_refs:
        errors.append("live proc/mount references: %r" % proc_refs[:5])
    if scan_errors:
        errors.append("proc/mount scan errors: %d" % scan_errors)
    ev = {"at": utc(), "phase": "quick", "authority": AUTH,
          "dest_present": sum(present.values()), "df": df(),
          "proc_mount_refs": proc_refs, "scan_errors": scan_errors, "errors": errors}
    write_json("evidence-quick.json", ev)
    return 1 if errors else 0


def post():
    errors = []
    arows = auth_rows()
    dests = [a["row"][2] for a in arows]
    still = [d for d in dests if os.path.exists(d) or os.path.islink(d)]
    if still:
        errors.append("destinations remain: %r" % still[:5])
    preserve_present = {}
    for name in PRESERVE:
        p = GAPS + "/" + name
        preserve_present[name] = os.path.isdir(p) and not os.path.islink(p)
        if not preserve_present[name]:
            errors.append("preserve dir missing: " + name)
    ev = {"at": utc(), "phase": "post", "authority": AUTH,
          "authorized_count": 21, "dest_remaining": len(still),
          "preserve_present": preserve_present, "df_after": df(), "errors": errors}
    write_json("evidence-post.json", ev)
    return 1 if errors else 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "pre":
        sys.exit(pre())
    if mode == "quick":
        sys.exit(quick())
    if mode == "post":
        sys.exit(post())
    print("usage: verify.py pre|quick|post", file=sys.stderr)
    sys.exit(2)
