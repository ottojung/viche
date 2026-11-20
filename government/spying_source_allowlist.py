#!/usr/bin/env python3
"""Act 32 clause 4 / amendment F -- enforced, fail-closed Spying source allowlist.

This is an INDEPENDENT validation module and launch preflight. It does not
activate any office, publish anything, contact private repositories, read
credentials or start any agent. It converts caller-supplied source claims into
an ALLOW verdict only when every claim is independently resolved against
authoritative data and pinned in a committed allowlist.

A caller-supplied ``antonina:`` or ``github:public:`` prefix is NEVER evidence.
The three permitted classes are:

  * antonina:<sha256:message-id>  -- an Antonina *message* whose exact author is
    `Vitalik`, resolved from authoritative board data and pinned by id, issue,
    author and body hash;
  * github:public:<owner>/<repo>#<ref> -- attributable public GitHub activity
    in an expressly allowlisted public repo, with an attributable actor and
    commit/ref hash, bound to a pinned Founder authorization;
  * authorized:<source-id> / project:<source-id> -- an expressly authorized
    project source pinned to an exact-author Vitalik authorization message,
    a scope, a content hash and a bounded term.

Every source and every statement is additionally screened for secret-bearing
content, private-repository references, prompt-injection text, copied or
non-independent conclusions, stale/forged evidence, and the forbidden
transformation of an inference into authorization or a NEEDS-FOUNDER line.

Design guarantees:
  * fail closed: any missing/malformed/unreadable input means DENY, never
    "empty", "zero" or "allowed";
  * observation, inference and corrected inference are distinct and an
    inference can never become an authorization, ballot, mandate, spending
    request or NEEDS-FOUNDER item;
  * no matched secret value is ever emitted -- only rule names;
  * unknown or missing board APIs are reported honestly as gaps;
  * board reads use bounded pagination (a pinned older message is not lost off
    page 1), and an unreadable required page fails closed.

HONEST LIMIT / NOT A SANDBOX: this is a source-validation and launch gate, not
access confinement. On the shared same-UID host an unconstrained coding agent
can still read arbitrary files after a successful preflight; this module never
claims global access control. The prompt-injection screen is a heuristic deny
screen, not a proof of safety; the no-authority / no-NEEDS-FOUNDER boundary is
enforced structurally on statement fields and is independent of source text.
Every claimed inference or outcome must be re-validated at publication time
against its ACTUAL cited source set through validate_bundle()/the `publish`
subcommand -- a dispatch preflight alone is not a publication-time boundary.

Standard library only. Python 3.8+.
"""
import argparse
import datetime as _dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

SCHEMA = "viche-spying-source-verdict-v1"
ALLOWLIST_SCHEMA = "viche-spying-source-allowlist-v1"
FOUNDER = "Vitalik"
DEFAULT_ALLOWLIST = "records/knowledge/spying-source-allowlist.json"
FUTURE_SKEW_SECONDS = 300
BOARD_TIMEOUT_SECONDS = 15
MAX_BOARD_PAGES = 5          # bounded: no unbounded board scan
BOARD_PAGE_SIZE = 50         # Antonina board show pages hold up to 50 messages

# Rule names only are ever returned; matched text is never retained or logged.
_SECRET_PATTERNS = {
    "pem-private-key": r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----",
    "github-token": r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{24,})\b",
    "openai-token": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
    "cloud-access-key": r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b",
    "slack-token": r"\bxox[baprs]-[A-Za-z0-9-]{24,}\b",
    "bearer-credential": r"(?i)\bBearer\s+[-._~+/A-Za-z0-9]{22,}\b",
    "secret-assignment": (
        r"(?i)\b(?:password|passphrase|api[_-]?key|client[_-]?secret|"
        r"access[_-]?token|refresh[_-]?token|ANTONINA_TOKEN|OPENAI_API_KEY)"
        r"\s*[:=]\s*[\"']?([A-Za-z0-9_+/=.-]{18,})"
    ),
    "ssh-private-path": r"(?i)(?:~|/home/[^/\s]+)/\.ssh/|/etc/shadow\b|\.env\b",
}
_PRIVATE_PATTERNS = {
    "private-repo-scheme": r"(?i)(git@github\.com:|ssh://git@|git://)",
    "private-repo-path": r"(?i)/(?:private|internal|secret|confidential)(?:/|\b)|[-_](?:private|internal|secret)\b",
    "url-embedded-credential": r"https?://[^/\s:@]+:[^/\s@]+@",
    "private-flag": r"(?i)\"?(?:is_private|private)\"?\s*[:=]\s*true",
}
_INJECTION_PATTERNS = {
    "ignore-prior-instructions": r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|rules|prompts)\b",
    "disregard-rules": r"(?i)\bdisregard\s+(?:the\s+)?(?:above|previous|system|safety)\b",
    "role-override": r"(?i)\byou\s+are\s+now\b|\bact\s+as\s+(?:the\s+)?(?:founder|administrator|system)\b",
    "system-prompt-probe": r"(?i)\b(?:reveal|print|show)\s+(?:your\s+)?(?:system\s+)?prompt\b",
    "fake-founder-claim": r"(?i)\b(?:i\s+am\s+Vitalik|this\s+is\s+(?:the\s+)?founder(?:'s)?\s+(?:instruction|authorization)|founder\s+authorizes)\b",
    "needs-founder-marker": r"NEEDS-FOUNDER\s*:",
    "authority-override": r"(?i)\b(?:override|bypass)\s+(?:the\s+)?(?:allowlist|guard|gate|safety|constitution)\b",
}
_SECRETS = {name: re.compile(p) for name, p in _SECRET_PATTERNS.items()}
_PRIVATE = {name: re.compile(p) for name, p in _PRIVATE_PATTERNS.items()}
_INJECTION = {name: re.compile(p) for name, p in _INJECTION_PATTERNS.items()}

_STATEMENT_KINDS = ("observation", "inference", "corrected_inference")
_PROMOTION_KEYS = ("authorization", "authorizes", "authorized", "mandate",
                   "needs_founder", "ballot", "vote", "spending", "spend",
                   "scope_expansion", "enacts", "grants_authority")


class AllowlistError(Exception):
    pass


class BoardUnavailable(Exception):
    pass


def _sha256_hex(text):
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _scan(text, rules):
    """Return sorted rule NAMES that matched; never the matched value."""
    if not isinstance(text, str):
        return []
    return sorted(name for name, rx in rules.items() if rx.search(text))


def secret_rules(*fields):
    out = set()
    for f in fields:
        out.update(_scan(f, _SECRETS))
    return sorted(out)


def private_rules(*fields):
    out = set()
    for f in fields:
        out.update(_scan(f, _PRIVATE))
    return sorted(out)


def injection_rules(*fields):
    out = set()
    for f in fields:
        out.update(_scan(f, _INJECTION))
    return sorted(out)


def _evidence_text(evidence):
    """Flatten only scalar string fields of an evidence record for scanning."""
    if not isinstance(evidence, dict):
        return ""
    parts = []
    for key, val in evidence.items():
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, (list, tuple)):
            parts.extend(x for x in val if isinstance(x, str))
    return "\n".join(parts)


def load_allowlist(path, now=None):
    """Load and structurally validate the committed enforced allowlist."""
    now = time.time() if now is None else now
    p = Path(path)
    if not p.is_file():
        raise AllowlistError("allowlist file missing: " + str(p))
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise AllowlistError("allowlist unreadable/malformed: %s" % type(exc).__name__)
    if not isinstance(data, dict) or data.get("schema") != ALLOWLIST_SCHEMA:
        raise AllowlistError("allowlist schema mismatch")
    if not isinstance(data.get("antonina"), dict):
        raise AllowlistError("allowlist missing antonina section")
    if data["antonina"].get("founder_author") != FOUNDER:
        raise AllowlistError("allowlist founder_author is not exact Vitalik")
    if not isinstance(data["antonina"].get("messages"), dict):
        raise AllowlistError("allowlist missing pinned messages")
    if not isinstance(data.get("github_public"), dict) or not isinstance(
            data["github_public"].get("repos"), dict):
        raise AllowlistError("allowlist missing github_public repos")
    if not isinstance(data.get("project_sources"), dict) or not isinstance(
            data["project_sources"].get("sources"), dict):
        raise AllowlistError("allowlist missing project_sources")
    age = data.get("max_evidence_age_seconds")
    if not isinstance(age, int) or age <= 0 or age > 15552000:
        raise AllowlistError("invalid max_evidence_age_seconds")
    pages = data.get("max_board_pages", MAX_BOARD_PAGES)
    if not isinstance(pages, int) or pages <= 0 or pages > 10:
        raise AllowlistError("invalid max_board_pages")
    data["max_board_pages"] = pages
    eff = data.get("effective_from")
    exp = data.get("expires_at")
    if not isinstance(eff, (int, float)) or not isinstance(exp, (int, float)):
        raise AllowlistError("allowlist term missing")
    if not (eff <= now < exp) or exp - eff <= 0 or exp - eff > 15552000:
        raise AllowlistError("allowlist term not currently in force")
    # Every github repo and project source must itself cite a pinned Vitalik
    # message; an unpinned authorization is not an authorization.
    pinned = set(data["antonina"]["messages"])
    for entry in list(data["github_public"]["repos"].values()) + list(
            data["project_sources"]["sources"].values()):
        if not isinstance(entry, dict) or entry.get("authorized_by") not in pinned:
            raise AllowlistError("source cites an unpinned authorization")
        if data["antonina"]["messages"][entry["authorized_by"]].get("author") != FOUNDER:
            raise AllowlistError("authorization message author is not exact Vitalik")
    return data


class BoardResolver:
    """Resolve board issues to authoritative JSON. Errors never become emptiness."""

    def __init__(self, fetch=None, offline_json=None):
        self._fetch = fetch
        self._offline = offline_json

    def resolve(self, issue_id, max_pages=MAX_BOARD_PAGES):
        """Read a bounded number of board pages; merge by stable message id.

        A pinned older message may no longer be on page 1 of an active issue.
        We read up to `max_pages` pages, following the documented rule that a
        further page exists only when the current page is full (50 messages).
        An unreadable/malformed required page fails closed. The scan is bounded
        and ends as soon as it is complete -- it is never an unbounded crawl.
        """
        if not isinstance(issue_id, str) or not issue_id or "\n" in issue_id:
            raise BoardUnavailable("invalid issue id")
        if self._offline is not None:
            doc = self._offline.get(issue_id)
            if doc is None:
                raise BoardUnavailable("issue absent from offline board snapshot: " + issue_id)
            return doc
        if self._fetch is not None:
            return self._fetch(issue_id)
        # Default: read-only Antonina CLI. No credentials, no writes.
        if not isinstance(max_pages, int) or max_pages <= 0 or max_pages > 10:
            raise BoardUnavailable("invalid pagination cap")
        merged = []
        seen = set()
        base = None
        for page in range(1, max_pages + 1):
            try:
                proc = subprocess.run(
                    ["antonina", "board", "show", "--id", issue_id,
                     "--page", str(page), "--json"],
                    capture_output=True, text=True, timeout=BOARD_TIMEOUT_SECONDS,
                    check=False)
            except (OSError, subprocess.SubprocessError) as exc:
                raise BoardUnavailable("board CLI unavailable: %s" % type(exc).__name__)
            if proc.returncode != 0:
                raise BoardUnavailable("board CLI exit %s on page %d" %
                                       (proc.returncode, page))
            try:
                doc = json.loads(proc.stdout)
            except (ValueError, TypeError):
                raise BoardUnavailable("board JSON unparseable on page %d" % page)
            if not isinstance(doc, dict) or not isinstance(doc.get("messages"), list):
                raise BoardUnavailable("board JSON missing messages array on page %d" % page)
            if base is None:
                base = doc
            for msg in doc["messages"]:
                mid = msg.get("id") if isinstance(msg, dict) else None
                if isinstance(mid, str) and mid not in seen:
                    seen.add(mid)
                    merged.append(msg)
            if len(doc["messages"]) < BOARD_PAGE_SIZE:
                break  # last page, per the Antonina board contract
        result = dict(base or {})
        result["messages"] = merged
        return result

    def resolve_founder_message(self, pinned, max_pages=MAX_BOARD_PAGES):
        """Return the authoritative message for a pinned Founder message id."""
        doc = self.resolve(pinned["issue"], max_pages=max_pages)
        found = None
        for msg in doc.get("messages", []):
            if isinstance(msg, dict) and msg.get("id") == pinned.get("id"):
                found = msg
                break
        if found is None:
            raise BoardUnavailable("pinned message id not present on authoritative board")
        return found


def _parse_created_ts(created_at):
    """Parse an ISO-8601 Z timestamp to epoch, or None if invalid."""
    if not isinstance(created_at, str):
        return None
    try:
        dt = _dt.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        return None
    ts = dt.timestamp()
    return ts if ts >= 0 else None


def _parse_created(created_at, now):
    """Validate an ISO-8601 Z timestamp; reject unparseable or future-dated."""
    ts = _parse_created_ts(created_at)
    if ts is None or ts > now + FUTURE_SKEW_SECONDS:
        return False
    return True


def _check_timestamp(value, now, max_age):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "evidence_timestamp_missing"
    if value > now + FUTURE_SKEW_SECONDS:
        return "future_dated_evidence"
    if value < now - max_age:
        return "stale_evidence"
    return None


def _deny(code, detail=""):
    return {"decision": "DENY", "reasons": [{"code": code, "detail": detail}]}


def _allow(extra=None):
    result = {"decision": "ALLOW", "reasons": []}
    if extra:
        result.update(extra)
    return result


def _board_attestation(evidence, allowlist, resolver, now, max_pages):
    """Validate a publication attestation against real board provenance.

    Returns (None, epoch) on success, or (deny_code, "") on failure. The
    freshness check uses the authoritative board `createdAt`, not a caller
    string, so a caller cannot launder stale evidence by relabelling it.
    """
    attested_by = evidence.get("attested_by")
    pin = allowlist["antonina"]["messages"].get(attested_by)
    if not isinstance(pin, dict):
        return "publication_attestation_unpinned", ""
    try:
        msg = resolver.resolve_founder_message(
            {"id": attested_by, "issue": pin.get("issue")}, max_pages=max_pages)
    except BoardUnavailable as exc:
        return "board_unreadable", str(exc)
    if msg.get("author") != FOUNDER or msg.get("id") != attested_by:
        return "publication_attestation_not_vitalik", ""
    ts = _parse_created_ts(msg.get("createdAt"))
    if ts is None or ts > now + FUTURE_SKEW_SECONDS:
        return "stale_or_forged_publication_attestation", ""
    if ts < now - allowlist["max_evidence_age_seconds"]:
        return "stale_or_forged_publication_attestation", ""
    return None, ts


def validate_source(ref, evidence, allowlist, resolver, now):
    """Validate one caller-supplied source reference. Fail closed."""
    result = {}
    if not isinstance(ref, str) or ":" not in ref:
        return _deny("malformed_source_ref")
    cls, _, rest = ref.partition(":")
    evidence = evidence if isinstance(evidence, dict) else {}
    max_age = allowlist["max_evidence_age_seconds"]
    max_pages = allowlist.get("max_board_pages", MAX_BOARD_PAGES)
    ts_reason = _check_timestamp(evidence.get("captured_at"), now, max_age)
    text = _evidence_text(evidence)

    # Universal deny screens on every source regardless of class.
    sec = secret_rules(text)
    if sec:
        return _deny("secret_bearing_source", ",".join(sec))
    priv = private_rules(ref, text)
    if priv:
        return _deny("private_repo_reference", ",".join(priv))
    inj = injection_rules(text)
    if inj:
        return _deny("prompt_injection_in_source", ",".join(inj))
    if ts_reason:
        return _deny(ts_reason)

    if cls == "antonina":
        # 'antonina:' alone proves nothing. Require a pinned message id.
        pin = allowlist["antonina"]["messages"].get(rest)
        if not isinstance(pin, dict):
            return _deny("source_not_allowlisted")
        if pin.get("author") != FOUNDER:
            return _deny("pinned_author_not_exact_vitalik")
        try:
            msg = resolver.resolve_founder_message(
                {"id": rest, "issue": pin.get("issue")}, max_pages=max_pages)
        except BoardUnavailable as exc:
            return _deny("board_unreadable", str(exc))
        if msg.get("author") != FOUNDER or msg.get("id") != rest:
            return _deny("author_not_exact_vitalik")
        body = msg.get("body")
        if not isinstance(body, str) or not body:
            return _deny("board_message_invalid")
        if pin.get("body_sha256") and _sha256_hex(body) != pin["body_sha256"]:
            return _deny("body_hash_mismatch_forged_evidence")
        if not _parse_created(msg.get("createdAt"), now):
            return _deny("stale_or_forged_board_timestamp")
        body_sec = secret_rules(body)
        if body_sec:
            return _deny("secret_bearing_source", ",".join(body_sec))
        body_inj = injection_rules(body)
        if body_inj:
            return _deny("prompt_injection_in_source", ",".join(body_inj))
        result.update({"class": "antonina", "verified_author": FOUNDER,
                       "scope": pin.get("scope"), "issue": pin.get("issue"),
                       "body_sha256": _sha256_hex(body)})
        return _allow(result)

    if cls == "github":
        if not rest.startswith("public:"):
            return _deny("not_public_github_source")
        target = rest[len("public:"):]
        repo, sep, refpart = target.partition("#")
        if not sep or not repo or not refpart or "/" not in repo:
            return _deny("malformed_github_ref")
        if re.search(r"(?i)\.\.|^\.|/private|/internal", repo):
            return _deny("github_repo_out_of_scope")
        entry = allowlist["github_public"]["repos"].get(repo)
        if not isinstance(entry, dict):
            return _deny("github_repo_not_allowlisted")
        # Attributable public activity requires actor + commit/ref hash + https url.
        actor = evidence.get("actor")
        sha = evidence.get("commit_sha") or evidence.get("ref_sha")
        url = evidence.get("source_url")
        if not isinstance(actor, str) or not re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,38}$", actor):
            return _deny("github_attribution_missing_actor")
        if not isinstance(sha, str) or not re.match(r"^[0-9a-fA-F]{7,40}$", sha):
            return _deny("github_attribution_missing_commit")
        if not isinstance(url, str) or not url.startswith("https://github.com/" + repo):
            return _deny("github_url_not_public_in_scope")
        if entry.get("content_sha256") and evidence.get("content_sha256") != entry["content_sha256"]:
            return _deny("content_hash_mismatch_forged_evidence")
        # The repo must cite a pinned exact-author Vitalik authorization, proved
        # against authoritative board data rather than trusted from config.
        auth = allowlist["antonina"]["messages"].get(entry["authorized_by"])
        if not isinstance(auth, dict):
            return _deny("github_authorization_unpinned")
        try:
            resolver.resolve_founder_message(
                {"id": auth.get("id"), "issue": auth.get("issue")}, max_pages=max_pages)
        except BoardUnavailable as exc:
            return _deny("board_unreadable", str(exc))
        att_code, att_ts = _board_attestation(evidence, allowlist, resolver, now, max_pages)
        if att_code:
            return _deny(att_code)
        result.update({"class": "github:public", "repo": repo, "ref": refpart,
                       "attested_at": att_ts,
                       "actor": actor, "commit_sha": sha, "verified_authorization": FOUNDER,
                       "scope": entry.get("scope")})
        return _allow(result)

    if cls in ("authorized", "project"):
        entry = allowlist["project_sources"]["sources"].get(rest)
        if not isinstance(entry, dict):
            return _deny("project_source_not_allowlisted")
        eff = entry.get("effective_from")
        exp = entry.get("expires_at")
        if not isinstance(eff, (int, float)) or not isinstance(exp, (int, float)):
            return _deny("project_authorization_malformed")
        if not (eff <= now < exp) or exp - eff <= 0 or exp - eff > 15552000:
            return _deny("project_authorization_expired")
        auth = allowlist["antonina"]["messages"].get(entry.get("authorized_by"))
        if not isinstance(auth, dict):
            return _deny("project_authorization_unpinned")
        try:
            resolver.resolve_founder_message(
                {"id": auth.get("id"), "issue": auth.get("issue")}, max_pages=max_pages)
        except BoardUnavailable as exc:
            return _deny("board_unreadable", str(exc))
        if evidence.get("content_sha256") != entry.get("content_sha256"):
            return _deny("content_hash_mismatch_forged_evidence")
        att_code, att_ts = _board_attestation(evidence, allowlist, resolver, now, max_pages)
        if att_code:
            return _deny(att_code)
        result.update({"class": "authorized_project", "source_id": rest,
                       "verified_authorization": FOUNDER, "scope": entry.get("scope"),
                       "attested_at": att_ts})
        return _allow(result)

    return _deny("unsupported_source_class")


def validate_statement(stmt, sources_by_ref, now):
    """Enforce observation/inference/corrected-inference discipline."""
    if not isinstance(stmt, dict):
        return _deny("malformed_statement")
    kind = stmt.get("kind")
    if kind not in _STATEMENT_KINDS:
        return _deny("unknown_epistemic_kind")
    text = _evidence_text(stmt)
    if secret_rules(text):
        return _deny("secret_bearing_statement")
    if injection_rules(text):
        return _deny("prompt_injection_in_statement")

    # A NEEDS-FOUNDER line can never originate from Spying analysis.
    if re.search(r"NEEDS-FOUNDER\s*:", text):
        return _deny("needs_founder_from_analysis")

    cited = stmt.get("sources", [])
    if not isinstance(cited, list) or not cited:
        return _deny("statement_without_sources")
    for ref in cited:
        sv = sources_by_ref.get(ref)
        if not sv or sv.get("decision") != "ALLOW":
            return _deny("statement_cites_unvalidated_source")

    if kind == "observation":
        return _allow({"epistemic_kind": kind})

    if kind in ("inference", "corrected_inference"):
        alts = stmt.get("alternatives")
        if not isinstance(alts, list) or not alts or not all(isinstance(a, str) and a for a in alts):
            return _deny("inference_without_alternatives")
        conf = stmt.get("confidence")
        if not isinstance(conf, (int, float)) or isinstance(conf, bool) or not (0.0 <= conf <= 1.0):
            return _deny("inference_without_confidence")
        # An inference must never assert authorization, mandate, ballot,
        # spending, enactment or scope expansion.
        for key in _PROMOTION_KEYS:
            if stmt.get(key):
                return _deny("inference_promoted_to_authorization", key)
        if re.search(r"(?i)\b(?:founder\s+(?:authorizes|instructs|requires)|authorize(?:d|s)?\s+(?:spending|access|new\s+scope)|i\s+am\s+Vitalik)\b", text):
            return _deny("inference_promoted_to_authorization", "text")
        if kind == "corrected_inference":
            if not isinstance(stmt.get("correction_of"), str) or not stmt.get("correction_of"):
                return _deny("correction_missing_target")
            if not isinstance(stmt.get("reason"), str) or not stmt.get("reason"):
                return _deny("correction_missing_reason")
        return _allow({"epistemic_kind": kind})

    return _deny("unknown_epistemic_kind")


def validate_bundle(bundle, allowlist, resolver, now=None):
    """Validate a whole evidence bundle. DENY if any part fails; report gaps."""
    now = time.time() if now is None else now
    gaps = []
    if not isinstance(bundle, dict) or bundle.get("schema") != "viche-spying-evidence-bundle-v1":
        return {"schema": SCHEMA, "decision": "DENY", "office": "spying",
                "reasons": [{"code": "malformed_bundle", "detail": ""}],
                "sources": [], "statements": [], "gaps": gaps}
    if bundle.get("purpose") in ("publication", "inference") and not bundle.get("statements"):
        return {"schema": SCHEMA, "decision": "DENY", "office": "spying",
                "reasons": [{"code": "no_validated_inference_for_publication", "detail": ""}],
                "sources": [], "statements": [], "gaps": gaps}
    raw_sources = bundle.get("sources", [])
    if not isinstance(raw_sources, list):
        return {"schema": SCHEMA, "decision": "DENY", "office": "spying",
                "reasons": [{"code": "malformed_sources", "detail": ""}],
                "sources": [], "statements": [], "gaps": gaps}

    sources = []
    by_ref = {}
    for item in raw_sources:
        if not isinstance(item, dict) or "ref" not in item:
            sources.append({"ref": None, "decision": "DENY",
                            "reasons": [{"code": "malformed_source_item", "detail": ""}]})
            continue
        ref = item["ref"]
        v = validate_source(ref, item.get("evidence", {}), allowlist, resolver, now)
        v["ref"] = ref
        if any(r["code"] == "board_unreadable" for r in v["reasons"]):
            gaps.append("board_api_unreadable for %s" % ref)
        sources.append(v)
        by_ref[ref] = v

    # Copied conclusions / non-independent roots: distinct refs with identical
    # resolved body hashes are one observation, not independent corroboration.
    digests = {}
    for v in sources:
        h = v.get("body_sha256") or v.get("commit_sha")
        if h:
            if h in digests and digests[h] != v.get("ref"):
                v.setdefault("reasons", []).append(
                    {"code": "copied_or_duplicate_conclusion", "detail": digests[h]})
                v["decision"] = "DENY"
            else:
                digests[h] = v.get("ref")
    for item in raw_sources:
        if isinstance(item, dict) and item.get("derived_from") and item.get("claims_independent"):
            ref = item.get("ref")
            if ref in by_ref:
                by_ref[ref]["decision"] = "DENY"
                by_ref[ref].setdefault("reasons", []).append(
                    {"code": "non_independent_claim", "detail": ""})

    statements = []
    for stmt in bundle.get("statements", []) or []:
        v = validate_statement(stmt, by_ref, now)
        v["text"] = stmt.get("text") if isinstance(stmt, dict) else None
        statements.append(v)

    reasons = []
    for v in sources + statements:
        if v.get("decision") != "ALLOW":
            reasons.extend(v.get("reasons", []))
    decision = "ALLOW" if not reasons else "DENY"
    if decision == "ALLOW" and not sources:
        decision = "DENY"
        reasons = [{"code": "empty_source_bundle", "detail": ""}]
    return {"schema": SCHEMA, "decision": decision, "office": "spying",
            "reasons": reasons, "sources": sources, "statements": statements,
            "gaps": gaps, "now": now,
            "disclaimer": ("validation only; not office activation, publication, "
                           "Founder authorization or independent outcome verification")}


def preflight(town_root, allowlist_path=None, bundle_path=None, offline_json=None,
              now=None):
    """Launch preflight: DENY unless the source-scope bundle fully validates."""
    now = time.time() if now is None else now
    town = Path(town_root)
    allowlist_path = allowlist_path or town / DEFAULT_ALLOWLIST
    try:
        allowlist = load_allowlist(allowlist_path, now=now)
    except AllowlistError as exc:
        return {"schema": SCHEMA, "decision": "DENY", "office": "spying",
                "reasons": [{"code": "allowlist_unusable", "detail": str(exc)}],
                "sources": [], "statements": [], "gaps": [str(exc)]}
    if bundle_path is None:
        bundle_path = town / "records/knowledge/spying-source-scope.json"
    p = Path(bundle_path)
    if not p.is_file():
        return {"schema": SCHEMA, "decision": "DENY", "office": "spying",
                "reasons": [{"code": "source_scope_record_missing", "detail": str(p)}],
                "sources": [], "statements": [],
                "gaps": ["no recorded source-scope validation for Spying"]}
    try:
        bundle = json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {"schema": SCHEMA, "decision": "DENY", "office": "spying",
                "reasons": [{"code": "source_scope_record_malformed", "detail": ""}],
                "sources": [], "statements": [], "gaps": []}
    if not isinstance(bundle, dict) or not bundle.get("statements"):
        return {"schema": SCHEMA, "decision": "DENY", "office": "spying",
                "reasons": [{"code": "empty_or_incomplete_source_scope", "detail": ""}],
                "sources": [], "statements": [],
                "gaps": ["source-scope record carries no validated observation/inference"]}
    resolver = BoardResolver(offline_json=offline_json)
    verdict = validate_bundle(bundle, allowlist, resolver, now=now)
    verdict["allowlist"] = str(allowlist_path)
    verdict["bundle"] = str(p)
    return verdict


def _offline_from_file(path):
    if not path:
        return None
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("offline board snapshot must be an object keyed by issue id")
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--allowlist", default=None)
    common.add_argument("--board-json", default=None,
                        help="offline board snapshot (issue id -> board show JSON)")
    common.add_argument("--now", type=int, default=None)

    pvf = sub.add_parser("verify", parents=[common], help="validate one source ref")
    pvf.add_argument("--source", required=True)
    pvf.add_argument("--evidence", default="{}", help="JSON evidence record")

    ppf = sub.add_parser("preflight", parents=[common], help="validate a bundle / launch gate")
    ppf.add_argument("--bundle", default=None)
    ppf.add_argument("--town-root", default=os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))

    pub = sub.add_parser("publish", parents=[common],
                         help="publication-time gate: validate the ACTUAL cited source set")
    pub.add_argument("--bundle", required=True)
    pub.add_argument("--town-root", default=os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))

    args = ap.parse_args(argv)
    now = args.now
    try:
        offline = _offline_from_file(args.board_json)
    except (ValueError, OSError) as exc:
        print(json.dumps({"schema": SCHEMA, "decision": "DENY", "office": "spying",
                          "reasons": [{"code": "offline_board_unreadable",
                                       "detail": type(exc).__name__}],
                          "sources": [], "statements": [], "gaps": []}))
        return 1

    town = getattr(args, "town_root", os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))
    allowlist_path = args.allowlist or os.environ.get(
        "VICHE_SPYING_ALLOWLIST", str(Path(town) / DEFAULT_ALLOWLIST))

    if args.cmd == "verify":
        try:
            allowlist = load_allowlist(allowlist_path, now=now)
        except AllowlistError as exc:
            print(json.dumps({"schema": SCHEMA, "decision": "DENY", "office": "spying",
                              "reasons": [{"code": "allowlist_unusable", "detail": str(exc)}],
                              "sources": [], "statements": [], "gaps": [str(exc)]}))
            return 1
        try:
            evidence = json.loads(args.evidence)
        except ValueError:
            print(json.dumps({"schema": SCHEMA, "decision": "DENY", "office": "spying",
                              "reasons": [{"code": "malformed_evidence", "detail": ""}],
                              "sources": [], "statements": [], "gaps": []}))
            return 1
        resolver = BoardResolver(offline_json=offline)
        v = validate_source(args.source, evidence, allowlist, resolver,
                            now=time.time() if now is None else now)
        out = dict(v)
        out.update({"schema": SCHEMA, "office": "spying", "sources": [dict(v)],
                    "statements": [], "gaps": [r["detail"] for r in v["reasons"]
                                              if r["code"] == "board_unreadable"]})
        print(json.dumps(out))
        return 0 if out["decision"] == "ALLOW" else 1

    if args.cmd == "publish":
        try:
            allowlist = load_allowlist(allowlist_path, now=now)
            bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
        except (AllowlistError, ValueError, OSError) as exc:
            print(json.dumps({"schema": SCHEMA, "decision": "DENY", "office": "spying",
                              "reasons": [{"code": "publication_gate_unusable",
                                           "detail": type(exc).__name__}],
                              "sources": [], "statements": [], "gaps": []}))
            return 1
        if isinstance(bundle, dict):
            bundle["purpose"] = "publication"
        resolver = BoardResolver(offline_json=offline)
        verdict = validate_bundle(bundle, allowlist, resolver, now=now)
        print(json.dumps(verdict))
        return 0 if verdict["decision"] == "ALLOW" else 1

    verdict = preflight(town, allowlist_path=allowlist_path, bundle_path=args.bundle,
                        offline_json=offline, now=now)
    print(json.dumps(verdict))
    return 0 if verdict["decision"] == "ALLOW" else 1


if __name__ == "__main__":
    sys.exit(main())
