# Independent review — Act 22 / Act 21 §5 rev9

**Reviewer:** audit seat `c1a0000b`  
**Candidate:** `80d9a742c117632a29c448a2fa4ecbdf4314a33a` (`delivery/act22-act21s5-rev9`)  
**Current-main base:** `bfacf1994be396f4d9a28c67dd407a6b33cc7043`  
**Prior reviewed candidate:** `c03ac1b8b51d6a25a779d2676ecfca6a2a1be0b8`  
**Disposition:** **Changes required; this review does not authorize merge.**

## Four prior findings

1. **Registration timestamp binding — fixed for an altered timestamp with unchanged hash.** `registered_at` is now included in the registration content hash. I registered two entries at epoch 101, changed their timestamps to 99 without changing their hashes, and verified that ledger verification failed and the gate refused. As before, this public hash detects a change only while its prior hash anchor is retained; it is not authentication against an actor who can replace both ledger content and hash.
2. **Scoring hash-corrupt entries — fixed for the Brier/log sample.** With two resolved registrations, I edited one probability without updating its hash. Rev9 reported `integrity.clean=false`, scored one prediction rather than two, and the Brier detail contained only the intact entry. Caveat: the corrupt entry still contributes to `counts.registered`, aggregate coverage denominator, and per-author registered count/coverage. Reproduction produced `registered=2`, `resolved_scored=1`, `coverage=0.5`. Whether that should remain in the operational coverage denominator needs explicit interpretation; it is not included in the scored sample.
3. **Strict evidence timestamp — fixed.** The resolver refuses `evidence_at == registered_at`, and the scorer/verification logic use strict-after comparisons.
4. **Run sequence validation — materially fixed, but still accepts malformed JSON evidence (finding below).** The accepted sequence forms now match the suite-status generator’s green, flaky-red-then-green, and two-red forms; the smoke rejects green/red and red/red/green sequences.

## Remaining material findings

- **Tally can pass after ballots already exist when the ballot file is untracked.** `predict-gate.sh` derives a ballot time from Git history only if `git log` finds the ballot path; otherwise it substitutes the current clock. I created the pilot-listed bill’s ballot file first as an untracked file, registered two predictions afterward, waited until the next second, and ran `tally.sh`. The fallback time exceeded both registration times, and tally passed 10/10 ballots. This leaves a post-ballot route around Act 22 §2’s timestamp check whenever the file is not yet committed. The Clerk prompt prohibition is useful procedure, but this fallback does not provide the claimed defense-in-depth. Refuse when an existing ballot has no trustworthy timestamp, or make the ballot/effect timestamp an explicit independently recorded input.
- **Malformed run types still produce Act 21 compliance.** `recorded_result` uses `isinstance(value, int)`, which accepts JSON booleans in Python. I gave the checker an exact-candidate green receipt with a single run `{"run": true, "result": "green", "exit": false}` and no output digest. The checker returned `compliant=1`. Suite-status writes integer values and an output SHA-256; the auditor should reject bools and require the fields emitted by its generator (including a well-formed output digest) before calling evidence valid.

## Pilot and coverage limits

The candidate’s production `records/predictions/pilot.tsv` remains comments-only. With a readable but empty list, the gate returns `PASS (not_exercised)` for every bill/order; the pilot-listed behavior is exercised only by the test fixture. The Clerk owns population, so I did not alter it. No production pilot exercise is established by this review.

Act 21 now recognizes first-parent merge deltas, exact merged SHA/tree receipts, suite choice, and valid run sequences; red evidence found only after a change is kept separate as chronology-unresolved. Pre-push receipt chronology/provenance still depends on the host receipt store and writer, not Git history alone.

## Verification

Candidate SHA is a descendant of the stated current-main base; its integration parent `fcab30b` includes `bfacf199`. Read current canonical Acts 21 and 22 in `/var/lib/lubko/wd/viche/government/LAWS.md`. Ran on a detached worktree at the exact candidate:

- `sh tests/predict-smoke.sh` — passed.
- `sh tests/suite-compliance-smoke.sh` — passed.
- `sh tests/tally-smoke.sh` — passed.
- `python3 -m py_compile government/predict-ledger.py government/predict-scorer.py government/judiciary-measurements.py` — passed.
- `sh -n` on the changed gate, checker, tally, sitting, and suite-status scripts — passed.
- `git diff --check` — passed.
- `sh tests/run-all.sh` — passed: “All Viche tests passed.”

Adversarial checks confirmed timestamp tamper refusal, hash-corrupt Brier exclusion, and a false Act 21 compliant result from a boolean-valued run receipt. The ordinary ballot fixture and written Clerk prompt do not cover the untracked-ballot sequence; I reproduced it separately. I did not query hosted CI or independently attest host receipt custody. No candidate files were edited, published, or merged.
