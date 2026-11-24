"""Index checked upstream proof sources, without executing them."""
import json
import math
from pathlib import Path
import re
import sqlite3
import subprocess

from .. import config, gitctl

TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9'.]*")
PROOF = re.compile(r"(?m)^theorem PEqualNP\.Outside\.[A-Za-z0-9_]+\s*:")
TACTICS = re.compile(r"\b(?:decide|fin_cases|interval_cases|simp|omega|norm_num|ring|aesop|exact|linarith|nlinarith|grind|bv_decide)\b")


def terms(s):
    return {x.lower() for t in TOKEN.findall(s) for x in [t, t.split(".")[-1]]
            if len(x) > 2 and not x.startswith("L_meta_")}


def statement(source):
    matches = list(PROOF.finditer(source))
    if not matches:
        return ""
    tail = source[matches[-1].end():]
    return re.split(r":=\s*by\b|:=\s*\n\s*[A-Za-z_]", tail, maxsplit=1)[0].strip()


def open_index():
    path = Path(config.CACHE_DIR, "proof-corpus.sqlite")
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.execute("create table if not exists proof(path text primary key, blob text, statement text, source text, tactics text, imports text)")
    db.execute("create table if not exists metadata(key text primary key, value text)")
    return db


def update(db, mirror=gitctl.MIRROR, revision="refs/remotes/upstream/main"):
    def git(*args):
        return subprocess.check_output(["git", "--git-dir=" + mirror, *args], timeout=60)
    sha = git("rev-parse", revision).decode().strip()
    old = db.execute("select value from metadata where key='revision'").fetchone()
    version = db.execute("select value from metadata where key='index_version'").fetchone()
    if old and old[0] == sha and version == ("2",):
        return sha
    rows = {}
    for line in git("ls-tree", "-r", sha, "lean/PEqualNP/Outside").decode().splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, blob = meta.split()
        if kind == "blob" and mode == "100644" and path.endswith(".lean"):
            rows[path] = blob
    known = dict(db.execute("select path,blob from proof")) if version == ("2",) else {}
    with db:
        if version != ("2",):
            db.execute("delete from proof")
        for path, blob in rows.items():
            if known.get(path) == blob:
                continue
            src = git("cat-file", "blob", blob)
            db.execute("delete from proof where path=?", (path,))
            if len(src) > config.MAX_FILE_BYTES:
                continue
            text = src.decode("utf-8", "replace")
            if re.search(r"[\u0400-\u04ff]", text):
                continue
            stmt = statement(text)
            if not stmt:
                continue
            imports = re.findall(r"(?m)^import ([A-Za-z0-9_.]+)$", text)
            db.execute("insert or replace into proof values(?,?,?,?,?,?)",
                       (path, blob, stmt, text, json.dumps(sorted(set(TACTICS.findall(text)))), json.dumps(imports)))
        for path in set(known) - set(rows):
            db.execute("delete from proof where path=?", (path,))
        db.execute("insert or replace into metadata values('revision',?)", (sha,))
        db.execute("insert or replace into metadata values('index_version','2')")
    return sha


def shape(s):
    """Heuristic skeleton, NOT a semantic implication or alpha-equivalence test."""
    s = re.sub(r"\((\d+) : ℕ\)", r"\1", s)
    s = s.replace("Bool.false", "false").replace("Bool.true", "true")
    s = re.sub(r"\b(x\d+|[a-z]|[CDGH]|h[a-z0-9]+)\b", "V", s)
    return re.sub(r"[()\s]", "", s)


def hypotheses(s):
    parts = []
    depth = 0
    start = 0
    for i,c in enumerate(s):
        if c in "([{⟨":
            depth += 1
        elif c in ")]}⟩":
            depth -= 1
        elif c == "→" and depth == 0:
            parts.append(s[start:i])
            start = i+1
    return parts, s[start:]


def structural_hint(query, stmt):
    qh, qc = hypotheses(query)
    sh, sc = hypotheses(stmt)
    # Variables are intentionally relaxed, so even a perfect score is only a
    # suggestion to instantiate and verify the actual theorem.
    haystack = shape(query)
    matched = sum(bool(shape(h)) and shape(h) in haystack for h in sh)
    same = bool(shape(qc)) and shape(qc) == shape(sc)
    return {"same_conclusion_shape": same, "hypotheses_matched": matched,
            "hypotheses_total": len(sh)}


def search(db, query, allowed=(), limit=8):
    q = terms(query)
    rows = list(db.execute("select path,blob,statement,tactics,imports from proof"))
    doc_terms = [terms(row[2]) for row in rows]
    freq = {t: sum(t in d for d in doc_terms) for t in q}
    def score(d):
        return sum(math.log((len(rows)+1)/(freq[t]+1))+1 for t in q & d) / math.sqrt(max(1,len(d)))
    found = []
    for row, d in zip(rows, doc_terms):
        rank = score(d)
        path, blob, stmt, tactics, imports = row
        hint = structural_hint(query, stmt)
        if rank <= 0 and not hint["same_conclusion_shape"]:
            continue
        rank += (8 if hint["same_conclusion_shape"] else 0)
        if hint["hypotheses_total"]:
            rank += 2 * hint["hypotheses_matched"] / hint["hypotheses_total"]
        module = path.removeprefix("lean/").removesuffix(".lean").replace("/", ".")
        found.append({"path": path, "blob": blob, "module": module,
                      "score": round(rank, 4), "statement": stmt, "structural_hint": hint,
                      "tactics": json.loads(tactics), "imports": json.loads(imports),
                      "direct_import_allowed": module in allowed})
    return sorted(found, key=lambda r: (-r["score"], r["path"]))[:limit]
