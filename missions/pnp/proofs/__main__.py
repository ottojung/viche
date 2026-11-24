"""Research tools: inspect the current assignment, find checked analogues, generate certificates."""
import argparse
import json
from pathlib import Path

from .. import assignment, state
from . import corpus, circuit, synthesis, search, fragments, rows, bank


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    find = sub.add_parser("find")
    find.add_argument("query", nargs="?")
    find.add_argument("--limit", type=int, default=8)
    source = sub.add_parser("source")
    source.add_argument("module")
    gen = sub.add_parser("circuit")
    gen.add_argument("--output", type=Path)
    syn = sub.add_parser("synthesize")
    syn.add_argument("--output", type=Path)
    sub.add_parser("index")
    sat = sub.add_parser("search", help="bounded finite circuit SAT/CEGIS search")
    sat.add_argument("specification", type=Path)
    sat.add_argument("--seconds", type=float, default=30)
    sat.add_argument("--checkpoint", type=Path)
    rv = sub.add_parser("rows", help="verify multi-output explicit-row circuit")
    rv.add_argument("specification",type=Path)
    rv.add_argument("witness",type=Path)
    rs = sub.add_parser("row-search",help="bounded multi-output explicit-row SAT/CEGIS")
    rs.add_argument("specification",type=Path)
    rs.add_argument("--seconds",type=float,default=30)
    rs.add_argument("--checkpoint",type=Path)
    bk = sub.add_parser("bank",help="generate exact monotone bipartite neighborhood-bank row constraints")
    bk.add_argument("specification",type=Path)
    bk.add_argument("--output",type=Path)
    share = sub.add_parser("share", help="snapshot a reusable Lean source for peers")
    share.add_argument("file",type=Path)
    share.add_argument("--message",required=True)
    listing = sub.add_parser("fragments")
    listing.add_argument("--all-attempts",action="store_true")
    args = p.parse_args()
    from .. import tools
    tools.record("proofs-"+args.command)
    if args.command in ("rows","row-search","bank"):
        try:
            raw=json.loads(args.specification.read_text())
            if args.command=="rows":
                result=rows.verify(raw,json.loads(args.witness.read_text()))
            elif args.command=="row-search":
                result=rows.solve(raw,args.seconds,args.checkpoint)
            else:
                result=bank.generate(raw)
                if args.output:
                    with args.output.open("x") as f:json.dump(result,f,indent=2)
        except (OSError,ValueError) as exc:
            p.error(str(exc))
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return
    if args.command in ("share","fragments"):
        try:
            result = (fragments.share(args.file,args.message) if args.command=="share"
                      else fragments.inventory(args.all_attempts))
        except (OSError,ValueError) as exc:
            p.error(str(exc))
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return
    if args.command == "search":
        try:
            result = search.solve(json.loads(args.specification.read_text()),
                                  args.seconds, args.checkpoint)
        except (OSError, ValueError) as exc:
            p.error(str(exc))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if args.command in ("find", "source", "index"):
        with corpus.open_index() as db:
            revision = corpus.update(db)
            if args.command == "index":
                print(json.dumps({"revision":revision,"proofs":db.execute("select count(*) from proof").fetchone()[0]}))
                return
            if args.command == "source":
                path = "lean/" + args.module.replace(".", "/") + ".lean"
                row = db.execute("select source from proof where path=?", (path,)).fetchone()
                if not row:
                    p.error("unknown checked proof")
                print(row[0])
                return
            binding = assignment.binding(Path.cwd())
            rec = state.load(binding[0]) if binding else None
            query = args.query or (rec["statement"] if rec else None)
            if not query:
                p.error("provide a query or run in a bound assignment")
            print(json.dumps({"revision":revision,"matches":corpus.search(db,query,
                rec["imports"] if rec else [],min(30,max(1,args.limit)))},ensure_ascii=False,indent=2))
            return
    gap, lease = assignment.resolve()
    rec = state.load(gap)
    if rec["lease"] != lease or rec["state"] not in ("LEASED","RESEARCHING"):
        p.error("no live bound assignment")
    meta = {"id":gap,"file":rec["path"],"module":rec["module"],"statement":rec["statement"],"imports":rec["imports"]}
    if args.command == "synthesize":
        from ..research import certificate
        report=certificate.render(meta,seconds=2)
        text=report.pop("candidate",None)
        report.pop("certificate",None)
        if not text:
            report = synthesis.candidate(meta)
            text = report.pop("candidate", None) if report else None
    else:
        report = circuit.explicit_circuit(meta)
        text = circuit.render(meta,"decide") if report and report["verified"] else None
    if not text:
        print(json.dumps({"result":"not-generated","details":report}))
        return
    # A finite semantic check is evidence, not a Lean compilation verdict.
    # The researcher must review the remaining clauses and choose to submit.
    if args.output:
        with args.output.open("x",encoding="utf-8") as f:
            f.write(text)
    print(json.dumps({"result":"candidate","details":report,"local_lean_checked":False,
                      "output":str(args.output) if args.output else None}))
    if not args.output:
        print(text)


if __name__ == "__main__":
    main()
