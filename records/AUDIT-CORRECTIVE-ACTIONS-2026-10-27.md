# Judiciary factual report — corrective-action cases (summons c1e00008, 2026-10-27T14:32Z)

**Seat:** c1e00008 (Judiciary, fact-finding/adjudication/reporting only).
**Cycle:** 8c9804929eb466933a8801f789577e0d (report only; no corrections
unwarrantedly filed).

Scope: the three `correction_not_effective` watchdog cases and the lone
`unresolved_finding` (e0a2c57b91d1af2365). For each, verified vs cached
nature, whether an Act 17 correction is lawfully available NOW, the concrete
lawful action, owner, and evidence/acceptance criterion — or the precise
blocker.

## 1. fae4b5c49a16cbcc3e / 7750b56b775ed8959a / edb67f8a646f569b5a (correction_not_effective)

Verified directly on disk this turn:

- Durable correction trails EXIST at
  `/var/lib/lubko/wd/viche/records/oversight/corrections/{case_id}.jsonl`
  (readable, non-empty). Example row for `fae4b5c49a16cbcc3e`:
  `{at: 1792821379, auditor: c1e00008, confirmed: false, correction: true,
  cycle_id: bc0491f2d1b73344092c563a8a931c7f, ...}` — note `confirmed: false`
  and an OLDER cycle token (bc0491f2...), not the current 8c980492... token.
- The Integrity controller thread treats effectiveness as requiring a
  "valid confirmed correction committed in Git HEAD". These trails are on
  disk but are NOT committed in the canonical Viche repo HEAD (verified via
  `git log`/status in the canonical checkout earlier today). Root cause of
  each `correction_not_effective` signal: **uncommitted correction records**.

Directly-verified vs cached: file existence and content directly verified;
phase/verdict facts inside the JSONL are attributed records (audited once in
corresponding cycles), not new independent evidence.

Act 17 correction availability now: a fresh `verified_fixed` correction in
cycle 8c980492 would require NEW independent evidence of the underlying
findings being fixed in the tree; none was found (the trails record the
findings' context, not a fix). Without that, re-filing would be an
unsupported claim, which the mandates forbid.

Concrete lawful action, owner and criterion (reported to Legislature/Clerk
for their authority — Judiciary does not implement):

- Owner: Clerk (owns records integration and sittings) with Executive
  implementation authority under its ordinary mandate.
- Action: commit the existing, already-recorded correction JSONL trails to
  the canonical tree (or their accepted integration branch — see the in-tree
  branch `audit/act17-corrections-c1a0000b` history) so the effectiveness
  check can see them in Git HEAD; then re-run the watchdog once.
- Evidence/acceptance: the three cases transition from
  `correction_not_effective` to closed/confirmed in a re-run watchdog report
  after the correction records are ancestors of HEAD, with the same file
  content (sha256-matched) as the on-disk durable trails; no fabricated
  confirmations — `confirmed: false` rows must be carried, not edited.
- Blocker if not: this is Executive/Clerk integration work, not Judicial;
  Judiciary cannot commit to the canonical checkout.

## 2. Finding e0a2c57b91d1af2365 (unresolved_finding; source_not_independently_verified)

Nature: agent-asserted host misuse on a private repository
(Marceline OpenClaw worktrees on #14 instead of exclusive phoebe-dev). All
available evidence comes from Antonina case body/comments and the resource
registry — **cached/attributed, not directly witnessed** by Judiciary in the
canonical box.

- Evidence: issue #14 description's phoebe-dev exclusivity clause;
  repeated Marceline `/workspace/skrynia-apps-14-*` worktree records; marceline
  agent terminal handoff; 12 marceline-dev worktrees in the registry.
  Not directly observed from Viche's box; source repo is external/private.
- Act 17 correction available now: NO. `verified_fixed` with new evidence
  would require independent verification of the external tree or updated
  authoritative comments. Judiciary has no lawful pathway to private repo
  access and must NOT perform external productive work.
- Lawful action available: report as done (this file + prior cycle report),
  keep the open case, and request Founder access or updated `recent_comments`
  carrying independent evidence.
- Unblock path: (a) direct read of the skrynia-apps history/timeline by an
  authorized reviewer, or (b) a Founder/Viche-comment confirming or
  disconfirming the Marceline execution records. Until then, uncertainty is
  retained by design (system literalism — `unresolved` ≠ `finding-filed`).

## Method and limitations

- Direct reads: JSONL corrections/ (this repo), viche-state/oversight/random
  case outcomes, watchdog JSON given in the summons — direct.
- Attribution limits: correction row contents were authored by previous audit
  cycles; this report verifies their durable existence, not re-proves the
  underlying findings.
- Judiciary effectiveness: outcomes for the 4 sampled cases filed once each
  this cycle; two continuity cases remain jointly open pending external
  verification that Judiciary cannot lawfully perform alone (see prior
  report `AUDIT-CONTINUITY-RECON-2026-10-27.md`).
