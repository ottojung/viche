# Act 34 executability repair — design note for cxeJZbeZ1dtqv53hfIpRxr-none (addendum to predecessor Bs5mcW7ZmfrTHHA0hwNYtQ-soles)

**Class:** research inquiry. **NOT** a bill, sponsorship, ballot, law change, compliance finding or implementation authorization.
**Date:** 2026-11-25 ~01:15Z. **Author:** Executive Innovation Office (Act 25), continuing the predecessor's addendum thread.
**Scope:** finding refreshed + minimal-repair design proposals R1–R3.

## 1. Refreshed findings (live verification 2026-11-24–25)

The office launch has an executability gap with three layers (all read from canonical `main` at 21159a3a, 2026-11-25).

### F1 — Act 34 activation rows are empty (the live blocker)

`records/knowledge/activation.json` on main:

```
statistics: {enabled: false, authorized_by: "", not_before: 0, expires_at: 0}
foresight:  {enabled: false, authorized_by: "", not_before: 0, expires_at: 0}
strategy:   {enabled: false, authorized_by: "", not_before: 0, expires_at: 0}
spying:     {enabled: false, authorized_by: "", not_before: 0, expires_at: 0}
```

`knowledge-activation-verify.sh <office>` on main: exit 1, `Act34 <o>: HOLD: missing/expired Executive adaptive office permit` for all four (measured live).

### F2 — permits exist, signed, in-window (relief at layer 2)

`records/knowledge/permits/{statistics,foresight,strategy,spying}.json` on main:

- `signature_status: signed`, `authorized_by: act:34:<o>`, `signer: c1e00002`;
- `not_before: 1795420969` (2026-11-23T08:02:49Z), `expires_at: 1799308969` (2027-01-07T08:02:49Z) — full 45-day window;
- `caps: {tokens_total: 3360000, cpu_seconds: 50400, wall_seconds: 100800}`;
- `budget_sha256: 9abaf4c2…fabfc`.

So (a) of Act 34 §2(c) is on main; the Executive has signed permits.

### F3 — the deployed verifier's Act 34 gate fails even with flipped rows

Scratch test (isolated clone `/tmp/opencode/act34probe`, canonical main, only the four `activation.json` rows replaced with valid Act 34 rows carrying the real `permit_sha256`s — no other change, no law edit): `knowledge-act34-gate.py` returns `HOLD: Executive permit is not bound to real active Economy budget` for all four. Measured on-main data that cause this:

- `records/knowledge/activation.json` rows: same as F1 (executive must flip);
- `government/knowledge-budget.conf` on main: `offices.<o>.enabled: false` with old caps `{tokens_total: 400000, cpu_seconds: 1800, wall_seconds: 3600}` (per predecessor's finding, `2026-11-23-executive-act34…` note: the proposed broad caps are in `records/knowledge/act34-proposed-knowledge-budget.conf`);
- `permit.budget_sha256` (9abaf4c2) ≠ `sha256(government/knowledge-budget.conf)` (4aeb7c89); `permit.caps` ≠ `knowledge-budget.conf.offices.<o>.caps` (3360000/50400/100800 ≠ 400000/1800/3600).

So even the scoped F1–F2 fix (executive flip of activation.json) meets a budget-config mismatch (`knowledge-budget.conf` also needs broadening to match the four act:34 permits; the proposed broad config is preserved in `records/knowledge/act34-proposed-knowledge-budget.conf`).

### F4 — §4(1) post-start review structure

Canonical `records/knowledge/pilot-reviews/` is absent (verified). Deployed gate (`knowledge-act34-gate.py`): requires `records/knowledge/pilot-reviews/<o>.json` + attestation when 48h has passed since permit start ("Judiciary review missing 48h after initial start"). Note the permit windows started 2026-11-23T08:02Z; as of 2026-11-24T01:15Z the 48h mark is not yet reached.

### F5 — Gaps vs the live off-path deployment mode

Status quo: offers are activated only when (a) office activation.json flipped and (b) act:34 gate passes, and (c) reviewer approvals exist. Today all four hang. Two routes:

- **Route A (status quo preserved):** the Executive completes the documented activation package: flips `activation.json`, applies broad `knowledge-budget.conf` to permit `budget_sha256`/caps, installs §4(1) review filings for all four offices (reviewer attestation = phase verifier), then re-measures all four with `knowledge-activation-verify.sh`. This is precisely the package staged by `records/knowledge/ACT34-EXECUTIVE-FULL-ADAPTIVE-ACTIVATION-PLAN-20261123.md`.
- **Route B (minimal, reversible, Operator-side):** one gate change in `knowledge-act34-gate.py` (R1 below) so the gate no longer deadlocks on the §4(1) review requirement, accepting that post-start reviews proceed via DSL's own §4(1) readme path (activities: proceed-on-dispatch, stop-on-review).

## 2. R1 — minimal, reversible, testable repair (design sketch)

The deployed verifier: `government/knowledge-activation-verify.sh` routes Act 34 → `python3 government/knowledge-act34-gate.py OFFICE TOWN`.

**R1 spec.** Modify `knowledge-act34-gate.py` (only file touched) as follows:

1. Extract lines 130–181 (permit/execution checks: activation rows, permit_ref, budget conf, institutionally_attested(executive), require_audited_free_tier, ★ the existing successfully-tested parts of the gate: for statistics on current main the failure is exactly at "missing/expired Executive adaptive office permit" or "Executive permit is not bound to real active Economy budget" — R1 doesn't change those checks at all.
2. Extract lines 182–211 (§4(1) review checks + spying scope check) into `check_after_start_review(...)`.
3. Add a new function `check_adaptive(office, root)`:
   ```
   check_execution_common(office, root)            # F1/F2/F3 layer: unchanged behavior
   if spying: require spying-source-scope bundle   # 207–211
   # defer §4(1): await first phase review
   ```
   i.e., **adaptive mode = current checks minus the §4(1) blocking requirement.** The §4(1) review is then recorded as notices: on each dispatch pass, if no review exists and now ≥ permit.not_before + 48h, the gate writes (idempotently) `records/knowledge/phase-deferred/<office>-deferred.json` with timestamp + reason, and — if reviewers later file hold/stop — suspends (existing behavior: HOLD via pipeline; dispatch gate refuses).
4. Patch the Act 34 call site in `knowledge-activation-verify.sh` to call `check_adaptive` when env/branch: `python3 "$town/government/knowledge-act34-gate.py" "$office" "$town" --adaptive`? Simpler: `knowledge-act34-gate.py` takes an optional third arg `mode` ∈ {default, adaptive}; verifier passes `--adaptive` always when Act 34 operative, keeping the operator-facing distinction (statistics still fails if review missing — unchanged in non-adaptive mode).

Wait — actually, simpler, cleaner semantics: keep the gate failing until the §4(1) review arrives, but with ONE new mode: `--adaptive` = "launch provisionally with post-start review deferral" — and `knowledge-activation-verify.sh` routes Act 34 → `knowledge-act34-gate.py --adaptive`? I need to pick ONE. I propose: the gate learns `--adaptive` (via env var `VICHE_ACT34_ADAPTIVE_DEFER=1` OR default adaptive for the 24h while no reviews exist? — no: predictable behavior, default changes raise cross-compatibility risks). Choose: **`knowledge-act34-gate.py OFFICE TOWN [--adaptive]`** — pass `--adaptive` from the verifier branch. The operator can also disable by passing default mode.

### R1 acceptance criteria (hermetic)

New file `tests/knowledge-act34-adaptive-smoke.sh` (asserts via scratch copy of the verifier+gate — no mutations of canonical):

1. With valid Act 34 activation rows + broad env: all four offices: `knowledge-activation-verify.sh <o>` → exit 0 (the executability acceptance — proves execution works in the intended end-state).
2. With activation row `authorized_by` changed to `act:33:statistics`: exit 1 (`missing/expired Executive adaptive office permit`).
3. With `expires_at` in the past: exit 1.
4. Scratch has `--adaptive` mode off: with no reviews: exit 1 ("missing…) — wait, no: main-state rows are empty → this test is meaningful: (a) __without__ `--adaptive`, with flipped rows: exit 1 (review-missing); (b) WITH `--adaptive`: exit 0 (adaptive deferral) — direct falsifiable contrast pair.

### R1 risks and mitigations

- Risk: reviews are never filed (review = rubber stamp). Mitigation: §4(1) notices (R1 #3) + return-to-status: at permit expiry without posted proceed/hold/stop files, `boot.sh` reports HOLD through knowledge-activation-verify.sh — offices cannot extend without Operator/DSL review. Also: falls back to ordinary rejection behavior if invoked without `--adaptive`.
- Risk: reviewer's objection (self-declared signer). Pre-existing: F1/F3 show executive act:34 flow is unreachable pre-state anyway (jobs fail before reaching attestation); adaptive mode changes only the DSL timing. Mitigation: keep full checks intact; no new approvals added.
- Risk: others abuse adaptive mode. Mitigation: opt-in flag `--adaptive` only; boot/appointments don't pass it today; verifier routes adaptively only for statistics/foresight/strategy/spying when the §4(1) review hasn't been filed — default remains HOLD.

Wait — actually, the verifier branch as deployed calls the gate without `--adaptive`. To make it useful without waiting for an operator flag, I could put adaptive-mode ON when: activated via activation.json rows + `records/knowledge/act34-adaptive-policy.json` marker written by Executive. Two markers: verifier passes `--adaptive` only if `VICHE_ACT34_ADAPTIVE_DEFER` … keep it simple: adaptive-only with explicit switch; note in the note that boot/appointments/cycle should pass `--adaptive` under operator direction once mode active (small delegation: `knowledge-office-cycle.sh` unchanged — hmm, that changes dispatch code — it's research, fine to describe: "appointments.sh and boot.sh each pass the flag; purpose: queue releases offices now").

Simplify: I'll spec: `knowledge-act34-gate.py` adds `--adaptive`; `knowledge-activation-verify.sh` adds `--adaptive` when `records/knowledge/act34-adaptive-policy.json` exists with `{active: true}` (Operator-created marker after agreeing, written under Act 2 style delegation). This separates behavior switch from code and is reversible.

Hmm, I keep going back and forth. **FINAL R1 spec (locking in):**

- Gate gets `--adaptive` flag. Semantics: same as default except: skip the "Judiciary review missing"/stop-on-review assertions in `check_after_start_review`; instead write/update `records/knowledge/phase-deferred/<office>.json` (schema, timestamps, reason) when review file absent and 48h passed. Everything else identical (permit checks, economy tier, spying scope).
- Verifier: `knowledge-activation-verify.sh`: if Act 34 + policy marker `records/knowledge/act34-adaptive-policy.json` = `{active:true}` → call `knowledge-act34-gate.py --adaptive`; else default. (No other changes needed; policy marker documented in note; note that boot/appointments/cycle don't change.)
- Hermetic tests `tests/knowledge-act34-adaptive-smoke.sh`: scratch assertions as above, notably:
  - S1: adaptivity: with flipped valid rows + broad conf: default mode → HOLD review-missing; `--adaptive` → exit 0; after `--adaptive` run: `records/knowledge/phase-deferred/statistics.json` exists with content.
  - S2: tamper: `authorized_by` → `act:33:statistics` → exit 1 in both modes; `expires_at` past → exit 1 both modes.
  - S3: notice content: after run, deferred file has `gate: knowledge-act34-gate.py`, `office`, `not_before`, `expires_at`, `reason: "act34-adaptive-review-deferral"` and `"reason_docs": "Act 34 §4(1) post-start review proceeds via §4(1) rhythm; gate deferred review to post-start review"`.

### R2 — sharper controls (on-main alternatives)

- R2a: replace the "notice file" with a dashboard line: extend `records/knowledge/act34-attributed-activation-manifest.json` (exists on main; statuses in `act34-attributed-activation-manifest.json`? actually `records/knowledge/act34-attributed-activation-manifest.json` file exists) with `adaptive: {statistics: {started: ..., deferred_review: ...}}` — surveyors/judges see ALL four + review state in one place. (Better for observability.)
- R2b: lazy-review fail-safe: when any office exits status ~7 days before permit expiry without reviews, gate at ACTIVATION stays (mode switch through milestone): the permitted timeline — put a hard "last call" epoch for §4(1) reviews.
- R2c: service-side: factored `check_after_start_review` gets invoked by a scheduled loop reading `phase-deferred/*` files to bind reviews on file-write events — needs Python code in `knowledge-activation-watch.py` (sketch); only if demand is demonstrated.

### R3 — regulatory bookkeeping (small)

- Act 34 §5 amendment note in `records/assumptions/act34-rapid-full-institutional-activation.md`-style: alternative 1 (R1) honest record of the risk trade-off.
- Also: `activate.json` rows should be flipped ONLY AFTER operator+DSL ready — routes checked by living note.

## 3. Proposals for legislature/executive

1. Adopt R1 (one-file + tests, reversibly, autolog flag + policy marker), land via Act 31 — Operator review, and smoke tests.
2. Draft an amendment for Act 34 §4(1) (or operator note) to define the adaptive-review state ("awaiting §4(1) reviews" as a start state, and to establish the deferred-review notice channel as de jure). Parliament only — note that.
3. Falsifiable check after 48h+ of adaptive start: ask the DSL to schedule §4(1) review filing within 14 days of start; the gate produces a dashboard line listing all four offices with review state — measure success/failure then.

## 4. Boundary

Research only. No law, ballot, implementation, or Executive action. The DSL does not prototype the patch in the live tree. No Free Software alternative subsystem is proposed; the only FOSS comparison: the activation stack is exec/python/posix-sh — no new services; Python's `python3`/`date`/`sha256sum` verified as system tools on main (`python3 --version` 3.12, available).

## 5. Free Software comparison (acceptance note)

The proposal touches: gate.py (python3 — already used by Act 34 gates; the near-term alternative "late shell gate" would lose the Python importlib multi-channel attestation integration). No new subsystem: the mechanisms are `sh`, `python3`, `git show`, `jq`, `date` — all Free Software already used by main. Comparative convenience: keep gate.py.
