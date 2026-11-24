#!/usr/bin/env python3
"""Deterministic verifier for the DRAFT first Act 33 Statistics trial design.

It does THREE narrow, mechanical jobs and never grants authority:

  verify-draft  the design/order/no-go records are internally coherent DRAFTs,
                the frozen baseline is byte-intact under one boot id, no office
                or budget flag was enabled, and the source dict is well formed.
  verify-landed every hash-pinned code source matches canonical main:<path> and
                Act 33 is enacted there. This fails closed until both deliveries
                have actually landed with the reviewed bytes.
  no-go         report mechanical blockers from the exact no-go list. Economy's
                zero-model finding and the Judiciary phase PROCEED are EXTERNAL
                gates: this Executive tool never evaluates or self-verifies them.

No network, no clock except the supplied boot id. POSIX-invocable from sh.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_DICT = "records/knowledge/first-trial-source-dict-20261122.json"
DESIGN = "records/knowledge/TRIAL-DESIGN-ACT33-20261122.md"
ORDER = "records/knowledge/EXEC-ORDER-DRAFT-ACT33-20261122.md"
NOGO = "records/knowledge/FIRST-TRIAL-NO-GO-LIST-20261122.md"
OFFICES = ("statistics", "foresight", "strategy", "spying")
CODE_KEYS = ("runner", "report", "post", "post_guard", "budget_tool",
             "budget_config", "preflight_gate", "first_trial_verifier")
BILL_SHA = "65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d"


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Problem(Exception):
    pass


def load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Problem("cannot read JSON %s: %s" % (path, exc))


def text(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise Problem("cannot read %s: %s" % (path, exc))


def git_bytes(town, *args):
    try:
        proc = subprocess.run(["git", "-C", str(town), *args],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise Problem("git unavailable: %s" % exc)
    if proc.returncode != 0:
        raise Problem("git failed: %s" % " ".join(args))
    return proc.stdout


def report(decision, ok, reasons, **extra):
    out = {"schema": "viche-first-trial-design-verifier-result-1",
           "decision": decision, "ok": ok, "reasons": reasons}
    out.update(extra)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if ok else 1


def boot_id(override):
    if override:
        return override
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return None


class Verifier:
    def __init__(self, town, dict_path):
        self.town = Path(town).resolve()
        self.dict_path = Path(dict_path)
        self.dict = load(self.dict_path)
        if not isinstance(self.dict, dict):
            raise Problem("source dict is not an object")

    # ---- source dict shape ------------------------------------------------
    def check_dict(self, problems):
        d = self.dict
        if d.get("schema") != "viche-first-trial-source-dict-1":
            problems.append("unsupported source dict schema")
        if d.get("status") not in ("DRAFT_PENDING_LANDING", "DRAFT_GATES_PENDING"):
            problems.append("source dict is not marked as a DRAFT status")
        law = d.get("law")
        if not isinstance(law, dict) or law.get("act") != 33 or law.get("bill_sha256") != BILL_SHA:
            problems.append("source dict does not bind enacted Act 33 bill hash")
        roots = d.get("original_source_roots")
        if not isinstance(roots, dict) or len(roots) < 10:
            problems.append("original source roots missing/incomplete")
        for k, v in roots.items():
            if not isinstance(v, str) or not v:
                problems.append("original source root %s malformed" % k)
        code = d.get("code_sources")
        if not isinstance(code, dict) or any(k not in code for k in CODE_KEYS):
            problems.append("code_sources missing required pinned paths")
            return {}
        for k in CODE_KEYS:
            entry = code[k]
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                problems.append("code source %s malformed" % k)
                continue
            if not isinstance(entry.get("sha256"), str) or not SHA_RE.fullmatch(entry["sha256"]):
                problems.append("code source %s has no valid sha256" % k)
        return code

    # ---- frozen baseline --------------------------------------------------
    def check_baseline(self, problems, override_boot):
        base = self.dict.get("baseline")
        if not isinstance(base, dict):
            problems.append("baseline block missing")
            return
        root = self.town / base.get("dir", "")
        freeze = load(root / base.get("freeze_record", "freeze.json"))
        if freeze.get("schema") != "viche-first-trial-baseline-freeze-1":
            problems.append("unsupported freeze record schema")
        if freeze.get("boot_unchanged_during_freeze") is not True:
            problems.append("baseline not frozen under one unchanged boot")
        want_boot = boot_id(override_boot)
        if not want_boot or freeze.get("boot_id") != base.get("boot_id") or freeze.get("boot_id") != want_boot:
            problems.append("baseline boot id does not match the observing host")
        if not isinstance(freeze.get("frozen_at_epoch"), int):
            problems.append("freeze epoch missing")
        manifest = {}
        for line in (root / base.get("manifest", "MANIFEST.sha256")).read_text(encoding="utf-8").splitlines():
            parts = line.split("  ", 1)
            if len(parts) == 2:
                manifest[parts[1]] = parts[0]
        declared = freeze.get("files")
        if not isinstance(declared, list) or not declared:
            problems.append("freeze file list empty")
            return
        names = set()
        for item in declared:
            name = item.get("name")
            if not isinstance(name, str) or "/" in name or name in (".", ".."):
                problems.append("unsafe freeze file name")
                continue
            names.add(name)
            path = root / name
            if not path.is_file() or path.is_symlink():
                problems.append("frozen file missing: %s" % name)
                continue
            data = path.read_bytes()
            if sha(data) != item.get("sha256") or path.stat().st_size != item.get("size_bytes"):
                problems.append("frozen file hash/size mismatch: %s" % name)
            if manifest.get(name) != sha(data):
                problems.append("MANIFEST mismatch: %s" % name)
        if names != set(manifest):
            problems.append("MANIFEST set differs from freeze file set")

    # ---- draft safety (no activation) ------------------------------------
    def check_draft_separation(self, problems):
        act = load(self.town / "records/knowledge/activation.json")
        offices = act.get("offices") if isinstance(act, dict) else None
        if not isinstance(offices, dict):
            problems.append("activation.json has no offices")
        else:
            for name in OFFICES:
                row = offices.get(name)
                if not isinstance(row, dict) or row.get("enabled") is not False:
                    problems.append("office %s is enabled (DRAFT must enable none)" % name)
            stats = offices.get("statistics") or {}
            for key in ("trial_mode", "phase_gate_record"):
                if key in stats:
                    problems.append("draft wrote activation statistics.%s" % key)
            # A DRAFT may carry informational source preregistration, but it
            # must have the exact six-field shape and valid hashes. These hashes
            # are not authority and may be historical; verify-landed checks the
            # authoritative current source dict. enabled=false is checked above.
            if "deterministic_sources" in stats:
                pinned = stats["deterministic_sources"]
                required = {"runner", "report", "post", "post_guard",
                            "budget_tool", "budget_config"}
                if not isinstance(pinned, dict) or set(pinned) != required:
                    problems.append("draft deterministic_sources must pin exactly the reviewed source set")
                else:
                    for key, digest in pinned.items():
                        if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                            problems.append("draft deterministic source %s has no valid sha256" % key)
        conf = load(self.town / "government/knowledge-budget.conf")
        cfg_offices = conf.get("offices") if isinstance(conf, dict) else None
        if not isinstance(cfg_offices, dict):
            problems.append("budget config has no offices")
        else:
            for name in OFFICES:
                if cfg_offices.get(name, {}).get("enabled") is not False:
                    problems.append("budget office %s enabled while DRAFT" % name)

    def check_records(self, problems):
        design = text(self.town / DESIGN)
        order = text(self.town / ORDER)
        nogo = text(self.town / NOGO)
        if "DRAFT" not in design or "NOT AN ACTIVE ORDER" not in design:
            problems.append("design record is not clearly DRAFT/inactive")
        if "DRAFT" not in order or "NOT SIGNED" not in order:
            problems.append("candidate order is not clearly DRAFT/unsigned")
        if "1000" not in design or "UNAVAILABLE" not in design:
            problems.append("design lacks a quantified endpoint/missingness rule")
        for token in ("agent", "report count", "merges"):
            if token not in nogo.lower() and token not in design.lower():
                problems.append("no-go/design omits forbidden claim class: %s" % token)
        for n in range(1, 11):
            if ("N%d" % n) not in nogo:
                problems.append("no-go list missing N%d" % n)

    def verify_draft(self, boot_override):
        problems = []
        try:
            self.check_dict(problems)
            self.check_baseline(problems, boot_override)
            self.check_draft_separation(problems)
            self.check_records(problems)
        except Problem as exc:
            problems.append(str(exc))
        return report("draft_coherent" if not problems else "hold", not problems, problems)

    # ---- canonical main byte check ---------------------------------------
    def verify_landed(self):
        problems = []
        matched = []
        try:
            code = self.check_dict(problems)
            laws = git_bytes(self.town, "show", "main:government/LAWS.md").decode("utf-8", "replace")
            if "## Act 33 — Prospective Statistics Trial Clarification (enacted " not in laws:
                problems.append("Act 33 not enacted on canonical main")
            if BILL_SHA not in laws:
                problems.append("canonical main LAWS.md lacks the voted bill hash")
            for key in CODE_KEYS:
                entry = code.get(key, {})
                path = entry.get("path", "")
                want = entry.get("sha256", "")
                try:
                    blob = git_bytes(self.town, "show", "main:" + path)
                except Problem as exc:
                    problems.append("%s not on canonical main: %s" % (key, exc))
                    continue
                got = sha(blob)
                matched.append({"key": key, "path": path, "match": got == want})
                if got != want:
                    problems.append("%s byte drift: main=%s pinned=%s" % (key, got[:12], want[:12]))
        except Problem as exc:
            problems.append(str(exc))
        return report("landed" if not problems else "hold", not problems, problems,
                      authority="mechanical byte check only; not activation, not Judiciary verification",
                      sources=matched)

    # ---- mechanical no-go status -----------------------------------------
    def no_go(self, boot_override):
        blockers = []
        try:
            for key in CODE_KEYS:
                entry = self.dict["code_sources"][key]
                blob = git_bytes(self.town, "show", "main:" + entry["path"])
                if sha(blob) != entry["sha256"]:
                    blockers.append("N1/N5: %s not landed with reviewed bytes" % key)
            act = load(self.town / "records/knowledge/activation.json")
            for name in OFFICES:
                if act.get("offices", {}).get(name, {}).get("enabled") is True:
                    blockers.append("N7: office %s enabled" % name)
            conf = load(self.town / "government/knowledge-budget.conf")
            for name in OFFICES:
                if conf.get("offices", {}).get(name, {}).get("enabled") is True:
                    blockers.append("N7: budget %s enabled" % name)
            if boot_id(boot_override) != self.dict["baseline"]["boot_id"]:
                blockers.append("N6: host boot changed")
        except (Problem, KeyError, TypeError) as exc:
            blockers.append("unreadable state (fail closed): %s" % exc)
        return report("no_mechanical_blocker" if not blockers else "hold",
                      not blockers, blockers,
                      external_gates_required=[
                          "N2 Economy zero-model strict-safety finding (external, not evaluated here)",
                          "N3 independent Judiciary phase PROCEED (Executive must NOT self-verify)",
                          "N4 Act 33 first-trial preflight passing with corroborated attestation (external verifier)",
                      ],
                      note="Even with no mechanical blocker, no activation is authorized until all external gates are independently satisfied.")


def main(argv):
    if len(argv) < 4 or argv[3] not in ("verify-draft", "verify-landed", "no-go"):
        print("usage: statistics-trial-design-verifier.py <town> <dict> verify-draft|verify-landed|no-go [--boot-id ID]",
              file=sys.stderr)
        return 2
    town, dict_path, cmd = argv[1], argv[2], argv[3]
    boot_override = argv[5] if len(argv) >= 6 and argv[4] == "--boot-id" else None
    try:
        ver = Verifier(town, dict_path)
        if cmd == "verify-draft":
            return ver.verify_draft(boot_override)
        if cmd == "verify-landed":
            return ver.verify_landed()
        return ver.no_go(boot_override)
    except Problem as exc:
        return report("invalid", False, [str(exc)])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
