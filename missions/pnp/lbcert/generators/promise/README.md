# Promise circuit witness generation

The generator searches small monotone and general circuit witnesses on the exact
promised domain. The independent evaluator checks every candidate against the
target truth table and gate budget. Standalone Lean verification is required
before claiming a proof-of lease. The ordinary publisher performs submission.

The batch lane shares bounded formula tables between five- and six-input two-lit
instances. One generator and two verification workers keep up to 32 eligible
checked proofs in reserve; at most 256 eligible unverified attempts are staged.
Held work has priority. Attempts are keyed by exact statement digest and solver
version, persisted in SQLite, and retried on infrastructure failures. A sharing-aware root-pair fallback counts the union of actual gate
subexpressions instead of their formula costs. A bounded
search refusal is not a mathematical impossibility result; it permits ordinary
plugin and sibling-search fallback.

Read-only inspection (from the town checkout):
```sh
python3 -m missions.pnp.lbcert.generators.promise.batch --status
```

The batch process is supervised by autosolve; it should not be launched as a
second independent production service. A recent heartbeat identifies its
ownership, and its singleton lock prevents duplicate work. No direct PRs or
desk acquisitions are made by this lane.

2026-11-26 pilot: shared formula search generated 157 independent semantically
valid six-input witnesses (advertised 4719 points, not credited points). Exact
standalone verification and normal proof-of publication are separate stages.
A subsequent sharing-aware pilot found 68 additional witnesses on its first
200 targets. The desk's actual frozen lease price and eventual accepted score are distinct.
