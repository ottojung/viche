# Reusable generator: coverage and honest status

## What was built

`missions/pnp/structural/` implements a parameterised version of the finite
bit-reflection cut of the public merged proof `L_meta_17487` (Apache-2.0, pinned blob
`1052b764...`). Given a projective-plane order `n` and difference set `diffs`, it emits
a complete Lean candidate: generic `pack`/`readPack`/`readMap`/`foldOr`/`anyEq` lemmas
(verbatim from the exact upstream blob, `theorem`→`lemma` for the desk one-theorem rule),
plus the parameterised `flag`/`word`/`input`/`input_read`/`bitwise` block and the main
theorem `word (input rs) = pack (rs.map Prod.fst)` under the labelled-row hypothesis.

The generator recognises a posted statement **exactly** (full-statement token match);
it never uses a title, and refuses anything outside this shape.

## Independent finite checks

`missions/pnp/structural/oracle.py` re-implements the calculation from scratch and
verifies, for each instance:

- `verify_identity`: 400 random labelled-row lists satisfy
  `word (input rs) = pack (map Prod.fst rs)`;
- `verify_generic_lemmas`: 400 random instances of `readPack`, `foldOr`, `input_read`
  and `bitwise` (the exact statements the reused lemmas prove).

## Coverage

| Split | `(n, diffs)` | Result | Oracle trials | Candidate sha256 (first 12) |
|---|---|---|---|---|
| development | `(13,[0,1,3,9])` | candidate | 400 + 400 | `0a45e0cd51c1` |
| development | `(7,[0,1,3])` | candidate | 400 + 400 | `6abca96454cd` |
| **held out** | `(21,[0,1,4,14,16])` | candidate | 400 + 400 | `0530dd531026` |
| **held out** | `(5,[0,1])` | candidate | 400 + 400 | `a1706f2f8e33` |
| **held out** | `(9,[0,1,3])` | candidate | 400 + 400 | `ad1035fbae5a` |
| **held out** | `(31,[0,1,3,8,12,18])` | candidate | 400 + 400 | `daa43680145e` |
| **held out** | `(3,[0,1])` | candidate | 400 + 400 | `5f592380a2d8` |

7/7 candidates generated, statically validated by `missions.pnp.validate`, and accepted
by both finite oracles. 5/7 are held-out parameter sets never used in development.
The order-4 difference set `(21,[0,1,4,14,16])` is included as a held-out instance;
`n=31` is the order-5 plane. All seven are general bit-reflection identities, not
circuit lower bounds.

Against the five named unmatched gaps (`L-meta-6136`, `6648`, `8101`, `7798`, `8217`)
the generator returns `not-recognized` for all five: it produces no candidate for a
statement it cannot verify. See `targets-analysis.md`.

## Limits and honest status

- **Not kernel-checked.** No Lean/lake/checklemma was run. Static validation proves only
  file shape, imports, statement identity and banned-command hygiene; the Python oracle
  proves only the finite calculations. A real Lean kernel must still accept each
  candidate before it could be submitted, and even then a lower-bound step needs its
  own mathematics.
- **No desk credit claimed.** No lease was acquired, no gap was held, no upstream PR was
  opened, and no leaderboard effect is asserted. Generation is not publication.
- **Coverage is of the finite bit-reflection cut family**, not of the deep 64/124/22-gate
  steps. Those remain unmatched and, on the evidence in `targets-analysis.md`, were not
  solved by the existing generators either.
- Generated files are candidates for a researcher to review and, only through the
  normal lease + managed compiler + signed publisher, potentially convert to checked
  steps.

## Commands

```sh
PYTHONPATH=. python3 -m missions.pnp.structural heldout \
  --out-dir records/pnp-structural-20261128/candidates \
  --report records/pnp-structural-20261128/generator-report.json
PYTHONPATH=. python3 -m missions.pnp.structural targets \
  --file records/pnp-structural-20261128/targets.json
/bin/sh /var/lib/lubko/wd/viche/government/suite-env.sh python3 tests/pnp-structural.py
```
