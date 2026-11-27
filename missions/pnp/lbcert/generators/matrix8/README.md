# 8x8 public witness reuse

The data file stores canonicalized gate lists derived from public merged
PEqualNP proofs at revision 2917ac9966d6f6d88122a6eaa0e699898ae4a494.
Each entry preserves its source lemma ID. Upstream is Apache-2.0; see
UPSTREAM-LICENSE.txt. Gate data were extracted from literal constructors only,
with no source execution, and semantically audited on the entire promise.
The row/column permutations are computed from invariant refinement followed by
exact enumeration within the remaining color classes. The target witness
is independently audited for the exact bound, topology, and allowed operations.
A class miss or failed audit is not matched; ordinary promise synthesis remains
available. No generated candidate is represented as a checked proof.

358 historical statements had 205 distinct masks and 85 isomorphism classes.
Literal extraction audited 122 source circuits, covering 62 classes.
The smallest extracted canonical circuit per class covers 234/358 historical
bounds (117 strictly below bound, 172 using a different source lemma).
No claim of credit or availability for already merged problems.

Rebuild on billy-dev with the local public mirror:
  python3 -m missions.pnp.lbcert.generators.matrix8.build_index 2917ac9966d6f6d88122a6eaa0e699898ae4a494 --output /tmp/matrix8.json
Compare audited contents before updating witnesses.json and the pinned digest.
