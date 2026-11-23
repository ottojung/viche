#!/usr/bin/env python3
"""Validate a self-directed Statistics Bureau inquiry, not a fixed metric list.

Questions and their methodologies are authored by the Bureau. This program
validates epistemic provenance and the life cycle of arbitrary inquiries;
it NEVER selects a question, computes predefined metrics, or declares value.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = "viche-statistics-inquiry-v1"
STAGES = {"candidate", "investigating", "measured", "challenged", "retired"}
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA = re.compile(r"^[0-9a-f]{64}$")


def text(obj, field, errors, required=True):
    val = obj.get(field)
    if required and (not isinstance(val, str) or not val.strip()):
        errors.append(f"{field}: meaningful text required")
    elif val is not None and not isinstance(val, str):
        errors.append(f"{field}: must be text")


def source(root, item, errors, index):
    if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
        errors.append(f"evidence[{index}]: use exact path and sha256")
        return
    name, digest = item["path"], item["sha256"]
    if not isinstance(name, str) or not name.startswith(("records/", "government/")):
        errors.append(f"evidence[{index}]: only frozen project source paths accepted")
        return
    if (name.startswith("records/statistics/inquiries/")
            or "\\" in name or ".." in Path(name).parts or Path(name).is_absolute()):
        errors.append(f"evidence[{index}]: own inquiry or unsafe path not primary evidence")
        return
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        errors.append(f"evidence[{index}]: original source missing")
        return
    if not isinstance(digest, str) or not SHA.fullmatch(digest):
        errors.append(f"evidence[{index}]: invalid digest")
    else:
        try:
            matches = hashlib.sha256(path.read_bytes()).hexdigest() == digest
        except OSError:
            matches = False
        if not matches:
            errors.append(f"evidence[{index}]: source missing or changed after measurement")


def validate(path, root):
    problems = []
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return None, [f"invalid inquiry file: {type(exc).__name__}"]
    if not isinstance(obj, dict):
        return None, ["inquiry must be a JSON object"]
    if obj.get("schema") != SCHEMA:
        problems.append("unsupported inquiry schema")
    ident = obj.get("id")
    if not isinstance(ident, str) or not ID.fullmatch(ident) or path.stem != ident:
        problems.append("id must match slug filename")
    stage = obj.get("stage")
    if not isinstance(stage, str) or stage not in STAGES:
        problems.append("invalid inquiry stage")
        stage = None
    # The Bureau selects questions, decision relevance, and priorities freely.
    # This validator deliberately contains NO catalog or predefined metric names.
    for field in ("question", "why_now", "decision_use"):
        text(obj, field, problems)
    for field in ("method", "population", "missingness", "limitations",
                  "source_dependence", "negative_controls", "revisit_when"):
        text(obj, field, problems, required=False)
    evidence = obj.get("evidence", [])
    if not isinstance(evidence, list):
        problems.append("evidence must be an array")
        evidence = []
    for ix, item in enumerate(evidence):
        source(root, item, problems, ix)
    if stage in {"measured", "challenged"}:
        for field in ("method", "population", "missingness", "limitations",
                      "source_dependence", "negative_controls"):
            text(obj, field, problems)
        # The measured quantity can be a distribution, category, interval,
        # qualitative observation or any future schema: NO fixed metric menu.
        if "result" not in obj or obj["result"] is None:
            problems.append("measured claim requires a result")
        if not evidence:
            problems.append("measured claim requires at least one primary evidence root")
        if obj.get("independently_verified") is True:
            problems.append("self-declared independent verification is not authority")
    if stage == "retired":
        text(obj, "retirement_reason", problems)
        text(obj, "revisit_when", problems)
    return obj, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "agenda"])
    parser.add_argument("files", nargs="*")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "check":
        if len(args.files) != 1:
            parser.error("check requires exactly one inquiry file")
        file = Path(args.files[0]).resolve()
        if not file.is_relative_to(root / "records/statistics/inquiries"):
            print("inquiry must live in records/statistics/inquiries", file=sys.stderr)
            return 1
        obj, problems = validate(file, root)
        for problem in problems:
            print(problem, file=sys.stderr)
        if problems:
            return 1
        print(json.dumps({"id": obj["id"], "stage": obj["stage"], "valid": True}))
        return 0
    folder = root / "records/statistics/inquiries"
    index = []
    problems = False
    for file in sorted(folder.glob("*.json")):
        obj, errors = validate(file, root)
        if errors:
            problems = True
            index.append({"file": file.name, "errors": errors})
        else:
            index.append({k: obj[k] for k in ("id", "stage", "question", "why_now", "decision_use")})
    print(json.dumps({"inquiries": index, "count": len(index)}, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
