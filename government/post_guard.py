"""Conservative secret-pattern barrier for PUBLIC Viche Post.

This is defense in depth, NOT confidentiality: all Post messages and the SQLite
database remain readable by the shared Unix user. Never include a matching
credential or substring in an error, log, receipt, or incident report.
"""
import re

PATTERNS = {
    "private-key": re.compile(
        r"-----BEGIN (?:[A-Z0-9 ]* )?PRIVATE KEY-----", re.I),
    "github-token": re.compile(
        r"\b(?:github_pat_[A-Za-z0-9_]{40,}|gh[pousr]_[A-Za-z0-9]{30,})\b"),
    "cloud-key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "openai-token": re.compile(
        r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}\b"),
    "gitlab-token": re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    "slack-token": re.compile(
        r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "bearer-token": re.compile(
        r"\b(?:Authorization\s*:\s*)?Bearer\s+[A-Za-z0-9_+./=-]{24,}\b",
        re.I),
    "ssh-key": re.compile(
        r"\bssh-(?:rsa|ed25519)\s+[A-Za-z0-9+/]{90,}={0,3}\b"),
}
ASSIGNMENT = re.compile(
    r"\b(?:password|api[_-]?key|access[_-]?token|client[_-]?secret|"
    r"secret[_-]?key|private[_-]?key)\s*[:=]\s*['\"]?"
    r"(?P<value>[A-Za-z0-9_+./=-]{12,})", re.I)
# Only explicit entire-value placeholders are exempt. A real secret may
# contain words such as "test" or "example" as a substring.
PLACEHOLDER = re.compile(
    r"^(?:redacted|placeholder|dummy|example|fake|sample|test)"
    r"(?:[_-](?:value|token|secret))?$|^(?:changeme|x{8,}|0{8,})$", re.I)


def detect(value):
    """Return IDs of likely credential patterns without retaining raw matches."""
    text = value if isinstance(value, str) else str(value)
    hits = {name for name, pattern in PATTERNS.items() if pattern.search(text)}
    for match in ASSIGNMENT.finditer(text):
        if not PLACEHOLDER.fullmatch(match.group("value")):
            hits.add("credential-assignment")
    return sorted(hits)


def check(*values):
    patterns = set()
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            patterns.update(check_ids(*value))
        else:
            patterns.update(detect(value))
    if patterns:
        # Never echo the matched value, even on an exception.
        raise ValueError("public Post rejected credential-like content; "
                         "pattern IDs: " + ",".join(sorted(patterns)))


def check_ids(*values):
    """Non-throwing helper for nested source/derivation arrays."""
    result = set()
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            result.update(check_ids(*value))
        else:
            result.update(detect(value))
    return sorted(result)
