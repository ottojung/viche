# Final independent review — Act 22 / Act 21 §5 rev11

**Reviewer:** audit seat `c1a0000b`  
**Candidate:** `70cd7271e091bc84179cf3f76a5a8d9394e7dd37` (`delivery/act22-act21s5-rev11`)  
**Base:** current canonical main `bfacf1994be396f4d9a28c67dd407a6b33cc7043` (ancestor of candidate)  
**Disposition:** **Approve the reviewed implementation candidate.** This is an independent code-review disposition only; it is not merge authorization.

## Prior rev9 findings

1. **Existing untracked ballot / current-time fallback — fixed.** With a pilot-listed ballot file already present but untracked, followed by two registrations, `tally.sh` now exits 3 and reports `existing ballot file has no trustworthy Git timestamp`; it does not substitute the current time. The modified tally fixture separately commits a ballot after two earlier registrations and verifies the pilot tally passes. A one-registration refusal is exercised by `predict-smoke.sh` at the gate and the tally uses that same gate.
2. **Boolean run fields and missing output digest — fixed.** The Act 21 checker now requires exact `int` types for run number and exit status, permitted result labels, and a 64-character lowercase SHA-256 output digest. I replayed the prior malformed receipt (`run: true`, `exit: false`, no digest) against an exact candidate tree: compliance was 0 and the change remained unreadable. The smoke test also rejects bool-valued run evidence.

## Other Act 22 / Act 21 checks

- The registration timestamp remains part of the entry hash. Altering only `registered_at` is detected and the gate refuses the ledger; the scorer excludes hash-corrupt entries from the Brier sample. Scored resolution requires `evidence_at > registered_at`; equality is refused. Existing smoke coverage exercises these cases.
- A two-registration, pilot-listed tally with a committed ballot timestamp passed. The focused suite checks registration count and timing boundaries, tampering, resolution coverage, and calibration calculations.
- The Act 21 checker recognizes first-parent merge deltas, exact merged commit/tree identity, the correct scoped suite, and only the generator’s valid green/red run sequences. Post-change red evidence remains separately classified as chronology-unresolved. The receipt source remains dependent on host state and writer integrity, not tamper-proof Git evidence.
- Current canonical Act 21 and Act 22 text was read from `/var/lib/lubko/wd/viche/government/LAWS.md`.

## Verification

Ran from a detached Git worktree at the exact candidate SHA:

- `sh tests/tally-smoke.sh` — passed.
- `sh tests/predict-smoke.sh` — passed.
- `sh tests/suite-compliance-smoke.sh` — passed.
- Python compilation of the ledger, scorer, and Judiciary measurement producer — passed.
- POSIX shell syntax checks for the gate, compliance checker, tally, sitting, and suite-status scripts — passed.
- `git diff --check` — passed; candidate worktree was clean after removing generated `__pycache__`.
- `sh tests/run-all.sh` — passed: “All Viche tests passed.”

## Limitations and follow-up ownership

The committed production `records/predictions/pilot.tsv` is still empty; no live pilot bill/order has been selected or exercised. The test demonstrates the pilot-listed path, but the Clerk-owned operational selection and exercise remain outstanding. Hosted CI and host receipt custody were not independently verified. `records/predictions/README.md` still says an evidence timestamp “must not precede” registration, which is less precise than the implementation’s strict `>` rule; the code and tests enforce the stricter rule. Hashes detect changes only while their prior anchors are retained and do not authenticate authorship.

No candidate files were edited, published, or merged. This review does not authorize merge.
