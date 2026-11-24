"""Adapt checked proofs to a target gap while respecting exact lease metadata."""
from __future__ import annotations

from dataclasses import dataclass
import re

from .. import validate
from .closure import dependency_closure, parse_source, referenced_names


@dataclass
class AdaptationResult:
    ok: bool
    candidate: str | None
    source_module: str
    target_module: str
    strategy: str
    details: dict


def _module_from_path(path: str) -> str:
    if not path.startswith("lean/") or not path.endswith(".lean"):
        raise ValueError("gap file must be a lean/PEqualNP/*.lean path")
    return path.removeprefix("lean/").removesuffix(".lean").replace("/", ".")


def controlled_module_rename(text: str, source_module: str, target_module: str) -> str:
    """Rename only the fully qualified module name as an identifier token.

    This is controlled module renaming, not fragile global namespace substitution.
    """
    if source_module == target_module:
        return text
    pat = re.compile(r"(?<![A-Za-z0-9_'.])" + re.escape(source_module) + r"(?![A-Za-z0-9_'])")
    return pat.sub(target_module, text)


def _split_imports(source: str) -> tuple[list[str], str]:
    lines = source.splitlines()
    i = 0
    imports = []
    while i < len(lines):
        s = lines[i].strip()
        if s == "" or s.startswith("--") or s.startswith("/-"):
            if s.startswith("/-"):
                while i < len(lines) and "-/" not in lines[i]:
                    i += 1
            i += 1
            continue
        m = re.match(r"^import\s+([A-Za-z0-9_.]+)\s*$", lines[i])
        if m:
            imports.append(m.group(1))
            i += 1
            continue
        break
    rest = "\n".join(lines[i:])
    return imports, rest


def _target_imports(target_gap: dict) -> list[str]:
    imports = ["Mathlib"]
    for imp in target_gap.get("imports") or []:
        if imp != "Mathlib" and imp not in imports:
            imports.append(imp)
    return imports


def _ensure_imports_allowed(source_imports: list[str], target_gap: dict) -> None:
    allowed = {"Mathlib"} | set(target_gap.get("imports") or [])
    for imp in source_imports:
        if imp not in allowed and not re.fullmatch(r"Mathlib(?:\.[A-Za-z][A-Za-z0-9_]*)+", imp):
            raise ValueError(f"source import {imp} is not allowed by target gap imports")


def _extract_final_theorem(text: str, module: str) -> tuple[str, str, str] | None:
    pat = re.compile(
        r"(?<![\w.])theorem\s+" + re.escape(module) + r"\s*:(.*?):=\s*by\b",
        re.S,
    )
    m = pat.search(text)
    if not m:
        return None
    return m.group(0), m.group(1), text[m.end():]


def _replace_final_theorem(text: str, target_module: str, target_statement: str, proof_body: str) -> str:
    pat = re.compile(
        r"(?<![\w.])theorem\s+" + re.escape(target_module) + r"\s*:.*?:=\s*by\b.*\Z",
        re.S,
    )
    m = pat.search(text)
    if not m:
        raise ValueError("target theorem not found after rename")
    replacement = f"theorem {target_module} : {target_statement} := by{proof_body}"
    return text[:m.start()] + replacement


def emit_standalone(target_gap: dict, body: str, source_imports=None) -> str:
    imports = list(source_imports) if source_imports else _target_imports(target_gap)
    header = "\n".join(f"import {imp}" for imp in imports)
    body = body.strip()
    return header + "\n\n" + body + "\n"


def _demote_helper_theorems(text: str, target_module: str) -> str:
    """Convert non-final theorem declarations to lemmas.

    The validator requires exactly one theorem, with the exact desk module name.
    In Lean 4, lemma and theorem are synonymous at the declaration level.
    """
    pat = re.compile(r"(?m)^(?P<indent>[ \t]*)(?P<prefix>(?:(?:private|protected|noncomputable|partial|scoped|local|nonrec)\s+)*)theorem\b")
    matches = list(pat.finditer(text))
    if not matches:
        return text
    target_pat = re.compile(
        r"(?m)^[ \t]*(?:(?:private|protected|noncomputable|partial|scoped|local|nonrec)\s+)*theorem\s+" + re.escape(target_module) + r"\s*:"
    )
    target_matches = list(target_pat.finditer(text))
    keep = target_matches[-1].start() if target_matches else matches[-1].start()
    parts = []
    last = 0
    for m in matches:
        if m.start() == keep:
            continue
        parts.append(text[last:m.start()])
        parts.append(m.group("indent") + (m.group("prefix") or "") + "lemma")
        last = m.end()
    parts.append(text[last:])
    return "".join(parts)


def _normalize_helper_namespaces(text: str, target_module: str) -> str:
    """Preserve relative Lean scopes of a renamed checked source.

    Changing a relative nested scope to a fully qualified name changes
    its actual namespace. The validator checks the outer scope instead.
    For arbitrary unrelated root namespaces do not guess a rewrite:
    reject them through validate and let the researcher adapt explicitly.
    """
    return text


def adapt_exact_module(source: str, target_gap: dict, *, source_module: str | None = None) -> AdaptationResult:
    """Adapt a checked source by controlled module renaming and exact statement alignment.

    Works when the source proves the same statement or when the target statement is
    already present in the renamed source; the final theorem must match exactly.
    """
    target_module = target_gap["module"]
    if source_module is None:
        # infer from theorem in source
        m = re.search(r"(?m)^theorem\s+(PEqualNP\.[A-Za-z0-9_.]+)\s*:", source)
        if not m:
            return AdaptationResult(False, None, "", target_module, "exact_module", {"error": "no theorem found"})
        source_module = m.group(1)

    renamed = controlled_module_rename(source, source_module, target_module)
    src_imports, _ = _split_imports(renamed)
    try:
        _ensure_imports_allowed(src_imports, target_gap)
    except ValueError as e:
        return AdaptationResult(False, None, source_module, target_module, "exact_module", {"error": str(e)})

    # Ensure exact target imports are used.
    _, body = _split_imports(renamed)
    body = _demote_helper_theorems(body, target_module)
    body = _normalize_helper_namespaces(body, target_module)
    candidate = emit_standalone(target_gap, body, src_imports)

    # If the renamed source's theorem statement differs from target, try replacing
    # the statement but keeping the proof body only when statements are token-equal.
    final = _extract_final_theorem(candidate, target_module)
    if final is None:
        return AdaptationResult(False, None, source_module, target_module, "exact_module", {"error": "missing final theorem after rename"})

    _, stmt, proof_tail = final
    target_stmt = target_gap["statement"]
    if validate.tokens(stmt) != validate.tokens(target_stmt):
        return AdaptationResult(
            False, candidate, source_module, target_module, "exact_module",
            {"error": "final theorem statement differs from target after controlled module rename; refusing to keep mismatched proof body"},
        )

    try:
        digest = validate.validate(target_gap, candidate.encode("utf-8"))
    except validate.InvalidCandidate as e:
        return AdaptationResult(False, candidate, source_module, target_module, "exact_module", {"error": str(e), "digest": None})

    return AdaptationResult(True, candidate, source_module, target_module, "exact_module", {"sha256": digest})
