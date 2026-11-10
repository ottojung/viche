#!/usr/bin/env python3
"""Deterministic oversight of randomized audit coverage and recorded findings.

Auditor submissions are claims with evidence references, not independently verified
facts. The controller never declares an issue solved from agent completion alone.

Act 27 §3 legacy marker schema (append-only row in a correction trail, e.g.
``records/oversight/corrections/<case>.jsonl``)::

    {"marker": "legacy_no_identity", "case_id": "<18 hex>", "at": <epoch>,
     "filing_office": "<filing office id>", "sponsor": "<sponsoring seat id>",
     "predates_anchor": true,
     "identity_asserted": false,
     "hash_convention": "with_newline" | "no_newline",
     "rows": [{"position": <1-based trail line>, "commit": "<introducing sha>",
               "sha256": "<sha256 of that line's bytes at that commit>"}, ...],
     "review": {"reviewer": "clerk" | "judiciary",
                "independence_basis": "<non-empty>",
                "clerk_unavailability_basis": "<non-empty, required iff reviewer is judiciary>",
                "confirmations": {"hashes_match": true,
                                  "rows_unmodified": true,
                                  "no_identity": true}}}

"Signed by the filing office" (§3(2)) is attribution only: the marker names the
filing office in a committed append-only row, but nothing here binds that name
to the committer or to a cryptographic signature (no per-office key
infrastructure exists; see the independent review).  The reviewer records which
row-hash convention was used in ``hash_convention``; the checker verifies the
cited digests strictly under the declared convention.

A row's hash is SHA-256 over the row's bytes as committed at the cited
introducing commit, either with or without the single trailing newline as
declared.  A marker is effective only for the
two case ids named in Act 27 §3(1), only when it is the single marker in the
committed trail, lists every correction row that existed when the trail was
first committed (and no later row) exactly once by position, and carries an
effective independent review.  Otherwise it has no effect and token-less rows
continue to fail closed.
"""
import argparse
import fcntl
import hashlib
import re
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def json_file(path, fallback=None):
    return json.loads(path.read_text()) if path.exists() else fallback


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    os.replace(temp, path)


def base():
    return Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state")) / "oversight" / "random"


def records_dir():
    # Authoritative, Git-anchored append-only trail (Act 17 §2.2). Lives in the
    # town repository, which the audit office does not solely control.
    return Path(os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche")) / "records" / "oversight" / "corrections"


def correction_trail(case_id):
    path = records_dir() / f"{case_id}.jsonl"
    if not path.exists():
        return []
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        try:
            row = json.loads(line)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"authoritative correction trail is malformed at line {number}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"authoritative correction trail row {number} is not an object")
        if row.get("correction") and row.get("case_id") != case_id:
            raise ValueError(f"authoritative correction trail case mismatch at line {number}")
        rows.append(row)
    return rows


LEGACY_MARKER = "legacy_no_identity"
# Act 27 §3(1): the only trails eligible for a legacy marker.
LEGACY_CASE_ALLOWLIST = frozenset({"7750b56b775ed8959a", "edb67f8a646f569b5a"})


def _git_show(town, rev, rel):
    return subprocess.run(["git", "-C", town, "show", f"{rev}:{rel}"],
                          capture_output=True, text=True, timeout=15)


def _line_sha256s(line):
    """The two defensible readings of "the row's bytes": with or without the
    single trailing newline that separates it from the next row.  The marker
    declares which was used (``hash_convention``); the checker verifies
    strictly under the declared convention.  This helper is retained for
    introspection only.
    """
    text = line.encode("utf-8")
    return {hashlib.sha256(text).hexdigest(),
            hashlib.sha256(text + b"\n").hexdigest()}


def _row_sha256(line, convention):
    """SHA-256 of a row's bytes under the declared ``hash_convention``."""
    text = line.encode("utf-8")
    if convention == "with_newline":
        return hashlib.sha256(text + b"\n").hexdigest()
    if convention == "no_newline":
        return hashlib.sha256(text).hexdigest()
    return None


def effective_legacy_marker(case_id):
    """Return the set of 1-based positions marked ``legacy_no_identity``.

    The marker is verified independently from Git (Act 27 §3(2)-(3)): every
    cited row's hash must match its bytes at the cited introducing commit, and
    the current committed bytes at that position must be unchanged.  The marker
    must list every correction row that existed when the trail was first
    committed (so a post-commencement token-less row cannot be marked legacy),
    and it must carry a complete independent review.  Fail closed: any defect
    returns None, i.e. the marker has no effect.
    """
    if case_id not in LEGACY_CASE_ALLOWLIST:
        return None
    town = os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche")
    rel = f"records/oversight/corrections/{case_id}.jsonl"
    shown = _git_show(town, "HEAD", rel)
    if shown.returncode:
        return None
    lines = shown.stdout.splitlines()
    parsed = []
    marker_positions = []
    for number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
        except (TypeError, ValueError):
            return None
        if not isinstance(row, dict):
            return None
        parsed.append(row)
        if row.get("marker") == LEGACY_MARKER:
            marker_positions.append(number)
    # Act 27 §3(1): at most one marker, appended to the same trail.
    if len(marker_positions) != 1:
        return None
    marker_number = marker_positions[0]
    marker = parsed[marker_number - 1]
    if (marker.get("case_id") != case_id or marker.get("predates_anchor") is not True
            or marker.get("identity_asserted") is not False):
        return None
    filing_office = marker.get("filing_office")
    if not isinstance(filing_office, str) or not filing_office.strip():
        return None
    # Act 27 §3(3): the filing office and the sponsor are excluded as reviewer.
    sponsor = marker.get("sponsor")
    if not isinstance(sponsor, str) or not sponsor.strip():
        return None
    # The marker must declare which row-hash convention was used (cf. C5);
    # the checker verifies strictly under the declared convention.
    convention = marker.get("hash_convention")
    if convention not in ("with_newline", "no_newline"):
        return None

    entries = marker.get("rows")
    if not isinstance(entries, list) or not entries:
        return None
    positions = []
    for entry in entries:
        if not isinstance(entry, dict):
            return None
        position = entry.get("position")
        commit = entry.get("commit")
        digest = entry.get("sha256")
        if not isinstance(position, int) or isinstance(position, bool) or position < 1:
            return None
        if not isinstance(commit, str) or re.fullmatch(r"[0-9a-fA-F]{4,64}", commit) is None:
            return None
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            return None
        positions.append(position)
    # Every pre-marker correction row must be listed exactly once.
    if sorted(positions) != sorted(set(positions)):
        return None
    pre_marker_corrections = [
        number for number, row in enumerate(parsed[:marker_number - 1], 1)
        if row.get("correction") is True
    ]
    if sorted(positions) != sorted(pre_marker_corrections):
        return None

    # The trail's original commit is the pre-anchor state.  A row introduced
    # later (a post-commencement token-less row) is not eligible.
    log = subprocess.run(["git", "-C", town, "log", "--reverse", "--format=%H",
                          "--", rel], capture_output=True, text=True, timeout=15)
    introducing = log.stdout.split()
    if log.returncode or not introducing:
        return None
    anchor = introducing[0]
    anchor_shown = _git_show(town, anchor, rel)
    if anchor_shown.returncode:
        return None
    anchor_lines = anchor_shown.stdout.splitlines()
    anchor_corrections = []
    for number, line in enumerate(anchor_lines, 1):
        try:
            anchor_row = json.loads(line)
        except (TypeError, ValueError):
            return None
        if not isinstance(anchor_row, dict):
            return None
        if anchor_row.get("correction") is True:
            anchor_corrections.append(number)
    if sorted(positions) != sorted(anchor_corrections):
        return None

    for entry in entries:
        position = entry["position"]
        resolved = subprocess.run(
            ["git", "-C", town, "rev-parse", "--verify", f"{entry['commit']}^{{commit}}"],
            capture_output=True, text=True, timeout=15)
        if resolved.returncode or resolved.stdout.strip() != anchor:
            return None
        anchor_line = anchor_lines[position - 1]
        head_line = lines[position - 1]
        if entry["sha256"] != _row_sha256(anchor_line, convention):
            return None
        if entry["sha256"] != _row_sha256(head_line, convention):
            return None
        row = parsed[position - 1]
        if row.get("correction") is not True:
            return None
        # A legacy row carries no identity at all.
        if valid_cycle_token(row.get("cycle_id")):
            return None

    review = marker.get("review")
    if not isinstance(review, dict):
        return None
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, str) or reviewer.strip().lower() not in ("clerk", "judiciary"):
        return None
    reviewer_norm = reviewer.strip().lower()
    if reviewer_norm == filing_office.strip().lower():
        return None
    if reviewer_norm == sponsor.strip().lower():
        return None
    basis = review.get("independence_basis")
    if not isinstance(basis, str) or not basis.strip():
        return None
    # Act 27 §3(3): the Judiciary reviews only on recorded Clerk unavailability.
    if reviewer_norm == "judiciary":
        unavailability = review.get("clerk_unavailability_basis")
        if not isinstance(unavailability, str) or not unavailability.strip():
            return None
    confirmations = review.get("confirmations")
    if not isinstance(confirmations, dict):
        return None
    for key in ("hashes_match", "rows_unmodified", "no_identity"):
        if confirmations.get(key) is not True:
            return None
    return set(positions)


def committed_confirmed_correction(case_id):
    """Only rows committed in HEAD are effective under Act17 §2.2.

    This NEVER reads untracked or modified worktree bytes as legal authority.
    Fail closed on malformed committed rows, duplicate cycles or unpaired
    confirmations. Returns the latest confirmed FILING (not its procedural
    confirmation reference), or None when no correction has taken effect.
    """
    town = os.environ.get("VICHE_TOWN_ROOT", "/var/lib/lubko/wd/viche")
    rel = f"records/oversight/corrections/{case_id}.jsonl"
    p = subprocess.run(["git", "-C", town, "show", f"HEAD:{rel}"],
                       capture_output=True, text=True, timeout=15)
    if p.returncode:
        return None
    legacy = effective_legacy_marker(case_id) or set()
    pending = {}
    confirmed = set()
    effective = None
    for idx, line in enumerate(p.stdout.splitlines(), 1):
        try:
            row = json.loads(line)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"committed correction row {idx} malformed") from exc
        if isinstance(row, dict) and row.get("marker") == LEGACY_MARKER:
            continue
        if not isinstance(row, dict) or row.get("case_id") != case_id or row.get("correction") is not True:
            raise ValueError(f"committed correction row {idx} wrong case or type")
        if idx in legacy:
            # Act 27 §3(4): marked rows are legacy, not effective corrections.
            continue
        token = row.get("cycle_id")
        if not valid_cycle_token(token):
            raise ValueError(f"committed correction row {idx} missing valid cycle identity")
        if row.get("confirmed") is False:
            if token in pending or token in confirmed:
                raise ValueError("more than one correction filing in committed cycle")
            pending[token] = row
        elif row.get("confirmed") is True:
            filed = pending.get(token)
            if filed is None or token in confirmed or filed.get("verdict") != row.get("verdict"):
                raise ValueError("orphan or mismatched committed correction confirmation")
            confirmed.add(token)
            effective = filed
        else:
            raise ValueError(f"committed correction row {idx} lacks confirmed status")
    return effective


def append_correction(case_id, record):
    # Append-only: never overwrite or rewrite a committed entry (Act 17 §2.2, §2.7).
    d = records_dir()
    d.mkdir(parents=True, exist_ok=True)
    with open(d / f"{case_id}.jsonl", "a") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")
    return d / f"{case_id}.jsonl"


def valid_cycle_token(token):
    return isinstance(token, str) and re.fullmatch(r"[0-9a-f]{32}", token) is not None


def used_cycle_tokens(prior, case_id):
    """Read only explicit identities; an effective Act 27 marker exempts legacy rows."""
    tokens = set()
    for item in prior.get("history", []):
        if item.get("correction") and valid_cycle_token(item.get("cycle_id")):
            tokens.add(item["cycle_id"])
    legacy = effective_legacy_marker(case_id) or set()
    for position, item in enumerate(correction_trail(case_id), 1):
        if item.get("marker") == LEGACY_MARKER:
            continue
        if item.get("correction"):
            if position in legacy:
                # Marked legacy: no identity exists or is asserted; the row is
                # not an effective correction (Act 27 §3(4), §3(6)).
                continue
            token = item.get("cycle_id")
            if not valid_cycle_token(token):
                raise ValueError("authoritative correction trail has a correction without a valid cycle_id")
            tokens.add(token)
    return tokens


def current_cycle_token():
    state = Path(os.environ.get("VICHE_STATE_ROOT", "/var/lib/lubko/wd/viche-state")) / "oversight"
    path = state / "current-audit-cycle"
    try:
        token = path.read_text().strip()
    except OSError:
        return ""
    if not valid_cycle_token(token):
        return ""
    # Cross-check active identity against the durable dispatch ledger. An
    # environment value alone is not proof that audit-cycle.sh dispatched it.
    ledger = state / "audit-cycle-identities.tsv"
    try:
        entries = [line.split("\t", 1)[1] for line in ledger.read_text().splitlines()
                   if "\t" in line]
    except OSError:
        return ""
    if entries.count(token) != 1:
        return ""
    return token


def report(args):
    root = base()
    if not re.fullmatch(r"[0-9a-f]{18}", args.case):
        raise ValueError("invalid audit case identifier")
    case = json_file(root / "cases" / f"{args.case}.json")
    if case is None:
        raise ValueError("unknown audit case")
    if not args.evidence or not args.evidence.strip():
        raise ValueError("durable evidence reference is required")
    path = root / "outcomes" / f"{args.case}.json"
    prior = json_file(path)
    now = int(os.environ.get("VICHE_OVERSIGHT_NOW", time.time()))

    if args.confirm:
        # Second procedural pass (Act 17 §2.4): same office, same pinned model.
        # Explicitly NOT independent verification (Constitution X single substrate).
        if prior is None:
            raise ValueError("no prior outcome to confirm against")
        if not prior.get("correction_pending"):
            raise ValueError("no pending correction to confirm")
        pending = None
        for h in prior.get("history", []):
            if h.get("correction") and not h.get("confirmed"):
                pending = h
        if pending is None:
            raise ValueError("no pending correction to confirm")
        pending_cycle = pending.get("cycle_id")
        trail = correction_trail(args.case)
        matching = [row for row in trail if row.get("correction")
                    and row.get("cycle_id") == pending_cycle]
        if not valid_cycle_token(pending_cycle) or len(matching) != 1 or matching[0].get("confirmed") is not False:
            raise ValueError("pending correction is not bound to a valid authoritative trail entry")
        if args.cycle_id and args.cycle_id != pending.get("cycle_id"):
            raise ValueError("confirmation cycle_id does not match pending correction")
        pending["confirmed"] = True
        pending["confirmed_at"] = now
        pending["confirm_evidence_ref"] = args.evidence
        append_correction(args.case, {
            "at": now, "case_id": args.case, "verdict": pending["verdict"],
            "evidence_ref": args.evidence, "auditor": pending.get("auditor", ""),
            "correction": True, "supersedes": pending["supersedes"],
            "reason_code": pending.get("reason_code", ""),
            "why_stronger": pending.get("why_stronger", ""),
            "cycle_id": pending_cycle,
            "confirmed": True, "phase": "second_procedural_pass_not_independent",
        })
        prior["verdict"] = pending["verdict"]
        prior["at"] = now
        prior["evidence_ref"] = pending["evidence_ref"]
        prior["details"] = pending.get("details", prior.get("details", ""))
        prior["correction_pending"] = False
        prior.pop("correction_cycle_id", None)
        if pending["verdict"] == "finding":
            prior.pop("corrected_from_finding", None)
        else:
            prior["corrected_from_finding"] = True
        if pending["supersedes"] == "finding" and pending["verdict"] != "finding":
            prior["corrected_from_finding"] = True
        atomic(path, prior)
        print(json.dumps(prior))
        return

    if args.correction:
        # File a superseding verdict (Act 17 §2.1-2.2, §2.5-2.6).
        if prior is None:
            raise ValueError("no prior verdict; file an ordinary verdict first")
        if not valid_cycle_token(args.cycle_id):
            raise ValueError("correction requires a valid current audit cycle token")
        current_cycle = current_cycle_token()
        if not current_cycle or args.cycle_id != current_cycle:
            raise ValueError("cycle_id is not the current audit dispatch token")
        if not args.supersedes or args.supersedes != prior["verdict"]:
            raise ValueError("correction must state the verdict it supersedes")
        if prior.get("correction_pending"):
            raise ValueError("one correction per case per cycle (finality)")
        if args.cycle_id in used_cycle_tokens(prior, args.case):
            raise ValueError("one correction per case per cycle (cycle_id already used)")
        if args.evidence == prior.get("evidence_ref"):
            raise ValueError("correction evidence must be distinct from the original reference")
        if not args.why_stronger or not args.why_stronger.strip():
            raise ValueError("correction must state why the new evidence is stronger")
        if not args.reason_code or not args.reason_code.strip():
            raise ValueError("correction requires a reason_code")
        if not args.auditor or not args.auditor.strip():
            raise ValueError("correction requires auditor identity")
        if args.verdict == "verified_fixed" and prior["verdict"] != "finding":
            raise ValueError("verified_fixed requires a previous finding")
        held = [h.get("verdict") for h in prior.get("history", [])]
        if args.verdict in held:
            raise ValueError("bare re-flip: target verdict already held by this case")
        # Preserve the original verdict and evidence for a Git-unanchored
        # correction's effective-state fallback and future independent audit.
        prior.setdefault("original_verdict", prior.get("verdict"))
        prior.setdefault("original_evidence_ref", prior.get("evidence_ref"))
        prior.setdefault("original_at", prior.get("at"))
        rec = {
            "at": now, "case_id": args.case, "verdict": args.verdict,
            "evidence_ref": args.evidence, "auditor": args.auditor,
            "correction": True, "supersedes": args.supersedes,
            "reason_code": args.reason_code, "why_stronger": args.why_stronger[:1000],
            "details": args.details[:1000], "confirmed": False,
            "phase": "correction_filed",
            "cycle_id": args.cycle_id,
        }
        append_correction(args.case, rec)
        hist = prior.get("history", [])
        hist.append(rec)
        prior["history"] = hist
        prior["correction_pending"] = True
        prior["correction_cycle_id"] = args.cycle_id
        atomic(path, prior)
        print(json.dumps(prior))
        return

    if prior and any(item.get("correction") for item in prior.get("history", [])):
        raise ValueError("outcome changes after a correction require the correction workflow")
    if prior and prior["verdict"] != "finding":
        raise ValueError("case already has a final verdict")
    if args.verdict == "verified_fixed" and (not prior or prior["verdict"] != "finding"):
        raise ValueError("verified_fixed requires a previous finding")
    result = {"case_id": args.case, "population": case["population"],
              "subject": case["id"], "verdict": args.verdict, "at": now,
              "evidence_ref": args.evidence, "details": args.details[:1000],
              "caveat": "auditor_report_not_independent_proof"}
    atomic(path, result)
    print(json.dumps(result))


def listed_agents():
    all_agents = []
    for page in range(1, 101):
        p = subprocess.run(["antonina", "agent", "list", "--running",
                            "--page", str(page), "--json"], capture_output=True,
                           text=True, timeout=30)
        if p.returncode:
            raise RuntimeError(f"agent list failed: {p.stderr[-160:]}")
        data = json.loads(p.stdout)
        if isinstance(data, dict):
            if data.get("unreadable", 0):
                raise RuntimeError("unreadable agent inventory entries")
            items = data.get("agents")
        else:
            items = data
        if not isinstance(items, list):
            raise RuntimeError("invalid agent list response")
        all_agents.extend(items)
        if len(items) < 50:
            return all_agents
    raise RuntimeError("incomplete agent list")


def check(args):
    root = base()
    now = int(os.environ.get("VICHE_OVERSIGHT_NOW", time.time()))
    deadline = int(os.environ.get("VICHE_AUDIT_EVIDENCE_DEADLINE", "21600"))
    if deadline <= 0:
        raise ValueError("invalid deadline")
    signals = []
    cases = list((root / "cases").glob("*.json")) if (root / "cases").exists() else []
    findings = {}
    overdue = 0
    for path in cases:
        case = json_file(path)
        verdict = json_file(root / "outcomes" / path.name)
        if verdict is None and now - int(case["at"]) > deadline:
            overdue += 1
            signals.append({"type": "unreported_sample", "case_id": case["case_id"]})
        if verdict is not None:
            # State-dir verdicts are a derived cache, NOT the legal correction
            # trail. A confirmed procedural recheck does not make a correction
            # effective until Git HEAD contains its filed+confirmed rows.
            effective = verdict.get("verdict")
            effective_ref = verdict.get("evidence_ref")
            effective_at = verdict.get("at", now)
            corrected_from_finding = bool(verdict.get("corrected_from_finding"))
            history = [h for h in verdict.get("history", [])
                       if isinstance(h, dict) and h.get("correction")]
            if history:
                original = verdict.get("original_verdict", history[0].get("supersedes"))
                anchored = None
                try:
                    anchored = committed_confirmed_correction(case["case_id"])
                except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
                    signals.append({"type": "correction_anchor_invalid",
                                    "case_id": case["case_id"], "detail": str(exc)[:180]})
                if anchored is None:
                    effective = original if original in (
                        "finding", "verified", "not_assigned", "inconclusive", "verified_fixed") else None
                    effective_ref = verdict.get("original_evidence_ref")
                    effective_at = verdict.get("original_at", effective_at)
                    corrected_from_finding = False
                    signals.append({"type": "correction_not_effective",
                                    "case_id": case["case_id"],
                                    "reason": "no valid confirmed correction committed in Git HEAD"})
                else:
                    effective = anchored.get("verdict")
                    effective_ref = anchored.get("evidence_ref")
                    effective_at = anchored.get("at", effective_at)
                    corrected_from_finding = (
                        effective != "finding" and
                        (original == "finding" or
                         any(h.get("supersedes") == "finding" for h in history)))
                    if effective != verdict.get("verdict"):
                        signals.append({"type": "correction_not_effective",
                                        "case_id": case["case_id"],
                                        "reason": "state cache ahead of committed correction"})
            if verdict.get("correction_pending"):
                signals.append({"type": "correction_pending", "case_id": case["case_id"]})
            if effective == "finding":
                subject = f"{case['population']}:{case['id']}"
                findings[subject] = findings.get(subject, 0) + 1
                signals.append({"type": "unresolved_finding", "case_id": case["case_id"],
                                "evidence_ref": effective_ref,
                                "caveat": "source_not_independently_verified"})
            elif corrected_from_finding:
                signals.append({"type": "corrected_finding", "case_id": case["case_id"],
                                "evidence_ref": effective_ref,
                                "git_anchored": True})
            if effective == "inconclusive" and now - effective_at > deadline:
                signals.append({"type": "unresolved_inconclusive", "case_id": case["case_id"]})
    for subject, count in findings.items():
        if count >= 2:
            signals.append({"type": "repeated_finding", "subject": subject,
                            "count": count})
    agents = 0
    try:
        inventory = listed_agents()
        agents = len(inventory)
        for agent in inventory:
            agent_id = str(agent.get("id", ""))
            p = subprocess.run(["antonina", "agent", "status", "--id", agent_id, "--json"],
                               capture_output=True, text=True, timeout=25)
            if p.returncode:
                signals.append({"type": "agent_status_unavailable", "agent_id": agent_id})
                continue
            metadata = json.loads(p.stdout)
            # Model choice belongs to Antonina. An idle agent with no model
            # history is normal; avoid inventing a compliance incident.
            if metadata.get("state") not in ("idle", "running", "clearexit", "failed", "stopped", "killed"):
                signals.append({"type": "agent_state_unrecognized", "agent_id": agent_id})
    except Exception as e:
        signals.append({"type": "agent_inventory_unavailable", "detail": str(e)[:180]})
    evidence = {"at": now, "cases_total": len(cases), "cases_unreported_overdue": overdue,
                "running_agents_checked": agents, "signals": signals,
                "finding_count": sum(findings.values()),
                "assessment": "requires_investigation_not_a_guilt_verdict"}
    atomic(root / "health.json", evidence)
    incident = root / "incident.json"
    if signals:
        atomic(incident, evidence)
    elif incident.exists():
        os.replace(incident, root / f"cleared-{now}.json")
    print(json.dumps(evidence))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["check", "report"])
    p.add_argument("--case", default="")
    p.add_argument("--verdict", choices=["verified", "not_assigned",
                                           "finding", "inconclusive", "verified_fixed"])
    p.add_argument("--evidence", default="")
    p.add_argument("--details", default="")
    p.add_argument("--correction", action="store_true",
                   help="file a superseding verdict (Act 17); requires --supersedes, "
                         "--why_stronger, --reason_code, --auditor, --cycle-id")
    p.add_argument("--confirm", action="store_true",
                   help="second procedural pass confirming a pending correction (Act 17 §2.4)")
    p.add_argument("--supersedes", default="")
    p.add_argument("--why_stronger", default="")
    p.add_argument("--reason_code", default="")
    p.add_argument("--auditor", default="")
    p.add_argument("--cycle-id", dest="cycle_id", default="",
                   help="durable audit-dispatch cycle identity (corrections only)")
    args = p.parse_args()
    if args.action == "report":
        if args.correction and args.confirm:
            raise ValueError("--correction and --confirm are mutually exclusive")
        if args.confirm:
            if not args.case:
                raise ValueError("case is required")
        elif not args.case or not args.verdict:
            raise ValueError("case and verdict are required")
        # Correctness of the cycle cap requires an exclusive per-case
        # read/check/append/cache transaction. Two Judiciary CLI invocations
        # must not both pass the one-per-cycle check concurrently.
        if not re.fullmatch(r"[0-9a-f]{18}", args.case):
            raise ValueError("invalid audit case identifier")
        lockdir = base() / "case-locks"
        lockdir.mkdir(parents=True, exist_ok=True)
        with (lockdir / f"{args.case}.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            report(args)
    else:
        check(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Audit accountability failed: {err}", file=sys.stderr)
        sys.exit(1)
