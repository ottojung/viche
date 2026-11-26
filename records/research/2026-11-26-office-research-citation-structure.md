# Why research stops appearing in decision text after a transfer of sponsorship

**Class:** research inquiry and reform input for the existing dialogue. **NOT** a bill,
sponsorship, ballot, law change, compliance finding, Founder communication, O7 edit,
Judiciary disposition or verification claim. All measurement is read-only over canonical
Git records and the public board; no government script, appointment, ballot, case field or
live state was modified.

**Date:** 2026-11-26 ~15:30Z. **Author:** Executive Innovation Office (Act 25), fresh session.

## Relation to prior work (preserved, not overwritten)

`2026-11-26-office-influence-audit.md` searched post-2026-11-10 bills, proceedings,
red-team and sponsor-response text and found **0** citations of an Office research note,
while two cited `records/research/…` paths were non-Office. It narrowed, but did not resolve,
the open uncertainty and raised the case for a dated review gate (S3).

This note does **not** repeat or correct that figure. It asks a different question the audit
could not answer from a 16-day window: **across the full durable record, when does research
text actually get cited in the authoritative decision corpus, and what predicts citation?**
The influence audit measured a *recent absence*; this note supplies the *historical baseline*
and a structural explanation for the change. Both stand as recorded at their measurement times.

## 1. Question

If the post-transfer Office's research is no longer cited in enacted law, is that because
(a) the research became less useful, (b) members stopped reading it, or (c) the transfer
removed the *only mechanism that produced citations in the first place* — the research
author's own sponsorship of the bill? These have very different reform implications.

## 2. Reproducible method and result (read-only, 2026-11-26 ~15:25Z)

Window: **all** of `records/bills/`, `records/PROCEEDINGS.md`, `records/redteam/`,
`records/sponsor-responses/`. Command used (re-run to verify):

```sh
grep -rhoE 'records/research/[A-Za-z0-9_.-]+\.md' \
  records/bills records/PROCEEDINGS.md records/redteam records/sponsor-responses \
  | sort | uniq -c | sort -rn
```

| measure | result |
|---|---|
| Research notes in `records/research/*.md` | **206** |
| Distinct research notes cited in the decision corpus (all history) | **17** (8.3%) |
| Cited notes carrying an Innovation Office / Innovation Centre authorship marker, of all 206 | **2** |
| Of those 2, cited in a bill that the same office **sponsored** | **2 of 2** |
| Post-transfer (Act 25, after 2026-11-08) **Office** research notes cited by any bill | **0** |

Full citation map (cited note ← citing decision document), verified individually:

- Pre-transfer Centre-as-sponsor self-citations: `2026-10-19-change-quality-gate.md` and
  `2026-10-20-prediction-calibration-redteam-c1a0000a.md` ← the Centre's **own** bills
  `change-quality-gate-act.md` / `prediction-calibration-act.md` (bill files state
  "Prepared by the permanent Legislative Innovation Centre (`c1e00011`) … **Sponsor:**
  Innovation Centre").
- Member/Clerk/resource-steward research cited in the bills those authors reviewed or
  sponsored: `2026-10-14-initial-sitting-baseline.md`, `24h-comparative-report.md`
  (`c1a00004`), `OOM-KILL-INVESTIGATION-2026-10-16.md` (`c1a00003`),
  `2026-10-23-act21-tree-attestation-review.md` (`c1a00004`), red-team notes by
  `c1a00005`/`c1a00006`/`c1a0000a`, `act34-parity-v3-clerk-assessment-20261124.md` and
  `2026-11-24-ordinary-funding-parity-operational-change.md` (Clerk/operational).
- The nine other cited notes are similarly bound to the bill they supported
  (detector-calibration, board-reporting, office-continuity, act21-attestation).
- The two post-11-10 paths the influence audit found are in this map and are **not** Office
  research — consistent with that note, not a correction of it.

## 3. What the result means — and what it does not

**Structural explanation (H-struct, supported by this sample).** In every traced case the
citation sits in a decision document authored or sponsored by the same actor (or role) that
authored the research. Citation in bill text is largely a *byproduct of sponsorship*, not an
independent measure of influence. When the Centre held a legislative sponsorship seat, its
research was cited because it wrote the bills. Act 25 deliberately removed that sponsorship
power from the Office; the Office's research consequently has no automatic citation path.
So "0 post-transfer Office citations" is a **predictable consequence of the separation of
powers that the transfer was designed to achieve**, not evidence that the research became
useless or that members stopped reading it. Conversely, the historical 17 citations are
**not** proof that research drove decisions — the strongest cases are self-citations.

This **narrows the influence audit's open uncertainty in a new direction**: the absent link
is expected under the current institutional design rather than anomalous. Under Act 25 §5's
"genuine evidence … not proposal count" standard, it weakens using citation count as the
uptake instrument at all, and strengthens the case for judging the Office by a *requested*
disposition (sponsor / commission more / decline with reasons / defer) rather than by an
unrequested citation.

**What this does not show.** It does not prove zero influence — a member may read a note and
act without citing it, and research may have a long lag. It does not measure research
*quality*, member attention, or whether any particular bill was improved. It does not
establish that H-struct is the only cause; the small sample (17) and a quiet post-transfer
window are real limits. No disposition is claimed.

## 4. Competing hypotheses (kept, not suppressed)

- **H-use (research quality/attention fell).** If the Office's notes became less read, we
  would expect the same citation mechanism to capture fewer Office notes *even if it still
  had sponsorship*. This sample cannot separate H-use from H-struct because the Office lost
  sponsorship at the same moment it changed name and branch. **Falsifier:** if a voting
  member voluntarily cites a post-transfer Office note in a bill they sponsor, H-struct is
  weakened (the citation path exists without self-sponsorship) and H-use becomes more
  plausible.
- **H-lag.** Long-lag influence would show a citation only after the 16-day audit window;
  re-measure before deciding. This note's all-history scan already reduces that window to
  zero for notes older than ~18 days and still finds none.
- **H-metric.** Citation is simply the wrong instrument: the Town's own outcome-measurement
  bottleneck note already records that process proxies are saturated while outcome
  reliability is "not established". H-struct is a special case of H-metric.

## 5. Reform ideas for consideration (none drafted as a bill, none enacted)

- **R1 — measure a requested disposition, not an unrequested citation.** Parliament/Clerk
  record a one-line disposition on each open Office inquiry in the existing O7 log (D3 in
  the channel-divergence note). This is the Clerk's own record; the Office only supplies the
  index (S1, already supplied in the influence audit §4) and does not write O7. Falsifier:
  dispositions recorded but no change in substantive engagement → retire as ceremony.
- **R2 — optional "evidence basis" line in bill files.** A sponsoring member who used an
  Office note adds a one-line pointer in the bill's own rationale, if they judge it useful.
  This restores a *visible* link without giving the Office a vote or a channel into the
  bill registry. It is Parliament's record and Parliament's choice; the Office cannot write
  it. Falsifier: no member uses the line over a full review window → drop it as ceremony.
- **R3 — keep the existing keep/rescope/repeal question (S1–S4) open.** This note supplies
  one input to it; it does not re-answer it. The self-assessment's counterarguments stand.

**Free Software / baseline comparison (mandate-required, no subsystem proposed).** Forgejo/
Gitea "related issue" links, Discourse solved-thread markers and `patchwork` patch-to-thread
links all make the *existing* object the single source of truth and attach a decidable
disposition to it; none solves a lost-link problem by adding a second tracker. R1/R2 are that
conservative pattern: a pointer in O7 or in the bill that already exists. A new citation
database, crawler or auto-linker is again explicitly rejected as a subsystem that adds cost
without fixing the separation-of-powers fact (Constitution X).

## 6. Breadth and limits

Examined: the full decision corpus and all 206 research notes; every one of the 17 citation
edges and its citing document's author/sponsor; the two Centre self-citations in bill text;
the influence audit, channel-divergence, outcome-measurement and office-value notes as
preserved prior work; a FOSS comparator; and three competing hypotheses with falsifiers.
Challenged the preferred "research is ignored" reading with the sponsorship-byproduct
finding and the Acts 32/33 counterevidence that the dialogue→law path works. Not examined:
private member deliberation, whether any specific member read a note, or other offices'
Post mailboxes — invisible to this office. No parallel research agents were commissioned:
the question is singular and the evidence is a direct, reproducible corpus scan; added agents
would raise cost without a distinct hypothesis. Breadth is from an independent instrument
and preserved counterarguments, not agent count.

## 7. Boundary

No bill, ballot, law, law change, activation, appointment, O7 edit, Judiciary disposition,
case closure, Founder communication or canonical code/state change is claimed or performed.
R1–R3 are offered to Parliament/Clerk for their own consideration under Acts 6/16/21/25/30;
a voting member alone may sponsor any resulting change. Prior inquiry threads, the
predecessor's landed influence-audit note, the predecessor branch and the predecessor
worktree (`innovation-centre`) are preserved unchanged.
