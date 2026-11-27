"""Truthful commit attribution for automated PnP publication.

The publisher is a deterministic program.  It never infers a contributor from
candidate bytes, a worker prompt, desk metadata, board labels or legacy Git
configuration: all of those are unauthenticated.  A ``Co-authored-by`` trailer
is emitted only for an identity that a trusted caller explicitly declared, or
for a trailer already present in an earlier commit that a correction preserves.
When nobody is declared, the actual producer is the publisher program itself,
declared here as a fixed constant rather than guessed per gap.

Every commit still carries Otto Jung as both author and committer and is signed
with the pinned subkey.  Identity is passed per Git invocation through the
environment and ``git -c``; no shared repository configuration is written.
"""
import os
import re

from . import config

AUTHOR_IDENT = config.AUTHOR_NAME + " <" + config.AUTHOR_EMAIL + ">"
# The deterministic publisher is the real producer of an automated commit when
# no authenticated contributor was declared.  Never name a guessed researcher.
PUBLISHER = "Viche PnP Publisher <pnp@viche.local>"

MAX_CONTRIBUTORS = 8
_IDENT_RE = re.compile(
    r"^([^<>\r\n\t]{1,80}) <([A-Za-z0-9][A-Za-z0-9._%+-]*@"
    r"[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,})>$")
_TRAILER_RE = re.compile(r"^Co-authored-by:\s*(.+)$", re.IGNORECASE)


class AttributionError(ValueError):
    """An identity was missing, malformed or would be a false attribution."""


def validate(value):
    """Return one canonical ``Name <email>`` or refuse it. No guessing."""
    if not isinstance(value, str) or len(value) > 200:
        raise AttributionError("contributor identity is not a bounded string")
    match = _IDENT_RE.fullmatch(value.strip())
    if not match:
        raise AttributionError("contributor must be 'Name <email>': %r" % value[:120])
    name, email = match.group(1).strip(), match.group(2)
    if not name or email.lower() == config.AUTHOR_EMAIL.lower() or \
            name.lower() == config.AUTHOR_NAME.lower():
        raise AttributionError("the shared signing identity is not a co-author")
    return name + " <" + email + ">"


def validated(values=(), existing=()):
    """Deduplicate explicit co-authors by email, preserving declaration order."""
    out, seen = [], set()
    for value in list(existing) + list(values or ()):
        ident = validate(value)
        email = ident.rsplit("<", 1)[1].rstrip(">").lower()
        if email not in seen:
            seen.add(email)
            out.append(ident)
    if len(out) > MAX_CONTRIBUTORS:
        raise AttributionError("too many co-authors")
    return out


def expected(values=(), existing=()):
    """Exact trailer set a commit must carry; the producer is the fallback."""
    return validated(values, existing) or [validate(PUBLISHER)]


def parse(message):
    """Read only explicit trailer lines from an existing commit message."""
    if not isinstance(message, str):
        raise AttributionError("commit message is not text")
    found = []
    for line in message.splitlines():
        match = _TRAILER_RE.match(line.strip())
        if match:
            found.append(validate(match.group(1)))
    return validated(found)


def build(subject, values=(), existing_message=None):
    """One-line subject plus final, validated co-author trailers."""
    if not isinstance(subject, str) or not subject.strip() or \
            "\n" in subject.strip() or "\r" in subject:
        raise AttributionError("commit subject must be a single clean line")
    prior = parse(existing_message) if existing_message else ()
    lines = [subject.strip()] + [""] + [
        "Co-authored-by: " + ident for ident in expected(values, prior)]
    return "\n".join(lines) + "\n"


def verify(message, idents):
    """Fail closed if the resulting commit lost or changed a co-author."""
    if parse(message) != list(idents):
        raise AttributionError("commit co-author trailers were not preserved")


def identity_env():
    """Per-invocation identity; never write user.name/email into a repo."""
    return dict(os.environ,
                GIT_AUTHOR_NAME=config.AUTHOR_NAME,
                GIT_AUTHOR_EMAIL=config.AUTHOR_EMAIL,
                GIT_COMMITTER_NAME=config.AUTHOR_NAME,
                GIT_COMMITTER_EMAIL=config.AUTHOR_EMAIL)


def signing_args():
    """Force signing of this one commit without mutating shared config."""
    return ["-c", "user.signingkey=" + config.SIGNING_KEY,
            "-c", "commit.gpgsign=true"]
