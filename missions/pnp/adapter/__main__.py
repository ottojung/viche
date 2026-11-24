"""CLI for family-level proof adaptation and certificate reuse."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from .. import assignment, config, state, support, tools, validate
from ..proofs import corpus
from .adapt import adapt_exact_module, controlled_module_rename, emit_standalone
from .closure import dependency_closure, parse_source
from .detect import detect_and_adapt


def _load_gap(args) -> dict:
    # Offline replay must be explicit. A stale bound workspace may not
    # silently borrow a newer attempt for the same public gap.
    if args.gap_json:
        if assignment.workspace(Path.cwd()):
            raise SystemExit("offline metadata must be used outside a bound workspace")
        return json.loads(Path(args.gap_json).read_text(encoding="utf-8"))
    if args.module and args.statement and args.file:
        if assignment.workspace(Path.cwd()):
            raise SystemExit("offline metadata must be used outside a bound workspace")
        return {
            "id": args.gap_id or "L-gap-000",
            "file": args.file, "module": args.module,
            "statement": args.statement, "imports": args.imports or [],
        }
    if assignment.workspace(Path.cwd()):
        binding = assignment.binding(Path.cwd())
        if not binding:
            raise SystemExit("unbound research workspace")
        rec = state.load(binding[0])
        if not support.active(rec) or rec["lease"] != binding[1]:
            raise SystemExit("stale or inactive research assignment")
        return {
            "id": rec["gap_id"], "file": rec["path"],
            "module": rec["module"], "statement": rec["statement"],
            "imports": rec.get("imports") or [],
        }
    raise SystemExit("provide --gap-json, or run in a bound workspace, or pass --file/--module/--statement")


def _emit(result, output: Path | None):
    if output and result.get("candidate"):
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as f:
            f.write(result["candidate"])
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_closure(args):
    source = Path(args.source).read_text(encoding="utf-8")
    model = parse_source(source)
    decls = dependency_closure(model, args.target)
    result = {
        "target": args.target,
        "declarations": [
            {
                "name": d.name,
                "kind": d.kind,
                "namespace": list(d.namespace),
                "start_line": d.start + 1,
                "end_line": d.end,
            }
            for d in decls
        ],
        "count": len(decls),
    }
    if args.emit:
        # Conservative minimal emission: include preamble/scope lines and closure decls in source order.
        wanted = {id(d) for d in decls}
        selected = []
        # include imports and top-level open/variable/namespace scaffolding lines that appear before preamble_end
        for i, line in enumerate(model.lines):
            if i < model.preamble_end:
                selected.append(line)
        # include namespace/section/open/variable commands and selected declarations in order
        i = model.preamble_end
        while i < len(model.lines):
            line = model.lines[i]
            if any(id(d) == id(x) for d in decls for x in [d] if d.start == i):
                decl = next(d for d in decls if d.start == i)
                selected.extend(model.lines[decl.start:decl.end])
                i = decl.end
                continue
            # keep structural scope commands
            if re.match(r"^[ \t]*(?:namespace|end|section|variable|open|universe|set_option|attribute|local|omit|include)\b", line):
                selected.append(line)
                i += 1
                continue
            # keep blank lines between kept items
            if line.strip() == "":
                selected.append(line)
                i += 1
                continue
            i += 1
        text = "\n".join(selected).rstrip() + "\n"
        result["candidate"] = text
    _emit(result, Path(args.output) if args.output else None)


def cmd_adapt(args):
    gap = _load_gap(args)
    source = Path(args.source).read_text(encoding="utf-8")
    r = adapt_exact_module(source, gap, source_module=args.source_module)
    result = {
        "ok": r.ok,
        "kernel_checked": False,
        "strategy": r.strategy,
        "source_module": r.source_module,
        "target_module": r.target_module,
        "details": r.details,
        "candidate": r.candidate,
    }
    _emit(result, Path(args.output) if args.output else None)


def cmd_detect(args):
    gap = _load_gap(args)
    source_text = Path(args.source).read_text(encoding="utf-8") if args.source else None
    with corpus.open_index() as db:
        revision = corpus.update(db)
        detections = detect_and_adapt(db, gap, limit=args.limit, source_text=source_text, source_module=args.source_module)
    result = {
        "kernel_checked": False,
        "revision": revision,
        "target": {"module": gap["module"], "file": gap["file"]},
        "matches": [
            {
                "path": d.path,
                "module": d.module,
                "score": d.score,
                "strategy": d.strategy,
                "ok": d.ok,
                "sha256": d.sha256,
                "error": d.error,
                "candidate": d.candidate if args.emit_candidates else None,
            }
            for d in detections
        ],
    }
    # If an output is requested, write the first successful candidate.
    if args.output:
        ok = next((d for d in detections if d.ok and d.candidate), None)
        if ok:
            out = Path(args.output)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("x", encoding="utf-8") as f:
                f.write(ok.candidate)
            result["output"] = str(out)
            result["output_sha256"] = ok.sha256
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_emit(args):
    gap = _load_gap(args)
    source = Path(args.source).read_text(encoding="utf-8")
    model = parse_source(source)
    target = args.target or gap["module"]
    decls = dependency_closure(model, target)
    wanted = {id(d) for d in decls}
    # Build minimal body: keep structural lines and wanted declarations.
    body_lines = []
    i = model.preamble_end
    while i < len(model.lines):
        decl = next((d for d in decls if d.start == i), None)
        if decl:
            body_lines.extend(model.lines[decl.start:decl.end])
            i = decl.end
            continue
        line = model.lines[i]
        if re.match(r"^[ \t]*(?:namespace|end|section|variable|open|universe|set_option|attribute|local|omit|include)\b", line):
            body_lines.append(line)
        elif line.strip() == "":
            if body_lines and body_lines[-1].strip() != "":
                body_lines.append("")
        i += 1
    body = "\n".join(body_lines).strip()
    body = controlled_module_rename(body, args.source_module or target, gap["module"])
    candidate = emit_standalone(gap, body)
    # Ensure final theorem matches target exactly if possible.
    final = re.search(r"(?<![\w.])theorem\s+" + re.escape(gap["module"]) + r"\s*:(.*?):=\s*by\b", candidate, re.S)
    if final and validate.tokens(final.group(1)) != validate.tokens(gap["statement"]):
        candidate = re.sub(
            r"(?<![\w.])theorem\s+" + re.escape(gap["module"]) + r"\s*:.*?:=\s*by\b",
            f"theorem {gap['module']} : {gap['statement']} := by",
            candidate, count=1, flags=re.S,
        )
    result = {"ok": False, "candidate": candidate}
    try:
        result["sha256"] = validate.validate(gap, candidate.encode("utf-8"))
        result["ok"] = True
    except validate.InvalidCandidate as e:
        result["error"] = str(e)
    _emit(result, Path(args.output) if args.output else None)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m missions.pnp.adapter", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_gap_args(sp):
        sp.add_argument("--gap-json", type=Path)
        sp.add_argument("--gap-id")
        sp.add_argument("--file")
        sp.add_argument("--module")
        sp.add_argument("--statement")
        sp.add_argument("--imports", nargs="*")
        sp.add_argument("--output")

    c = sub.add_parser("closure", help="extract declaration dependency closure")
    c.add_argument("source", type=Path)
    c.add_argument("--target", required=True, help="target declaration name")
    c.add_argument("--emit", action="store_true", help="include minimal emitted source")
    c.add_argument("--output")
    c.set_defaults(func=cmd_closure)

    a = sub.add_parser("adapt", help="adapt a checked source to exact gap metadata")
    a.add_argument("source", type=Path)
    a.add_argument("--source-module")
    add_gap_args(a)
    a.set_defaults(func=cmd_adapt)

    d = sub.add_parser("detect", help="detect stronger reusable lemmas in corpus")
    d.add_argument("--source", type=Path, help="optional local source instead of corpus search")
    d.add_argument("--source-module")
    d.add_argument("--limit", type=int, default=8)
    d.add_argument("--emit-candidates", action="store_true")
    add_gap_args(d)
    d.set_defaults(func=cmd_detect)

    e = sub.add_parser("emit", help="emit minimal standalone Lean from dependency closure")
    e.add_argument("source", type=Path)
    e.add_argument("--target", help="target declaration name; defaults to gap module")
    e.add_argument("--source-module")
    add_gap_args(e)
    e.set_defaults(func=cmd_emit)

    args = p.parse_args(argv)
    tools.record("adapter-"+args.cmd)
    args.func(args)


if __name__ == "__main__":
    main()
