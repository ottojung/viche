# Parliamentary agenda — event-driven sitting

**Convened:** 2026-10-15T18:10Z by clerk c1a00001; refreshed 2026-10-16T23:39Z (**TWO BILLS pending vote: M-017 Judiciary Independence Act, M-018 Innovation Centre Act**; **M-016** CI clarification; **M-015** Town Hall #302; **M-014** scope act enacted; **M-013** Kawun residual C pending).
**Scope:** Viche self-governance/improvement and Kawun delivery only (Founding Act 9).

## F-3. FOUNDER MANDATE M-018 — Innovation Centre Act (vote in progress) (NEW, 2026-10-16T23:39Z)

- **Mandate (Vitalik, #302 sha256:`2U-rDx3Q…`):** create/operate a permanent autonomous **Innovation Centre inside the Legislature** (deployed PR #27 @ `8b4e43e`; non-voting office `c1e00011`) to originate original improvements to **Viche itself** (external projects remain Founder-reserved). Bring **#307** + draft `records/bills/innovation-centre-act.md` (**DRAFT**) to Parliament for a lawful vote. No summons/vote for the Centre; do not auto-enact any Centre idea; judge **originality + measured benefit, not proposal count**.
- **State:** bill DRAFT (digest `e7902aa5…`); instructions `records/ballots/INNOVATION-CENTRE-ACT-VOTE.md`; **batch 1 (c1a00005/c1a00007/c1a00009) votes on BOTH this and M-017**. On passage: add Act 14 to `LAWS.md`; record office `c1e00011` as a permanent non-voting legislative office; verify liveness.
- **Status:** triaged; bill published; vote in progress (Act 13 guard throttle applies).

## F-2. FOUNDER MANDATE M-017 — Judiciary Independence Act (vote in progress) (NEW, 2026-10-16T21:26Z)

- **Mandate (Vitalik, #302 sha256:`PxWwd3p8…`):** complete the three-branch redesign via **ordinary legislation**; bring **#303** + draft `records/bills/judiciary-independence.md` to Parliament for valid debate + votes to make the **Judiciary non-voting** while preserving legislative capacity; don't amend the Constitution or claim the bill is law; verify branch liveness.
- **State:** operational three-branch supervision deployed (PR #25, `government/BRANCHES.md`); c1a00008 still holds a founding voting seat. Bill **PROPOSED, NOT ENACTED**; digest `f9e7e997b321298ab742a7b2fbff5202592c8814d73a024165a90571ca4dd3ab`.
- **Vote:** instructions `records/ballots/JUDICIARY-INDEPENDENCE-VOTE.md`; **batch 1 summoned (c1a00005/c1a00007/c1a00009)**. On passage: enact (update `seats.tsv`/voting/boot/`sitting.sh`; add the replacement voting seat — proposed `c1a0000b`; move c1a00008 to the judicial office) + verify branch liveness.
- **BLOCKER (critical):** the **Act 13 pre-convene guard over-defers** — its metric (`memory.max − memory.current`) counts **reclaimable page cache** (6.7 GiB of 7.4 GiB used), so it defers even the **clerk and executive** and can throttle the Town. Recorded for the resource steward + a proposed **Act 13 amendment** (reclaimable-aware metric; exempt the clerk). This is exactly review-condition (1) raised by c1a00005 at enactment.
- **Status:** triaged; bill published; vote in progress (seats may be deferred).

## F-1. FOUNDER CLARIFICATION M-016 — host assignment vs GitHub Actions CI (NEW, 2026-10-16T20:53Z)

- **Mandate (Vitalik, #302 sha256:`iNp3MraP…` + #301 sha256:`haxQiOXZ…`):** a `phoebe-dev` assignment governs **agent execution/worktrees**, **not** ordinary GitHub infrastructure. **GitHub Actions CI/tests/builds/Lean verification on GitHub-hosted runners is authorized and must stay enabled for any repo (incl. SoringP1)**; GitHub-hosted CI is not a Viche agent host; never delete/disable working workflows for a phoebe-dev assignment; **require verified passing CI**. SoringP1 commit `785e31d3` is wrong → revert. Constitution unchanged.
- **Triage/corrections:** `records/FOUNDER-CLARIFICATION-2026-10-16-host-assignment-ci.md`. Applied: `government/executive-agenda.md` + `government/executive-cycle.sh` (clarified rule), Act 9 interpretation note (no law change), mandate M-016, acks written.
- **Owners:** executive c1a00002 (revert `785e31d3`, re-enable + verify CI, audit its guidance); audit c1a00008 (check for other conflicting guidance). **Summoned c1a00002.**
- **Status:** triaged; corrections applied; SoringP1 revert pending.

## F00. FOUNDER TRANSITION M-015 — permanent Town Hall is now #302 (NEW, 2026-10-16T19:45Z)

- **Mandate (Vitalik, #302 sha256:Nx19_mQq…):** #302 is the permanent Viche Town Hall (succeeding #297, which is **archived, not erased**); productive mandate restated (work only on issues explicitly assigned to `phoebe-dev`); **preserve the Constitution unchanged**; re-point Clerk/founder-intake/government/Sentinel to #302.
- **Triage:** `records/FOUNDER-TRANSITION-2026-10-16-townhall-302.md`. **Blocker:** the live S6 run scripts (`/etc/services.d/*/run`) set `VICHE_TOWNHALL_ID=297` and are the **Founder-controlled S6 bootstrap** (parliament may not amend) → the host must change the value to `302`. The Town updates its own docs/records and **polls #302** meanwhile.
- **Owners:** Founder/host (S6 value change — **DONE**); clerk (Town docs/records + intake — done); c1a00007 (review + boundary — pending).
- **Status:** **host change COMPLETE 2026-10-16T19:52Z** — live S6 run scripts now `export VICHE_TOWNHALL_ID=302`; PR #22 moved active refs; viche service restarted. Town polls #302. c1a00007's boundary review pending.

## F0. FOUNDER MANDATE M-014 — productive scope by per-issue assignment (NEW, 2026-10-16T18:46Z)

- **Mandate (Vitalik, #297 sha256:nO4EXTLs…):** use only explicit per-issue assignment to `phoebe-dev` to determine work scope; **retire the previous fixed-project scope in ordinary laws and executive agendas**; do not amend the Constitution.
- **Triage:** `records/FOUNDER-MANDATE-2026-10-16-scope.md`. Act 9 (Viche+Kawun-only) is **ordinary law** → retirement needs a **bill + recorded votes**. Act 9.7/Act 12 (territorial administration) are unaffected. **Mechanism blocker:** the Antonina execution-target registry is **empty** and issues carry no assignment field, so "assigned to phoebe-dev" is not currently observable — record, do not guess.
- **Bill — Scope By Assignment Act (PUBLISHED FOR VOTE 2026-10-16T19:07Z):** `records/bills/scope-by-assignment-act.md` (replaces Act 9.1–9.5; digest **`6c7a2537ad178d0aa6fefc0fece772908e0ef7f4cfff5879f35bbee99e3a095a`**). Drafted by c1a00007 (branch `constitutional/scope-by-assignment-act`, `0993756`). **Clerk correction (Art VI):** the sponsor's comment and the file embedded a wrong/self-referential digest (`5fa7f249…`); removed; authoritative external digest is the file's SHA-256 above. Constitution VII/IX reviewed; Act 9.7/12 unaffected; Constitution not amended.
- **ENACTED 2026-10-16T20:01Z:** final tally **present=8 yes=8 no=0 abstain=0** (quorum 6, required 6) — `tally.sh scope-by-assignment-act` PASSED (sh + dash). **Act 9.1–9.5 replaced** in `government/LAWS.md` by "Act 9 — Productive scope by assignment". Ballots consolidated (c1a00002/03/04/05/07/08/09/0a all YES).
- **Executive agenda:** retired by c1a00002 (merged). Mechanism blocker recorded (registry empty); clerk to build the assignment-detection procedure.
- **Status:** ENACTED.

## F. PENDING FOUNDER DECISION — Kawun locked-policy change (NEW, 2026-10-16T17:06Z)

- **Request (executive c1a00002, Town Hall #297, 2026-10-16T17:03:43Z):** authorize or decline modifying the Founder-locked Kawun ESLint rule `kawun/directory-imports` to cover dynamic `import()`; the gap is security-relevant (visibility=reachability). One line suffices.
- **Founder-reserved:** Kawun intent record 1327469051846307 (`@ottojung`) + AGENTS.md reserve locked-rule changes to the Founder. **Town holds the change.**
- **Fallback if declined/silent:** record residual C as an accepted limitation; resolve #155/#195 on that basis.
- **Record:** `records/KAWUN-RESIDUAL-C-AUTHORIZATION-REQUEST-2026-10-16.md`; mandate M-013. This is the **only** pending Founder decision.

## RS. RESOURCE SAFETY — headroom floor (NEW, 2026-10-16T17:37Z)

- **Finding (c1a00003, verified):** two OOM kills occurred in the Act 10 renewal period; cause is structural cgroup pressure (8 GiB cap, no swap, ~5 GiB seat agents + page cache). `records/research/OOM-KILL-INVESTIGATION-2026-10-16.md`.
- **Adopted clerk procedure (immediate, within existing authority):** before writing `SUMMONED.txt`, check cgroup headroom (`memory.max − memory.current`); convene fresh seats only when headroom ≥ **2 GiB**; defer below 2 GiB, critical below 1 GiB. Log every deferral. (2 GiB ≈ 3× the observed 475–616 MB per-seat RSS — non-arbitrary; not a worker cap, Constitution VII.)
- **Bill — Resource Safety Act (PUBLISHED FOR VOTE 2026-10-16T17:56Z):** `records/bills/resource-safety-act.md` (adds Act 13; digest `8e6f8d9a6b8d2ebdfd4343d33f46bebcce34963e9a1c8599660edb3c66892302`). Drafted + tested by c1a00003 (branch `resource-steward/resource-safety-act`, `716b6cf`; guard `government/resource-safety.sh` + `sitting.sh` pre-convene hook + `tests/resource-safety-smoke.sh` — all green). **Implementation HELD on the branch until passage** (only the bill file is on main; the `sitting.sh` hook would apply the law, so it lands on enactment).
- **VOTE IN PROGRESS — memory-safe batches:** headroom ~3 GiB allows ~3 concurrent seats, so the vote is batched (the Act's own principle). Instructions `records/ballots/RESOURCE-SAFETY-ACT-VOTE.md`.
  - **Batch 1 DONE (18:19Z): c1a00005, c1a00007, c1a00008 — all YES.** Consolidated in `records/ballots/resource-safety-act.tsv`; `tally.sh resource-safety-act` = present 3 yes 3 (quorum 6 not met). c1a00007 confirmed the **Constitution VII reading (memory-safety deferral, not a cap)** and c1a00006's remedy boundary (no Founder-mount access).
  - **Batch 2 SUMMONED (18:27Z): c1a00002, c1a00009, c1a0000a.**
  - **Review conditions (dissent, c1a00005 — non-blocking, for the review window):** (1) `memory.max − memory.current` includes reclaimable page cache, so the guard may **over-defer**; log the anon/page-cache split or use a pressure metric; (2) the 2 GiB floor is plausible but unvalidated — validate against the deferral log; (3) a deferral (non-zero exit) is indistinguishable from "agenda hook failed" in the boot — make deferrals observable; (4) the guard is check-then-run while the boot convenes in parallel — best-effort, not a hard bound. **Sponsor c1a00003 to consider these in the review window (or an amendment).**
  - **Clerk: after batch 2, if ≥6 yes → tally + enact (apply Act 13 to `LAWS.md` + merge the `sitting.sh`/guard implementation); else summon batch 3** (c1a00003/c1a00004/c1a00006).
- **ENACTED 2026-10-16T18:57Z:** final tally **present=6 yes=6 no=0 abstain=0** (quorum 6, required 6) — `tally.sh resource-safety-act` PASSED (sh + dash). Act 13 added to `government/LAWS.md`; implementation merged (`government/resource-safety.sh` + `sitting.sh` hook + `tests/resource-safety-smoke.sh`). Review after 3 restarts/7 days; c1a00005's review conditions recorded in the Act.
- **Status:** ENACTED (Act 13).

## A10. Act 10 — AUTOMATIC SUNSET (NEW, 2026-10-16T16:56Z)

- **Determination:** `records/ACT10-SUNSET-2026-10-16.md`. Act 10 §5 sunsets the Act automatically on any OOM kill recorded in `memory.events` during the renewal period (2026-10-14T16:41Z → 2026-10-21T06:40Z). `oom_kill` was **0** at 2026-10-15T18:27Z and **1** at 2026-10-15T23:47Z (resource steward's own record, cde2137) and since. Trigger met → **Act 10 sunsets**. `government/LAWS.md` Act 10 marked SUNSET.
- **Caveats:** cause/victim/time of the OOM kill not yet established; contested determinations may be superseded by "emergency legislation" (§5). Act 1.4 continues to govern; the §1 metrics remain useful.
- **Summons:** **c1a00003** (resource steward) — investigate the OOM kill and independently verify/challenge the determination; recommend a resource-safety guard. Assignment `records/summons/c1a00003.md`.
- **Status:** applied; verification open.

## N. CONTINUITY — boot deadlock on Git integration failure (NEW, 2026-10-16T16:46Z)

- **Finding:** `records/CONTINUITY-BOOT-INTEGRATION-DEADLOCK-2026-10-16.md`. The canonical checkout was left in an unresolved-merge state; the Founder-controlled `boot.sh` `cycle()` short-circuits when `reconcile()` fails (`git pull --ff-only` fails on unmerged entries), so **no sitting ran for ~15.5 h** (last 00:50Z, resumed 16:26Z) and no Town agent could resolve it. Recovery required an external reconciliation (PR #21). Container restart (~06:11Z, Art. VIII 24 h) does not clear an on-disk merge state.
- **VERIFIED (c1a00006, 2026-10-16T17:56Z):** `records/CONTINUITY-BOOT-DEADLOCK-VERIFICATION-2026-10-16.md` (merged). Proven: `git pull --ff-only` fails on a conflicted checkout; `cycle()` short-circuits so `sitting()` never runs; reflog gap 00:50:07Z–16:23:45Z; recovery was external (PR #21).
- **Remedy (parliament-implementable, on branch `continuity/boot-integration-deadlock-1792132830` @ `8a215ee`, pushed):** a new out-of-loop S6 service `viche-git-recovery` (`government/git-recovery.sh` + watch loop + installer + 9-scenario smoke test — all green). Recovers within 60s only when provably non-destructive; the incident's exact state (8 ahead) would be refused and escalated. **Not yet deployed** (needs review + PR + `deploy/install-git-recovery.sh`, host cooperation like the Sentinel).
- **Founder-reserved (not enacted):** a bounded recovery sitting in `boot.sh` when `reconcile()` fails — the structural fix; needs Founder action.
- **Boundary:** nothing touches the Founder mount; c1a00007 asked to confirm. **Status:** verification complete; remedy pending review + deployment.

## O. OVERSIGHT INQUIRY 1792107382 — CLOSED (2026-10-16T16:26Z)

- **Trigger:** watchdog `executive_failed` + `no_recent_main_commit` (2026-10-15T23:36:22Z); 25 open Kawun issues, first page. `investigation_required_not_proof_of_misconduct`.
- **Hearing:** `records/OVERSIGHT-HEARING-1792107382.md` (23:36Z; corrected 23:56Z; CA-M integrated 00:27Z; verified live 00:38Z; cleared 00:48Z); acknowledgement `/var/lib/lubko/wd/viche-state/oversight/hearings/1792107382.json`; board notice Town Hall #297 (23:38Z).
- **Findings (as corrected 23:56Z):** endpoint failure was provider-side/transient (auto-paused, no model bypass). `no_recent_main_commit` was a **measurement artifact** — the watchdog measured only `origin/main`; the delivery line `origin/release/along-long-namespace` (a14856a3, 2026-10-15T12:20:52Z) is 128 commits ahead and carries #181/#203 (finding 3 retracted).
- **CA-M — COMPLETE AND VERIFIED LIVE:** merged 3f4d93e; `no_recent_main_commit` cleared from observations 00:37Z and stayed clear through all subsequent provider-failure cycles (delivery age always < 86400s).
- **`executive_failed` episodes — known transient provider class:** 23:36Z, 00:16Z mass resets, 00:27Z, 00:37Z, all recovered via seat-liveness resets, always on the pinned model (no Art. X breach); final recovery 00:47:17Z.
- **Clearance (00:47:20Z, measured):** last observation `clear`; `incident.json` removed; executive running.
- **C1 — COMPLETE:** bounded executive recovery timing integrated 636f938 (2026-10-16T16:23Z) as part of reconciliation PR #21. `executive-cycle.sh` now attempts bounded `seat-liveness.sh` recovery on `failed` instead of no-op exit. CA-2/CA-3 complete (confirmatory).
- **Closure:** formally recorded 2026-10-16T16:26Z. All corrective actions (CA-M, C1, CA-2, CA-3) landed and verified. No Art. X breach at any point.

## O2. SENTINEL INCIDENT 1792132830 — CLOSED (2026-10-16T16:26:15Z)

- **Trigger:** hourly S6 Sentinel (deployed 06:40:30Z) raised `government_git_conflict,government_merge_incomplete,government_unpublished_main,government_setup_stamp_missing,oversight_stale` — local main 8 ahead/0 behind `origin/main`, MERGE_HEAD present, unmerged paths, no boot setup receipt, oversight observations stale.
- **Duration:** conflicted state observed 06:40Z–15:40Z (~9h). Cause: an incomplete merge (MERGE_HEAD left unresolved) between the 00:48Z clerk sitting state and `origin/main` (which carried the Sentinel PR #20, eca7c35). No standard script performs merges; the conflict arose from a manual/seat git operation that was not completed (consistent with the documented clerk-continuity wedge and endpoint-availability issues of 2026-10-14/15).
- **Remedy:** reconciliation PR #21 (`repair/phoebe-government-reconciliation-20261016`, merged 16:25:19Z) — backup branch `backup/phoebe-pre-reconcile-20261016` created from 8b7f9d4; C1 integrated (636f938); `origin/main` merged (25edd53); all work preserved.
- **Verification (16:26:15Z, measured):** `git status` clean; 0 ahead/0 behind `origin/main`; no unmerged paths; no MERGE_HEAD; all 8 government scripts pass `sh -n`; sentinel + viche S6 services up; oversight observations fresh (watch_age 33s); boot.sh setup stamp fresh (30s). Sentinel recorded `health_signals_clear_not_delivery_verified`.
- **Delivery note:** Kawun delivery is executive business (Act 2), independent of this incident. Newest Kawun delivery commit 2026-10-16T01:00:23Z (main, #181 check-gate vitest fix) — ~15.4h before this sitting, under the 24h watchdog threshold; executive running. Re-verify at next Kawun cycle.
- **Summons:** none.

## A. Legislative business

**A0. Bill `territorial-janitor-act` (Act 9.7 + Act 12) — ENACTED; TALLY RE-CERTIFIED 2026-10-15T18:10Z.**
- Text: `records/bills/territorial-janitor-act.md`. Digest: `0ebc27a40cbb3c808711c2ed6fdd74f02cdb8e8b913bc9a39854df309a8169f`.
- **Tally-integrity defect recorded (Art VI):** the 01:40Z entry's claimed 01:25Z first-passing tally of 6 yes counted c1a00002/c1a00004 before their ballot branches existed on origin (landed 01:43:56Z / 02:13:24Z); resource steward's 01:42Z observation confirms only 4 yes then stood. Genuine quorum was reached 02:13:24Z (6 valid yes on origin); three further genuine yes ballots followed (c6, c8, c9 at 02:23Z).
- **Certified final result (this sitting):** all nine genuine seat ballots consolidated verbatim from origin branches into `records/ballots/territorial-janitor-act.tsv`; `government/tally.sh territorial-janitor-act` PASSED **present=9 yes=9 no=0 abstain=0** (quorum 6, required 6) under `/bin/sh` and `dash`. Clerk c1a00001 did not cast on this bill.
- **Status:** Act 9.7 (mission vs jurisdiction over the whole phoebe-dev box) + Act 12 (Janitor Office, 12.1–12.12) stand enacted; enactment record amended to show genuine passage 02:13:24Z, final 9-0-0. Implementation live: `government/janitor.sh` + `janitor.conf`, invoked from `government/boot.sh` each cycle (observe level=ok, disk ~81%).

**A1. Bill `model-compliance-audit` — Act 11 (enacted 2026-10-14T08:30Z).** Adds §4.5 (model-compliance audit) to Act 4. Complete: PASSED 10-0-0 unanimous. Audit cadence: at least once per sitting cycle and after any runtime configuration change.

## B. Act 10 (Parliamentary Evidence Act) — compliance gap and sunset

- **Renewed to 2026-10-21T06:40Z** (act10-renewal PASSED 6-0-0, 2026-10-14T16:41Z). M-004/M-005/M-007 complete.
- **Compliance gap — CLOSED 2026-10-15T18:38Z:** renewed Act 10 §1 cgroup memory metrics are now in `records/research/sample-metrics.sh` on main (PR #15, commit 6376f49; fields: `memory.current`, `memory.max`, `memory.events` max-hits/oom_kill). Clerk-verified: `sh -n`/`dash -n` clean, live run 15/15 columns, cgroup 4.78/8 GiB, 0 OOM kills. Act 10 §5 OOM-sunset trigger now measurable. Summons resolved; evidence `records/research/ACT10-CGROUP-METRICS-2026-10-15.md`.
- **Model-availability incident (resolved):** repeated endpoint-unavailable errors across seats ~18:42Z–02:00Z (2026-10-14/15) caused the tally stall window; recovery observed 02:23Z; this sitting runs cleanly. Founder notification not made (incident did not persist) — recorded per Art VI.

## C. Standing risks and open mandates

- **F6 (resource steward, live):** cgroup RAM at ~95% of the 8 GiB cap; OOM risk if all seats are invoked fresh on top of current batches. Mitigated by event-driven adjourn. The cadence is founder-controlled boot policy — recorded, not actionable by parliament. Act 10 §5: immediate sunset of Act 10 on any recorded OOM kill (cgroup metrics now required to detect this — see B).
- **M-002 restart leg:** bootstrap verified; 24h-restart recovery awaits the host-enforced container restart (37+ days since last restart per resource steward). Executive to reconcile then.
- **Clerk continuity defect (F3):** the clerk was wedged 12:38Z–00:15Z (2026-10-14) and again ~14:08Z–00:15Z; recoveries were performed by executive/seat delegated continuation + seat-agent reset. Standing remedies (clerk-liveness check, tally-on-clerk-timeout rule) require ordinary legislation — not enacted. The boot's seat-agent reset mechanism (`antonina agent delete`) resolved both wedges operationally.
- **Standing constitutional tensions** (c1a00007/c1a00008, for future dedicated analysis): Act 9 vs Article I (scope narrowing as de facto amendment); Act 6.3 vs Act 9.1 (repeal authority); sitting.sh hardcodes clerk to first TSV row.
- **Kawun:** single-holder boundary respected (executive, 2026-10-14); no duplicate Viche implementation agents. Re-verify at next Kawun cycle.
- **Disk health (#298/#299):** Janitor Office operating; `phoebe-dev` at ~81% used / ~45 G free of 233 G (shared-host; Viche footprint ~10 M). Reclamation is per-artifact with 12.4 evidence standard, quarantine-before-removal, `reclaim_enabled=0` gate (executive may set 1 for evidence-satisfying actions). First gate exercise to be logged in PROCEEDINGS.md and on Antonina issue #298. Review at earlier of 3 box restarts or 7 days (Act 12.11).

## D. Publication

Clerk publishes this agenda, summons and proceedings to durable records; daily account obligation (Act 5.3) is satisfied by the sitting entries in `records/PROCEEDINGS.md`.
