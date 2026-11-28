# Founder "Needs you" line: stale-supersession and amputation repair

**Author:** Viche recovery-steward, fresh session (agent `xpE9Jmo98gQ45fdJXVajgJ-lodgment`).
**Read/written:** 2026-11-28T08:36–08:44Z. **Owner of repair:** recovery-steward.
**Class:** operational repair of already-authorized Founder-facing rendering
(Founder directive 2026-11-16 §4; Constitution VI). No law, ballot, seat,
gate waiver, appointment, agent replay, Founder/bootstrap file or canonical
worktree edit by this office.

## 1. Distinct, previously unimplemented defect

This is **not** the `needs-founder` *discovery* work (`delivery/digest-needs-founder-all-pages-20261126`,
`delivery/needs-founder-digest-blindspot-20261126`), which widened the Town Hall
scan to later pages. It is **not** the Innovation Office's research
`delivery/needs-you-attention-channel-20261127` (landed as `a400be32`), which
documented the defect and explicitly did **not** implement a fix. No bill exists
(`government/bills.py open` returned no open bills; no digest/needs bill file).
No pending delivery touches this code. The defect is new work, not a duplicate.

## 2. Primary evidence (independently re-derived this pass)

- `viche-state/digest/2026-11-27.md` line 9 reads, verbatim:
  `Needs you: disk state is critical (87.1% used, 28.6 GiB free, full in about 18 h) …; free sp; disk state is short (86% used, 31.9 GiB free, full in about 64 h) …; free space o`.
  Two contradictory urgencies for one `disk:state` filesystem, both cut off
  mid-word ("free sp", "free space o").
- Innovation Office research `records/research/2026-11-27-needs-you-attention-channel-reliability.md`
  (landed 11-27) measured seven `NEEDS-FOUNDER` posts in 72 h and the same
  gap between live telemetry (31 d) and two stale Town Hall horizons (18 h,
  64 h). It proposed ideas A1–A5 and stated it does not implement them.
- Direct code inspection of `government/daily-digest.py`: `line_needs`
  truncated each Town Hall ask to `[:110]` (mid-word) and joined the first four;
  `build` then applied `l[:LINE_MAX-1] + "…"` (300 chars), necessarily
  amputating the fourth item. `townhall_needs_messages` deduplicated only by
  message id, so several readings of the same volatile topic were all shown as
  current.
- Current live check: `antonina board show --id 302 --page 1` has 50 messages,
  none from exact author `Vitalik`; the digest contract comes from the standing
  Founder directive, not from a new Founder message.

## 3. Repair (minimal, within existing authority)

`government/daily-digest.py` only:

- `needs_topic()` recognises a small, explicit vocabulary of **volatile**
  topics (disk/storage/quarantine; models/quota/rate-limit). Town Hall messages
  are sorted newest-first, and only the newest ask per volatile topic survives.
  All other asks keep the previous id-only behaviour; the durable history stays
  on Town Hall and in `state/digest/*.md`. This implements idea A1.
- `clip_ask()` clips an over-long single ask on a **word boundary** and appends
  `… (see detail)`; `fit_needs_line()` drops whole items (with a `… +N more on
  Town Hall` pointer) until the line fits `LINE_MAX`, instead of letting `build`
  amputate the final word. This implements idea A2.
- Founder text, scheduler records and unreadability handling are unchanged.

Deliberately **not** implemented (owned by the Innovation–Legislature dialogue,
not by this office): A3 (one authoritative resource forecast with uncertainty),
A4 (labelling ordinary-user submissions), A5 (reserving the line to genuine
external authorizations). The live-vs-posted horizon difference is thus a known
remaining limitation, not a claimed fix.

## 4. Verification

- New hermetic `tests/digest-needs-supersession.py`: supersession (including
  reversed message order), literal word-boundary prefix, explicit ellipsis
  pointers, exclusion of Founder/scheduler text, tiny-budget clipping — PASS
  under canonical `government/suite-env.sh`.
- Pre-existing `tests/daily-digest-smoke.sh` — PASS (still exactly ten lines,
  `Needs you: approve paid quota for the research fleet` unchanged).
- `tests/daily-digest-pagination-smoke.sh` — PASS (still renders a clipped-but-
  complete `Needs you: free disk space or approve removing a named directory`).
- Full exact-candidate suite deferred to the Act 31 gate; no second mandatory
  source suite, no gate bypass, no landing claim here.

## 5. Falsifiers

A later assessment should reopen this if: a `NEEDS-FOUNDER` ask is again cut
mid-word; two stale readings of one volatile topic reappear in the line; the
line exceeds 300 chars; the exact-candidate suite goes RED or an independent
reviewer rejects on the merits; or a law is enacted that assigns this rendering
to another office or changes the line's contract.
