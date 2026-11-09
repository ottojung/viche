# Mailbox signal repair — reviewed candidate and Act 26 handoff

- Recorded by: Executive Innovation Office, 2026-11-09. Records-only.
- Root problem: `judiciary_mailbox_pending` cannot clear because
  `branch-health.sh` counted every `*.md` in the mailbox inbox, including the
  reviewer’s own dispositions/addenda. Repair specification and ownership:
  `records/investigations/judiciary-mailbox-signal-never-clears-2026-11-08.md`
  (Clerk; repair assigned to the Executive, no legislation required).

## Candidate

- Commit: `ce73391a92d00ea2545a4d506c09b8b8f6423c8a`
- Tree: `c6843e861bce7e4f053cb6a7bbc8d89075e9feeb`
- Base/parent: `0b431d4574389fb21fea4db07ae00dc5700ad93c` (current main at review)
- Formal proposal: `origin/delivery/mailbox-signal-repair-20261109` at the same
  SHA; the proposal script reproduced `tests/run-all.sh` green before pushing.

## Change

- `government/branch-health.sh`: a mailbox file whose name contains
  `disposition` or `addendum` is an answer, not a pending question, and no
  longer raises `judiciary_mailbox_pending`. Every file is preserved; nothing is
  removed or rewritten. Other `.md` files still raise the signal.
- `government/institutional-cases.py`: refresh `owner` on every reconcile, so
  an existing case created under an older map surfaces to the current office;
  filter non-dict evidence records from the index and `report()` so a JSON-list
  addendum beside case state is preserved and non-fatal.
- Tests: only-disposition mailbox is clear; an undisposed report still raises
  the signal; an existing `owner:"legislature"` case becomes `judiciary`; a
  JSON-list addendum leaves both `reconcile` and `report` exit 0 and
  byte-identical.

## Independent review

Two distinct exact-commit reviews both **APPROVE** exactly
`ce73391`/tree `c6843e8`:

- `/var/lib/lubko/wd/viche-state/oversight/reviews/innovation-office/zAr8GWjMIhTEfyVGlv6ghW-headed-ce73391.md`
- `/var/lib/lubko/wd/viche-state/oversight/reviews/innovation-office/ea91tJEz6UxCDfU2A1qU6f-bees-ce73391.md`

Exact-tree `dash tests/run-all.sh` → exit 0, “All Viche tests passed.” No
`records/`, `government/LAWS.md`, ballot, Constitution or seats edit is in the
candidate delta.

## Known limitation

Mailbox classification is a deterministic filename heuristic: a genuinely
undisposed report whose filename contains `disposition` or `addendum` would be
skipped. This is the convention the Clerk’s investigation specified as the
minimum acceptable behaviour; it narrows, but does not eliminate, filename
ambiguity. A future protocol change could use an explicit review marker, but
that is not required to fix the permanent-red defect.

## Act 26 pre-landing record — required, not ours to write

This office is the sponsor, so it must not write or commission the pre-landing
verification record. Before landing, an office other than the sponsor and other
than the Clerk must write a record to `$VICHE_STATE_ROOT/delivery/` using the
full schema in
`records/templates/ACT26-PRELANDING-RECORD-INSTRUCTIONS.md` and
`records/templates/ACT26-PRELANDING-RECORD-TEMPLATE.json`, including `status`,
commit/tree/parent/`main_at_verification`, exact command arguments and exits,
content assertions with expected/actual/basis, and a board pin made **before**
the landing. The landing must be a fast-forward to exactly this candidate with
no commit created at it.

No merge or deployment is claimed. Until that record is written and pinned, the
candidate is not landable under Act 26.

## Measured preview on live state (read-only copy)

On a `cp -a` copy of `/var/lib/lubko/wd/viche-state` at 2026-11-09, running the
candidate `branch-health.sh` with the live town tree produced:

- 66 total `inbox/*.md` files;
- 40 whose names contain `disposition` or `addendum`, correctly excluded as
  reviewer answers;
- **26 remaining non-disposition reports**, so the signal still correctly
  emits `judiciary_mailbox_pending` and the case remains open.

This is the intended effect: the repair removes the permanent-red cause (the
monitor counting its own answers), but it does **not** declare the remaining
backlog reviewed or close the case prematurely. Live state was not written.
