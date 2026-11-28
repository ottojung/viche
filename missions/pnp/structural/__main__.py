"""CLI for the isolated bit-reflection structural generator (research only)."""
import argparse
import hashlib
import json
from pathlib import Path

from . import bitpack, extract, oracle

HELD_OUT = [(21, [0, 1, 4, 14, 16]), (5, [0, 1]),
            (9, [0, 1, 3]), (31, [0, 1, 3, 8, 12, 18]), (3, [0, 1])]
DEV = [(13, [0, 1, 3, 9]), (7, [0, 1, 3])]


def meta_for(n, diffs, module=None):
    module = module or "PEqualNP.Outside.L_meta_struct_%d" % n
    return {"id": "L-meta-17487" if n == 13 else "L-meta-struct-%d" % n,
            "file": "lean/PEqualNP/Outside/%s.lean" % module.rsplit(".", 1)[-1],
            "module": module, "statement": bitpack.statement_for(n, diffs),
            "imports": ["PEqualNP.Defs"]}


def slim(rep):
    return {k: rep[k] for k in ("result", "family", "n", "diffs", "sha256",
                                "oracle_identity", "oracle_lemmas", "upstream",
                                "local_lean_checked", "desk_credit_claimed")
            if k in rep}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--n", type=int, required=True)
    g.add_argument("--diffs", required=True)
    g.add_argument("--module")
    g.add_argument("--output", type=Path)
    h = sub.add_parser("heldout")
    h.add_argument("--out-dir", type=Path, required=True)
    h.add_argument("--report", type=Path)
    t = sub.add_parser("targets")
    t.add_argument("--file", type=Path, required=True)
    a = p.parse_args()
    if a.cmd == "generate":
        diffs = [int(x) for x in a.diffs.split(",")]
        rep = bitpack.candidate(meta_for(a.n, diffs, a.module))
        out = slim(rep)
        if rep.get("candidate") and a.output:
            a.output.parent.mkdir(parents=True, exist_ok=True)
            with a.output.open("w", encoding="utf-8", newline="\n") as f:
                f.write(rep["candidate"])
            out["output"] = str(a.output)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    if a.cmd == "heldout":
        a.out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for label, cases in (("development", DEV), ("held_out", HELD_OUT)):
            for n, diffs in cases:
                rep = bitpack.candidate(meta_for(n, diffs))
                name = "n%d_%s.lean" % (n, "-".join(map(str, diffs)))
                path = a.out_dir / name
                with path.open("w", encoding="utf-8", newline="\n") as f:
                    f.write(rep.get("candidate", ""))
                row = slim(rep)
                row["split"] = label
                row["file"] = str(path)
                row["file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                results.append(row)
        report = {"generator": "missions.pnp.structural.bitpack",
                  "purpose": "reusable finite bit-reflection structural cut",
                  "kernel_checked": False,
                  "desk_credit_claimed": False,
                  "upstream": {"path": extract.SOURCE_PATH,
                               "revision": extract.PINNED_REVISION,
                               "blob": extract.PINNED_BLOB,
                               "license": extract.LICENSE},
                  "results": results}
        if a.report:
            with a.report.open("w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        print(json.dumps({k: report[k] for k in
                          ("generator", "kernel_checked", "desk_credit_claimed", "upstream")},
                         ensure_ascii=False, indent=2))
        print("generated %d candidates (%d held out)" %
              (len(results), len(HELD_OUT)))
        return
    if a.cmd == "targets":
        data = json.loads(a.file.read_text(encoding="utf-8"))
        rows = data["gaps"] if isinstance(data, dict) else data
        out = []
        for r in rows:
            meta = {k: r.get(k) for k in ("id", "file", "module", "statement", "imports")}
            rep = bitpack.candidate(meta)
            out.append({"id": r["id"], "title": r.get("title"),
                        "result": rep["result"], "reason": rep.get("reason"),
                        "desk_credit_claimed": False, "kernel_checked": False})
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
