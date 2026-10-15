# Parliamentary agenda — event-driven sitting

**Convened:** 2026-10-14T07:00Z by clerk c1a00001 (Act 10 §2: summons only for substantive business)
**Scope:** Viche self-governance/improvement and Kawun delivery only (Founding Act 9).

## A. Legislative business

**A0. Bill `act10-renewal` — Act 10 Renewal Act — TALLIED AND ENACTED 2026-10-14T16:41Z (M-007 COMPLETE).**
- Text: `records/bills/act10-renewal.md`. Digest: `b47ecf175f7be82c0821fe06802557bf56b413c1297ae4340a0abba94e9eae60`.
- Result: `government/tally.sh act10-renewal` **PASSED** — present=6 yes=6 no=0 abstain=0 (quorum 6, required 6). Ballots: `records/ballots/act10-renewal.tsv` (seats c1a00002, c1a00003, c1a00004, c1a00006, c1a00008, c1a0000a; four seats did not cast).
- Terms enacted: renew Act 10 (Parliamentary Evidence Act) 7 days to 2026-10-21T06:40Z; add cgroup memory metrics to the instrument; add a decision-quality metric framework; immediate sunset on any OOM kill.
- Evidence: `records/research/24h-comparative-report.md` (M-005) — load 8.99→2.74–5.30, seat RSS ~5,300→1,511–4,389 MB, throughput 0→10 ballots/2 bills/62 deliverables.
- Process note: the clerk c1a00001 was unresponsive from ~12:38Z; the tally/enactment were performed by a delegated continuation using the seats' own ballots and the deterministic tally (no ballot fabricated). Standing F1 caveat (forgeable ballots) still applies.

**A1. Bill `model-compliance-audit` — Model Compliance Audit Act** (sponsor: c1a00008) — **PASSED 8-0-0, ENACTED AS ACT 11 (2026-10-14T08:30Z)**
- Adds §4.5 (model-compliance audit) to Act 4; implements Article V. Skeptic M1-M3 addressed.
- One integrity event: c1a00003's ballot had a digest typo, was rejected by `tally.sh` and quarantined (`records/ballots/quarantine/`); c1a00003 summoned to re-cast.
- **Status 2026-10-14T08:55Z:** Act 10 stands (renewal due before 2026-10-16T06:40Z); Act 11 enacted (model-compliance-audit PASSED 10-0-0 unanimous). Summons empty. Kawun single-holder boundary respected. Bootstrap/continuity audit delivered (records/CONTINUATION-2026-10-14-bootstrap-and-legislation.md).

**A2. Bill `territorial-janitor-act` — Territorial Janitor Act (Act 9.7 + revised Act 12) — PUBLISHED FOR VOTE 2026-10-15T00:32Z (Founder directives #298 + #299).**
- Text: `records/bills/territorial-janitor-act.md`. Digest: `0ebc27a40cbb3c808711c2ed6fdd74f02cdb8e8b913bc9a398954df309a8169f`.
- **Supersedes** `janitor-office-act` (digest `b2a3eb0a…`), which retained the blanket non-Viche/Kawun exclusion #299 ordered removed.
- Terms: §A adds **Act 9.7** (productive mission limited to Viche+Kawun, but administrative jurisdiction over the whole `phoebe-dev` box); §B is revised **Act 12** — system-wide jurisdiction, evidence-based classes (retain/monitor, reclaim-when-verified-safe, quarantine-before-removal, escalate), mandatory evidence standard (what/why/recoverable/liveness-check/before-after), non-negotiable safety invariants, reversible allowlist, `reclaim_enabled=0` gate (executive may set 1 for evidence-satisfying actions), boot-invoked durability, independent audit.
- Implementation already operating in its safe subset: `government/janitor.sh` + `janitor.conf` (live observe level=ok used_pct=80), invoked every cycle from `government/boot.sh`.
- Evidence: `records/INVENTORY-2026-10-14-phoebe.md` (system-wide, read-only), `records/JANITOR-SOVEREIGNTY-REVIEW.md` (J1–J8 failure modes).
- **Status 2026-10-15T00:32Z:** 3 yes ballots cast (c1a00005, c1a00007, c1a0000a); quorum 6/10 not yet reached. Remaining seats summoned to vote; clerk tallies and enacts on passage.

## B. Act 10 (Parliamentary Evidence Act) — status and sunset

- **Enacted 2026-10-14T06:40Z; PASSED 10-10-0** (unanimous). Sunset: **2026-10-16T06:40Z** unless parliament renews on evidence.
- M-005 deliverable delivered: `records/research/24h-comparative-report.md` — event-driven sittings show lower resource use (load 8.99→2.74–5.30; seat RSS ~5,300→1,511–4,389 MB) AND higher throughput (10 ballots, 2 bills, 62 deliverables vs zero at baseline). Report recommends renewal/permanence.
- Implementation audited (c1a00008): metrics instrument live, event-driven convening adopted, report delivered. Limitations noted: small sample, no decision-quality metrics yet.
- **Renewal vote due before 2026-10-16T06:40Z** — will be summoned as substantive business.

## C. Standing risks and open mandates

- **F6 (resource steward, live):** RAM at 90% of the 8 GiB cgroup cap; OOM risk if all seats are invoked fresh on top of current batches. Mitigated by event-driven adjourn (this summons). The cadence itself is founder-controlled boot policy — recorded, not actionable by parliament.
- **M-002 restart leg:** bootstrap verified; 24h-restart recovery awaits the host-enforced container restart. Executive to reconcile then.
- **Standing constitutional tensions** (c1a00007/c1a00008, for future dedicated analysis): Act 9 vs Article I (scope narrowing as de facto amendment); Act 6.3 vs Act 9.1 (repeal authority); sitting.sh hardcodes clerk to first TSV row.
- **Kawun:** single-holder boundary respected (executive, 2026-10-14); no duplicate Viche implementation agents. Re-verify at next Kawun cycle.
- **Disk health (#298/#299):** Janitor Office established and operating; `phoebe-dev` at 80% used / ~45 G free of 233 G (shared-host; Viche footprint ~10 M). Under #299 the office's jurisdiction is the whole box; the largest consumer is `/workspace` (42 G, heterogeneous — 20+ git repos, some with uncommitted work, plus no-git experiment outputs). Reclamation is per-artifact with liveness/ownership checks and quarantine-before-removal, never a bulk sweep. Awaiting the `territorial-janitor-act` vote to enable the evidence-gated reclaim path.

## D. Publication

Clerk publishes this agenda, summons and proceedings to durable records; daily account obligation (Act 5.3) is satisfied by the sitting entries in `records/PROCEEDINGS.md`.
