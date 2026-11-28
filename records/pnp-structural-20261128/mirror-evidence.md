# Exact public merged Lean source evidence

All mirror operations were **read-only** (`git rev-parse`, `git ls-tree`, `git cat-file`,
`git grep` against the bare mirror object store). No fetch, worktree creation, push or
state write was performed by this research pass.

- Mirror object store: `/var/lib/lubko/wd/viche-state/pnp/cache/fork.git`
- Upstream ref queried: `refs/remotes/upstream/main`
- Pinned upstream revision used: `54000fdbe91c846adb213e5acde692ef02bec05f`
  (the production mirror is fetched continuously; the pin makes this evidence
  reproducible. A later observation saw `7a6b34b9ff2ddf5622f58710f6d511aa577282d8`.)
- Exact source path: `lean/PEqualNP/Outside/L_meta_17487.lean`
- Exact blob object id: `1052b76494a2972ca5ee978fd4dfa6e60b9bd302`
- Saved verbatim copy: `extracted/L_meta_17487.lean`
  - SHA-256 `002c741d558142d0baf492d0b0121290d7e8e6301e1147fed9d1a0bd44c57c77`
  - size 4475 bytes
  - `git hash-object` of the saved file reproduces the pinned blob id exactly.
- Upstream license, read from the same revision's root `LICENSE`: **Apache License 2.0**.

## Reusable finite calculation extracted

From the exact blob, the generic block `def pack` through `lemma anyEq` (upstream calls
these `theorem`s) is independent of the projective-plane parameters:

- `pack : List Bool → Nat` — `xs.foldr Nat.bit 0`
- `readPack` — `(pack xs).testBit k = xs.getD k false`
- `readMap` — bit of a mapped pack equals the mapped defaulted element
- `foldOr` — bit of a bitwise-OR fold equals an `any` of bits
- `anyEq` — extensionality of `List.any`

The parameterised part of the same blob is `flag`, `word`, `input`, `input_read` and
`bitwise`. The generator reproduces that skeleton for arbitrary `(n, diffs)`:
`n` is the number of points/lines and `diffs` the Singer difference set, e.g.
`(13,[0,1,3,9])` for the order-3 plane and `(21,[0,1,4,14,16])` for order 4.

## Attribution rule applied

Generated files carry this header:

```
-- Reuses the finite bit-reflection lemmas from the public merged proof
-- lean/PEqualNP/Outside/L_meta_17487.lean
-- upstream revision 54000fd..., blob 1052b764...
-- Upstream project is licensed Apache-2.0; those lemma statements and proof
-- skeletons are attributed to that source. Parameterisation, assembly and the
-- independent oracle are original research tooling.
```

The reusable declarations are changed from upstream `theorem` to `lemma` only to satisfy
the desk candidate rule requiring exactly one top-level `theorem`; no proof body was
weakened. No upstream proof is claimed as checked by this research pass.

## Reproduction commands (read-only)

```sh
GD=/var/lib/lubko/wd/viche-state/pnp/cache/fork.git
SHA=54000fdbe91c846adb213e5acde692ef02bec05f
git --git-dir=$GD rev-parse $SHA:lean/PEqualNP/Outside/L_meta_17487.lean
git --git-dir=$GD cat-file blob 1052b76494a2972ca5ee978fd4dfa6e60b9bd302
git --git-dir=$GD show $SHA:LICENSE | head -5
git hash-object records/pnp-structural-20261128/extracted/L_meta_17487.lean
```
