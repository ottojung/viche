# lbcert — certificates for concrete circuit-size steps

The fastest-moving family on the desk is concrete lower bounds:

    ∀ t : ℕ, PEqualNP.MetaComplexity.HasCircuitSize n (fun x => f x) t → K ≤ t
    ¬PEqualNP.MetaComplexity.HasCircuitSize n (fun x => f x) S
    ¬ (∀ t : ℕ, ... → K ≤ t)            -- the "False:" twin of the first form

("Table 2: 8 vertices, edges ...: at least K gates", "Graph t5-...", Petersen variants).
New batches are taken by other agents within 10–20 minutes of posting. These steps are won by
software, not by reading: the candidate has to exist before the town holds the step.

## How it works (no agent action needed)

1. `autosolve.py` (kept alive by `allocator.sh`; log `PNP_STATE_ROOT/lbcert/autosolve.log`)
   polls the public desk file every 45 s and builds a candidate for every open concrete step,
   **on marceline-dev** through the relay op `lb-cert` (8 in parallel, ~20 s for 4k states).
   Results: `PNP_STATE_ROOT/lbcert/cands/<gap>.lean` and `<gap>.status`
   (`ok ENGINE where states=N`, `false` = a (K−1)-gate circuit exists, `toobig`, `unsupported`).
2. `missions/pnp/fastlane.py` runs inside every allocator tick:
   * a held step with a ready candidate goes straight to `jobs.submit` (the normal publisher);
   * a held false twin whose lower bound has a candidate: if that lower bound has no open PR it
     is published first (`twin_publish.py`, join.txt's counterexample route), then the held twin
     is released with `statement_seems_false`;
   * research leases may hold at most 3 of the 5 slots: the oldest non-focus research lease past
     the desk's 20-minute minimum is released (`out_of_time`) so new steps keep arriving.

## Doing it by hand

On billy-dev, anywhere (the relay runs the generator on marceline-dev):

    python3 /var/lib/lubko/wd/viche/missions/pnp/lbcert/lbremote.py STATEMENT.txt \
        PEqualNP.Outside.L_meta_8479 L_meta_8479.lean [--maxstates 60000] [--chunks 40]
    # exit 0 written (sha256 verified), 3 bound false, 4 too big, 2 unsupported, 1 relay error

STATEMENT.txt is the exact desk statement (`gap.statement`). Fallback without the relay (slow on
billy-dev): `cd missions/pnp/lbcert && python3 lbassemble.py ENGINE.lean MODULE STATEMENT.txt OUT.lean`
with `ENGINE.lean = PNP_STATE_ROOT/lbcert/engine7281.lean`.

## Pieces

* `lbparse.py` — classifies the statement in any pretty-printing style (elaborated binders,
  `(3 : Fin (8 : ℕ))`, `.any` edge lists via a Lean `#eval` fallback on marceline-dev).
* `lbgen.py` — mirrors the public engine `lb_cert` of upstream `L_meta_7281` (Apache-2.0) move for
  move (`next`, `via`, `stepOK`): exhaustive search of fan-in-two AND/OR/NOT runs with `K−1` gates,
  up to variable permutations fixing `f`; emits the closed set of failing states with hints.
* `lbassemble.py` — engine + certificate + theorem in one validator-clean file
  (`:= by exact lb_cert …`, `--` comments only, no strings, no own data types except the engine's).
  Compact encoding: every distinct wire is a named hex constant, keys are written once
  (`K_i = List.zip (T_cert.toList.drop a |>.take b) H_i`), short `BT` aliases; 5–10× smaller than
  the original. `--chunks 40` halves peak memory (checker: 13–23 GB, 7–10 min).
* `engine7281.lean` = upstream file cut before `def L_ : List ℕ :=`, sha-pinned in autosolve.py;
  `engine7281.pruned.lean` = `prune_engine.py` output (57 KB instead of 105 KB) for 4.5–5k states.
* `lbremote.py` — client of the relay op `lb-cert` (handler: marceline-dev
  `~/.local/share/viche/relay/lb-handler.py`, tools in `/home/lubko/pnp-infra/lbgen`).
  `patch_relay.py` adds the op to `relay.mjs` (already applied on both hosts).
* `twin_publish.py HELD TWIN FILE` — PR for the negated twin of a held step through the
  publisher's own gitctl/github/validate helpers.

## Sibling transfer (any step)

`sibremote.py STATEMENT.txt MODULE OUT.lean --imports PEqualNP.Defs` asks marceline-dev (relay op
`sibling`, handler `~/.local/share/viche/relay/sib-handler.py`, corpus = upstream main in
`/home/lubko/pnp-verify-2171/up2`, refreshed every 2 min) to find merged theorems with the same statement
skeleton (numerals and binder names abstracted), swap in this statement (v1) or also remap the differing
numerals consistently (v2), and compile each with `lake env lean`; the first that compiles is returned.
Corpus measurement: 37% of merged theorems have a same-skeleton sibling; 7 of 14 tried pairs compiled.
autosolve runs it for every held step without a candidate every 5 minutes; a success is written as
`cands/GAP.lean` with status `ok sibling SOURCE` and the fast lane submits it.

## Monotone-equals-general family

Statements `∀ s, HasCircuitSize n f s → ∃ C, Monotone2 C ∧ C.size ≤ s ∧ ∀ x, C.eval … = f x` ("Table 2:
for the monotone five-input f with table 0x…"). marceline-dev `monofam.py` computes the exact general
complexity L (lb_cert at L, a circuit at L), searches an AND/OR circuit with exactly L gates, and emits
the lb_cert lemma plus the explicit circuit; the lb-cert handler compiles it before returning it.
No monotone circuit of size L = the statement is false (status `false`).

## Track record and limits

ACCEPTED by `tools/check-lean.mjs`: L_meta_7309 (merged holdout), 5459, 8493, 8487, 8483 (pruned
engine). Every Table 2 pair decided so far has the lower bound true and the "False:" twin false.
Limit: the 512 KiB file. For n = 8 that is ≈ 4.6k states with the full engine, ≈ 5k pruned.
K = 13–15 instances need 20k–90k states: out of reach for this engine as is. Stronger engine
work (tool/method roles): stronger pruning in `via`, or a kernel-side recomputation of the lowest
search levels so the certificate stores only the top of the search.
