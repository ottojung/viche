# PnP proof adapter / certificate reuse

## What this module does

`missions.pnp.adapter` implements source-level proof adaptation for reusable PnP
Lean proofs. It does **not** perform fragile global namespace substitution.

- **Controlled module renaming**: rewrites only the fully qualified source module
  identifier (`PEqualNP.Outside.L_meta_*`) as a token, preserving unrelated names.
- **Declaration dependency closure extraction**: parses Lean declarations and
  computes a conservative transitive closure from a target declaration
  (`python3 -m missions.pnp.adapter closure ...`).
- **Stronger-lemma / reusable-proof detection**: searches the checked upstream
  corpus for exact or structurally stronger candidates, then attempts adaptation
  while respecting exact leased `imports/module/file/statement`
  (`python3 -m missions.pnp.adapter detect ...`).
- **Hypothesis instantiation**: when a stronger source proof has a compatible
  conclusion with fewer/subset hypotheses, the adapter emits a module-derived
  helper lemma and a final target theorem wrapper (heuristic, validator-checked).
- **Minimal standalone emission**: emits Mathlib-first imports from the target gap,
  demotes helper `theorem` declarations to `lemma`, normalizes helper namespaces
  under the target module, and validates with `missions.pnp.validate`.

## Worked adaptation (measured)

Archived accepted example: `PEqualNP.Outside.L_meta_1152` (commit `1731dbf`,
`lean/PEqualNP/Outside/L_meta_1152.lean`, 8-gate monotone circuit, 8 variables).

Adaptation: read the checked upstream source, applied controlled module renaming /
exact-statement adaptation through `missions.pnp.adapter.adapt.adapt_exact_module`,
and emitted a validator-clean candidate. The adapted candidate passed
`missions.pnp.validate.validate` (exact path/module/statement/import checks).

Measured compile (billy-dev, 2026-11-24, scratch worktree from upstream main
`a6a7084`, copied `.lake` from an existing gap worktree; shared compile queue via
`PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.compile`):

- `--light -- lake env lean PEqualNP/Outside/L_meta_1152.lean`
  - result: `RESOURCE DEFERRED: light compilation exceeded 2 GiB; retry as heavy`
- `-- lake env lean PEqualNP/Outside/L_meta_1152.lean` (heavy slot, LEAN_NUM_THREADS=1)
  - exit: `0`
  - output: empty (Lean success)

This measures adaptation+compile for a small archived accepted proof. It is not a
universal benchmark; larger family files (e.g. L_meta_2455/L_meta_2457) require
the same controlled adaptation but have much larger compile cost.

## Family case

`L_meta_2455` and `L_meta_2457` share the same large theta-graph engine; the
checked sources differ by controlled module name and final theorem/wrapper. The
adapter's closure extraction finds the shared engine declarations, and corpus
detection can select the exact checked target or a stronger compatible lemma when
present. Tests cover closure extraction on `L_meta_2455` and family detection
against archived `L_meta_2455/L_meta_2457` sources.
