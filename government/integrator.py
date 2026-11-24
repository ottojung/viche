#!/usr/bin/env python3
"""The integration queue: lands reviewed work on main (Act 31, Founder directive
2026-11-18). Deterministic; the only model call it makes is to commission an
independent reviewer.

Measured problem. Landing a change used to be a procedure performed by hand
across several offices: the Clerk ran the suite on the exact commit, another
office wrote and pinned a pre-landing record, the Clerk fast-forwarded main and
then committed a copy of the record. If main moved at any point the whole
verification was void (Act 28 §3.4). Commits reaching main fell from 380 in
the week of 2 November to 57 and then 2; more than forty delivery branches were
left unlanded, many of them the same change rebuilt as -r2, -r3, -refreshed.
Nobody owned the queue, and the Clerk's inputs did not include it.

What the integrator does, every boot cycle, under a lock:

  1. Reads proposals made with government/propose-delivery.sh --office.
  2. Decides whether each needs review. Additive records (only new files, or
     pure appends to existing files, all under records/) do not: they cannot
     destroy evidence. Everything else needs an approval from an office other
     than the proposer. When no review exists the integrator commissions a
     fresh, independent Antonina reviewer agent for that exact commit.
  3. Lands ready proposals one at a time, each built afresh on the current
     main: a single squashed candidate commit whose parent is main (Act 28
     §3.2), the applicable suite run on that exact commit and tree by
     government/suite-status.sh (Act 21 §§1-3, flaky-red rule included), a
     status carrier commit whose only path is records/suite-status.json
     (Act 28 §§1, 3.3), and one non-force push of the carrier (Act 28 §3.4).
     If main moved meanwhile, the push is refused and the next cycle rebuilds.
     Nothing has to be re-verified by hand.
  4. Writes what happened where the proposer will see it:
     state/delivery/office/OFFICE.json (an input of the office's dispatch gate,
     so the office wakes when its delivery lands, is rejected, goes red or
     conflicts), state/delivery/queue.json, and for every landing a pre-landing
     record state/delivery/integration-CANDIDATE.json with content assertions,
     plus state/delivery/landed.jsonl and trailers in the candidate commit.

Refused, never landed: constitution/ (Founder only); government/LAWS.md or
government/seats.tsv unless the delivery's commits carry "Enacts: BILL" and
government/tally.sh BILL passes on the exact candidate; deliveries marked
"Act25-Phase:" (Act 26 governs those; land them manually).

  integrator.py run             one pass (government/boot.sh)
  integrator.py status          the queue as JSON
  integrator.py office OFFICE   what an office needs to know about its deliveries

Environment: VICHE_TOWN_ROOT, VICHE_STATE_ROOT, VICHE_INTEGRATOR=off,
VICHE_INTEGRATOR_NOW (tests), VICHE_INTEGRATOR_NO_REVIEWER=1 (never commission).
"""
import datetime
import fcntl
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

TOWN = pathlib.Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"))
STATE = pathlib.Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
DELIVERY = STATE / "delivery"
ROOT = DELIVERY / "integrator"
OFFICES = DELIVERY / "office"
EXPIRE_SECONDS = 14 * 86400
REVIEW_TIMEOUT = 24 * 3600
REVIEW_ATTEMPTS = 2
# Prefer ready short deliveries, but allow an old full-suite candidate first.
RECORD_BATCH_LIMIT = 32
GIT_LOCAL_TIMEOUT = 60
GIT_REMOTE_TIMEOUT = 90
LANDED_VISIBLE = 3 * 86400
# Final for this exact head: a new proposal (a new head) starts again.
TERMINAL = {"landed", "no_delta", "refused", "rejected", "superseded", "expired", "red", "conflict"}
OFFICE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


# ---------------------------------------------------------------- utilities

def now():
    return int(os.environ.get("VICHE_INTEGRATOR_NOW", time.time()))


def iso(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic_write(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".tmp.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load(path, default):
    try:
        return json.loads(pathlib.Path(path).read_text())
    except (OSError, ValueError):
        return default


def append(path, obj):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as handle:
        handle.write(json.dumps(obj, sort_keys=True) + "\n")


def git(*args, cwd=None, check=True, env=None):
    command = ["git", "-C", str(cwd or TOWN)] + list(args)
    deadline = GIT_REMOTE_TIMEOUT if args and args[0] in ("fetch", "push") else GIT_LOCAL_TIMEOUT
    # A blocked SSH helper is part of this invocation, not a reason for the
    # queue to hold its worktree lock indefinitely. Never wait for a terminal
    # credential prompt. Kill only our own new process group on timeout.
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True,
                               env=dict(os.environ if env is None else env, GIT_TERMINAL_PROMPT="0"))
    try:
        stdout, stderr = process.communicate(timeout=deadline)
        done = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        done = subprocess.CompletedProcess(command, 124, stdout,
                                           (stderr or "") + "\nGit invocation exceeded its deadline")
    if check and done.returncode != 0:
        raise GitError("git %s: %s" % (" ".join(args[:3]), done.stderr.strip()[-300:]))
    return done.stdout.strip() if check else done


class GitError(Exception):
    pass


# Commits the integrator makes say who made them; signing follows the host's
# Git configuration, as for every other office.
IDENT = dict(os.environ, GIT_AUTHOR_NAME="Viche Integrator", GIT_AUTHOR_EMAIL="integrator@viche.local",
             GIT_COMMITTER_NAME="Viche Integrator", GIT_COMMITTER_EMAIL="integrator@viche.local")


def log(message):
    print("%s integrator: %s" % (iso(now()), message), file=sys.stderr)


# ---------------------------------------------------------------- inputs

def proposals():
    """Latest proposal per delivery branch, from propose-delivery.sh rows that
    name an office (column 7). Older rows without an office predate Act 31."""
    path = DELIVERY / "proposals.tsv"
    latest = {}
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return []
    for line in lines:
        f = line.split("\t")
        if len(f) < 7 or not f[2].startswith("refs/heads/delivery/") or not OFFICE_RE.match(f[6]):
            continue
        if not re.fullmatch(r"[0-9a-f]{40}", f[3]):
            continue
        branch = f[2][len("refs/heads/"):]
        try:
            at = int(datetime.datetime.strptime(f[0], "%Y-%m-%dT%H:%M:%SZ")
                     .replace(tzinfo=datetime.timezone.utc).timestamp())
        except ValueError:
            continue
        latest[branch] = {"branch": branch, "head": f[3], "office": f[6], "at": at}
    return sorted(latest.values(), key=lambda p: p["at"])


def reviews():
    out = []
    try:
        for line in (DELIVERY / "reviews.jsonl").read_text().splitlines():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def verdict_for(p, all_reviews):
    """Latest verdict on this exact head by an office other than the proposer."""
    found = None
    for r in all_reviews:
        if (r.get("branch") == p["branch"] and r.get("head") == p["head"]
                and r.get("office") and r.get("office") != p["office"]
                and r.get("verdict") in ("approve", "reject")):
            found = r
    return found


# ---------------------------------------------------------------- classification

def changes(base, head):
    """[(status, path, old_blob, new_blob)] from the merge base to head."""
    mb = git("merge-base", base, head)
    out = git("diff", "--raw", "--no-renames", "--no-abbrev", mb, head)
    found = []
    for line in out.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) >= 5:
            found.append((parts[4], path, parts[2], parts[3]))
    return found


def is_append(old_blob, new_blob):
    old = subprocess.run(["git", "-C", str(TOWN), "cat-file", "blob", old_blob], capture_output=True).stdout
    new = subprocess.run(["git", "-C", str(TOWN), "cat-file", "blob", new_blob], capture_output=True).stdout
    return len(new) >= len(old) and new.startswith(old)


def classify(base, head):
    found = changes(base, head)
    paths = [c[1] for c in found]
    if not paths:
        return {"paths": [], "protected": None, "laws": False, "additive": False}
    protected = next((p for p in paths if p.startswith("constitution/")), None)
    laws = any(p in ("government/LAWS.md", "government/seats.tsv") for p in paths)
    additive = all(
        path.startswith("records/") and path != "records/suite-status.json" and
        (status == "A" or (status == "M" and is_append(old, new)))
        for status, path, old, new in found)
    return {"paths": paths, "protected": protected, "laws": laws, "additive": additive}


def messages(base, head):
    return git("log", "--format=%B", "%s..%s" % (git("merge-base", base, head), head))


# ---------------------------------------------------------------- reviewers

def commission_reviewer(p, base, entry):
    if os.environ.get("VICHE_INTEGRATOR_NO_REVIEWER") == "1":
        return
    attempt = int(entry.get("review_attempts", 0)) + 1
    wt = ROOT / "review" / p["head"][:12]
    if not wt.exists():
        git("worktree", "add", "--detach", str(wt), p["head"])
    title = "Viche reviewer: %s" % p["branch"]
    done = subprocess.run(["antonina", "agent", "new", "--title", title, "--cwd", str(wt)],
                          capture_output=True, text=True, timeout=120)
    agent = done.stdout.strip().split()[-1] if done.returncode == 0 and done.stdout.strip() else ""
    if not agent:
        entry["note"] = "could not create a reviewer agent: " + done.stderr.strip()[-160:]
        return
    office = "reviewer-" + re.sub(r"[^a-z0-9-]", "", agent.lower())[:50]
    prompt = REVIEW_PROMPT.format(branch=p["branch"], head=p["head"], proposer=p["office"],
                                  base=base, town=TOWN, office=office,
                                  charter=os.environ.get("VICHE_CONSTITUTION",
                                                         "/var/lib/lubko/from-host/viche-constitution/CONSTITUTION.md"))
    run = subprocess.run(["antonina", "agent", "run", "--id", agent, "--cwd", str(wt),
                          "--prompt", prompt, "--detach", "--wait-for-model"],
                         capture_output=True, text=True, timeout=120)
    if run.returncode != 0:
        entry["note"] = "reviewer run refused: " + run.stderr.strip()[-160:]
        return
    entry.update({"status": "reviewing", "reviewer_agent": agent, "reviewer_office": office,
                  "review_commissioned_at": now(), "review_attempts": attempt})
    log("commissioned reviewer %s for %s@%s" % (agent, p["branch"], p["head"][:12]))


def reviewer_finished(agent):
    try:
        done = subprocess.run(["antonina", "agent", "status", "--id", agent, "--json"],
                              capture_output=True, text=True, timeout=60)
        state = json.loads(done.stdout).get("state") if done.returncode == 0 else None
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False
    return state in ("clearexit", "failed", "stopped", "killed")


REVIEW_PROMPT = """You are an independent reviewer for Viche (Act 31). You did not write this change and
you have no other duty in this session.

Change: {branch} at commit {head}, proposed by office {proposer}.
You are in a checkout of that commit. Main is at {base}.
  git diff {base}...{head}      the change
  git log {base}..{head}        its commit messages

Decide whether it should land on main:
- Does it do what its messages say, correctly, without collateral damage?
- Does it respect the Constitution ({charter}) and current law ({town}/government/LAWS.md)?
  A change to government/LAWS.md or government/seats.tsv must carry an "Enacts: BILL"
  trailer for a bill that government/tally.sh BILL passes.
- Does it delete or rewrite evidence under records/ without a stated reason?
The integrator runs the test suite on the exact merged commit; you need not run it.
Reject only for a concrete defect the proposer can fix, and say exactly what it is.

Record your verdict exactly once, then stop:
  /bin/sh {town}/government/review-delivery.sh {branch} {head} approve --office {office} --reason "one or two sentences"
  /bin/sh {town}/government/review-delivery.sh {branch} {head} reject --office {office} --reason "the defect"
Do not modify any branch, worktree or file.
"""


# ---------------------------------------------------------------- landing

def trailer(text, name):
    found = re.findall(r"^%s:\s*(\S+)\s*$" % re.escape(name), text, re.MULTILINE)
    return found[-1] if found else None


def suite_for(paths):
    return "tests/records-smoke.sh" if all(p.startswith("records/") or p == "AGENTS.md" for p in paths) \
        else "tests/run-all.sh"


def ballot_rows(blob, digest, seats):
    """Validate exact newline-terminated rows; never normalize or invent votes."""
    if blob and not blob.endswith(b"\n"):
        raise ValueError("incomplete ballot row")
    rows = {}
    for row in blob.splitlines(keepends=True):
        fields = row[:-1].split(b"\t")
        if (len(fields) != 3 or fields[0] not in seats
                or fields[1] not in (b"yes", b"no", b"abstain")
                or fields[2] != digest or fields[0] in rows):
            raise ValueError("invalid or conflicting ballot row")
        rows[fields[0]] = row
    return rows


def resolve_ballot_append(wt, path, proposer):
    """Merge only independent, exact-SHA append-only ballots.

    An incoming auto-resolution may add only the proposing seat's own row.
    All prior rows and current main rows stay byte-identical; a conflicting
    same-seat vote or amended bill is never guessed at. The actual merged
    candidate still runs the ordinary suite and any required tally.
    """
    match = re.fullmatch(r"records/ballots/([A-Za-z0-9_-]+)[.]tsv", path)
    if not match:
        return False
    bill = wt / "records" / "bills" / (match[1] + ".md")
    roster = wt / "government" / "seats.tsv"
    if any(x.is_symlink() or not x.is_file() for x in (bill, roster)):
        return False
    target = wt / path
    # Never interpret a symlink, gitlink, or non-regular conflict stage as
    # ballot data or write through it. The merge worktree is disposable.
    stages = git("ls-files", "-u", "--", path, cwd=wt).splitlines()
    if target.is_symlink() or any(line.split()[0] != "100644" for line in stages):
        return False
    def stage(n):
        result = subprocess.run(["git", "-C", str(wt), "show", ":%d:%s" % (n, path)],
                                capture_output=True)
        return result.stdout if result.returncode == 0 else None
    old, ours, theirs = stage(1), stage(2), stage(3)
    if ours is None or theirs is None:
        return False  # deletion, not a concurrent append
    old = old if old is not None else b""
    if not ours.startswith(old) or not theirs.startswith(old):
        return False
    try:
        digest = hashlib.sha256(bill.read_bytes()).hexdigest().encode("ascii")
        seats = {line.split(b"\t", 1)[0] for line in roster.read_bytes().splitlines()}
        before = ballot_rows(old, digest, seats)
        current = ballot_rows(ours, digest, seats)
        incoming = ballot_rows(theirs, digest, seats)
        additions = {seat: row for seat, row in incoming.items() if seat not in before}
        if set(additions) - {proposer.encode("ascii")}:
            return False
        for seat, row in additions.items():
            if seat in current and current[seat] != row:
                return False
        combined = ours + b"".join(row for seat, row in additions.items() if seat not in current)
        ballot_rows(combined, digest, seats)
        target.write_bytes(combined)
        git("add", "--", path, cwd=wt)
        return True
    except (OSError, ValueError, GitError):
        return False


def canonical_preflight(base, candidate):
    """The canonical checkout must be at base and hold no untracked or edited
    file the landing would overwrite (same rule as reviewed-merge.sh)."""
    head = git("rev-parse", "HEAD")
    if head != base:
        # The boot supervisor normally fast-forwards first; do it here too.
        git("merge", "--ff-only", base, check=False)
        if git("rev-parse", "HEAD") != base:
            return "canonical checkout is at %s, not main %s" % (head[:12], base[:12])
    for path in git("diff", "--name-only", base, candidate).splitlines():
        if not path:
            continue
        if path == "records/suite-status.json":
            # A generated record (Act 21 §3). The old manual route copied
            # receipts into the canonical tree; the carrier now supersedes it.
            # Keep the local copy in state, then let the landing replace it.
            local = TOWN / path
            if local.is_file() and (git("diff", "--quiet", "HEAD", "--", path, check=False).returncode != 0):
                shutil.copyfile(str(local), str(DELIVERY / ("suite-canonical-%d.json" % now())))
                git("restore", "--staged", "--worktree", "--source=HEAD", "--", path, check=False)
            continue
        full = TOWN / path
        tracked = git("ls-files", "--error-unmatch", "--", path, check=False).returncode == 0
        if (full.exists() or full.is_symlink()) and not tracked:
            return "untracked canonical file would be overwritten: " + path
        if tracked and (git("diff", "--quiet", "--", path, check=False).returncode != 0 or
                        git("diff", "--cached", "--quiet", "--", path, check=False).returncode != 0):
            return "edited canonical file would be overwritten: " + path
    return None


def pending_publication(candidate):
    return DELIVERY / "pending-publication" / (candidate + ".json")


def finalize_publication(prelanding, entry, recovered=False):
    """Record only a known successful push or an observed reachable carrier.

    An interrupted acknowledgement never manufactures a publication. The
    prelanding record and exact verification receipt must still match.
    """
    candidate, carrier = prelanding["candidate"], prelanding["carrier"]
    receipt = DELIVERY / ("verified-%s.json" % candidate)
    digest = hashlib.sha256(receipt.read_bytes()).hexdigest()
    if digest != prelanding["suite_record_sha256"]:
        raise GitError("publication receipt digest mismatch")
    event_path = DELIVERY / ("published-%s.json" % candidate)
    event = load(event_path, None)
    if event is None:
        event = {"generated_by": "government/integrator.py", "commit": candidate,
                 "published_at_ns": time.time_ns(), "receipt_sha256": digest,
                 "observation": "remote ancestry recovered" if recovered else "push acknowledged"}
        atomic_write(event_path, json.dumps(event, sort_keys=True) + "\n")
    elif event.get("commit") != candidate or event.get("receipt_sha256") != digest:
        raise GitError("existing publication evidence differs")
    # The carrier object is already present locally after our verified build
    # or a fresh remote fetch. Avoid another redundant network request.
    sync = git("merge", "--ff-only", carrier, check=False)
    landed_path = DELIVERY / "landed.jsonl"
    seen = False
    if landed_path.exists():
        for line in landed_path.read_text().splitlines():
            try:
                seen = seen or json.loads(line).get("candidate") == candidate
            except (ValueError, AttributeError):
                continue
            if seen:
                break
    if not seen:
        append(landed_path, {k: prelanding[k] for k in
               ("at", "branch", "head", "office", "reviewed_by", "candidate", "carrier", "suite", "enacts")})
    entry.update({"status": "landed", "reason": None if sync.returncode == 0 else
                  "remote landed; canonical checkout synchronization pending",
                  "candidate": candidate, "carrier": carrier,
                  "landed_at": now(), "log": None})
    log("landed %s (%s) as %s%s" % (prelanding["branch"], prelanding["office"],
        candidate[:12], " (remote ancestry confirmed)" if recovered else ""))


def recover_publications(state, remote_main):
    """Reconcile uncertain pushes after a successful authoritative fetch."""
    for marker in (DELIVERY / "pending-publication").glob("*.json"):
        try:
            data = load(marker, None)
            if not isinstance(data, dict):
                raise GitError("pending publication marker unreadable")
            candidate, carrier = data["candidate"], data["carrier"]
            if not all(isinstance(x, str) and re.fullmatch(r"[0-9a-f]{40}", x) for x in (candidate, carrier)):
                raise GitError("pending publication identifiers malformed")
            if marker != pending_publication(candidate):
                raise GitError("pending publication filename mismatch")
            if load(DELIVERY / ("integration-%s.json" % candidate), None) != data:
                raise GitError("pending publication differs from prelanding record")
            result = git("merge-base", "--is-ancestor", carrier, remote_main, check=False)
            if result.returncode == 1:
                # Fresh remote main does not contain our carrier. Nothing
                # is claimed as published; ordinary candidate rebuild may retry.
                marker.unlink()
                continue
            if result.returncode != 0:
                raise GitError("cannot establish remote publication ancestry")
            if (git("rev-parse", carrier + "^") != candidate
                    or git("rev-parse", candidate + "^") != data["base"]
                    or git("rev-parse", candidate + "^{tree}") != data["tree"]
                    or git("diff", "--name-only", candidate, carrier) != "records/suite-status.json"):
                raise GitError("remote carrier no longer matches exact prelanding assertions")
            key = "%s@%s" % (data["branch"], data["head"])
            entry = state.setdefault(key, {"branch": data["branch"], "head": data["head"],
                                          "office": data["office"], "proposed_at": data.get("proposed_at", now())})
            finalize_publication(data, entry, recovered=True)
        except (GitError, OSError, KeyError, ValueError, TypeError) as error:
            log("pending publication %s not reconciled: %s" % (marker.name, error))


def clear_finalized_publications(state):
    # A crash before the atomic queue-state write leaves the marker available
    # for idempotent recovery. Remove only after the landed status is durable.
    for marker in (DELIVERY / "pending-publication").glob("*.json"):
        data = load(marker, {})
        if not isinstance(data, dict):
            continue
        key = "%s@%s" % (data.get("branch"), data.get("head"))
        entry = state.get(key, {})
        if entry.get("status") == "landed" and entry.get("candidate") == data.get("candidate"):
            marker.unlink(missing_ok=True)


def land(p, entry, review):
    git("fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main")
    base = git("rev-parse", "refs/remotes/origin/main")
    info = classify(base, p["head"])
    wt = ROOT / "work"
    if wt.exists():
        git("worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(str(wt), ignore_errors=True)
    git("worktree", "prune", check=False)
    git("worktree", "add", "--detach", str(wt), base)
    try:
        merged = git("merge", "--no-commit", "--no-ff", p["head"], cwd=wt, check=False,
                     env=dict(os.environ, GIT_MERGE_AUTOEDIT="no"))
        if merged.returncode != 0:
            conflicted = [f for f in git("diff", "--name-only", "--diff-filter=U", cwd=wt).splitlines() if f]
            if not conflicted:
                raise GitError("merge failed without conflicts: " + merged.stderr.strip()[-200:])
            unresolved = [path for path in conflicted if path != "AGENTS.md"
                          and not resolve_ballot_append(wt, path, p["office"])]
            if unresolved:
                entry.update({"status": "conflict", "reason": "conflicts with main in " + ", ".join(unresolved[:8])})
                return False
        # The canonical Founder policy always wins over a branch's old copy.
        git("checkout", base, "--", "AGENTS.md", cwd=wt, check=False)
        git("add", "-A", cwd=wt)
        tree = git("write-tree", cwd=wt)
        if tree == git("rev-parse", base + "^{tree}"):
            entry.update({"status": "no_delta", "reason": "main already contains this change"})
            return False
        blocked = canonical_preflight(base, tree)
        if blocked:
            entry.update({"status": "approved", "reason": "waiting: " + blocked})
            return False
        text = messages(base, p["head"])
        if "Act25-Phase:" in text:
            entry.update({"status": "refused", "reason": "an Act 25 phase lands under Act 26, by hand"})
            return False
        bill = None
        if info["laws"]:
            bill = trailer(text, "Enacts")
            if not bill or not re.fullmatch(r"[a-zA-Z0-9_-]+", bill):
                entry.update({"status": "refused", "reason": "changes law or seats without an 'Enacts: BILL' trailer"})
                return False
        git("merge", "--quit", cwd=wt, check=False)
        subject = git("log", "-1", "--format=%s", p["head"])
        body = ["Integrate %s (%s): %s" % (p["branch"], p["office"], subject[:120]), "",
                "Landed by the integration queue (Act 31) as one candidate on main %s." % base[:12], "",
                "Delivery-Branch: " + p["branch"],
                "Delivery-Head: " + p["head"],
                "Proposed-By: " + p["office"],
                "Reviewed-By: " + (review["office"] if review else "none (additive records, Act 31 §3)"),
                "Integrated-By: government/integrator.py (Act 31)"]
        if review:
            body.insert(-1, "Review-Reason: " + " ".join(str(review.get("reason", "")).split())[:300])
        if bill:
            body.insert(-1, "Enacts: " + bill)
        msgfile = ROOT / "message.txt"
        atomic_write(msgfile, "\n".join(body) + "\n")
        git("commit", "-q", "--no-verify", "-F", str(msgfile), cwd=wt, env=IDENT)
        candidate = git("rev-parse", "HEAD", cwd=wt)
        if git("rev-parse", candidate + "^") != base or git("rev-parse", candidate + "^{tree}") != tree:
            entry.update({"status": "refused", "reason": "candidate is not a single commit on main"})
            return False
        if bill:
            tally = subprocess.run(["/bin/sh", str(wt / "government" / "tally.sh"), bill],
                                   capture_output=True, text=True, cwd=str(wt),
                                   env=dict(os.environ, VICHE_TOWN_ROOT=str(wt)))
            if tally.returncode != 0:
                entry.update({"status": "refused", "reason": "tally.sh %s does not pass: %s" % (bill, tally.stdout.strip()[-200:])})
                return False
        suite = suite_for(info["paths"])
        logs = DELIVERY / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        check = subprocess.run(["/bin/sh", str(wt / "government" / "suite-status.sh"),
                                "--commit", candidate, "--suite", suite],
                               capture_output=True, text=True, cwd=str(wt),
                               env=dict(os.environ, VICHE_TOWN_ROOT=str(wt),
                                        SUITE_STATUS_VERIFIER="integrator",
                                        SUITE_STATUS_LOG_DIR=str(logs)))
        status_file = wt / "records" / "suite-status.json"
        record = load(status_file, {})
        exact = record.get("commit") == candidate and record.get("tree") == tree
        if not exact:
            if check.returncode != 0:
                # A verifier setup failure, timeout before a record, or lost
                # evidence is not two red tests. Never reuse main's old result.
                entry.update({"status": "approved", "reason":
                              "verification unavailable (exit %d); no fresh exact-candidate record; retry" % check.returncode,
                              "log": None})
            else:
                entry.update({"status": "refused", "reason": "suite record does not name the exact candidate"})
            return False
        if check.returncode != 0 or record.get("result") != "green":
            runs = record.get("runs")
            twice_red = (check.returncode == 1 and record.get("result") == "red"
                         and isinstance(runs, list) and len(runs) == 2
                         and all(isinstance(run, dict) and run.get("run") == i
                                 and run.get("result") == "red"
                                 and type(run.get("exit")) is int and run["exit"] != 0
                                 and isinstance(run.get("output_sha256"), str)
                                 and re.fullmatch(r"[0-9a-f]{64}", run["output_sha256"])
                                 for i, run in enumerate(runs, 1)))
            if twice_red:
                entry.update({"status": "red", "reason": "%s failed twice on the merged candidate" % suite,
                              "log": str(logs / ("suite-%s.log" % runs[-1]["output_sha256"]))})
            else:
                entry.update({"status": "approved", "reason":
                              "verification unavailable or inconsistent exact record (exit %d); retry" % check.returncode,
                              "log": None})
            return False
        receipt = DELIVERY / ("verified-%s.json" % candidate)
        shutil.copyfile(str(status_file), str(receipt))
        git("add", "records/suite-status.json", cwd=wt)
        git("commit", "-q", "--no-verify", "-m", "Act 21 suite-status for %s (%s green)" % (candidate[:12], suite),
            cwd=wt, env=IDENT)
        carrier = git("rev-parse", "HEAD", cwd=wt)
        carrier_paths = git("diff", "--name-only", candidate, carrier).splitlines()
        assertions = [
            {"name": "candidate parent is main", "expected": base, "actual": git("rev-parse", candidate + "^")},
            {"name": "candidate tree is the merge of main and the delivery head", "expected": tree,
             "actual": git("rev-parse", candidate + "^{tree}")},
            {"name": "suite result on the exact candidate", "expected": "green", "actual": record.get("result")},
            {"name": "carrier changes only records/suite-status.json",
             "expected": ["records/suite-status.json"], "actual": carrier_paths},
            {"name": "carrier parent is the candidate", "expected": candidate, "actual": git("rev-parse", carrier + "^")},
        ]
        if any(a["expected"] != a["actual"] for a in assertions):
            # No push occurred. A concurrent process may have replaced the
            # temporary working HEAD during verification. Preserve the failed
            # assertion and retry under the internal lock, never waive the gate.
            entry.update({"status": "approved",
                          "reason": "pre-landing assertion failed; no push; retry",
                          "assertions": assertions})
            return False
        blocked = canonical_preflight(base, carrier)
        if blocked:
            entry.update({"status": "approved", "reason": "waiting: " + blocked})
            return False
        prelanding = {"generated_by": "government/integrator.py", "act": 31, "at": iso(now()),
                      "branch": p["branch"], "head": p["head"], "office": p["office"],
                      "proposed_at": p["at"],
                      "reviewed_by": review["office"] if review else None,
                      "review_reason": review.get("reason") if review else None,
                      "base": base, "candidate": candidate, "tree": tree, "carrier": carrier,
                      "suite": suite, "suite_record_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
                      "enacts": bill, "paths": info["paths"], "assertions": assertions}
        atomic_write(DELIVERY / ("integration-%s.json" % candidate), json.dumps(prelanding, sort_keys=True, indent=1) + "\n")
        atomic_write(pending_publication(candidate), json.dumps(prelanding, sort_keys=True, indent=1) + "\n")
        pushed = git("push", "-q", "origin", carrier + ":refs/heads/main", cwd=wt, check=False)
        if pushed.returncode != 0:
            entry.update({"status": "approved", "reason":
                          "publication unconfirmed (git exit %d); reconcile against fresh remote main" % pushed.returncode})
            return False
        finalize_publication(prelanding, entry)
        return True
    finally:
        git("worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(str(wt), ignore_errors=True)


# ---------------------------------------------------------------- the pass

def run():
    if os.environ.get("VICHE_INTEGRATOR", "on") == "off":
        return 0
    ROOT.mkdir(parents=True, exist_ok=True)
    # Supervisor locking is not enough: agents may invoke integrator.py
    # directly. Shared ROOT/work must never have two concurrent writers.
    # A DIFFERENT file from the outer S6 run.lock avoids self-deadlock.
    with (ROOT / "internal.lock").open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("internal lock busy; another integration run owns worktree")
            return 0
        return run_locked()


def landing_batch(ready):
    """Bounded record-first service, with a guaranteed oldest-code slot.

    The ready set is a finite snapshot. An aged code candidate cannot force
    ballots or evidence to wait for a full suite before making any progress;
    an unbounded record arrival stream cannot starve code either.
    """
    records = sorted((item for item in ready if item[3] == "tests/records-smoke.sh"),
                     key=lambda item: (item[0]["at"], item[0]["branch"]))
    full = sorted((item for item in ready if item[3] != "tests/records-smoke.sh"),
                  key=lambda item: (item[0]["at"], item[0]["branch"]))
    return records[:RECORD_BATCH_LIMIT] + full[:1]


def run_locked():
    try:
        git("fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main",
            "+refs/heads/delivery/*:refs/remotes/origin/delivery/*")
    except GitError as error:
        log("fetch failed, nothing done: %s" % error)
        return 1
    base = git("rev-parse", "refs/remotes/origin/main")
    state = load(ROOT / "state.json", {})
    recover_publications(state, base)
    all_reviews = reviews()
    ready = []
    for p in proposals():
        key = "%s@%s" % (p["branch"], p["head"])
        entry = state.setdefault(key, {"status": "queued", "branch": p["branch"], "head": p["head"],
                                       "office": p["office"], "proposed_at": p["at"]})
        if entry["status"] in TERMINAL:
            continue
        current = git("rev-parse", "refs/remotes/origin/" + p["branch"], check=False)
        if current.returncode != 0 or current.stdout.strip() != p["head"]:
            entry.update({"status": "superseded", "reason": "the branch no longer points at this commit; propose again"})
            continue
        if now() - p["at"] > EXPIRE_SECONDS and entry["status"] != "approved":
            entry.update({"status": "expired", "reason": "not landed within 14 days; propose again if still wanted"})
            continue
        try:
            info = classify(base, p["head"])
        except GitError as error:
            entry.update({"status": "refused", "reason": "unreadable history: %s" % error})
            continue
        if not info["paths"]:
            entry.update({"status": "no_delta", "reason": "nothing to land"})
            continue
        if info["protected"]:
            entry.update({"status": "refused", "reason": "the Constitution is the Founder's: " + info["protected"]})
            continue
        review = None
        if not info["additive"] or info["laws"]:
            review = verdict_for(p, all_reviews)
            if review and review["verdict"] == "reject":
                entry.update({"status": "rejected", "reason": "%s: %s" % (review["office"], review.get("reason", ""))})
                continue
            if not review:
                commissioned = int(entry.get("review_commissioned_at", 0))
                agent = entry.get("reviewer_agent")
                due = (not agent or now() - commissioned > REVIEW_TIMEOUT or reviewer_finished(agent))
                if due and int(entry.get("review_attempts", 0)) >= REVIEW_ATTEMPTS:
                    entry.update({"status": "review_stalled",
                                  "reason": "no verdict after %d reviewer attempts" % REVIEW_ATTEMPTS})
                elif due:
                    entry["status"] = "awaiting_review"
                    commission_reviewer(p, base, entry)
                continue
        entry.update({"status": "approved", "reason": None,
                      "reviewed_by": review["office"] if review else None})
        ready.append((p, entry, review, suite_for(info["paths"])))
    # A newer proposal on the same branch replaces every older unfinished one.
    latest = {p["branch"]: p["head"] for p in proposals()}
    for entry in state.values():
        if (entry.get("status") not in TERMINAL and entry.get("branch") in latest
                and entry.get("head") != latest[entry["branch"]]):
            entry.update({"status": "superseded", "reason": "a newer commit was proposed on this branch"})
    def persist():
        publish(state)
        atomic_write(ROOT / "state.json", json.dumps(state, sort_keys=True, indent=1) + "\n")
        clear_finalized_publications(state)

    persist()
    for p, entry, review, suite in landing_batch(ready):
        if entry.get("status") in TERMINAL:
            continue
        try:
            land(p, entry, review)
        except (GitError, OSError, subprocess.SubprocessError) as error:
            entry.update({"status": "approved", "reason": "landing error, retried next cycle: %s" % error})
            log("landing %s failed: %s" % (p["branch"], error))
        entry["updated_at"] = now()
        persist()  # wake an office as soon as its record lands, before a full suite
    for key, entry in state.items():
        if entry.get("status") in TERMINAL and entry.get("head"):
            review_wt = ROOT / "review" / entry["head"][:12]
            if review_wt.exists():
                git("worktree", "remove", "--force", str(review_wt), check=False)
    publish(state)
    atomic_write(ROOT / "state.json", json.dumps(state, sort_keys=True, indent=1) + "\n")
    return 0


def publish(state):
    queue = sorted(state.values(), key=lambda e: e.get("proposed_at", 0))
    atomic_write(DELIVERY / "queue.json", json.dumps(
        {"at": iso(now()), "entries": queue}, sort_keys=True, indent=1) + "\n")
    by_office = {}
    for e in queue:
        if e.get("_seen_status") != e["status"]:
            e["_seen_status"], e["status_since"] = e["status"], now()
        if e["status"] in TERMINAL and now() - int(e.get("status_since", 0)) > LANDED_VISIBLE:
            continue
        if e["status"] in ("superseded", "no_delta"):
            continue
        # Only state that should wake the office; no timestamps that change by themselves.
        by_office.setdefault(e["office"], []).append(
            {k: e.get(k) for k in ("branch", "head", "status", "reason", "candidate", "log", "reviewer_agent")})
    OFFICES.mkdir(parents=True, exist_ok=True)
    for path in OFFICES.glob("*.json"):
        if path.stem not in by_office:
            path.unlink()
    for office, entries in by_office.items():
        atomic_write(OFFICES / (office + ".json"), json.dumps(entries, sort_keys=True, indent=1) + "\n")


ADVICE = {
    "landed": "landed on main as {candidate}",
    "approved": "approved; landing ({reason})",
    "queued": "queued",
    "awaiting_review": "waiting for an independent reviewer",
    "reviewing": "under independent review by agent {reviewer_agent}",
    "review_stalled": "no reviewer verdict ({reason}); ask any other office to review it with government/review-delivery.sh",
    "rejected": "REJECTED by {reason}. Fix it on your branch and propose again",
    "red": "RED: {reason}; log {log}. Fix it on your branch and propose again",
    "conflict": "CONFLICT: {reason}. Merge main into your branch and propose again",
    "refused": "REFUSED: {reason}",
    "expired": "expired: {reason}",
}


def office_brief(office):
    entries = load(OFFICES / (office + ".json"), [])
    if not entries:
        return ""
    lines = ["=== YOUR DELIVERIES (integration queue, Act 31) ==="]
    for e in entries:
        text = ADVICE.get(e.get("status"), e.get("status") or "?").format(
            **{k: (e.get(k) or "")[:300] if isinstance(e.get(k), str) else (e.get(k) or "") for k in
               ("candidate", "reason", "log", "reviewer_agent")})
        lines.append("- %s (%s): %s" % (e["branch"], (e.get("head") or "")[:12], text))
    lines.append("=== END YOUR DELIVERIES ===")
    return "\n".join(lines)


def main(argv):
    command = argv[0] if argv else "run"
    if command == "run":
        return run()
    if command == "status":
        print(json.dumps(load(DELIVERY / "queue.json", {}), sort_keys=True, indent=1))
        return 0
    if command == "office" and len(argv) == 2:
        brief = office_brief(argv[1])
        if brief:
            print(brief)
        return 0
    print("usage: integrator.py run | status | office OFFICE", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
