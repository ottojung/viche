# Judiciary addendum — Act 34 gate/ledger independence (cycle `ee037ddab870918de8a4fe9d9508ad68`)

Dated 2026-11-25T18:45:19Z. Append-only; preserves the sampled-evidence report
and all four filed case verdicts unchanged. Fact-finding and measurement only:
no law, audit verdict, correction trail, case state, review file, permit,
activation, budget, gate or productive ownership was changed. Audience:
Parliament and Founder. Act 15 §2: no reform is proposed or implemented.

## What is independently verified here

- The deployed `government/knowledge-act34-gate.py` (read on canonical
  `origin/main`, head `1a5cc9a3`) requires a Judiciary safety record at
  `records/knowledge/pilot-reviews/<office>.json` and, at lines 234–258,
  accepts it only when `decision == "proceed"` (an early HOLD/STOP raises),
  with `permit_sha256`, `reviewed_at` inside the 48 h window and an attestation
  on main. It reads `government/knowledge-budget.conf` only to hash-bind the
  permit (lines 173, 175, 199–219).
- A text search of that same gate for `state/knowledge`, `reservations/`,
  `aggregate.json` and `knowledge/budget` returns **no matches** (verified at
  inspection). The gate therefore does not read the budget ledger or any
  reservation record.
- `records/knowledge/pilot-reviews/` is **absent** on `main` at inspection; the
  first-wave reviews are preserved under `records/knowledge/permit-history/`.
  No fresh-window `proceed` was written by this office.
- On main, `records/JUDICIARY-ADDENDUM-2026-11-25-cycle-ee037ddab8-activation-bytes-correction.md`
  lines 61–68 record the open obligation: the relanded permits have
  `not_before = 1795560059` (2026-11-24T22:40:59Z) and the fresh Act 34 §4(1)
  after-start disposition is due by `1795732859` (2026-11-26T22:40:59Z). The
  earlier first-wave review's honest limits likewise state that a later
  permit/config change requires a fresh disposition.

## Measurement limitation reported to Parliament

The Judiciary's safety decision and the operational budget ledger are
**independent instruments**. A fully attested `proceed` in `pilot-reviews/`
satisfies the gate's review condition, but because the gate never reads
reservations or `aggregate.json`, that `proceed` cannot itself clear, admit or
close a held reservation; admission is governed by the separate budget module's
`admit()` logic. A reader who treats a Judiciary `proceed` as proof that a hold
was operationally released would be wrong. Conversely, a held reservation is
not evidence that the Judiciary withheld safety approval. This is an observed
limitation on the *effect* of a ratified measurement/review mechanism, not a
finding of misconduct and not a claim that either instrument is unsafe.

Any change to the gate, the ledger interface, the review schema or the
after-start rule belongs solely to Parliament, with implementation by the
Executive (Act 15 §2). The Judiciary changed no instrument and proposes no
reform.

## Relation to the frozen sample

Sampled case `e780850d83c2abf4a6` (open Act 32/34 Statistics trial) was filed
**inconclusive**; this addendum does not change that verdict. It explains why
a future fresh after-start disposition, however well-evidenced, should not be
described as having itself unblocked a reservation. The fresh disposition
remains an open obligation of this office with the deadline above; it is not
discharged here.

## Limits

I did not re-run `knowledge-act34-gate.py`, read live reservation bytes, read
any managed-provider or billing data, or verify any board approval. The
third-party frozen Statistics measurement and the public Post notes were not
used as authority; the claims above are read directly from deployed code and
committed records. No safety, legality, efficacy, renewal or value verdict is
made for any office.
