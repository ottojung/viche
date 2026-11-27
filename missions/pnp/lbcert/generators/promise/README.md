# Promise circuit witness generation

The generator searches small monotone and general circuit witnesses on the exact
promised domain. The independent evaluator checks every candidate against the
target truth table and gate budget. Standalone Lean verification is required
before claiming a proof-of lease. The ordinary publisher performs submission.

The batch lane shares bounded formula tables between five- and six-input two-lit
instances. One local generator stages candidates. Held exact candidates go
through the ordinary lease-fenced publisher; unheld candidates remain staged
for the separately authorized private checker. Only a valid exact managed
compiler receipt can turn an unheld candidate into checked stock. Normally
up to 256 eligible unverified attempts are staged; fresh and held work may
bypass that cap.
Held work has priority. Attempts are keyed by exact statement digest and solver
version, persisted in SQLite, and retried on infrastructure failures. A sharing-aware root-pair fallback counts the union of actual gate
subexpressions instead of their formula costs. A bounded
search refusal is not a mathematical impossibility result; it permits ordinary
local plugin fallback. Sibling indexing is local; sibling adaptation is not
automatically checked.

Read-only inspection (from the town checkout):
```sh
python3 -m missions.pnp.lbcert.generators.promise.batch --status
```

The batch process is supervised by autosolve; it should not be launched as a
second independent production service. Its singleton lock prevents duplicate
work. No direct PRs or desk acquisitions are made by this lane.

2026-11-26 pilot: shared formula search generated 157 independent semantically
valid six-input witnesses (advertised 4719 points, not credited points). Exact
managed local verification and normal proof-of publication are separate stages.
Historical pilot measurements do not authorize external compute.
A subsequent sharing-aware pilot found 68 additional witnesses on its first
200 targets. The desk's actual frozen lease price and eventual accepted score are distinct.

### Optional bit-parallel stochastic synthesis

The fallback annealer compiles a process-private C executable when a C compiler
is available. It searches only topologically valid bounded circuits, evaluates
their truth tables in one 64-bit word, and mutates/recombines a small population
of candidates. The ordinary Python evaluator rechecks every returned witness.
A separate exact managed Lean compiler receipt from a bound workspace is still
mandatory. An unavailable compiler, timeout, or failure is an unknown result,
never a lower bound.
The batch attempt version includes both the Python wrapper and C source.

Historical record only: a November 26 pilot on another host tested 40 known-solvable six-input
two-lit instances with their supplied witnesses withheld: the initial
compiled search recovered 23 within 0.5 seconds each, versus 4 using only
the standalone Python heuristic. This is not a comparison with the entire
existing solver (which also uses sketches, formula tables and DAG/SAT methods).
On the harder remaining unclaimed rows, the exploratory searches did not
find a witness; do not interpret the pilot as a promised conversion rate.

### Optional persistent positive-witness index

A read-only local index can bypass expensive repeated formula enumeration.
It contains only candidate circuits, never checked receipts or lower bounds.
Each lookup checks the exact input truth tables, size, topology, allowed gate
types and the target truth table with the ordinary independent evaluator.
Missing, malformed, or out-of-budget records fall back to the usual solver.
The batch version changes when an index file is installed or replaced.

The native offline builder is `formula_index.cpp`. It takes on stdin
`input_count row_count max_formula_gates allow_not` followed by the exact
input truth tables from `gen.input_tables`; its sole argument is the output
file. Build only on billy-dev, in a research directory, with a bounded
CPU/time/memory budget and authorized local generation. The builder uses
little-endian x86-64 binary files; install only a completed, audited file by
atomic rename under `PNP_STATE_ROOT/lbcert/formula-index/`. File names are
`two-6-6-FanInTwo.idx`, `two-5-5-Monotone2.idx`, etc.; the dimension
pair is exactly the parsed problem dimensions, not the total input count.
No runtime process automatically builds or downloads these files. Do not
enable or promote anything before the relevant Executive gates.

Historical November 27 billy-dev pilot: depth-eight general formulas on
the six-input two-lit domain produced 241724 replayed distinct truth tables
in a roughly 14 MiB file. Independent Python bitwise replay checked every
stored circuit and the per-row evaluator checked a random sample of 256.
331 of 365 accepted corpus targets (gate bound at most eight) were recovered.
No witness met the bound of the then-current catalog in this family.
This measures retrospective candidate recovery, not future points.
