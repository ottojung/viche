# Two five-input cofactors vs 12-gate certificates — bounded investigation

Date: 2026-11-28. Owner: Antonina research agent (isolated branch
`research/cofactor-two-gate-20261128`). No Lean was launched; no lease, PR or
proof-of claim was made. All numbers are static, bounded Python results.

## Question

Merged `L_meta_40976` (upstream `35c502ce4729f3e7469f7130fd41a8c4710cf78b`)
uses `one`: `Low n` for one five-input cofactor `rs i c f` gives `Low (n+1) f`.
Its companion `two` needs `Low n` for BOTH cofactors `rs i false f` and
`rs i true f`, giving `Low (n+2) f`. To certify a 12-gate monotone witness by
`two`, both five-input cofactors must have general circuit complexity >= 10
(`Low 10`), i.e. `CoreSearch.search 9` must be false on suitable samples.

## What was done

1. Ported the merged 40976 `CoreSearch` (BitVec 64, 32 sample columns,
   `cuts`/`dispatch`/`optimized`/`search`) to Python with a state cap.
2. Validated the port on the exact columns of `L_meta_40976.sixLower`:
   `search 7 = false` at 27,553 states and `search 8 = true` at 8,704 states
   (matching the merged proof's `Low 8` cofactor).
3. For a deterministic sample of six-input monotone functions whose
   constructive witness has 12 gates, computed bounded `Low` values for all 12
   five-input cofactors (fixed reproducible sample pairs, 8,000-state cap per
   search) and tested whether any variable has both cofactors with `Low >= 10`.
4. `python3 -m missions.pnp.research.cofactor_two.experiment` reproduces the
   exact JSON results (35 s, 4 cores not used in parallel).

## Results (negative)

- The merged proof's hardest known five-input cofactor has `Low 8`
  (`search 7` false, `search 8` true). No sample in this investigation reached
  `Low 9`, let alone the `Low 10` needed for `Low 12`.
- Sample of 2 deterministic 12-gate-witness functions (of 6 generated):
  0 certified; maximum cofactor `Low` observed was 5. Several cofactor searches
  hit the 8,000-state cap and are reported `null` (inconclusive, not a result).
- Coverage estimate for this route at target 12: **0 of 2** in the bounded
  sample; no evidence that the two-cofactor method can certify 12-gate
  witnesses on this family. No generator was produced because the evidence is
  negative/inconclusive.

## Limitations

- The lower bound depends strongly on sample-pair selection. The merged
  proof's hand-picked columns decide `search 7` in 27k states; a naive cyclic
  pairing of ones/zeros on the same function hit a 200k-state cap without
  proving the bound. The experiment therefore uses a fixed reproducible
  pairing and reports budget hits explicitly.
- State caps and the 120 s wall-clock budget limit the search depth; `null`
  means "not decided within cap", not "no lower bound".
- `synthesize` witnesses are upper bounds, not proven minima; the sampled
  functions are not confirmed to have monotone complexity exactly 12.
- Static candidates are not kernel verification. No Lean acceptance is claimed.

## Outcome

Recorded negative result. No Act 31 delivery of a generator is warranted from
this evidence; the reproducible experiment and its exact numbers are delivered
instead.
