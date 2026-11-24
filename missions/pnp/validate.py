"""Deterministic, offline validation of a candidate Lean file.

A candidate is data, never code: nothing here imports, executes or trusts it.
Fail closed: any ambiguity is a rejection.
"""
import re
import unicodedata

from . import config

BANNED_DECLARATIONS = (
    "initialize", "macro", "syntax", "notation", "elab", "native_decide",
)
BANNED_AXIOM = re.compile(r"(?<![\w.])axiom\b")
BANNED_SORRY = re.compile(r"(?<![\w.])sorry\b")
HASH_COMMAND = re.compile(r"(?m)^\s*#")
SET_OPTION = re.compile(
    r"(?m)^\s*set_option\s+([A-Za-z.]+)\s+(\d+)\s+in\s*$")
ANY_OPTION = re.compile(r"(?<![\w.])set_option\s+([A-Za-z.]+)\b")
ALLOWED_OPTIONS = {
    "maxRecDepth", "maxHeartbeats", "synthInstance.maxSize",
    "synthInstance.maxHeartbeats",
}
IMPORT_LINE = re.compile(r"^import\s+([A-Za-z0-9_.]+)\s*$")
TOKEN = re.compile(r"[A-Za-z0-9_]+|[^\sA-Za-z0-9_]")


class InvalidCandidate(Exception):
    pass


def _reject(msg):
    raise InvalidCandidate(msg)


def strip_comments(text):
    """Remove -- line comments and {-- -} block comments, preserving lines."""
    out = []
    i = 0
    n = len(text)
    block = False
    while i < n:
        if block:
            if text.startswith("-}", i):
                block = False
                i += 2
                continue
            out.append("\n" if text[i] == "\n" else " ")
            i += 1
            continue
        if text.startswith("{-", i):
            block = True
            i += 2
            continue
        if text.startswith("--", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        out.append(text[i])
        i += 1
    if block:
        _reject("unterminated block comment")
    return "".join(out)


def comment_text(text):
    """Collect comment bodies so banned words are rejected there too."""
    found = []
    for m in re.finditer(r"--[^\n]*|\{-.*?-\}", text, re.S):
        found.append(m.group(0))
    return "\n".join(found)


def tokens(text):
    return TOKEN.findall(unicodedata.normalize("NFKC", text))


def validate(gap, candidate_bytes):
    """Validate byte content against desk metadata.  Return sha256 hex.

    `gap` must contain id, file, module, statement and imports, all obtained
    independently from the desk/public repository (never from the candidate).
    """
    if not isinstance(gap, dict):
        _reject("gap metadata is not an object")
    gid = gap.get("id")
    if not isinstance(gid, str) or not config.GAP_ID_RE.match(gid):
        _reject("gap id fails the published grammar")
    path = gap.get("file")
    if not isinstance(path, str) or not path.startswith("lean/PEqualNP/"):
        _reject("desk file path is not a PEqualNP Lean file")
    if not path.endswith(".lean") or not re.match(
            r"^lean/PEqualNP/[A-Za-z0-9_/]+\.lean$", path):
        _reject("illegal Lean file path")
    module = gap.get("module")
    if not isinstance(module, str) or not re.match(
            r"^PEqualNP\.[A-Za-z0-9_.]+$", module):
        _reject("gap module is not a PEqualNP module")
    statement = gap.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        _reject("missing desk statement")
    imports = gap.get("imports") or []
    if not isinstance(imports, (list, tuple)):
        _reject("gap imports is not a list")
    for imp in imports:
        if not isinstance(imp, str) or not re.match(
                r"^(Mathlib|[A-Za-z][A-Za-z0-9_.]*)$", imp):
            _reject("illegal project import in desk metadata")

    if not isinstance(candidate_bytes, (bytes, bytearray)):
        _reject("candidate is not raw bytes")
    if len(candidate_bytes) > config.MAX_FILE_BYTES:
        _reject("candidate exceeds 512 KiB")
    try:
        text = bytes(candidate_bytes).decode("utf-8")
    except UnicodeDecodeError:
        _reject("candidate is not UTF-8")
    if "\x00" in text or '"' in text:
        _reject("candidate has NUL or double quotes")
    if not text.strip():
        _reject("empty candidate")

    code = strip_comments(text)
    comments = comment_text(text)
    for word in BANNED_DECLARATIONS + ("sorry", "axiom"):
        if re.search(r"(?<![\w.])%s\b" % re.escape(word), comments):
            _reject("banned word %s in comment" % word)
    if BANNED_SORRY.search(code) or BANNED_SORRY.search(comments):
        _reject("sorry is forbidden")
    if BANNED_AXIOM.search(code):
        _reject("new axiom is forbidden")
    if "native_decide" in code or HASH_COMMAND.search(code):
        _reject("command/native_decide is forbidden")
    for word in BANNED_DECLARATIONS:
        if re.search(r"(?<![\w.])%s\b" % re.escape(word), code):
            _reject("forbidden declaration: " + word)
    for m in ANY_OPTION.finditer(code):
        if m.group(1) not in ALLOWED_OPTIONS:
            _reject("unapproved option: " + m.group(1))
    valid_options = len(ANY_OPTION.findall(code)) == len(SET_OPTION.findall(code))
    if not valid_options:
        _reject("set_option must be '<allowed name> <number> in' on its own line")
    for m in re.finditer(r"@\[([^\]]*)\]", code):
        attrs = [a.strip() for a in m.group(1).split(",")]
        for a in attrs:
            if a not in ("simp", "local simp"):
                _reject("unapproved attribute: " + a)
    if re.search(r"(?m)^\s*(attribute|instance)\b", code):
        _reject("attribute/instance command is forbidden")

    lines = code.splitlines()
    n = 0
    while n < len(lines) and not lines[n].strip():
        n += 1
    seen_imports = []
    while n < len(lines):
        m = IMPORT_LINE.match(lines[n])
        if not m:
            break
        seen_imports.append(m.group(1))
        n += 1
    if not seen_imports:
        _reject("at least one allowed import is required")
    allowed_imports = {"Mathlib"} | set(imports)
    for imp in seen_imports:
        if imp not in allowed_imports and not re.fullmatch(r"Mathlib(?:\.[A-Za-z][A-Za-z0-9_]*)+", imp):
            _reject("unapproved import: " + imp)
    rest = "\n".join(lines[n:])
    if re.search(r"(?<![\w.])import\b", rest):
        _reject("import after the import block")
    if len(re.findall(r"(?<![\w.])theorem\b", code)) != 1:
        _reject("exactly one theorem is required")

    pat = re.compile(r"(?<![\w.])theorem\s+" + re.escape(module) +
                     r"\s*:(.*?):=\s*by\b", re.S)
    m = pat.search(code)
    if not m:
        _reject("theorem with the exact desk module name is missing")
    if tokens(m.group(1)) != tokens(statement):
        _reject("theorem statement differs from the posted statement")

    # Upstream permits relative nested namespaces, but the root must
    # belong to the module. Lean namespace names are relative, so forcing
    # every nested name to be fully qualified duplicates the root.
    stack = []
    seen_theorem = False
    own = lambda ns: (ns == module or ns.startswith(module + ".")
                     or ns == module + "_aux" or ns.startswith(module + "_aux."))
    for line in lines[n:]:
        if not line.strip():
            continue
        if seen_theorem:
            if re.match(r"^\s*(namespace|section|end|mutual)\b", line):
                _reject("scope command after theorem")
            continue
        scope = re.match(r"^(namespace|section|end|mutual)(?:[ \t]+([A-Za-z_][A-Za-z0-9_.]*))?[ \t]*$", line)
        if scope:
            kind, name = scope.groups()
            if kind == "namespace":
                if not name or name.startswith("_root_") or (not stack and not own(name)):
                    _reject("helper namespace is not derived from the module")
                stack.append((kind, name))
            elif kind in ("section", "mutual"):
                if not stack or (kind == "mutual" and name):
                    _reject("scope outside helper namespace")
                stack.append((kind, name))
            else:
                if not stack or stack[-1][1] != name:
                    _reject("scope end does not match")
                stack.pop()
            continue
        if re.match(r"^\s*(namespace|section|end|mutual)\b",line):
            _reject("scope commands must stand alone at column zero")
        if stack:
            continue
        if re.match(r"^theorem\s+" + re.escape(module) + r"\s*:",line):
            seen_theorem = True
            continue
        if line.startswith("open ") or SET_OPTION.fullmatch(line):
            continue
        _reject("declaration or command outside helper namespace")
    if stack or not seen_theorem:
        _reject("unclosed helper scope or theorem not at top level")
    tail = code[m.end():]
    if re.search(r"(?<![\w.])(lemma|theorem|def|abbrev|axiom|namespace)\b",
                 tail):
        _reject("the theorem must be the last declaration")

    import hashlib
    return hashlib.sha256(candidate_bytes).hexdigest()
