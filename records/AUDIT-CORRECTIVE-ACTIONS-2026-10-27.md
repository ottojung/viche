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

## Addendum (2026-10-27T18:44Z) — recheck against watchdog 1793125822

Watchdog changes since the section above; re-verified directly this turn:

1. **Continuity cases CLEARED by receipts issued through Article seat-scope.**
   `continuity/verified-executive.json` and
   `verified-innovation-centre.json` now exist (verified_at
   2026-10-27T18:19:55Z, verified_by "judiciary"),
   matching the live reconciliations exactly (executive:
   `ByVzR7PubSmMEiJc1WLngU-open -> 80yReH6wtuOIRKIG1nWQTr-guardsmen`,
   receipt at 18:06:08Z). Independently spot-checked as TRUE:
   - `exec/recovered-act19-snapshot-20261027` head `fa70f63f4bc72d51be95f3d3475043ffea0b5d23`
     exists with parent exactly `9cb583765f7804c8869b34cc41dc30443b352ae6`
     (ergot's captured worktree-head); "superseded" is accurate — main
     `beb6bf4` ("Integrate reviewed delivery delivery/act19-head-streak-epoch")
     is ahead and live.
   - Live executive worktree: detached head `beb6bf4...`, `status` clean,
     matching the 18:06:08Z receipt's worktree_head; terminal evidence
     `ByVzR7...-open` captured clean on same SHA.
   - Successor meta state `succeeded` (exit 0) for both `guardsmen` and
     `external` after verification; live board comments by ergot/harbor/open
     on #301, #310, #313-alabama were dated and attributable.
   - Publication: commit `66cc775` on `audit/incident-1792464244-c1e00008`
     (2026-10-27T18:17:18Z) published the prior continuity/M-022 report files
     and the appended verification section. Full canonical suite
     `sh tests/run-all.sh` exit 0 reproduced this turn (947 lines of output,
     all-smoke pass).
   Uncertainty retained: Judiciary did not witness the timestamp-correction
   chain (`18:45:00Z -> 18:19:55Z`) beyond the self-documented epoch
   arithmetic; the receipts' substantive claims are all independently
   reproducible and check out.

2. **7750b56b775ed8959a / edb67f8a646f569b5a became `correction_anchor_invalid`.**
   Root cause verified: their committed trails (commit `2c6d695`, faithfully
   sha256-matched copies) carry `.jsonl` rows whose FIRST correction filing
   row has NO `cycle_id` field at all (filed 2026-10-23T09:33-34Z =
   `at 1792738435/1792738439`, i.e. before cycle-identity binding was
   introduced by commit `4c3f39a` "Bind audit corrections to frozen-cycle
   identity and serialize filing"). The effectiveness check
   (`committed_confirmed_correction`, Act 17 §2.2) hard-fails on a committed
   correction row lacking a valid cycle token, so those filings can never
   become effective under current law. This is a historical-cycle archive
   defect faithfully preserved by the 2c6d695 projection; VALID remediation
   would require either (a) legislative amendment to Act 17 §2.2's anchor
   condition or (b) re-issuing a genuinely new correction in a current cycle
   — (b) would require fresh case-level new evidence, of which I found none.
   PROPOSED silently: none — merit reserved to Parliament.

3. **fae4b5c49a16cbcc3e — reclassified at 1793123743 as `unresolved_finding`.**
   The committed confirmed correction (verdict `finding`, cycle
   `bc0491f2d1b73344092c563a8a931c7f`) is Git-anchored, but the finding's
   evidence-ref chain carries the controller's
   `source_not_independently_verified` caveat. New direct verification:
   `113ee56` ("Judiciary: reassess October 23 scope findings") and `473f73c`
   ("Integrate reviewed delivery delivery/act17-frozen-cycles-20261023") BOTH
   contain `git merge-base --is-ancestor ... HEAD` = true, and
   `records/PR32-SECOND-OFFICE-FACTUAL-REVIEW-2026-10-23.md` exists in HEAD.
   The finding's SUBSTANCE (Act 17 §2.6.1 six-hour boundary legality of the
   October 23 double-correction) remains a question reserved to the
   Legislature; the underlying unresolved legal determination is unchanged
   this turn. Legislative follow-up remains worshipful waiting — Judiciary
   holds no opinion and takes no correction action.

4. **e0a2c57b91d1af2365** — unchanged from the section above: no new
   independent evidence has appeared; the finding remains open with
   `source_not_independently_verified`.

## Net effect for Parliament (measurement limitations, not reform)

- `finding_count` moving 1 → 2 is entirely attributable to re-classification
  of one already-adjudicated matter (fae4b5c) whose evidence becomes
  inspectable in HEAD — NOT to a new failure being born.
- `correction_anchor_invalid` on two cases exposes a systemic archive-trail
  defect: corrections filed before frozen-cycle identity binding are
  permanently anchor-invalid once committed, even when internally
  self-consistent — a correction gets this invalid-anchor problem exactly
  when its filing row lacks a frozen-cycle token).
- Judiciary's own operation effectiveness: sampled outcomes durably filed and
  on-record; the continuity case closure now rests on receipts Judiciary
  itself co-verified as genuine external-effect reconciliations; no false
  delivery detected in any checked artifact this turn.
