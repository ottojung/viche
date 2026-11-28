# Bounded research tools: November 28

These tools are deliberately outside automatic plugin discovery. They emit only
upper-bound witnesses or untrusted screening results, never an external checker
receipt, a solved-gap assertion, or a reason to claim an unbound lease. No Lean
is launched here. A native hash collision can create an incorrect screen result;
a full proof must be independently reconstructed and checked by the authorized
Lean pipeline.

* screen128/screen.c: complement-canonical sorted 128-bit live sets, cut masks
  computed before recursion. Input protocol matches onenot/lsearch.c for up to
  64 row pairs. Regression: python3 tests/pnp-screen128-research.py.
* screen128/floors.py and project.c: full 64-row truth tables and projection
  cost hints. The latter records the number of paid prefix operations after
  fixing a variable. A nonconstant target cannot retain constant live wires
  to the end; consuming a constant wire allows its operation to be simplified.
  This motivates the cut paid + remaining - constant_mass < slice_floor.
  Native hint generation and pruning are research only.
* neighbor/extract.py: literal witnesses from a pinned public upstream revision.
  Only exact truth-table replays are retained; source commit/blob accompany each
  seed. Upstream repository open-goat/pequalnp-proofs, Apache-2.0. The search
  wrapper builds variable-permutation and duality orbits of a live snapshot.
  search.c explores up to two different gate edits per seed. run.py replays
  every emitted witness in the original target basis. Example:
      python3 missions/pnp/lbcert/research/neighbor/extract.py MIRROR REF corpus.json
      python3 missions/pnp/lbcert/research/neighbor/run.py corpus.json gaps-cache.json witnesses.json
* rectangles/local.c and weighted.c: bounded constructive set-cover search
  on an exact enumerated family. Input little-endian u32 box count, u32 bound,
  then a target 448-bit mask and that many 448-bit candidate masks. Native
  output is indices only; independently verify coverage and each rectangle.
  weighted.c reports diverse near-solutions to stderr (not certificates).
  repair.py uses exact inverted bitsets to repair a bounded number of slots.
* sixcore/engine.py: preserved research version of the rejected sixcore
  delivery, fixing literal placeholder substitution and the missing circuit
  bridge, with a pinned template digest. Tests explicitly assert the required
  definitions and that discovery does not route production to this generator.

Tests: python3 tests/pnp-neighbor-research.py and
python3 tests/pnp-sixcore-research.py. These are research regressions, not a
substitute for exact kernel verification or the integration suite.
