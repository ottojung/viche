"""Preserve upstream proof sketches and checked-cut provenance, not new authority.

The public catalog is advisory. It cannot grant a lease or change a leased
statement, imports, module, or file. Only work on a live bound assignment.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

from . import assignment, config, state, support

PUBLIC = "https://data.pequalnp.com/data/desk/gaps.json"
FIELDS = ("sketch", "refutation", "reductions", "reductions_live", "shard_spec",
          "shards", "unlocks", "weight", "parallel", "lane", "kind")


def catalog_path():
    return Path(config.CACHE_DIR, "proof-catalog.json")


def acquisition(gap, answer):
    fields = {k: gap[k] for k in FIELDS if k in gap}
    for k in ("shard", "shards"):
        if k in answer:
            fields[k] = answer[k]
    return fields


def matches(rec, row):
    return all(rec.get(k) == row.get(v) for k, v in (
        ("gap_id", "id"), ("statement", "statement"), ("module", "module"),
        ("path", "file"), ("imports", "imports")))


def related(sketch, cuts):
    parents = list(dict.fromkeys(re.findall(r"checked cut of (L-[a-z0-9]+(?:-[a-z0-9]+)*-\d+)", sketch)))
    siblings = []
    for text in re.findall(r"(?i)sibling steps:\s*([^.]*)", sketch):
        siblings.extend(re.findall(r"L-[a-z0-9]+(?:-[a-z0-9]+)*-\d+", text))
    artifacts = []
    for cut in cuts:
        if not isinstance(cut, dict) or cut.get("parent") not in parents or cut.get("state") == "dead":
            continue
        artifact = cut.get("artifact") or {}
        path = artifact.get("lean_file")
        if isinstance(path, str) and re.fullmatch(r"lean/PEqualNP/Outside/R_[a-z0-9]+_\d+_\d+\.lean", path):
            artifacts.append({"parent":cut["parent"], "path":path,
                              "content_hash":artifact.get("content_hash")})
    return {"parents":parents, "siblings":list(dict.fromkeys(siblings)), "reduction_sources":artifacts}


def read(rec, catalog=None):
    """Return metadata only; never fetch inside a worker guard."""
    notes = rec.get("desk_notes") or {}
    out = dict(notes) if isinstance(notes, dict) else {}
    try:
        if catalog is None:
            catalog = json.loads(catalog_path().read_text())
        rows = catalog.get("gaps", [])
        row = next((r for r in rows if r.get("id")==rec["gap_id"]), None)
        if row and matches(rec,row):
            # The acquisition response wins if its metadata differs.
            out = {**acquisition(row,{}), **out}
        if isinstance(out.get("sketch"), str):
            out.update(related(out["sketch"], catalog.get("reductions",[])))
        if row and matches(rec,row):
            out["catalog_at"] = catalog.get("updated_at")
    except (OSError,ValueError,AttributeError,TypeError,KeyError):
        pass
    if isinstance(out.get("sketch"),str) and "parents" not in out:
        out.update(related(out["sketch"],[]))
    if rec.get("dead"):
        out["dead"] = rec["dead"]
    return out


def refresh():
    """One shared bounded read-only refresh, independent of allocation."""
    proc = subprocess.run(["curl","-fsS","--max-time","15",PUBLIC],
                          capture_output=True,timeout=20,check=True)
    if len(proc.stdout)>12_000_000:
        raise ValueError("catalog too large")
    obj = json.loads(proc.stdout)
    if not isinstance(obj,dict) or not isinstance(obj.get("gaps"),list) or not isinstance(obj.get("reductions"),list):
        raise ValueError("invalid catalog")
    if any(not isinstance(r,dict) for r in obj["gaps"]):
        raise ValueError("invalid catalog row")
    state.atomic_write(str(catalog_path()),json.dumps(obj,ensure_ascii=False)+"\n")
    return {"rows":len(obj["gaps"]),"reductions":len(obj["reductions"]),"at":obj.get("updated_at")}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--refresh",action="store_true")
    ns=p.parse_args()
    if ns.refresh:
        print(json.dumps(refresh()))
        return
    gap,lease=assignment.resolve()
    rec=state.load(gap)
    if not support.active(rec) or rec["lease"]!=lease:
        p.error("live bound assignment required")
    print(json.dumps({"gap":gap,"statement":rec["statement"],"imports":rec["imports"],
                      "context":rec.get("context"),"desk_notes":read(rec)},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
