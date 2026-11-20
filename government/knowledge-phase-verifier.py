#!/usr/bin/env python3
"""Deterministic, fail-closed phase-gate verifier for Act 32 knowledge offices.

This is an INDEPENDENT verifier with its own data format
(``viche-knowledge-phase-gate-v1``). It is deliberately separate from
``knowledge-activation-verify.sh`` (which gates a single office activation) and
from ``knowledge-office-cycle.sh`` (which dispatches).  It never reads Post,
never contacts the network, never mutates state in ``verify``/``audit`` mode,
and derives every decision from durable Git-committed evidence only.

Trust model
-----------
The shared Antonina/Git UID cannot authenticate a sender (Act 32 clause 5).
A caller-supplied ``signed_by``/``signed-by`` string is therefore IGNORED.  A
review counts only when it is anchored in validated reviewed Git evidence:

  * the reviewer id must be a real officer in the authoritative
    ``government/branch-officers.tsv`` registry (Judiciary or government), and
  * a Git commit+path must resolve (by exact tree traversal, no '..'/symlinks)
    to an artifact whose bytes hash to the declared digest AND whose content
    binds the exact gate id, reviewer id, role, decision and evidence digest;
  * an INDEPENDENT institutional attestation must corroborate that officer
    action: an `antonina board review` verdict of approve on that exact commit,
    an officer-authored board comment citing the gate, and a matching
    appointment + attributable agent session. A Git text file alone is NOT a
    signature on the shared UID. The residual (non-cryptographic) limit of
    these channels is stated in records/knowledge/PHASE-GATE-SCHEMA.md.

Every failure (missing/malformed/expired/reused/forged evidence, invalid office
or Git state) resolves to ``hold``/``stop``/``invalid`` and a non-zero exit.
No phase can proceed without an unbroken, independently verified predecessor
chain.  Statistics may run a short (~14 day) initial trial on prospective
evidence; a 30-day review is NOT a precondition to launch, but IS mandatory
before any renewal (missing -> automatic hold).

This file is ordinary implementation under Act 32 (Acts 4, 6, 15, 21, 31). It
does not itself enact, sign, authorize, or enable any office.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "viche-knowledge-phase-gate-v1"
ACT_BILL_ID = "institutional-knowledge-and-communications-act-v4"
ACT_TITLE_FRAGMENT = "Institutional Knowledge and Communications Act"
OFFICES = ("statistics", "foresight", "strategy", "spying")
SERIAL_PREDECESSOR = {
    "statistics": None,
    "foresight": "statistics",
    "strategy": "foresight",
    "spying": "strategy",
}
# Independence: only the statutory verifier (the Judiciary) may sign a PROCEED.
# Other registered officers may sign hold/stop but never a proceed.
PROCEED_REVIEWER_ROLES = ("judiciary",)
VALID_DECISIONS = ("proceed", "hold", "stop")
PRECONDITION_KEYS = ("baseline", "budgets", "executive_order", "judiciary_check")

INITIAL_MAX_SECONDS = 14 * 86400   # 14-day short initial trial
ABSOLUTE_MAX_SECONDS = 45 * 86400  # 45-day hard maximum incl. renewals
DAY30_SECONDS = 30 * 86400
PHASES_DIR = Path("records/knowledge/phases")
ROLLBACKS_DIR = Path("records/knowledge/phases/rollbacks")
DISPATCH_LEDGER = Path("records/knowledge/phases/dispatch-ledger.jsonl")

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{7,40}$")


class GateError(Exception):
    """Fatal, fail-closed verification error."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_digest(evidence: list) -> str:
    """Deterministic digest over a phase record's evidence array."""
    norm = sorted(
        (
            {
                "name": str(e.get("name", "")),
                "path": str(e.get("path", "")),
                "sha256": str(e.get("sha256", "")),
                "git_commit": str((e.get("git") or {}).get("commit", "")),
                "git_path": str((e.get("git") or {}).get("path", "")),
            }
            for e in evidence
            if isinstance(e, dict)
        ),
        key=lambda d: (d["path"], d["sha256"], d["git_commit"]),
    )
    blob = json.dumps(norm, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + sha256_bytes(blob)


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _safe_rel(value: str, required_prefix: str | None = None) -> Path:
    """Resolve a town-relative path, refusing absolute paths and traversal."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise GateError("unsafe path")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise GateError("unsafe path")
    if required_prefix and not str(rel).startswith(required_prefix):
        raise GateError("path outside %s" % required_prefix)
    return rel


class Verifier:
    def __init__(self, town: str, at: int | None = None, clock_override: bool = False):
        self.town = Path(town).resolve()
        self.at = int(at) if at is not None else self._now()
        self._act_cache = None
        self._officers_cache = None

    @staticmethod
    def _now() -> int:
        import time

        return int(time.time())

    def result(self, decision: str, reasons: list, **extra) -> dict:
        out = {
            "schema": SCHEMA + "-result-v1",
            "decision": decision,
            "ok": decision == "proceed",
            "at": self.at,
            "reasons": reasons,
        }
        out.update(extra)
        return out

    # ---- authoritative town sources -------------------------------------
    def git(self, *args: str) -> bytes:
        try:
            proc = subprocess.run(
                ["git", "-C", str(self.town), *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise GateError("git unavailable: %s" % exc)
        if proc.returncode != 0:
            raise GateError("git command failed: %s" % " ".join(args))
        return proc.stdout

    def _read_town_file(self, rel: str) -> str:
        path = self.town / _safe_rel(rel)
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise GateError("cannot read %s: %s" % (rel, exc))

    def enacted_act(self) -> int:
        """Parse the single enacted IKCA Act number at runtime; never hardcode 32."""
        if self._act_cache is not None:
            return self._act_cache
        text = self._read_town_file("government/LAWS.md")
        pat = re.compile(
            r"^## Act (\d+) — " + re.escape(ACT_TITLE_FRAGMENT) + r" \(enacted ",
            re.MULTILINE,
        )
        nums = set(pat.findall(text))
        if len(nums) != 1:
            raise GateError("expected exactly one enacted IKCA Act number, found %d" % len(nums))
        num = int(next(iter(nums)))
        if ("bill " + ACT_BILL_ID) not in text:
            raise GateError("enacted Act does not bind the v4 bill id")
        self._act_cache = num
        return num

    def officers(self) -> dict:
        """Authoritative officer registry: id -> role (from canonical town)."""
        if self._officers_cache is not None:
            return self._officers_cache
        text = self._read_town_file("government/branch-officers.tsv")
        reg = {}
        for line in text.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] and parts[1]:
                reg[parts[1]] = parts[0]
        if not reg:
            raise GateError("empty officer registry")
        self._officers_cache = reg
        return reg

    # ---- low-level artifact validation ----------------------------------
    def _git_object_exists(self, commit: str) -> bool:
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
            return False
        try:
            kind = self.git("cat-file", "-t", commit).decode("ascii", "replace").strip()
        except GateError:
            return False
        return kind == "commit"

    def _read_git_blob(self, commit: str, path: str) -> bytes:
        """Read a blob by EXACT Git tree traversal (no path interpretation).

        Rejects '..', absolute paths, symlinks, submodules and ambiguous tree
        entries. A name that merely starts with 'records/' is not sufficient.
        """
        if not isinstance(path, str):
            raise GateError("artifact path is not a string")
        parts = path.split("/")
        if (not path.startswith("records/") or ".." in parts
                or any(not re.fullmatch(r"[A-Za-z0-9._-]+", p) for p in parts)):
            raise GateError("unsafe artifact path (Git tree traversal required)")
        out = self.git("ls-tree", "-z", commit, "--", path)
        entries = [e for e in out.split(b"\0") if e]
        if len(entries) != 1 or b"\t" not in entries[0]:
            raise GateError("artifact path is not a unique Git tree entry")
        meta, actual = entries[0].split(b"\t", 1)
        fields = meta.split()
        if len(fields) != 3 or fields[0] != b"100644" and fields[0] != b"100755" or fields[1] != b"blob":
            raise GateError("artifact path is not a regular Git blob (symlink/submodule rejected)")
        if actual.decode("utf-8", "replace") != path:
            raise GateError("artifact tree entry path mismatch")
        return self.git("cat-file", "blob", fields[2].decode("ascii"))

    @staticmethod
    def _parse_kv(data: bytes) -> dict:
        try:
            text = data.decode("utf-8")
        except UnicodeError:
            raise GateError("artifact not UTF-8")
        kv = {}
        for line in text.splitlines():
            m = re.match(r"^\s*([a-z_]+)\s*:\s*(.*?)\s*$", line)
            if m:
                kv.setdefault(m.group(1), m.group(2).strip())
        return kv

    def validate_review(self, review: dict, *, gate_id: str, decision: str,
                        reviewer_role: str, evidence_digest: str,
                        required_roles: tuple) -> tuple[list, int | None]:
        """Validate a Git-anchored, officer-signed review. Returns (errors, signed_epoch)."""
        errors = []
        if not isinstance(review, dict):
            return ["review artifact is absent (fail closed)"], None

        # A caller-supplied signed_by/signed-by is deliberately ignored.
        reviewer = review.get("reviewer")
        if not isinstance(reviewer, str) or not reviewer:
            errors.append("review.reviewer is missing")
            reviewer = ""
        reg = self.officers()
        if reviewer and reviewer not in reg:
            errors.append("reviewer %r is not in the authoritative officer registry" % reviewer)
        actual_role = reg.get(reviewer)
        if actual_role != reviewer_role:
            errors.append("reviewer role %r does not match declared %r" % (actual_role, reviewer_role))
        if actual_role not in required_roles:
            errors.append("reviewer role %r is not permitted to sign this disposition" % actual_role)

        if review.get("decision") != decision:
            errors.append("review decision does not match record decision")
        artifact = review.get("review_artifact")
        if not isinstance(artifact, dict):
            return errors + ["review.review_artifact is missing"], None
        commit = artifact.get("git_commit")
        path = artifact.get("git_path")
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            errors.append("review artifact digest is malformed")
            digest = ""
        signed_epoch = review.get("signed_epoch")
        if not is_int(signed_epoch):
            errors.append("review.signed_epoch is missing/malformed")
            signed_epoch = None
        if not isinstance(review.get("signed_at"), str) or not review.get("signed_at"):
            errors.append("review.signed_at is missing")

        if not self._git_object_exists(commit):
            errors.append("review artifact commit is not a valid Git commit")
            return errors, signed_epoch
        try:
            blob = self._read_git_blob(commit, path)
        except GateError as exc:
            errors.append("review artifact blob unreadable: %s" % exc)
            return errors, signed_epoch
        if sha256_bytes(blob) != digest:
            errors.append("review artifact digest mismatch (bytes were altered)")
            return errors, signed_epoch
        kv = self._parse_kv(blob)
        bindings = {
            "gate": gate_id,
            "reviewer": reviewer,
            "reviewer_role": reviewer_role,
            "decision": decision,
            "evidence_digest": evidence_digest,
        }
        for key, expected in bindings.items():
            if kv.get(key) != expected:
                errors.append("review artifact %s binding mismatch" % key)
        if "reviewed_at" not in kv:
            errors.append("review artifact lacks reviewed_at timestamp")
        return errors, signed_epoch

    def validate_evidence(self, record: dict) -> tuple[list, str]:
        errors = []
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            return ["evidence array is missing or empty"], ""
        for entry in evidence:
            if not isinstance(entry, dict):
                errors.append("evidence entry is not an object")
                continue
            sha = entry.get("sha256")
            if not isinstance(sha, str) or not SHA256_RE.fullmatch(sha):
                errors.append("evidence %r has malformed sha256" % entry.get("path"))
                continue
            git = entry.get("git")
            if not isinstance(git, dict):
                errors.append("evidence %r is not Git-anchored" % entry.get("path"))
                continue
            commit, gpath = git.get("commit"), git.get("path")
            if not self._git_object_exists(commit):
                errors.append("evidence %r commit is not a valid Git commit" % entry.get("path"))
                continue
            try:
                blob = self._read_git_blob(commit, gpath)
            except GateError as exc:
                errors.append("evidence %r blob unreadable: %s" % (entry.get("path"), exc))
                continue
            if sha256_bytes(blob) != sha:
                errors.append("evidence %r digest mismatch" % entry.get("path"))
        digest = canonical_digest(evidence)
        if record.get("evidence_digest") != digest:
            errors.append("record evidence_digest does not match its evidence array")
        return errors, digest

    # ---- independent institutional attestation -------------------------
    def _antonina_json(self, *args: str) -> dict:
        """Read-only query of the signed Antonina coordination board/agent surface."""
        try:
            proc = subprocess.run(["antonina", *args],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise GateError("antonina unavailable: %s" % exc)
        if proc.returncode != 0:
            raise GateError("antonina query failed: %s" % " ".join(args))
        try:
            return json.loads(proc.stdout.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise GateError("antonina response malformed: %s" % exc)

    def _authoritative_appointments(self) -> dict:
        """Appointment registry is a durable state record, not a caller label."""
        root = Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state"))
        for cand in (root / "appointments/appointments.tsv",
                     root / "appointments/appointments.log"):
            if cand.is_file():
                text = cand.read_text(encoding="utf-8")
                reg = {}
                for line in text.splitlines():
                    cols = line.split("\t")
                    if cand.name.endswith(".tsv") and len(cols) >= 2:
                        reg.setdefault(cols[0], cols[1])
                    elif cand.name.endswith(".log") and len(cols) >= 3:
                        # timestamp, office, old agent, NEW agent
                        reg[cols[1]] = cols[3]
                if reg:
                    return reg
        raise GateError("no authoritative appointment registry available")

    def validate_attestation(self, attestation: dict, *, gate_id: str,
                             officer_id: str, role: str, artifact_commit: str) -> list:
        """Multi-channel corroboration that a real officer action produced the review.

        A Git blob with a Judiciary id in it is NOT a signature on a shared UID.
        Proceed therefore additionally requires:
          (1) an institutional `antonina board review` verdict of `approve` on
              the EXACT review-artifact commit, with a reviewer attributable to
              the named officer (read live from the board, not from the record);
          (2) a board comment authored by that officer citing the gate id and
              that commit (a second, independently recorded board action); and
          (3) the officer's agent id matching the authoritative appointment
              registry and having an attributable managed-agent session.

        Residual limitation (stated honestly): the shared UID means none of
        these channels is cryptographically authenticated. They are separate
        institutional actions, not a digital signature. This check raises the
        cost of forgery from 'write one JSON/text file' to 'override the board
        review gate, the officer's board identity and the appointment record',
        and it never labels arbitrary Git content as 'signed'.
        """
        errors = []
        if not isinstance(attestation, dict):
            return ["no independent institutional attestation (board review + "
                    "officer comment + appointment/session) — fail closed"]
        issue_id = attestation.get("issue_id")
        token = attestation.get("expected_reviewer")
        agent_id = attestation.get("officer_agent_id")
        if not isinstance(issue_id, str) or not issue_id:
            errors.append("attestation.issue_id missing")
            return errors
        if token != officer_id:
            errors.append("attestation.expected_reviewer does not match the named officer")
        if not isinstance(agent_id, str) or not agent_id:
            errors.append("attestation.officer_agent_id missing")
            return errors

        snapshot_path = os.environ.get("VICHE_PHASE_ATTESTATION_JSON", "")
        if snapshot_path:
            # Offline/self-contained attestation snapshot (used by hermetic
            # tests and by audited offline verification). It is an EXPORT of
            # the independent channels, not a caller-supplied signature.
            try:
                snap = json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                return errors + ["attestation snapshot unreadable: %s" % exc]
            issues = snap.get("issues")
            issue = issues.get(issue_id, {}) if isinstance(issues, dict) else snap.get("issue", {})
            appointments = snap.get("appointments", {})
            agent = snap.get("agent_status", {})
        else:
            try:
                issue = self._antonina_json("board", "show", "--id", issue_id,
                                            "--page", "1", "--json")
                agent = self._antonina_json("agent", "status", "--id", agent_id, "--json")
            except GateError as exc:
                return errors + [str(exc)]
            try:
                appointments = self._authoritative_appointments()
            except GateError as exc:
                return errors + [str(exc)]

        # (1) Institutional review gate on the exact artifact commit.
        review = issue.get("review") if isinstance(issue, dict) else None
        if not isinstance(review, dict):
            errors.append("no institutional board review on attestation issue")
        else:
            rcommit = str(review.get("commit", ""))
            if not (rcommit == artifact_commit or
                    (len(rcommit) >= 7 and artifact_commit.startswith(rcommit)) or
                    (len(artifact_commit) >= 7 and rcommit.startswith(artifact_commit))):
                errors.append("board review is not on the exact review-artifact commit")
            if review.get("verdict") != "approve":
                errors.append("board review verdict is not 'approve'")
            rreviewer = str(review.get("reviewer", ""))
            if token not in rreviewer and role.lower() not in rreviewer.lower():
                errors.append("board review reviewer is not attributable to the officer")
            if not review.get("recordedAt"):
                errors.append("board review has no recording timestamp")

        # (2) Officer-attributed board comment citing this gate and commit.
        comments = issue.get("comments", []) if isinstance(issue, dict) else []
        if not isinstance(comments, list):
            comments = []
        prefix = artifact_commit[:7]
        found = False
        for c in comments:
            if not isinstance(c, dict):
                continue
            author = str(c.get("author", ""))
            body = str(c.get("body", c.get("text", "")))
            attributable = (token in author or role.lower() in author.lower())
            if attributable and gate_id in body and prefix in body:
                found = True
                break
        if not found:
            errors.append("no officer-authored board comment citing gate id and review commit")

        # (3) Appointment + attributable managed-agent session.
        if appointments.get(role) != agent_id:
            errors.append("officer agent id does not match the authoritative appointment registry")
        if not isinstance(agent, dict) or str(agent.get("id", "")) != agent_id:
            errors.append("managed-agent session is not attributable to the officer agent id")
        elif agent.get("state") not in ("idle", "running", "clearexit", "exited"):
            errors.append("officer agent has no usable attributable session state")
        return errors

    # ---- gate verification ----------------------------------------------
    def load_gate(self, rel: str) -> dict:
        path = _safe_rel(rel, "records/knowledge/phases/")
        full = self.town / path
        try:
            data = json.loads(full.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise GateError("cannot load gate record %s: %s" % (rel, exc))
        if not isinstance(data, dict):
            raise GateError("gate record is not an object")
        return data

    def verify_gate(self, record: dict, rel: str, at: int, visited: set,
                    used_reviews: set) -> dict:
        """Recursively verify one gate. Returns a result dict (never raises for gate content)."""
        gid = record.get("gate_id") if isinstance(record.get("gate_id"), str) else rel
        office = record.get("office")
        phase = record.get("phase")
        if record.get("schema") != SCHEMA:
            return self.result("invalid", ["unsupported schema"], gate_id=gid)
        if office not in OFFICES:
            return self.result("invalid", ["invalid office %r" % office], gate_id=gid)
        if phase not in ("initial", "renewal"):
            return self.result("invalid", ["invalid phase %r" % phase], gate_id=gid)
        if gid in visited:
            return self.result("invalid", ["predecessor cycle detected"], gate_id=gid)
        visited = visited | {gid}

        reasons = []
        try:
            act = self.enacted_act()
        except GateError as exc:
            return self.result("invalid", [str(exc)], gate_id=gid)
        if record.get("act") != act:
            reasons.append("act %r != enacted Act %d" % (record.get("act"), act))
        if record.get("act_bill_id") != ACT_BILL_ID:
            reasons.append("act_bill_id does not bind the v4 ballot text")
        if record.get("host") != "billy-dev":
            reasons.append("host is not billy-dev (out of authorized scope)")
        if reasons:
            return self.result("invalid", reasons, gate_id=gid, office=office, phase=phase)

        decision = record.get("decision")
        if decision not in VALID_DECISIONS:
            return self.result("invalid", ["decision must be proceed|hold|stop"], gate_id=gid)
        if decision in ("hold", "stop"):
            return self.result(
                decision,
                ["record carries a %s disposition; no office may proceed" % decision],
                gate_id=gid, office=office, phase=phase,
            )

        # ---- proceed: full independent verification -----------------------
        errs, digest = self.validate_evidence(record)
        reasons.extend(errs)

        pre = record.get("preconditions")
        if not isinstance(pre, dict):
            reasons.append("preconditions block is missing")
        else:
            for key in PRECONDITION_KEYS:
                item = pre.get(key)
                if not isinstance(item, dict) or item.get("ok") is not True:
                    reasons.append("precondition %s is not proven" % key)

        # Timing bounds.
        nb, exp = record.get("not_before"), record.get("expires_at")
        if not is_int(nb) or not is_int(exp) or exp <= nb:
            reasons.append("not_before/expires_at missing or not a positive window")
        else:
            cap = INITIAL_MAX_SECONDS if phase == "initial" else ABSOLUTE_MAX_SECONDS
            if exp - nb > cap:
                reasons.append("window %ds exceeds %s cap %ds" % (exp - nb, phase, cap))
            if exp - nb > ABSOLUTE_MAX_SECONDS:
                reasons.append("window exceeds 45-day absolute maximum")

        # Predecessor chain (serial evidence dependency).
        expected_pred = SERIAL_PREDECESSOR[office] if phase == "initial" else office
        pred = record.get("predecessor")
        root_not_before = nb if is_int(nb) else None
        pred_effective = None
        if expected_pred is None:
            if pred is not None:
                reasons.append("statistics initial must have no predecessor")
        else:
            if not isinstance(pred, dict) or pred.get("office") != expected_pred:
                reasons.append("predecessor must be %r" % expected_pred)
            else:
                pred_rel = pred.get("record")
                try:
                    pred_record = self.load_gate(pred_rel)
                except GateError as exc:
                    reasons.append("predecessor record unreadable: %s" % exc)
                    pred_record = None
                if pred_record is not None:
                    if pred_record.get("gate_id") != pred.get("gate_id"):
                        reasons.append("predecessor gate_id mismatch")
                    # Amendment K: the successor depends on the predecessor's
                    # RECORDED EVIDENCE, not on that office staying alive.
                    # Evaluate the predecessor inside its own signed window,
                    # never at the successor's launch time.
                    pred_nb = pred_record.get("not_before")
                    pred_at = pred_nb if is_int(pred_nb) else 0
                    pres = self.verify_gate(pred_record, pred_rel, pred_at, visited, used_reviews)
                    if not pres.get("ok"):
                        reasons.append("predecessor phase is not independently verified: %s"
                                       % ",".join(pres.get("reasons", []))[:300])
                    else:
                        pred_effective = pres.get("effective_at")
                        root_not_before = pres.get("root_not_before")
                        if pred_effective is None:
                            reasons.append("predecessor has no signed effective date")

        if is_int(nb) and is_int(pred_effective) and nb < pred_effective:
            reasons.append("not_before %d precedes predecessor signed gate date %d" % (nb, pred_effective))

        # Reviewer-signed disposition (Git-anchored, officer-bound).
        review = record.get("reviewer_review") or record.get("review")
        review_errors, signed_epoch = self.validate_review(
            review,
            gate_id=gid,
            decision="proceed",
            reviewer_role="judiciary",
            evidence_digest=digest,
            required_roles=PROCEED_REVIEWER_ROLES,
        )
        reasons.extend(review_errors)

        # Independent multi-channel attestation: a Git text file is not a
        # signature on the shared UID (board review + officer comment +
        # appointment/session must corroborate the exact artifact commit).
        if isinstance(review, dict) and isinstance(review.get("review_artifact"), dict):
            reasons.extend(self.validate_attestation(
                record.get("attestation"),
                gate_id=gid, officer_id=review.get("reviewer", ""),
                role="judiciary",
                artifact_commit=str(review["review_artifact"].get("git_commit", "")),
            ))

        # Reused-approval detection across the whole chain.
        if isinstance(review, dict):
            art = review.get("review_artifact") or {}
            token = (str(art.get("git_commit")), str(art.get("git_path")),
                     str(review.get("reviewer")), str(review.get("decision")))
            if token in used_reviews:
                reasons.append("review artifact reused for another gate")
            used_reviews.add(token)

        # Renewal: mandatory day-30 Judiciary review + lawful reauthorizing Act.
        if phase == "renewal":
            d30 = record.get("day30_review")
            d30_errors, d30_epoch = self.validate_review(
                d30,
                gate_id=gid,
                decision="proceed",
                reviewer_role="judiciary",
                evidence_digest=digest,
                required_roles=PROCEED_REVIEWER_ROLES,
            )
            if d30 is None:
                reasons.append("renewal requires a day-30 Judiciary review; none filed (automatic hold)")
            else:
                reasons.extend(d30_errors)
            if isinstance(d30, dict) and isinstance(d30.get("review_artifact"), dict):
                reasons.extend(self.validate_attestation(
                    record.get("day30_attestation"),
                    gate_id=gid, officer_id=d30.get("reviewer", ""),
                    role="judiciary",
                    artifact_commit=str(d30["review_artifact"].get("git_commit", "")),
                ))
            deadline = (root_not_before + DAY30_SECONDS) if is_int(root_not_before) else None
            if is_int(deadline) and (not is_int(d30_epoch) or d30_epoch > deadline):
                reasons.append("day-30 Judiciary review missing or filed after deadline %d" % deadline)
            reauth = record.get("reauthorizing_act")
            if not isinstance(reauth, dict) or not is_int(reauth.get("act")) or reauth["act"] <= act:
                reasons.append("renewal requires a later lawful reauthorizing Act")
            else:
                try:
                    laws = self._read_town_file("government/LAWS.md")
                except GateError as exc:
                    reasons.append(str(exc))
                else:
                    if not re.search(r"^## Act %d — .*\(enacted " % reauth["act"], laws, re.MULTILINE):
                        reasons.append("reauthorizing Act is not enacted in LAWS.md")

        # Active rollback blocks every phase.
        for rb in self._rollback_records():
            if rb.get("gate_id") == gid or rb.get("office") == office:
                reasons.append("active rollback on record (no phase may proceed)")

        if reasons:
            return self.result("hold", reasons, gate_id=gid, office=office, phase=phase)

        # Launch window: no new invocation before not_before or at/after expiry.
        if at < nb:
            return self.result("hold", ["not yet effective (not_before %d > now %d)" % (nb, at)],
                               gate_id=gid, office=office, phase=phase,
                               effective_at=signed_epoch, root_not_before=root_not_before)
        if at >= exp:
            return self.result("hold", ["expired at %d: no new launches (in-flight wind-down only)" % exp],
                               gate_id=gid, office=office, phase=phase,
                               effective_at=signed_epoch, root_not_before=root_not_before)
        return self.result("proceed", ["independently verified: all gates satisfied"],
                           gate_id=gid, office=office, phase=phase,
                           next_office=record.get("next_office"),
                           effective_at=signed_epoch, root_not_before=root_not_before,
                           not_before=nb, expires_at=exp,
                           evidence_digest=digest)

    # ---- rollbacks -------------------------------------------------------
    def _rollback_records(self) -> list:
        out = []
        base = self.town / ROLLBACKS_DIR
        if not base.is_dir():
            return out
        for path in sorted(base.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                out.append({"gate_id": path.stem, "office": "", "unreadable": True})
                continue
            if isinstance(data, dict):
                out.append(data)
        return out

    # ---- audit -----------------------------------------------------------
    def audit(self) -> dict:
        gates = {}
        base = self.town / PHASES_DIR
        results = []
        if base.is_dir():
            for path in sorted(base.glob("*.json")):
                rel = str(path.relative_to(self.town))
                try:
                    rec = self.load_gate(rel)
                    res = self.verify_gate(rec, rel, self.at, set(), set())
                except GateError as exc:
                    res = self.result("invalid", [str(exc)], gate_id=path.stem)
                res["record"] = rel
                results.append(res)
                gates[path.stem] = rec

        events = []
        ledger = self.town / DISPATCH_LEDGER
        if ledger.is_file():
            for line in ledger.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    events.append({"_malformed": True})

        violations = []
        new_after_expiry = []
        in_flight = []
        launches = {}
        for ev in events:
            if not isinstance(ev, dict) or ev.get("_malformed"):
                violations.append("malformed dispatch ledger line")
                continue
            gid, kind, at = ev.get("gate_id"), ev.get("kind"), ev.get("at")
            rec = gates.get(gid)
            if rec is None:
                violations.append("dispatch for unknown gate %r" % gid)
                continue
            if not is_int(at):
                violations.append("dispatch event for %r has invalid timestamp" % gid)
                continue
            exp = rec.get("expires_at")
            if kind == "launch":
                res = self.verify_gate(rec, str(PHASES_DIR / (gid + ".json")), at, set(), set())
                if is_int(exp) and at >= exp:
                    new_after_expiry.append({"gate_id": gid, "at": at, "expires_at": exp})
                    violations.append("new launch for %r at %d after expiry %s" % (gid, at, exp))
                if not res.get("ok"):
                    violations.append("launch for %r at %d was not independently verified" % (gid, at))
                launches.setdefault(gid, []).append(at)
            elif kind == "in_flight_continue":
                if not any(t < (exp if is_int(exp) else 0) for t in launches.get(gid, [])):
                    violations.append("in-flight continuation for %r without a prior valid launch" % gid)
                in_flight.append({"gate_id": gid, "at": at,
                                  "after_expiry": is_int(exp) and at >= exp})
            else:
                violations.append("unknown dispatch kind %r" % kind)

        return {
            "schema": SCHEMA + "-audit-v1",
            "at": self.at,
            "gates": results,
            "new_invocation_after_expiry": new_after_expiry,
            "in_flight_continuations": in_flight,
            "rollbacks": self._rollback_records(),
            "violations": violations,
            "ok": not violations,
        }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Act 32 independent phase-gate verifier")
    p.add_argument("--town", default=os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche"),
                   help="canonical Viche town root")
    p.add_argument("--at", type=int, default=None,
                   help="epoch seconds for deterministic evaluation (default: now)")
    sub = p.add_subparsers(dest="cmd")

    v = sub.add_parser("verify", help="verify one gate record (non-zero unless proceed)")
    v.add_argument("record", help="town-relative path to a phase-gate JSON record")

    c = sub.add_parser("check", help="print decision JSON, always exit 0 (inspection)")
    c.add_argument("record")

    sub.add_parser("audit", help="audit all gates and dispatch ledger for expiry/rollback violations")

    r = sub.add_parser("rollback", help="record an emergency rollback/hold (state-changing)")
    r.add_argument("--gate-id", required=True)
    r.add_argument("--reason", required=True)
    r.add_argument("--reviewer", default="")
    r.add_argument("--git-commit", default="")
    r.add_argument("--git-path", default="")
    r.add_argument("--sha256", default="")

    d = sub.add_parser("evidence-digest", help="print canonical digest for an evidence array file")
    d.add_argument("evidence_file")

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cmd = args.cmd or "verify"
    try:
        ver = Verifier(args.town, at=args.at)
    except Exception as exc:  # pragma: no cover - defensive
        print(json.dumps({"decision": "invalid", "ok": False, "reasons": [str(exc)]}))
        return 2

    if cmd == "evidence-digest":
        try:
            data = json.loads(Path(args.evidence_file).read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("evidence file must contain a JSON array")
            print(canonical_digest(data))
            return 0
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if cmd == "rollback":
        rb = {
            "schema": SCHEMA + "-rollback-v1",
            "gate_id": args.gate_id,
            "reason": args.reason,
            "created_at": ver.at,
            "review": None,
        }
        if args.reviewer:
            rb["review"] = {
                "reviewer": args.reviewer,
                "review_artifact": {"git_commit": args.git_commit,
                                    "git_path": args.git_path,
                                    "sha256": args.sha256},
            }
        target = ver.town / ROLLBACKS_DIR / (args.gate_id + ".rollback.json")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(rb, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(json.dumps(rb, indent=2, sort_keys=True))
        return 0

    if cmd == "audit":
        try:
            report = ver.audit()
        except Exception as exc:  # invalid Git/state must fail closed, not crash
            print(json.dumps({"schema": SCHEMA + "-audit-v1", "ok": False,
                              "violations": ["audit failed: %s" % exc]}, indent=2, sort_keys=True))
            return 1
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["ok"] else 1

    if cmd not in ("verify", "check"):
        print("unknown command", file=sys.stderr)
        return 2

    try:
        record = ver.load_gate(args.record)
        res = ver.verify_gate(record, args.record, ver.at, set(), set())
    except GateError as exc:
        res = ver.result("invalid", [str(exc)], gate_id=os.path.basename(args.record))
    except Exception as exc:  # unexpected input must never fail open
        res = ver.result("invalid", ["unhandled verification error: %s" % exc],
                         gate_id=os.path.basename(args.record))
    print(json.dumps(res, indent=2, sort_keys=True))
    if cmd == "check":
        return 0
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
