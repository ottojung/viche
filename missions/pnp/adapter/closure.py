"""Lean declaration dependency closure extraction.

This is source-level and heuristic by design: it extracts a conservative
dependency closure of named declarations from a Lean source file. It does NOT
perform global namespace substitution; module renaming is a separate, controlled
operation in adapt.py.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

DECL_KEYWORDS = (
    "theorem", "lemma", "def", "abbrev", "noncomputable def",
    "instance", "structure", "class", "inductive", "opaque",
)

# A declaration starts at column 0 or after only whitespace in a namespace/section,
# but we parse conservatively: lines whose stripped form begins with a decl keyword
# or attribute+decl keyword.
DECL_START = re.compile(
    r"^(?P<indent>[ \t]*)(?P<attrs>(?:@\[.*?\][ \t]*)*)"
    r"(?P<kw>theorem|lemma|def|abbrev|noncomputable\s+def|instance|structure|class|inductive|opaque)\b"
    r"(?:[ \t]+(?P<name>[A-Za-z_][A-Za-z0-9_'.]*))?"
)

NAMESPACE_START = re.compile(r"^(?P<indent>[ \t]*)namespace[ \t]+([A-Za-z_][A-Za-z0-9_'.]*)[ \t]*$")
NAMESPACE_END = re.compile(r"^(?P<indent>[ \t]*)end[ \t]+([A-Za-z_][A-Za-z0-9_'.]*)[ \t]*$")
SECTION_START = re.compile(r"^(?P<indent>[ \t]*)section(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")
SECTION_END = re.compile(r"^(?P<indent>[ \t]*)end(?:[ \t]+[A-Za-z_][A-Za-z0-9_'.]*)?[ \t]*$")
# Commands that affect scope/context and should be retained when relevant.
SCOPE_COMMAND = re.compile(
    r"^(?P<indent>[ \t]*)(?:variable\b|open\b|universe\b|set_option\b|attribute\b|local\b|export\b|omit\b|include\b)"
)

IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_'.]*")


@dataclass
class Declaration:
    name: str
    start: int  # line index
    end: int    # exclusive line index
    kind: str
    text: str
    namespace: tuple[str, ...]


@dataclass
class SourceModel:
    lines: list[str]
    declarations: list[Declaration]
    by_name: dict[str, Declaration]
    preamble_end: int  # line index where first namespace/decl starts after imports


def _line_starts_decl(line: str):
    m = DECL_START.match(line)
    return m


def parse_source(source: str) -> SourceModel:
    lines = source.splitlines()
    declarations: list[Declaration] = []
    ns_stack: list[str] = []
    section_depth = 0

    # Find preamble end: after imports and blank lines.
    preamble_end = 0
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s == "" or s.startswith("import ") or s.startswith("--") or s.startswith("/-"):
            if s.startswith("/-"):
                # skip block comment
                while i < len(lines) and "-/" not in lines[i]:
                    i += 1
            i += 1
            continue
        preamble_end = i
        break
    else:
        preamble_end = len(lines)

    i = 0
    while i < len(lines):
        line = lines[i]
        m_ns = NAMESPACE_START.match(line)
        if m_ns:
            ns_stack.append(m_ns.group(2))
            i += 1
            continue
        m_ne = NAMESPACE_END.match(line)
        if m_ne:
            name = m_ne.group(2)
            if ns_stack and ns_stack[-1] == name:
                ns_stack.pop()
            elif name in ns_stack:
                while ns_stack and ns_stack[-1] != name:
                    ns_stack.pop()
                if ns_stack:
                    ns_stack.pop()
            i += 1
            continue
        m_sec = SECTION_START.match(line)
        if m_sec:
            section_depth += 1
            i += 1
            continue
        m_se = SECTION_END.match(line)
        if m_se and section_depth > 0 and not NAMESPACE_END.match(line):
            # `end` without a namespace name may close section
            section_depth -= 1
            i += 1
            continue

        m_decl = _line_starts_decl(line)
        if m_decl:
            name = m_decl.group("name")
            kind = re.sub(r"\s+", " ", m_decl.group("kw"))
            start = i
            # include preceding attributes/doc comments attached to decl
            j = start - 1
            while j >= 0:
                prev = lines[j].strip()
                if prev.startswith("@[") or prev.startswith("/--") or prev.startswith("/-!") or prev.startswith("--"):
                    if prev.startswith("/-"):
                        k = j
                        while k >= 0 and "/-" not in lines[k]:
                            k -= 1
                        j = k - 1
                        continue
                    start = j
                    j -= 1
                    continue
                break
            # find end: next decl start at same or lower structural level, or namespace/section end
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if NAMESPACE_START.match(nxt) or NAMESPACE_END.match(nxt) or SECTION_START.match(nxt):
                    # section end is `end` or `end <name>` - ambiguous; treat named end matching ns as boundary
                    if SECTION_START.match(nxt):
                        break
                    if NAMESPACE_START.match(nxt) or NAMESPACE_END.match(nxt):
                        break
                if _line_starts_decl(nxt):
                    break
                # A bare `end` can close section; be conservative
                if re.match(r"^[ \t]*end[ \t]*$", nxt) and section_depth > 0:
                    break
                i += 1
            text = "\n".join(lines[start:i])
            if name:
                decl = Declaration(name=name, start=start, end=i, kind=kind, text=text, namespace=tuple(ns_stack))
                declarations.append(decl)
            continue
        i += 1

    by_name: dict[str, Declaration] = {}
    for d in declarations:
        by_name[d.name] = d
        qualified = ".".join((*d.namespace, d.name)) if d.namespace else d.name
        by_name[qualified] = d
        # also register with full module-like paths seen in text
        if d.namespace:
            by_name[".".join(d.namespace) + "." + d.name] = d
    return SourceModel(lines=lines, declarations=declarations, by_name=by_name, preamble_end=preamble_end)


def referenced_names(text: str) -> set[str]:
    # Remove comments/strings crudely to reduce noise.
    cleaned = re.sub(r"/-.*?-/", " ", text, flags=re.S)
    cleaned = re.sub(r"--[^\n]*", " ", cleaned)
    cleaned = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', " ", cleaned)
    return set(IDENT.findall(cleaned))


def dependency_closure(model: SourceModel, target: str) -> list[Declaration]:
    """Return declarations in source order forming a conservative transitive closure."""
    target_decl = model.by_name.get(target)
    if target_decl is None:
        # try suffix match
        for d in model.declarations:
            qualified = ".".join((*d.namespace, d.name))
            if qualified == target or d.name == target or qualified.endswith("." + target):
                target_decl = d
                break
    if target_decl is None:
        raise ValueError(f"target declaration not found: {target}")

    # Build lookup by short name and qualified names.
    defs: dict[str, Declaration] = {}
    for d in model.declarations:
        defs[d.name] = d
        q = ".".join((*d.namespace, d.name))
        defs[q] = d
        # also suffixes for nested namespace refs
        parts = q.split(".")
        for k in range(1, len(parts)):
            defs[".".join(parts[k:])] = d

    wanted: set[int] = set()
    queue = [target_decl]
    while queue:
        d = queue.pop()
        key = id(d)
        if key in wanted:
            continue
        wanted.add(key)
        refs = referenced_names(d.text)
        for ref in refs:
            dep = defs.get(ref)
            if dep is None:
                # try progressively shorter suffixes / longer prefixes are already in defs
                continue
            if id(dep) not in wanted:
                queue.append(dep)
    # Preserve source order.
    return [d for d in model.declarations if id(d) in wanted]
