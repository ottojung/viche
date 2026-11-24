"""Detect reusable stronger lemmas in the checked upstream corpus."""
from __future__ import annotations

from dataclasses import dataclass
import re

from ..proofs import corpus
from .. import validate
from .adapt import adapt_exact_module, controlled_module_rename, emit_standalone, _extract_final_theorem, _replace_final_theorem, _split_imports, _ensure_imports_allowed, _demote_helper_theorems, _normalize_helper_namespaces


@dataclass
class Detection:
    path: str
    module: str
    score: float
    strategy: str
    ok: bool
    sha256: str | None
    error: str | None
    candidate: str | None


def _hypothesis_parts(statement: str) -> tuple[list[str], str]:
    # Reuse corpus.hypotheses but keep raw text parts.
    parts, conclusion = corpus.hypotheses(statement)
    return [p.strip() for p in parts if p.strip()], conclusion.strip()


def _is_stronger_or_equal(source_stmt: str, target_stmt: str) -> str | None:
    """Return a strategy name if source can justify target, else None.

    Strategies:
    - exact: token-equal statements.
    - stronger_hypotheses: same conclusion shape, source hypotheses are subset.
    - weaker_target: target has extra hypotheses; source can be applied after introducing them.
    """
    if validate.tokens(source_stmt) == validate.tokens(target_stmt):
        return "exact"
    sh, sc = _hypothesis_parts(source_stmt)
    th, tc = _hypothesis_parts(target_stmt)
    if validate.tokens(sc) != validate.tokens(tc):
        # Try structural conclusion shape equality
        if corpus.shape(sc) != corpus.shape(tc) or not corpus.shape(sc):
            return None
    # Source stronger if its hypotheses are a subset of target hypotheses (by normalized token shape).
    sset = {corpus.shape(h) for h in sh if corpus.shape(h)}
    tset = {corpus.shape(h) for h in th if corpus.shape(h)}
    if sset and sset <= tset:
        return "stronger_hypotheses"
    if not sset and tset:
        # Source has no hypotheses, target does - source is stronger.
        return "stronger_hypotheses"
    if sset == tset:
        return "exact_shape"
    return None


def _instantiate_candidate(source: str, source_module: str, target_gap: dict, strategy: str) -> Detection:
    target_module = target_gap["module"]
    renamed = controlled_module_rename(source, source_module, target_module)
    src_imports, _ = _split_imports(renamed)
    try:
        _ensure_imports_allowed(src_imports, target_gap)
    except ValueError as e:
        return Detection("", source_module, 0.0, strategy, False, None, str(e), None)

    _, body = _split_imports(renamed)
    body = _demote_helper_theorems(body, target_module)
    body = _normalize_helper_namespaces(body, target_module)
    candidate = emit_standalone(target_gap, body, src_imports)
    final = _extract_final_theorem(candidate, target_module)
    if final is None:
        return Detection("", source_module, 0.0, strategy, False, None, "missing final theorem after rename", candidate)

    _, stmt, proof_tail = final
    target_stmt = target_gap["statement"]

    if validate.tokens(stmt) != validate.tokens(target_stmt):
        if strategy in ("exact", "exact_shape"):
            candidate = _replace_final_theorem(candidate, target_module, target_stmt, proof_tail)
        elif strategy == "stronger_hypotheses":
            # Source is stronger (fewer/equal hypotheses, same conclusion). Keep the
            # renamed source theorem as a helper lemma inside a module-derived namespace,
            # then emit exactly one final theorem matching the target statement.
            pat = re.compile(
                r"(?<![\w.])theorem\s+" + re.escape(target_module) + r"\s*:.*?:=\s*by\b.*\Z",
                re.S,
            )
            m = pat.search(candidate)
            if not m:
                return Detection("", source_module, 0.0, strategy, False, None, "cannot locate theorem for wrapping", candidate)
            helper_ns = target_module + "_aux"
            helper_lemma = f"lemma adapted_stronger :{stmt} := by{proof_tail}"
            wrapper = (
                f"namespace {helper_ns}\n"
                f"{helper_lemma}\n"
                f"end {helper_ns}\n\n"
                f"theorem {target_module} : {target_stmt} := by\n"
                f"  intros\n"
                f"  first\n"
                f"  | exact {helper_ns}.adapted_stronger\n"
                f"  | apply {helper_ns}.adapted_stronger <;> assumption\n"
                f"  | (have h := {helper_ns}.adapted_stronger; first | exact h | (apply h <;> assumption))\n"
            )
            candidate = candidate[:m.start()] + wrapper
        else:
            candidate = _replace_final_theorem(candidate, target_module, target_stmt, proof_tail)

    try:
        digest = validate.validate(target_gap, candidate.encode("utf-8"))
    except validate.InvalidCandidate as e:
        return Detection("", source_module, 0.0, strategy, False, None, str(e), candidate)
    return Detection("", source_module, 0.0, strategy, True, digest, None, candidate)


def detect_and_adapt(db, target_gap: dict, *, limit: int = 8, source_text: str | None = None, source_module: str | None = None) -> list[Detection]:
    target_stmt = target_gap["statement"]
    target_module = target_gap["module"]
    results: list[Detection] = []

    if source_text is not None:
        mod = source_module
        if mod is None:
            m = re.search(r"(?m)^theorem\s+(PEqualNP\.[A-Za-z0-9_.]+)\s*:", source_text)
            mod = m.group(1) if m else target_module
        strat = "exact" if mod == target_module else "module_rename"
        r = adapt_exact_module(source_text, target_gap, source_module=mod)
        results.append(Detection(path="<source>", module=mod, score=1.0, strategy=r.strategy,
                                 ok=r.ok, sha256=(r.details or {}).get("sha256"), error=(r.details or {}).get("error"), candidate=r.candidate))
        return results

    matches = corpus.search(db, target_stmt, target_gap.get("imports") or [], limit=limit)
    for m in matches:
        src_module = m["module"]
        src_stmt = m["statement"]
        strat = _is_stronger_or_equal(src_stmt, target_stmt)
        if strat is None:
            # still try module rename adaptation if same conclusion shape
            hint = m.get("structural_hint") or {}
            if hint.get("same_conclusion_shape"):
                strat = "conclusion_shape"
            else:
                continue
        src = db.execute("select source from proof where path=?", (m["path"],)).fetchone()
        if not src:
            continue
        det = _instantiate_candidate(src[0], src_module, target_gap, strat)
        det.path = m["path"]
        det.module = src_module
        det.score = m["score"]
        det.strategy = strat
        results.append(det)
    results.sort(key=lambda d: (not d.ok, -d.score, d.path))
    return results
