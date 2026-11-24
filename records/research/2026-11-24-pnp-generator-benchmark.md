# PnP retrospective generator benchmark (2026-11-24)

Durable note for Founder handoff H-1795547911-c50a / study
`records/research/2026-11-24-founder-proof-production-study.md` (canonical Viche).

## What this is

`missions/pnp/bench/` is a self-contained retrospective benchmark for
graph-circuit-construction generators. It loads only public checked-corpus
metadata from the PnP proof-corpus SQLite index and generator outputs, then
scores:

- **bound satisfaction**: `gate_count <= bound`
- **gate count**: reported per row and summarized
- **independent truth-table verification**: exhaustive semantic check of the
  generated gate list against the edge-function, independent of generator code
- **checked-bound satisfaction**: truth table verified AND bound satisfied

It reports family-level holdouts (`n{n}-e{edge_count}` group tail split) and
time-based holdouts (tail by public module numeric key), so it measures
generalization rather than memorization.

No network services, no credentials, no unpublished proof sources. It does not
execute untrusted proof code.

## Corpus

Current public checked-corpus snapshot (`proof-corpus.sqlite`, revision
`5558ab4fa2fde8e9b642e634327daa66f48603b3`, index v2): 1269 checked proof rows,
55 match the finite graph-circuit construction shape recognized by
`missions.pnp.proofs.synthesis.parse` (all `n=8`, edges 4-7, bounds 7-11,
modules `PEqualNP.Outside.L_meta_1143`..`L_meta_1206` with gaps).

The 2026-11-24 study identified ~42 recognized accepted constructions across the
top six; this benchmark evaluates all shape-matching checked constructions in the
current public corpus snapshot and reports holdouts. Results should be read as a
retrospective benchmark, not a claim about unpublished or unheld gaps.

## Measured results (full current snapshot, 55 rows)

Command:

```sh
cd /var/lib/lubko/wd/viche-state/pnp/swarm/engineering/benchmark
PYTHONPATH=. python3 -m missions.pnp.bench --pretty --no-results
```

| Generator | Checked-bound | Rate | Bound sat | TT verified | Gate mean | Gate max | Margin mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| legacy_greedy | 35/55 | 63.636% | 35/55 | 55/55 | 9.182 | 13 | -0.382 |
| exact_star_cover | 55/55 | 100.000% | 55/55 | 55/55 | 8.800 | 11 | 0.000 |

Holdouts:

| Generator | Family holdout (n8-e7, 37 rows) | Time holdout (tail 14 modules) |
|---|---:|---:|
| legacy_greedy | 20/37 = 54.054% | 6/14 = 42.857% |
| exact_star_cover | 37/37 = 100.000% | 14/14 = 100.000% |

Small sample (5 rows, `--limit 5`): legacy_greedy 5/5, exact_star_cover 5/5;
both truth-table verified. The small sample is not representative; use the full
snapshot for comparison.

## How to run

Full benchmark (default generators, default public corpus cache DB):

```sh
PYTHONPATH=. python3 -m missions.pnp.bench --pretty --no-results
```

Quick smoke sample:

```sh
PYTHONPATH=. python3 -m missions.pnp.bench --limit 5
```

JSON for tooling:

```sh
PYTHONPATH=. python3 -m missions.pnp.bench --json --no-results > /tmp/pnp-bench.json
```

Evaluate precomputed generator outputs:

```sh
PYTHONPATH=. python3 -m missions.pnp.bench --outputs mygen=outputs.json --no-results
```

Tests:

```sh
PYTHONPATH=. python3 tests/pnp-bench.py
```

## Notes

- `legacy_greedy` is the pre-star-cover 3-strategy block-cover search.
- `exact_star_cover` computes an exact minimum vertex cover and assigns each
  edge to exactly one cover endpoint (single ownership). It is an upper bound,
  not a globally optimal circuit claim.
- Independent verification rejects semantic mismatches, out-of-range wires, bad
  ops, and output/bound failures even if a generator reports success.
