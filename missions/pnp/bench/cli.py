"""CLI for the retrospective PnP graph-circuit-construction benchmark."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .corpus import DEFAULT_DB, load_graph_circuits, checked_timestamps
from .evaluate import evaluate_row, evaluate_with_holdouts, summarize
from .generators import GENERATORS, get as get_generator


def _load_output_file(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict) and "outputs" in data:
        data = data["outputs"]
    if not isinstance(data, list):
        raise ValueError("generator output file must be a JSON list or {outputs:[...]}")
    return data


def _index_rows(rows):
    by_module = {r["module"]: r for r in rows}
    by_path = {r["path"]: r for r in rows}
    return by_module, by_path


def evaluate_loaded_outputs(rows, output_records, generator_name=None):
    by_module, by_path = _index_rows(rows)
    results = []
    for rec in output_records:
        key = rec.get("module") or rec.get("path")
        row = by_module.get(key) or by_path.get(key)
        if row is None:
            continue
        gates = rec.get("gates")
        output = rec.get("output")
        if gates is None or output is None:
            raise ValueError(f"output record missing gates/output: {key!r}")
        res = evaluate_row(row, gates, output)
        res["generator"] = generator_name or rec.get("generator")
        res["family"] = f"n{row['n']}-e{row['edge_count']}"
        results.append(res)
    return results


def build_report(rows, generators, output_files, test_fraction):
    reports = []
    for name in generators:
        gen = get_generator(name)
        reports.append(evaluate_with_holdouts(rows, gen, name, test_fraction=test_fraction))
    for spec in output_files:
        if "=" in spec:
            name, path = spec.split("=", 1)
        else:
            path = spec
            name = Path(spec).stem
        records = _load_output_file(path)
        results = evaluate_loaded_outputs(rows, records, generator_name=name)
        reports.append({
            "generator": name,
            "source": str(path),
            "overall": summarize(results),
            "results": results,
        })
    return reports


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-db", default=str(DEFAULT_DB),
                        help="Public checked-corpus sqlite index (read-only).")
    parser.add_argument("--contributors-export", type=Path,
                        help="Frozen public official contributors JSON export; enables real checked-time splits.")
    parser.add_argument("--generator", action="append", default=[],
                        choices=sorted(GENERATORS),
                        help="Generator to run. May be given multiple times.")
    parser.add_argument("--outputs", action="append", default=[],
                        help="Generator outputs JSON file, or name=path.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of corpus rows (for quick smoke runs).")
    parser.add_argument("--test-fraction", type=float, default=0.25,
                        help="Group/tail fraction for holdouts.")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON report.")
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty-print JSON.")
    parser.add_argument("--no-results", action="store_true",
                        help="Omit per-row results from JSON.")
    args = parser.parse_args(argv)

    timestamps = None
    export_sha256 = None
    if args.contributors_export is not None:
        import hashlib
        raw = args.contributors_export.read_bytes()
        timestamps = checked_timestamps(json.loads(raw))
        export_sha256 = hashlib.sha256(raw).hexdigest()
    rows = load_graph_circuits(args.corpus_db, limit=args.limit, timestamps=timestamps)
    if not rows:
        print("no graph-circuit constructions found in corpus", file=sys.stderr)
        return 2

    generators = args.generator or (["legacy_greedy", "exact_star_cover"] if not args.outputs else [])
    reports = build_report(rows, generators, args.outputs, args.test_fraction)

    payload = {
        "corpus_db": str(args.corpus_db),
        "rows": len(rows),
        "test_fraction": args.test_fraction,
        "contributors_export_sha256": export_sha256,
        "reports": reports,
    }
    if args.no_results:
        for r in payload["reports"]:
            r.pop("results", None)

    if args.json or args.pretty:
        json.dump(payload, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
        if args.pretty:
            sys.stdout.write("\n")
        return 0

    print(f"corpus_rows={len(rows)} db={args.corpus_db}")
    for r in reports:
        o = r["overall"]
        rate = o["checked_bound_satisfaction_rate"]
        rate_s = "n/a" if rate is None else f"{rate:.3%}"
        print(f"\n== {r['generator']} ==")
        print(f"checked_bound_satisfaction={o['checked_bound_satisfied']}/{o['total']} ({rate_s})")
        print(f"bound_satisfied={o['bound_satisfied']}/{o['total']} truth_table_verified={o['truth_table_verified']}/{o['total']}")
        print(f"gate_count_mean={o['gate_count_mean']:.3f} gate_count_max={o['gate_count_max']} bound_margin_mean={o['bound_margin_mean']:.3f}")
        for hk in ("family_holdout", "time_holdout"):
            h = r.get(hk)
            if not h:
                continue
            hs = h["summary"]
            hr = hs["checked_bound_satisfaction_rate"]
            hr_s = "n/a" if hr is None else f"{hr:.3%}"
            print(f"  {hk}: {hs['checked_bound_satisfied']}/{hs['total']} ({hr_s}) groups/modules={len(h.get('test_groups', h.get('test_modules', [])))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
