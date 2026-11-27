#!/usr/bin/env python3
"""Signed, truthfully attributed commits for Viche office/seat workflows.

One invocation-safe tool: Git author, committer and signer are always Otto Jung,
supplied through GIT_AUTHOR_*/GIT_COMMITTER_* and `git -c` rather than a shared
repository config (linked worktrees share that config and racing writers corrupt
each other).  Each commit is made with `git commit -S`, and its identity,
signature and final Co-authored-by trailers are verified before the tool exits.

Co-authors are accepted only as explicit, validated `--contributor 'Name <email>'`
values from the caller.  No identity is inferred from Git config, board labels,
agent prompts or file content.  With no declaration the actual producer is the
deterministic workflow itself, recorded as WORKFLOW.  Existing trailers can be
supplied with `--existing FILE` so squash/merge/correction style flows preserve
them.  Synthetic fixture repositories may set VICHE_COMMIT_FIXTURE=1; that is a
test-only escape hatch and never applies to a real delivery commit.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

AUTHOR_NAME = "Otto Jung"
AUTHOR_EMAIL = "otto.jung@vauplace.com"
SIGNING_KEY = "08AF2726387BD4A4C87DF1821BEDDF96D7B1BA2B!"
WORKFLOW = "Viche Commit Workflow <commits@viche.local>"
GOOD_SIGNATURES = {"G", "U"}

_IDENT_RE = re.compile(
    r"^([^<>\r\n\t]{1,80}) <([A-Za-z0-9][A-Za-z0-9._%+-]*@"
    r"[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,})>$")
_TRAILER_RE = re.compile(r"^Co-authored-by:\s*(.+)$", re.IGNORECASE)


class AttributionError(ValueError):
    pass


def validate(value):
    if not isinstance(value, str) or len(value) > 200:
        raise AttributionError("contributor identity is not a bounded string")
    match = _IDENT_RE.fullmatch(value.strip())
    if not match:
        raise AttributionError("contributor must be 'Name <email>': %r" % value[:120])
    name, email = match.group(1).strip(), match.group(2)
    if not name or email.lower() == AUTHOR_EMAIL.lower() or \
            name.lower() == AUTHOR_NAME.lower():
        raise AttributionError("the shared signing identity is not a co-author")
    return name + " <" + email + ">"


def validated(values=(), existing=()):
    out, seen = [], set()
    for value in list(existing) + list(values or ()):
        ident = validate(value)
        email = ident.rsplit("<", 1)[1].rstrip(">").lower()
        if email not in seen:
            seen.add(email)
            out.append(ident)
    if len(out) > 8:
        raise AttributionError("too many co-authors")
    return out


def expected(values=(), existing=()):
    return validated(values, existing) or [validate(WORKFLOW)]


def parse(message):
    found = []
    for line in (message or "").splitlines():
        match = _TRAILER_RE.match(line.strip())
        if match:
            found.append(validate(match.group(1)))
    return validated(found)


def build(subject, values=(), existing_message=None):
    if not isinstance(subject, str) or not subject.strip() or \
            "\n" in subject.strip() or "\r" in subject:
        raise AttributionError("commit subject must be a single clean line")
    prior = parse(existing_message) if existing_message else ()
    lines = [subject.strip()] + [""] + [
        "Co-authored-by: " + ident for ident in expected(values, prior)]
    return "\n".join(lines) + "\n"


def git(repo, args, env=None, check=True):
    p = subprocess.run(["git", "-C", repo] + list(args), env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, timeout=120)
    if check and p.returncode != 0:
        raise RuntimeError("git %s failed: %s" % (args[0], p.stderr.strip()[:600]))
    return p


def verify(repo, sha, idents):
    fmt = git(repo, ["log", "-1", "--format=" +
                     "%G?%n%GF%n%an%n%ae%n%cn%n%ce", sha]).stdout.splitlines()
    if len(fmt) != 6 or fmt[0] not in GOOD_SIGNATURES:
        raise RuntimeError("commit is not good-signed: %r" % fmt[:2])
    if fmt[1].upper() != SIGNING_KEY.rstrip("!").upper():
        raise RuntimeError("wrong signing subkey: " + fmt[1])
    if fmt[2:4] != [AUTHOR_NAME, AUTHOR_EMAIL]:
        raise RuntimeError("wrong author: %r" % fmt[2:4])
    if fmt[4:6] != [AUTHOR_NAME, AUTHOR_EMAIL]:
        raise RuntimeError("wrong committer: %r" % fmt[4:6])
    body = git(repo, ["log", "-1", "--format=%B", sha]).stdout
    if parse(body) != list(idents):
        raise RuntimeError("commit co-author trailers were not preserved")
    if git(repo, ["verify-commit", sha], check=False).returncode != 0:
        raise RuntimeError("git verify-commit failed")


def commit(repo, subject, contributors, extra, fixture=False):
    idents = expected(contributors)
    message = build(subject, contributors)
    env = dict(os.environ,
               GIT_AUTHOR_NAME=AUTHOR_NAME, GIT_AUTHOR_EMAIL=AUTHOR_EMAIL,
               GIT_COMMITTER_NAME=AUTHOR_NAME, GIT_COMMITTER_EMAIL=AUTHOR_EMAIL)
    args = ["-c", "user.signingkey=" + SIGNING_KEY, "-c", "commit.gpgsign=true"]
    commit_args = ["commit"]
    if not fixture:
        commit_args.append("-S")
    else:
        print("commit-identity: fixture mode, signing verification skipped",
              file=sys.stderr)
    fd, path = tempfile.mkstemp(prefix="viche-commit-message-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(message)
        git(repo, args + commit_args + ["-F", path] + list(extra), env=env)
    finally:
        os.unlink(path)
    sha = git(repo, ["rev-parse", "HEAD"]).stdout.strip()
    if not fixture:
        verify(repo, sha, idents)
    print(sha)
    return sha


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("commit", "message", "verify"):
        p = sub.add_parser(name)
        if name in ("commit", "message"):
            p.add_argument("--subject", required=True)
            p.add_argument("--contributor", action="append", default=[])
        else:
            p.add_argument("--contributor", action="append", default=[])
        if name in ("commit", "verify"):
            p.add_argument("--repo", required=True)
        if name == "message":
            p.add_argument("--existing")
        if name == "verify":
            p.add_argument("--commit", dest="sha", required=True)
        if name == "commit":
            p.add_argument("extra", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.cmd == "message":
            existing = None
            if args.existing:
                with open(args.existing, encoding="utf-8") as f:
                    existing = f.read()
            sys.stdout.write(build(args.subject, args.contributor, existing))
        elif args.cmd == "commit":
            extra = list(args.extra)
            if extra and extra[0] == "--":
                extra = extra[1:]
            fixture = os.environ.get("VICHE_COMMIT_FIXTURE") == "1"
            commit(args.repo, args.subject, args.contributor, extra, fixture)
        else:
            verify(args.repo, args.sha, expected(args.contributor))
    except (AttributionError, RuntimeError, OSError) as exc:
        print("commit-identity: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
