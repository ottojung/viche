# Act 32 independent phase gates — implementation record (2026-11-20)

**Agent:** independent serial phase-gate workstream `spurs`
(ANTONINA_AGENT_ID `70w4I5JNjBvOkuavI3X2my-spurs`), pin
`sZadXosqQSRmOish1t0ouH-pinched`, origin hub `SvMHxlO6F1R6u3cQcr3lKA-repeated`.
**Authority:** user/operator implementation mandate under lawfully enacted
Act 32. This is ordinary implementation on billy-dev, **not** a Founder
communication, ballot, vote, Judicial verdict, Executive activation order or
Governor approval. No office is enabled by this work.

## Delivered (production code)

* `government/knowledge-phase-verifier.py` — standalone, deterministic,
  fail-closed phase-gate verifier with its own data format
  (`viche-knowledge-phase-gate-v1`). No Post/network reads; no state mutation in
  `verify`/`audit`. POSIX-independent Python 3 stdlib only.
* `government/knowledge-phase-gate.sh` — POSIX `/bin/sh` wrapper (no authority).
* `records/knowledge/PHASE-GATE-SCHEMA.md` — data-format and verification spec,
  including the residual trust-model limitation.
* `records/knowledge/phases/statistics-initial.json` — an **honest draft HOLD**
  record: no review, all four preconditions unproven, `decision: hold`. It is
  not an activation, not a signature, not an Executive order. It anchors real
  source digests for the frozen baseline and the all-disabled activation record.
* `tests/test_knowledge_phase_verifier.py` — 34 end-to-end tests in throwaway
  Git repositories.
* `tests/knowledge-phase-verifier-smoke.sh` — production-record smoke test
  (fail-closed hold, all offices disabled, wrapper POSIX, no Post dependence).

## What the verifier enforces

* exact enacted Act number parsed at runtime from canonical LAWS.md (not
  hardcoded) plus the exact v4 bill id, exact office and `billy-dev` host;
* serial chain statistics → foresight → strategy → spying; a successor's
  `not_before` must be ≥ the predecessor's independently verified signed gate
  date (evidence dependency, not predecessor liveness — amendment K);
* Git-anchored evidence with recomputed SHA-256 and canonical `evidence_digest`;
  artifact reads by exact Git tree traversal (`ls-tree` + `cat-file blob`),
  rejecting `..`, absolute paths, symlinks and non-blob entries;
* reviewer must be a real registered officer; only the Judiciary may sign a
  proceed; Git artifact bytes must bind gate id, reviewer, role, decision and
  evidence digest; replay/reuse and forged/missing/expired approvals fail closed;
* **multi-channel attestation**: a board institutional review verdict of
  `approve` on the exact artifact commit, an officer-attributed board comment
  citing the gate, and a matching appointment plus attributable agent session —
  a Git text file alone is never treated as a signature (response to the
  independent trust-model review, board 2026-11-20T18:10Z);
* 14-day initial cap, 45-day absolute maximum, no 30-day wait to launch the
  authorized Statistics trial (prospective evidence allowed), mandatory day-30
  Judiciary review before renewal with automatic hold if missing, later lawful
  reauthorizing Act required for renewal;
* expiry refuses new launches while recorded in-flight work may wind down;
  `audit` emits `new_invocation_after_expiry`, `in_flight_continuations`,
  `rollbacks` and `violations`; rollback records block every phase.

## Test evidence

* `python3 tests/test_knowledge_phase_verifier.py`: **34 tests, all pass**,
  including rogue-Git-artifact with wrong board commit, missing attestation,
  wrong reviewer/commit/agent, unsafe path, forged/missing/reused approvals,
  crash/reboot determinism (identical output on repeat), Post outage
  irrelevance, invalid Git state, rollback, expiry/in-flight distinction and
  day-30 auto-hold.
* `/bin/sh tests/knowledge-phase-verifier-smoke.sh` and `dash` variant: pass.
* Full `tests/run-all.sh`: green (no regression).

## Honest status and limits

* No phase currently proceeds. The only production record is a HOLD; the
  verifier returns `decision: hold`, non-zero `verify` exit, and `audit` shows
  no dispatch, no violations and no new invocation after expiry.
* The four offices remain `enabled: false` in `records/knowledge/activation.json`.
* The Statistics preflight (independent comparator workstream) found the frozen
  baseline diagnostic, the outcome numerator unverified, Economy resource cost
  unavailable and no Executive order / Judiciary determination yet. Those are
  exactly the unmet preconditions the verifier refuses. This mechanism does not
  supply them and does not fake them.
* Residual trust limit: the shared UID cannot cryptographically authenticate
  board authorship, appointments or Git commits (Act 32 clause 5). The
  attestation channels are separate institutional actions, not a digital
  signature; they are labelled "attested", never "signed". No real Judiciary or
  Governor sign-off was created in this work.

## Integration plan (isolated follow-up — NOT done here)

Three concurrent workstreams edit `government/knowledge-office-cycle.sh` or
`government/boot.sh`: `budget-engine-20261120`, `spying-allowlist-20261120`,
`statistics-comparator-20261120`. Per mandate, **no shared file was edited**.
Once those land or are ready, an isolated follow-up change will add a single
guard in the runner that calls `knowledge-phase-gate.sh verify <gate>` before
any new office dispatch (in-flight wind-down exempt), preserving all of their
edits, with its own Act 21 suite and independent Act 31 review. A future
Post/Gazette migration still requires a separate Cutover Act (amendment N).

## Next

Request independent Act 31 review of this branch; land only when safe. Keep all
offices disabled pending real Executive order, Judiciary determination and
filed, independently attested phase-gate evidence.
