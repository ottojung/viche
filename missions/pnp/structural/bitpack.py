"""Reusable structural generator for the finite bit-reflection cut family.

Upstream source (public merged, Apache-2.0):
  lean/PEqualNP/Outside/L_meta_17487.lean
  upstream revision 54000fdbe91c846adb213e5acde692ef02bec05f
  blob 1052b76494a2972ca5ee978fd4dfa6e60b9bd302

The generic finite lemmas below are verbatim from that blob (with ``theorem``
adapted to ``lemma`` so a generated candidate satisfies the desk validator's
single-theorem rule).  The definitions and main-theorem skeleton are a direct
parameterisation of the same upstream proof.  This module independently checks
the finite calculation with :mod:`oracle`; it never compiles Lean, claims a
lease, publishes, or asserts leaderboard credit.
"""
import hashlib
import re

from .. import validate
from . import extract, oracle

# Verbatim generic block from the pinned upstream blob, with declarations
# changed from ``theorem`` to ``lemma`` for the desk single-theorem rule.
GENERIC_BLOCK = """def pack (xs : List Bool) := xs.foldr Nat.bit 0
lemma readPack (xs : List Bool) (k : ℕ) : (pack xs).testBit k = xs.getD k false := by
  induction xs generalizing k with
  | nil => simp [pack]
  | cons x xs ih =>
    cases k with
    | zero =>
      change (Nat.bit x (pack xs)).testBit 0 = x
      cases x <;> simp [Nat.bit, Nat.testBit_zero, Nat.add_mod]
    | succ k =>
      change (Nat.bit x (pack xs)).testBit (k+1) = xs.getD k false
      rw [Nat.testBit_bit_succ, ih]
lemma readMap (xs : List (Bool × List Bool)) (f : Bool × List Bool → Bool) (k : ℕ)
    (hf : f (false,[]) = false) :
    (pack (xs.map f)).testBit k = f (xs.getD k (false,[])) := by
  rw [readPack]
  simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
  cases xs[k]? <;> simp [hf]
lemma foldOr (xs : List ℕ) (a k : ℕ) :
    (xs.foldl (· ||| ·) a).testBit k = (a.testBit k || xs.any (fun n => n.testBit k)) := by
  induction xs generalizing a with
  | nil => simp
  | cons x xs ih => simp only [List.foldl_cons, ih, Nat.testBit_or, List.any_cons, Bool.or_assoc]
lemma anyEq {α : Type} (xs : List α) (f g : α → Bool) (h : ∀ i ∈ xs, f i = g i) : xs.any f = xs.any g := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [List.any_cons, h x List.mem_cons_self, ih (fun i hi => h i (List.mem_cons_of_mem _ hi))]
"""

PROOF = """  dsimp only
  intro rs h
  change word (input rs) = pack (rs.map Prod.fst)
  apply Nat.eq_of_testBit_eq
  intro k
  rw [bitwise, readMap rs Prod.fst k rfl]
  by_cases hk : k < rs.length
  · rw [List.getD_eq_getElem _ _ hk]
    exact (h _ (List.getElem_mem hk)).symm
  · rw [List.getD_eq_default _ _ (by omega)]
    decide +kernel
"""


def _nat_list(xs):
    return "[" + ", ".join("(%d : ℕ)" % d for d in xs) + "]"


def params(n, diffs):
    """Validate and canonicalise generator parameters."""
    n, diffs = int(n), [int(d) for d in diffs]
    if n < 2 or n > 64:
        raise ValueError("n must be between 2 and 64")
    if not diffs or len(set(diffs)) != len(diffs) or \
            any(not (0 <= d < n) for d in diffs):
        raise ValueError("diffs must be distinct residues mod n")
    return n, diffs


def statement_for(n, diffs):
    """Exact desk-style statement produced for (n, diffs)."""
    n, diffs = params(n, diffs)
    d = _nat_list(diffs)
    two_n = 2 * n
    return (
        "have x1 : List Bool → Bool := fun (x1 : List Bool) => (List.range (%d : ℕ)).any fun (x2 : ℕ) => "
        "x1.getD ((%d : ℕ) + x2) Bool.false && %s.any fun (x3 : ℕ) => "
        "x1.getD ((x3 + (%d : ℕ) - x2) %% (%d : ℕ)) Bool.false; "
        "have x2 : List ℕ → ℕ := fun (x2 : List ℕ) => List.foldl (fun (x3 x4 : ℕ) => x3 ||| x4) (0 : ℕ) "
        "(List.map (fun (x3 : ℕ) => x2.getD ((%d : ℕ) + x3) (0 : ℕ) &&& "
        "List.foldl (fun (x4 x5 : ℕ) => x4 ||| x5) (0 : ℕ) "
        "(List.map (fun (x4 : ℕ) => x2.getD ((x4 + (%d : ℕ) - x3) %% (%d : ℕ)) (0 : ℕ)) %s)) "
        "(List.range (%d : ℕ))); "
        "∀ (x3 : List (Bool × List Bool)),   (∀ x4 ∈ x3, x4.1 = x1 x4.2) →     "
        "have x5 : List ℕ := List.ofFn fun (x5 : Fin (%d : ℕ)) => List.foldr Nat.bit (0 : ℕ) "
        "(List.map (fun (x6 : Bool × List Bool) => x6.2.getD (↑x5) Bool.false) x3);     "
        "x2 x5 = List.foldr Nat.bit (0 : ℕ) (List.map Prod.fst x3)"
    ) % (n, n, d, n, n, n, n, n, d, n, two_n)


def recognize(statement):
    """Find (n, diffs) if a statement is exactly this generator's shape.

    Recognition is syntactic and full-statement; a title or a partial match is
    never treated as proof.  Whitespace is normalised because the desk printer
    varies indentation between rows.
    """
    s = " ".join(statement.split())
    m = re.match(
        r"have x1 : List Bool → Bool := fun \(x1 : List Bool\) => \(List\.range \((\d+) : ℕ\)\).*",
        s)
    if not m:
        return None
    n = int(m[1])
    if not (2 <= n <= 64):
        return None
    ds = [int(x) for x in re.findall(r"\((\d+) : ℕ\)", s[1:])]
    # The posting prints the difference set twice; take the first run that has
    # distinct residues under n and is non-empty.
    seen = []
    for d in ds:
        if d < n and d not in seen:
            seen.append(d)
        if seen and d >= n:
            break
    if not seen or len(seen) > 8:
        return None
    if " ".join(statement_for(n, seen).split()) != s:
        return None
    return n, seen


def render(n, diffs, module, imports=("PEqualNP.Defs",), attributed=True,
           generic=None):
    """Render a complete candidate Lean file for (n, diffs)."""
    n, diffs = params(n, diffs)
    block = generic if generic is not None else GENERIC_BLOCK
    if not module.startswith("PEqualNP.") or not re.fullmatch(
            r"PEqualNP\.[A-Za-z0-9_.]+", module):
        raise ValueError("unsafe module name")
    ns = module + "_aux"
    d = _nat_list(diffs)
    two_n = 2 * n
    lines = ["\n".join("import " + i for i in imports), ""]
    if attributed:
        lines.append(extract.attribution().rstrip())
    lines += [
        "namespace " + ns,
        block.rstrip(),
        "def flag : List Bool → Bool := fun (v : List Bool) => "
        "(List.range (%d : ℕ)).any fun (l : ℕ) => "
        "v.getD ((%d : ℕ) + l) Bool.false && %s.any fun (d : ℕ) => "
        "v.getD ((d + (%d : ℕ) - l) %% (%d : ℕ)) Bool.false" % (n, n, d, n, n),
        "def word : List ℕ → ℕ := fun (m : List ℕ) => "
        "List.foldl (fun (a b : ℕ) => a ||| b) (0 : ℕ) "
        "(List.map (fun (l : ℕ) => m.getD ((%d : ℕ) + l) (0 : ℕ) &&& "
        "List.foldl (fun (a b : ℕ) => a ||| b) (0 : ℕ) "
        "(List.map (fun (d : ℕ) => m.getD ((d + (%d : ℕ) - l) %% (%d : ℕ)) (0 : ℕ)) %s)) "
        "(List.range (%d : ℕ)))" % (n, n, n, d, n),
        "def input (rs : List (Bool × List Bool)) := "
        "List.ofFn (fun i : Fin (%d : ℕ) => pack (rs.map (fun r => r.2.getD i.val false)))" % two_n,
        "lemma input_read (rs : List (Bool × List Bool)) (k j : ℕ) (hj : j < %d) : "
        "((input rs).getD j 0).testBit k = (rs.getD k (false,[])).2.getD j false := by" % two_n,
        "  rw [List.getD_eq_getElem _ _ (by simpa [input] using hj)]",
        "  simp only [input, List.getElem_ofFn]",
        "  apply readMap",
        "  simp",
        "lemma bitwise (rs : List (Bool × List Bool)) (k : ℕ) : "
        "(word (input rs)).testBit k = flag (rs.getD k (false,[])).2 := by",
        "  unfold word flag",
        "  simp only [foldOr, Nat.zero_testBit, Bool.false_or, List.any_map, Function.comp_apply, Nat.testBit_and]",
        "  apply anyEq",
        "  intro i hi",
        "  have hi' := List.mem_range.mp hi",
        "  simp only [Function.comp_apply, Nat.testBit_and, foldOr, Nat.zero_testBit, Bool.false_or, List.any_map]",
        "  rw [input_read rs k ((%d : ℕ) + i) (by omega)]" % n,
        "  congr 1",
        "  apply anyEq",
        "  intro j _",
        "  exact input_read _ _ _ (lt_trans (Nat.mod_lt _ (by decide : 0 < %d)) (by decide))" % n,
        "end " + ns,
        "",
        "open " + ns + " in",
        "theorem " + module + " : " + statement_for(n, diffs) + " := by",
        PROOF.rstrip(),
        "",
    ]
    return "\n".join(lines)


def candidate(meta, n=None, diffs=None, use_mirror=False, mirror=None):
    """Generate and independently check a candidate for a gap metadata record.

    ``meta`` supplies id/file/module/statement/imports from the desk or catalog.
    When n/diffs are omitted the statement is recognised exactly; no title is
    used.  The returned report never claims a kernel check or desk credit.
    """
    if n is None or diffs is None:
        found = recognize(meta["statement"])
        if found is None:
            return {"result": "not-recognized",
                    "reason": "statement is not the bit-reflection shape",
                    "local_lean_checked": False}
        n, diffs = found
    generic = None
    if use_mirror:
        from .. import gitctl
        generic = extract.generic_block(extract.blob(
            mirror or gitctl.MIRROR)[0]).replace("theorem ", "lemma ")
    text = render(n, diffs, meta["module"], meta.get("imports") or ["PEqualNP.Defs"],
                  generic=generic)
    digest = validate.validate(meta, text.encode("utf-8"))
    ident = oracle.verify_identity(n, diffs)
    lemmas = oracle.verify_generic_lemmas(n, diffs)
    ok = ident["verified"] and lemmas["verified"]
    return {"result": "candidate" if ok else "oracle-rejected",
            "family": "bitpack_flag", "n": n, "diffs": list(diffs),
            "sha256": digest, "candidate": text,
            "oracle_identity": ident, "oracle_lemmas": lemmas,
            "upstream": {"path": extract.SOURCE_PATH,
                         "revision": extract.PINNED_REVISION,
                         "blob": extract.PINNED_BLOB, "license": extract.LICENSE},
            "local_lean_checked": False, "desk_credit_claimed": False}
