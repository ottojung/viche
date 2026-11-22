#!/usr/bin/env python3
"""Fail-closed verifier for the enacted Act 33 FIRST Statistics trial preflight.

This is the narrow exception to Act 32 amendments D/E/H/K and clause 9: for the
FIRST reversible Statistics measurement trial only, a historical independently
verified numerator and actual per-office CPU are NOT prerequisites. They must be
declared UNAVAILABLE (never zero, never "verified"). Everything else is stricter,
not looser: prospective design, frozen primary sources with reliable same-boot
observations, an independently measured and genuinely ENFORCED hard cap, an
explicit <=14-day Executive order and an independently corroborated Judiciary
proceed bound to the exact frozen source bytes.

Authority is never a bag of all-green JSON keys. Every gate must additionally
carry a Git-anchored, officer-bound review artifact AND be corroborated by a
separate institutional export (board review + officer comment + appointment
registry). A forged officer, wrong Act, missing/expired order, unavailable cap,
missing source, tampered source or absent corroboration fails closed.

Deterministic: no network, no clock except the caller-supplied `at` epoch.
POSIX-invocable from sh. This verifier never enables an office; it only decides
whether the recorded evidence is sufficient WITHHOLDING authority.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "viche-statistics-first-trial-preflight-1"
RESULT_SCHEMA = "viche-statistics-first-trial-preflight-result-1"
LEGACY_HELPER_NAME = "statistics-evidence.py"

ACT = 33
ACT_TITLE = "Prospective Statistics Trial Clarification"
ACT_BILL_ID = "act32-prospective-statistics-trial-amendment"
ACT_BILL_SHA256 = "65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d"

MAX_TRIAL_SECONDS = 14 * 24 * 3600
OBSERVATION_SKEW_SECONDS = 24 * 3600

GATE_SIGNERS = {
    "prospective_design": "executive",
    "frozen_sources_same_boot": "economy",
    "economy_safety_hard_cap": "economy",
    "executive_order_14d": "executive",
    "judiciary_proceed": "judiciary",
    "source_corroboration": "judiciary",
}
GATE_KEYS = frozenset(GATE_SIGNERS)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
PATH_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class VerifyError(Exception):
    pass


# ---- reuse the legacy helper's byte-pinning primitives -------------------
def load_legacy_helper(town):
    """Import the verified byte-pinning helpers by path; fail closed if absent."""
    path = Path(town) / "government" / LEGACY_HELPER_NAME
    if not path.is_file() or path.is_symlink():
        raise VerifyError("legacy evidence helper missing")
    try:
        spec = importlib.util.spec_from_file_location("viche_legacy_evidence", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception as exc:  # pragma: no cover - defensive
        raise VerifyError("legacy evidence helper unreadable: %s" % exc)
    for name in ("sha256_of", "snapshot_path"):
        if not callable(getattr(mod, name, None)):
            raise VerifyError("legacy evidence helper lacks %s" % name)
    return mod


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerifyError("cannot read JSON %s: %s" % (path, exc))


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def nonempty(value):
    return isinstance(value, str) and len(value.strip()) > 0


class Verifier:
    def __init__(self, town, at):
        self.town = Path(town).resolve()
        self.at = int(at)
        self._legacy = None
        self._registry = None

    # ---- authoritative town sources -------------------------------------
    def legacy(self):
        if self._legacy is None:
            self._legacy = load_legacy_helper(str(self.town))
        return self._legacy

    def read_laws(self):
        path = self.town / "government" / "LAWS.md"
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise VerifyError("cannot read government/LAWS.md: %s" % exc)

    def officers(self):
        """Authoritative officer registry: role -> id and id -> role."""
        if self._registry is not None:
            return self._registry
        path = self.town / "government" / "branch-officers.tsv"
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise VerifyError("cannot read officer registry: %s" % exc)
        by_role, by_id = {}, {}
        for line in text.splitlines():
            cols = line.split("\t")
            if len(cols) >= 2 and cols[0] and cols[1]:
                # branch-officers.tsv columns are: role <TAB> officer-id <TAB> name
                by_role.setdefault(cols[0].strip(), cols[1].strip())
                by_id.setdefault(cols[1].strip(), cols[0].strip())
        if not by_role or not by_id:
            raise VerifyError("empty officer registry")
        self._registry = (by_role, by_id)
        return self._registry

    def git(self, *args):
        try:
            proc = subprocess.run(["git", "-C", str(self.town), *args],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise VerifyError("git unavailable: %s" % exc)
        if proc.returncode != 0:
            raise VerifyError("git command failed: %s" % " ".join(args))
        return proc.stdout

    def git_object_is_commit(self, commit):
        if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
            return False
        try:
            kind = self.git("cat-file", "-t", commit).decode("ascii", "replace").strip()
        except VerifyError:
            return False
        return kind == "commit"

    def read_git_blob(self, commit, path):
        """Read a blob by EXACT Git tree traversal (no path interpretation)."""
        if not isinstance(path, str):
            raise VerifyError("artifact path is not a string")
        parts = path.split("/")
        if (not path.startswith("records/") or ".." in parts
                or any(not PATH_RE.fullmatch(p) for p in parts)):
            raise VerifyError("unsafe artifact path (Git tree traversal required)")
        out = self.git("ls-tree", "-z", commit, "--", path)
        entries = [e for e in out.split(b"\0") if e]
        if len(entries) != 1 or b"\t" not in entries[0]:
            raise VerifyError("artifact path is not a unique Git tree entry")
        meta, actual = entries[0].split(b"\t", 1)
        fields = meta.split()
        if (len(fields) != 3 or fields[0] not in (b"100644", b"100755")
                or fields[1] != b"blob"):
            raise VerifyError("artifact path is not a regular Git blob")
        if actual.decode("utf-8", "replace") != path:
            raise VerifyError("artifact tree entry path mismatch")
        return self.git("cat-file", "blob", fields[2].decode("ascii"))

    @staticmethod
    def parse_kv(data):
        try:
            text = data.decode("utf-8")
        except UnicodeError:
            raise VerifyError("artifact not UTF-8")
        kv = {}
        for line in text.splitlines():
            m = re.match(r"^\s*([a-z_]+)\s*:\s*(.*?)\s*$", line)
            if m:
                kv.setdefault(m.group(1), m.group(2).strip())
        return kv

    # ---- law recognition -------------------------------------------------
    def check_law(self, problems):
        """Require precisely ONE enacted Act 33, with the exact voted bill."""
        try:
            laws = self.read_laws()
        except VerifyError as exc:
            problems.append(str(exc))
            return
        pat = re.compile(r"^## Act (\d+) — ([^\n(]+)\(enacted ", re.MULTILINE)
        enacted = [(int(n), t.strip()) for n, t in pat.findall(laws)]
        acts33 = [(n, t) for n, t in enacted if n == ACT]
        if len(acts33) != 1:
            problems.append("expected exactly one enacted Act 33, found %d" % len(acts33))
            return
        title = acts33[0][1]
        if ACT_TITLE not in title:
            problems.append("Act 33 title is not the Prospective Statistics Trial Clarification")
        # Section text spans from its heading to the next '## ' heading.
        m = re.search(r"^## Act 33 — [^\n]*\(enacted .*?(?=^## |\Z)", laws,
                      re.MULTILINE | re.DOTALL)
        section = m.group(0) if m else ""
        if "Historical enactments" in section or "SUPERSEDED" in section:
            problems.append("Act 33 is historical/superseded, not operative law")
        if ("bill " + ACT_BILL_ID) not in section:
            problems.append("Act 33 does not bind the exact voted bill id")
        if ACT_BILL_SHA256 not in section:
            problems.append("Act 33 does not bind the exact voted bill sha256")
        if not any(n == 32 for n, _ in enacted):
            problems.append("Act 32 (amended base law) is not enacted")

    # ---- evidence digest -------------------------------------------------
    @staticmethod
    def evidence_digest(sources):
        norm = sorted(
            ({"snapshot": s.get("snapshot"), "sha256": s.get("sha256"),
              "size_bytes": s.get("size_bytes")} for s in sources),
            key=lambda d: (str(d["snapshot"]), str(d["sha256"])),
        )
        blob = json.dumps(norm, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8")
        return "sha256:" + sha256_bytes(blob)

    # ---- source pinning + same-boot -------------------------------------
    def check_sources(self, att, design, problems):
        legacy = self.legacy()
        sources = att.get("sources")
        if not isinstance(sources, list) or not sources:
            problems.append("no pinned primary sources")
            return []
        source_dir = self.town / "records/knowledge/first-trial-sources-20261122"
        if not source_dir.is_dir():
            # The attestation may name an alternative in-town frozen source dir.
            rel = att.get("source_dir")
            if nonempty(rel):
                candidate = self._safe_town_path(rel)
                source_dir = candidate if candidate is not None and candidate.is_dir() else source_dir
        if not source_dir.is_dir():
            problems.append("frozen source directory missing")
            return []
        boot = design.get("same_boot")
        if not isinstance(boot, dict):
            problems.append("design.same_boot missing")
            return []
        boot_id = boot.get("boot_id")
        observed_at = boot.get("observed_at")
        if not nonempty(boot_id):
            problems.append("same_boot.boot_id missing")
        if not is_int(observed_at):
            problems.append("same_boot.observed_at missing/malformed")
        if boot.get("reliable") is not True:
            problems.append("same_boot.reliable is not true")
        if not nonempty(boot.get("observed_by")):
            problems.append("same_boot.observed_by missing")
        declared = []
        for entry in sources:
            if not isinstance(entry, dict):
                problems.append("malformed source entry")
                continue
            name = entry.get("snapshot")
            path = legacy.snapshot_path(source_dir, name)
            if path is None:
                problems.append("unsafe or missing snapshot name: %r" % (name,))
                continue
            declared.append(name)
            if not path.is_file():
                problems.append("missing source: %s" % name)
                continue
            if entry.get("sha256") != legacy.sha256_of(str(path)):
                problems.append("source hash mismatch: %s" % name)
            if not is_int(entry.get("size_bytes")) or entry["size_bytes"] != path.stat().st_size:
                problems.append("source size mismatch: %s" % name)
            if entry.get("boot_id") != boot_id:
                problems.append("source observed under a different boot: %s" % name)
            so = entry.get("observed_at")
            if not is_int(so) or not is_int(observed_at) or abs(so - observed_at) > OBSERVATION_SKEW_SECONDS:
                problems.append("source observation outside same-boot window: %s" % name)
        present = {p.name for p in source_dir.iterdir()
                   if p.is_file() and not p.is_symlink() and p.name != "MANIFEST.sha256"}
        extra = sorted(present - set(declared))
        if extra:
            problems.append("unattested files present: %s" % ",".join(extra))
        observed = boot.get("sources_observed")
        if (not isinstance(observed, list) or len(observed) != len(declared)
                or set(observed) != set(declared)):
            problems.append("same_boot.sources_observed does not equal pinned sources")
        manifest_path = source_dir / "MANIFEST.sha256"
        if manifest_path.is_file() and not manifest_path.is_symlink():
            declared_manifest = {}
            for line in manifest_path.read_text(encoding="utf-8").splitlines():
                parts = line.split("  ", 1)
                if len(parts) == 2:
                    declared_manifest[parts[1]] = parts[0]
            for name, digest in sorted(declared_manifest.items()):
                path = legacy.snapshot_path(source_dir, name)
                if path is None or not path.is_file():
                    problems.append("manifest file missing or unsafe: %s" % name)
                elif legacy.sha256_of(str(path)) != digest:
                    problems.append("manifest hash mismatch: %s" % name)
        return sources

    def _safe_town_path(self, rel):
        if not isinstance(rel, str) or not rel or "\\" in rel:
            return None
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts:
            return None
        return self.town / path

    # ---- design / UNAVAILABLE honesty -----------------------------------
    def check_design(self, att, design, problems):
        if not isinstance(design, dict):
            problems.append("design block missing")
            return
        pro = design.get("prospective")
        if not isinstance(pro, dict):
            problems.append("design.prospective missing")
        else:
            for key in ("endpoint", "population", "selection", "missingness",
                        "comparator", "observation_window"):
                if not nonempty(pro.get(key)):
                    problems.append("prospective.%s missing" % key)
            for key in ("negative_controls", "falsifiers"):
                val = pro.get(key)
                if not isinstance(val, list) or not val or not all(nonempty(x) for x in val):
                    problems.append("prospective.%s missing or empty" % key)
        for key in ("historical_numerator", "per_office_cpu"):
            item = design.get(key)
            if not isinstance(item, dict) or item.get("status") != "UNAVAILABLE":
                problems.append("%s must be explicitly UNAVAILABLE" % key)
            elif not nonempty(item.get("reason")):
                problems.append("%s lacks an unavailable reason" % key)
            elif "value" in item and item["value"] is not None:
                problems.append("%s carries an imputed value" % key)
            elif item.get("verified") is True:
                problems.append("%s is claimed verified" % key)
        cpu = design.get("whole_host_cpu")
        if (not isinstance(cpu, dict) or cpu.get("tag") != "UPPER_BOUND"
                or cpu.get("status") not in ("MEASURED_UPPER_BOUND", "MEASURED")):
            problems.append("whole_host_cpu must be a tagged UPPER_BOUND safety measure")

    # ---- gates, artifacts and institutional corroboration ---------------
    def check_gates(self, att, digest, sources, problems):
        gates = att.get("gates")
        if not isinstance(gates, dict) or frozenset(gates) != GATE_KEYS:
            problems.append("gates must be exactly the six first-trial gates")
            return
        by_role, by_id = self.officers()
        export_ref = att.get("corroboration_export")
        export = None
        if not nonempty(export_ref):
            problems.append("corroboration_export missing")
        else:
            export_path = self._safe_town_path(export_ref)
            if export_path is None or not export_path.is_file():
                problems.append("corroboration_export unreadable")
            else:
                export = load_json(str(export_path))
        reviews = export.get("reviews", {}) if isinstance(export, dict) else {}
        comments = export.get("comments", []) if isinstance(export, dict) else []
        appointments = export.get("appointments", {}) if isinstance(export, dict) else {}
        if not isinstance(reviews, (dict, list)) or not isinstance(comments, list):
            problems.append("corroboration export malformed")
            reviews, comments = {}, []
        source_hashes = sorted(str(s.get("sha256")) for s in sources if isinstance(s, dict))
        for key in sorted(GATE_KEYS):
            gate = gates[key]
            if not isinstance(gate, dict):
                problems.append("gate %s malformed" % key)
                continue
            if gate.get("status") != "green":
                problems.append("gate %s is not green" % key)
            if not nonempty(gate.get("owner")) or not nonempty(gate.get("evidence_ref")):
                problems.append("gate %s lacks owner/evidence_ref" % key)
            role = GATE_SIGNERS[key]
            signer = gate.get("reviewer")
            expected = by_role.get(role)
            if not expected or signer != expected or by_id.get(str(signer)) != role:
                problems.append("gate %s reviewer is not the registered %s officer" % (key, role))
                continue
            artifact = gate.get("artifact")
            if not isinstance(artifact, dict):
                problems.append("gate %s has no Git-anchored artifact" % key)
                continue
            commit = artifact.get("git_commit")
            gpath = artifact.get("git_path")
            adigest = artifact.get("sha256")
            if not isinstance(adigest, str) or not SHA256_RE.fullmatch(adigest):
                problems.append("gate %s artifact digest malformed" % key)
                continue
            if not self.git_object_is_commit(commit):
                problems.append("gate %s artifact commit invalid" % key)
                continue
            try:
                blob = self.read_git_blob(commit, gpath)
            except VerifyError as exc:
                problems.append("gate %s artifact unreadable: %s" % (key, exc))
                continue
            if sha256_bytes(blob) != adigest:
                problems.append("gate %s artifact digest mismatch" % key)
                continue
            kv = self.parse_kv(blob)
            bindings = {
                "gate": key, "reviewer": str(signer), "role": role,
                "decision": "proceed", "evidence_digest": digest,
            }
            for field, want in bindings.items():
                if kv.get(field) != want:
                    problems.append("gate %s artifact %s binding mismatch" % (key, field))
            if not nonempty(kv.get("reviewed_at")):
                problems.append("gate %s artifact lacks reviewed_at" % key)
            if key in ("judiciary_proceed", "frozen_sources_same_boot", "source_corroboration"):
                declared_hashes = [h.strip() for h in kv.get("source_hashes", "").split(",")
                                   if h.strip()]
                if sorted(declared_hashes) != source_hashes:
                    problems.append("gate %s source_hashes do not match frozen sources" % key)
            # Independent institutional corroboration of this exact artifact.
            # The export may hold one review dict keyed by commit, or a list of
            # reviews (each naming its commit) when several officers review the
            # same commit. Require an approve by THIS gate's officer.
            if isinstance(reviews, dict):
                cand = [reviews.get(str(commit))]
            elif isinstance(reviews, list):
                cand = [r for r in reviews if isinstance(r, dict)
                        and str(r.get("commit")) == str(commit)]
            else:
                cand = []
            cand = [r for r in cand if isinstance(r, dict)]
            approved = [r for r in cand if r.get("verdict") == "approve"
                        and str(r.get("reviewer", "")) == str(signer)
                        and nonempty(r.get("recordedAt"))]
            if not approved:
                problems.append("gate %s lacks an officer-attributed approve board review on the exact commit" % key)
            prefix = str(commit)[:7]
            if not any(isinstance(c, dict) and str(c.get("author", "")) == str(signer)
                       and key in str(c.get("body", "")) and prefix in str(c.get("body", ""))
                       for c in comments):
                problems.append("gate %s lacks officer-attributed board comment" % key)
            if appointments.get(role) != signer:
                problems.append("gate %s appointment registry mismatch" % key)
        return by_role

    # ---- safety / order / judiciary / scope ------------------------------
    def check_safety(self, att, by_role, problems):
        safety = att.get("safety")
        if not isinstance(safety, dict):
            problems.append("safety block missing")
            return
        must_be_true = ("hard_cap", "strict_inflight", "enforced", "accumulate_across_trials")
        for key in must_be_true:
            if safety.get(key) is not True:
                problems.append("safety.%s is not true" % key)
        if safety.get("stop_on_detection") is not False:
            problems.append("cap is stop-on-detection, not a strictly enforced hard cap")
        for key in ("tokens_cap", "host_cpu_upper_bound"):
            val = safety.get(key)
            if not is_int(val) or val <= 0:
                problems.append("safety.%s missing or non-positive" % key)
        if safety.get("host_cpu_tag") != "UPPER_BOUND":
            problems.append("host CPU is not tagged UPPER_BOUND")
        if not nonempty(safety.get("negative_test_digest")):
            problems.append("safety.negative_test_digest missing")

    def check_order(self, att, by_role, problems):
        order = att.get("order")
        if not isinstance(order, dict):
            problems.append("order block missing")
            return
        if order.get("office") != "statistics" or order.get("act") != ACT or order.get("host") != "billy-dev":
            problems.append("order binds wrong office/act/host")
        nb, exp = order.get("not_before"), order.get("expires_at")
        if not is_int(nb) or not is_int(exp) or exp <= nb:
            problems.append("order has no positive window")
        else:
            if exp - nb > MAX_TRIAL_SECONDS:
                problems.append("order window exceeds 14 days")
            if self.at < nb:
                problems.append("order not yet effective")
            if self.at >= exp:
                problems.append("order expired; no new launch")
        executive = by_role.get("executive")
        if not executive or order.get("signer") != executive:
            problems.append("order signer is not the registered Executive officer")
        for key in ("cancellation", "reboot_recovery"):
            if not nonempty(order.get(key)):
                problems.append("order.%s missing" % key)

    def check_judiciary(self, att, by_role, sources, problems):
        jud = att.get("judiciary")
        if not isinstance(jud, dict):
            problems.append("judiciary block missing")
            return
        if jud.get("decision") != "proceed":
            problems.append("judiciary decision is not proceed")
        expected = by_role.get("judiciary")
        if not expected or jud.get("reviewer") != expected:
            problems.append("judiciary reviewer is not the registered Judiciary officer")
        declared = jud.get("source_hashes")
        want = sorted(str(s.get("sha256")) for s in sources if isinstance(s, dict))
        if (not isinstance(declared, list) or len(declared) != len(want)
                or sorted(str(x) for x in declared) != want):
            problems.append("judiciary proceed is not tied to the exact frozen source hashes")
        if not nonempty(jud.get("finding_ref")):
            problems.append("judiciary finding_ref missing")

    def check_scope(self, att, problems):
        if att.get("schema") != SCHEMA:
            problems.append("unsupported schema (legacy/efficacy records cannot authorize a first trial)")
        if att.get("office") != "statistics" or att.get("host") != "billy-dev":
            problems.append("wrong office/host")
        if att.get("act") != ACT or att.get("act_bill_id") != ACT_BILL_ID:
            problems.append("wrong act/bill")
        if att.get("act_bill_sha256") != ACT_BILL_SHA256:
            problems.append("wrong act bill sha256")
        if att.get("readiness") != "ready":
            problems.append("readiness is not ready")
        if att.get("scope") != "first_trial_only":
            problems.append("scope is not first_trial_only")
        if att.get("successors_enabled") is not False:
            problems.append("successors are not disabled")
        if att.get("efficacy_claimed") is not False:
            problems.append("an efficacy/value claim is present; first trial certifies none")
        if not nonempty(att.get("authority")):
            problems.append("authority/limitation statement missing")

    # ---- top level -------------------------------------------------------
    def result(self, decision, reasons, digest=""):
        return {
            "schema": RESULT_SCHEMA,
            "decision": decision,
            "ok": decision == "proceed",
            "at": self.at,
            "act": ACT,
            "evidence_digest": digest,
            "reasons": reasons,
        }

    def verify(self, attestation_path):
        problems = []
        try:
            att = load_json(attestation_path)
            if not isinstance(att, dict):
                raise VerifyError("attestation is not an object")
            self.check_law(problems)
            self.check_scope(att, problems)
            design = att.get("design", {})
            self.check_design(att, design, problems)
            sources = self.check_sources(att, design, problems)
            digest = self.evidence_digest(sources)
            if att.get("evidence_digest") != digest:
                problems.append("evidence_digest does not match the pinned sources")
            by_role, _ = self.officers()
            self.check_gates(att, digest, sources, problems)
            self.check_safety(att, by_role, problems)
            self.check_order(att, by_role, problems)
            self.check_judiciary(att, by_role, sources, problems)
        except VerifyError as exc:
            problems.append(str(exc))
            return self.result("hold", problems)
        except Exception as exc:  # unexpected input must never fail open
            problems.append("unhandled verification error: %s" % exc)
            return self.result("hold", problems)
        if problems:
            return self.result("hold", problems, digest)
        return self.result("proceed", ["enacted Act 33 first-trial evidence independently corroborated"],
                           digest)


def now_epoch():
    import time
    return int(time.time())


def main(argv):
    if len(argv) < 3:
        print("usage: statistics-first-trial.py verify|check|digest <town> <attestation> [at]",
              file=sys.stderr)
        return 2
    cmd = argv[1]
    if cmd == "digest":
        # argv[2] is a JSON array file; print its canonical evidence digest.
        try:
            data = load_json(argv[2])
            if not isinstance(data, list):
                raise VerifyError("digest input must be a JSON array")
            print(Verifier(".", 0).evidence_digest(data))
            return 0
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if cmd not in ("verify", "check"):
        print("unknown command", file=sys.stderr)
        return 2
    if len(argv) < 4:
        print("missing attestation path", file=sys.stderr)
        return 2
    at = int(argv[4]) if len(argv) >= 5 else now_epoch()
    ver = Verifier(argv[2], at)
    report = ver.verify(argv[3])
    print(json.dumps(report, indent=2, sort_keys=True))
    if cmd == "check":
        return 0
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
