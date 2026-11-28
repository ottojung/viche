# Five-input cofactor lower-bound transfer

Source: public merged proof L-meta-16507 at upstream commit
7a6b34b9ff2ddf5622f58710f6d511aa577282d8, blob
dea480c9378dc48de4aa925f484365b72bbdae56. The exact source is pinned by SHA256
in gen.py and preserved with its upstream Apache-2.0 license.

Its five-input certificate proves a nine-binary-gate lower bound with free
NOT. The adapter relabels rows (variable permutations and duality), fixes
one essential sixth variable, proves the induced restriction and essential
input conditions using kernel decidability, and reuses lower_slice and
lb_with_not. For a monotone circuit of eleven gates this suffices: any
circuit with NOT has at least eleven gates; otherwise the original circuit
is already monotone. The generator declines smaller witnesses to prefer
the compact engine. Python independently replays every witness and checks
the row mapping; it does not issue proof receipts or claim Lean acceptance.

The pinned template's existing certificate remains intact; its original
six-input goal is not used in the extracted lower-bound proof. All new
transport and witness obligations remain in the generated Lean source.
The offline tests check all 480 combinations of orbit mask, fixed
position, and polarity, direct and dual static emission, and refusals.

A read-only corpus scan found 86 current positive six-input statements
with a cofactor in this certificate's 40-mask orbit. This is a match
count, not a proof yield. Two other known eight-gate certificates cover
additional restrictions but are not used by this adapter.
