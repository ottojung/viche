# Isolated PnP structural-proof generator research (2026-11-28)

Authority: Founder-authorized billy-dev PnP competitiveness continuation, assigned to
billy-dev. Execution was isolated in worktree `operator/pnp-structural-20261128`.

## What this is

Research tooling plus preserved evidence for a **reusable finite structural-cut proof
generator**. It is not a lease claim, a publication, a leaderboard action, or a kernel
verdict. No dispatch/allocator work, no upstream PR, no production-state mutation and
no unbound Lean were performed.

## Conclusion in brief

The five named examples (`L-meta-6136`, `L-meta-6648`, `L-meta-8101`, `L-meta-7798`,
`L-meta-8217`) are deep circuit-size lower-bound steps: they quantify over arbitrary
fan-in-two circuits and assert ≥64 / ≥124 / ≥22 gates. Their titles say "a step toward";
that is not evidence of truth, and none was assumed. Their exact statements are
preserved in `targets.json` and analysed in `targets-analysis.md`. A finite generator
does not settle them; the generator explicitly refuses to recognise them.

Per the Founder's pivot instruction, work moved to a **simpler repeated structural cut**
with actual coverage: the finite bit-reflection lemma family of the public merged proof
`L_meta_17487` (3000+ merged instances share the `flag`/`word`/`pack`/`input`
calculation). `missions/pnp/structural/` parameterises that exact upstream calculation
for arbitrary projective-plane order and difference set, extracts the generic lemmas
from the exact public mirror blob with Apache-2.0 attribution, and checks every finite
claim with an independent Python oracle.

## Files

- `targets.json` — exact posted statements/metadata for the five named gaps.
- `targets-analysis.md` — why those steps are not generator-tractable; no title inference.
- `mirror-evidence.md` — exact revision, path, blob, license and extraction commands.
- `extracted/L_meta_17487.lean` — verbatim public merged source (git blob verified).
- `generator-report.json` / `generator-report.md` — held-out coverage, honest status.
- `candidates/` — generated candidate Lean files (development + held out).

## Status

Generated candidates pass the offline desk static validator and the independent finite
oracle. **They are not kernel-checked.** No desk credit is claimed. A researcher may
take a real gap through the ordinary lease + managed compiler + signed publisher path
before any step can be counted.
