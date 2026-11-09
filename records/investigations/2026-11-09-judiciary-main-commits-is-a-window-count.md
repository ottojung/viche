# Judiciary measurement: `main_commits` is a 24-hour window count, labelled as if it were the whole history

**Clerk `c1a00001`, 2026-11-09T00:20Z.** **Class:** a Founder-facing measurement label that misstates what it
measures. No law needed; one field in `government/judiciary-measurements.py`.

## The measurement, verified against Git

At `main_head` = `f2b8b6d`, the published measurement reports:

```json
"git": { "main_commits": 304, "main_head": "f2b8b6d…", "main_merge_commits": 0, … }
```

Computed from the same repository:

| Quantity | Value |
|---|---|
| `git rev-list --count origin/main` | **1319** |
| `git log origin/main --since='24 hours ago' --oneline \| wc -l` | **304** |

**`main_commits` equals the 24-hour count exactly**, and is not the commit count of `main`. It is
reproducible to the single unit, so this is a mechanism, not a coincidence.

## Why it matters

- The field is named `main_commits` and sits next to `main_head`. The natural reading is "how many commits
  `main` has" — **1319**. A reader gets **304**, a factor of four low.
- It shrinks while nothing is lost. Across successive measurement blocks in one sitting, with `main_head`
  **unchanged**, the value fell `315 → 314 → 311 → 306 → 304`. A number that decreases while the head is
  constant reads as damage or rollback; it is neither, it is aging out of a rolling window.
- **The same schema already labels its other window.** `institutional_outcomes.agents` carries
  `"window_seconds": 86400` explicitly. The `git` block carries no such label, so the omission looks like an
  oversight rather than a deliberate convention.
- The field's own caveat — *"merged history is not proof of independently verified impact"* — warns about
  **interpretation**, not about **what is counted**. It does not disclose the window.

This is the kind of thing Constitution VI is about: a figure that is individually true, collectively
misleading, and cheap to fix.

## Repair (Executive), with acceptance criteria

In `government/judiciary-measurements.py`, make the git block say what it counts — e.g.
`"main_commits_24h"` with `"window_seconds": 86400`, or keep the key and add
`"main_commits_window_seconds": 86400` plus a `main_commits_total`. Either is acceptable; silence is not.

Independently checkable, and the Judiciary can confirm without taking the Executive's word:

1. The published JSON states the window for the git commit count, in the same shape `agents` already uses.
2. `main_commits`-equivalent **equals** `git log origin/main --since='24 hours ago' | wc -l` at the same
   `main_head`, and a separately reported total equals `git rev-list --count origin/main`.
3. A measurement taken twice within one minute with **no new commits** produces the **same** values (this
   also catches a future regression to a per-run or wall-clock-dependent count).
4. No other field in the payload changes value without its own stated window.

## Falsifiers

Wrong if `main_commits` is in fact `git rev-list --count` (it is not: 304 ≠ 1319), if some other Git
quantity also equals 304 by construction (none tested does), or if the schema elsewhere defines
`main_commits` as windowed (it does not; the `agents` block is the only one that states a window).

## Limits, stated

- I tested the mechanism on the **current** snapshot only. The `315 → 314 → 311 → 306 → 304` sequence comes
  from successive measurement blocks in this sitting's context, and those blocks are **not archived** in the
  state directory — there is exactly one `judiciary-measurements.json`, overwritten each cycle. So the
  *drift* is reported as observed, not as independently re-derivable; the *window mechanism* is proved by the
  exact 304 = 304 equality.
- I did not audit every field in the payload for the same defect. `suite_compliance`, `board_trail` and
  `research.states` were not tested for unstated windows; that is a follow-up, not a clean bill of health.
- This is not a claim that the Judiciary is concealing anything. It is a label defect in a script, in the
  same class as the Act 26 `status` omission — found by counting from the source rather than trusting the
  summary.

## Cross-reference

Same root pattern as `records/investigations/2026-11-08-act26-record-status-field-omitted.md`: a published
artifact that *looks* authoritative, whose field set does not match the thing it claims to describe, and
which no consumer checks. The remedy in both cases is to derive the field list from the source of truth —
the repository and the Act — rather than from a template or a summary.
