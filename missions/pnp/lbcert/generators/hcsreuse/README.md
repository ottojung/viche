# Audited positive small-circuit reuse

Public source: open-goat/pequalnp-proofs, Apache-2.0, pinned upstream
491b9d7f1ef497d41e346ead5326157c2da595c9. The data records the source lemma
number and exact Git blob per witness. The builder reads literal circuit
constructors only (never executes source), scans ranges 10200–11150 and
20780–20790, and independently checks each extracted circuit against the
statement's complete truth table before transporting it. From 18 audited
positive source proofs we retain 12 best source witnesses and 1458 distinct
truth tables after free input relabelling and counted output negation.

Reproduce from the repository root:

    python3 -m missions.pnp.lbcert.generators.hcsreuse.build_index MIRROR /tmp/hcs.json
    cmp /tmp/hcs.json missions/pnp/lbcert/generators/hcsreuse/witnesses.json

This is witness coverage, not an optimality table. Lookup checks the requested
gate limit and all rows before generating a complete candidate. Unsupported
syntax, negative claims and tighter bounds are refused. The final proof still
requires the authorized exact check. No direct publication or prelease scope
change. Current held comparator 9929 is parsed correctly but has no witness
within its 11-gate bound in this library.
