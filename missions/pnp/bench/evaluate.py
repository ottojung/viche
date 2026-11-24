"""Evaluate generator outputs against checked-corpus metadata.

Scoring uses only public metadata and generated circuits. Truth-table
verification is independent of the generator implementation: it evaluates the
gate list directly against the edge-function semantics.
"""
from __future__ import annotations

from collections import defaultdict

from .corpus import family_key, time_key


class EvalError(ValueError):
    pass


def normalize_edges(edges):
    norm = []
    for e in edges:
        if len(e) != 2:
            raise EvalError(f"bad edge: {e!r}")
        a, b = int(e[0]), int(e[1])
        if a == b:
            raise EvalError(f"self-loop: {e!r}")
        norm.append(tuple(sorted((a, b))))
    return tuple(sorted(set(norm)))


def independent_truth_table(n, edges, gates, output):
    """Independently verify circuit semantics by exhaustive truth table.

    Returns (ok, detail). This does not trust generator-side verification.
    """
    if not isinstance(n, int) or n < 0 or n > 16:
        return False, {"error": "unsupported_n", "n": n}
    edges = normalize_edges(edges)
    if any(b >= n for _, b in edges):
        return False, {"error": "edge_out_of_range"}
    if not isinstance(gates, list):
        return False, {"error": "gates_not_list"}
    if not isinstance(output, int):
        return False, {"error": "output_not_int"}
    if not (0 <= output < n + len(gates)):
        return False, {"error": "output_out_of_range", "output": output}

    for idx, g in enumerate(gates):
        if not (isinstance(g, (tuple, list)) and len(g) == 3):
            return False, {"error": "bad_gate_shape", "gate_index": idx}
        op, a, b = g
        if op not in ("and", "or"):
            return False, {"error": "bad_op", "gate_index": idx, "op": op}
        wire_limit = n + idx
        if not (isinstance(a, int) and isinstance(b, int)):
            return False, {"error": "bad_wire_type", "gate_index": idx}
        if not (0 <= a < wire_limit and 0 <= b < wire_limit):
            return False, {"error": "wire_out_of_range", "gate_index": idx}

    for mask in range(1 << n):
        wires = [(mask >> i) & 1 for i in range(n)]
        for op, a, b in gates:
            va, vb = wires[a], wires[b]
            wires.append((va & vb) if op == "and" else (va | vb))
        expected = 1 if any(wires[a] and wires[b] for a, b in edges) else 0
        got = wires[output]
        if got != expected:
            return False, {
                "error": "semantic_mismatch",
                "counterexample_mask": mask,
                "expected": expected,
                "got": got,
            }
    return True, {"cases": 1 << n}


def evaluate_row(row, gates, output):
    """Score one generator output against one corpus metadata row."""
    n = int(row["n"])
    bound = int(row["bound"])
    edges = normalize_edges(row["edges"])
    ok, detail = independent_truth_table(n, edges, gates, output)
    gate_count = len(gates)
    bound_satisfied = gate_count <= bound
    checked = bool(ok and bound_satisfied)
    return {
        "module": row.get("module"),
        "path": row.get("path"),
        "n": n,
        "bound": bound,
        "edge_count": len(edges),
        "gate_count": gate_count,
        "bound_satisfied": bound_satisfied,
        "truth_table_verified": bool(ok),
        "checked_bound_satisfied": checked,
        "verification": detail,
    }


def summarize(results):
    total = len(results)
    bound_ok = sum(r["bound_satisfied"] for r in results)
    tt_ok = sum(r["truth_table_verified"] for r in results)
    checked = sum(r["checked_bound_satisfied"] for r in results)
    gates = [r["gate_count"] for r in results]
    margins = [r["bound"] - r["gate_count"] for r in results]
    return {
        "total": total,
        "bound_satisfied": bound_ok,
        "truth_table_verified": tt_ok,
        "checked_bound_satisfied": checked,
        "checked_bound_satisfaction_rate": (checked / total) if total else None,
        "gate_count_mean": (sum(gates) / total) if total else None,
        "gate_count_max": max(gates) if gates else None,
        "bound_margin_mean": (sum(margins) / total) if total else None,
    }


def holdout_split(rows, key_fn, test_fraction=0.25):
    """Deterministic holdout split by a key function.

    Groups rows by key, sorts groups by key, then assigns the tail fraction of
    groups to test. Group-level splitting avoids leaking near-identical family
    members across train/test.
    """
    groups = defaultdict(list)
    for row in rows:
        groups[key_fn(row)].append(row)
    keys = sorted(groups)
    if not keys:
        return [], []
    test_group_count = max(1, int(round(len(keys) * test_fraction)))
    test_keys = set(keys[-test_group_count:])
    train, test = [], []
    for k in keys:
        (test if k in test_keys else train).extend(groups[k])
    return train, test


def evaluate_generator(rows, generator, generator_name=None):
    results = []
    for row in rows:
        gates, output = generator(row["n"], [tuple(e) for e in row["edges"]])
        res = evaluate_row(row, gates, output)
        res["generator"] = generator_name
        res["family"] = family_key(row)
        results.append(res)
    return results


def evaluate_with_holdouts(rows, generator, generator_name=None, test_fraction=0.25):
    all_results = evaluate_generator(rows, generator, generator_name)
    _, fam_test = holdout_split(rows, family_key, test_fraction)
    fam_test_keys = {r["module"] for r in fam_test}
    fam_results = [r for r in all_results if r["module"] in fam_test_keys]

    ordered = sorted(rows, key=time_key)
    cut = max(1, int(round(len(ordered) * (1 - test_fraction)))) if ordered else 0
    time_test = ordered[cut:]
    time_test_keys = {r["module"] for r in time_test}
    time_results = [r for r in all_results if r["module"] in time_test_keys]

    return {
        "generator": generator_name,
        "overall": summarize(all_results),
        "family_holdout": {
            "split": "group_tail_by_family_key",
            "family_key": "n{n}-e{edge_count}",
            "test_fraction": test_fraction,
            "test_groups": sorted({family_key(r) for r in fam_test}),
            "summary": summarize(fam_results),
        },
        "time_holdout": {
            "split": "tail_by_public_module_time_key",
            "test_fraction": test_fraction,
            "test_modules": [r["module"] for r in time_test],
            "summary": summarize(time_results),
        },
        "results": all_results,
    }
