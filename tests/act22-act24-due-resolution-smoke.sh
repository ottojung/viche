#!/bin/sh
# Act 22 regression: the three DUE Act 24 (WITHDRAWN bill) registrations must be
# independently resolved as `unresolved` by the Audit fallback resolver c1a0000b,
# with specific failed-evidence paths, and must never be silently scored from the
# distinct Act 25 re-enactment. Read-only against the committed ledger.
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
ledger=$root/records/predictions/ledger.json
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM

VICHE_PREDICT_LEDGER=$ledger python3 "$root/government/predict-ledger.py" verify >/dev/null

python3 - "$ledger" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
ids = [
    "act24-validation-and-record-correction-act-registration-1",
    "act24-validation-and-record-correction-act-registration-2",
    "act24-validation-and-record-correction-act-registration-3",
]
# Registration content hashes are immutable (Act 22 section 3.5); these are the
# hashes computed at registration, before the bill was withdrawn. Editing a
# registration to change its outcome narrative must be detected.
hashes = {
    ids[0]: "sha256:19559ac0a3c49709f6b57aff182bf59fc6979cc34eb547f1de1f6293cfc289f4",
    ids[1]: "sha256:ba96b5c74cd2402cf7459933d751bd64508c45638cb297997ab0a7112d68779b",
    ids[2]: "sha256:8331c04b2f199da1774e261c3ef01d26f430760b9b9f2b58d35c1b9dbac8b942",
}
reg = {e["id"]: e for e in d["entries"] if e.get("kind") == "registration"}
for i in ids:
    assert i in reg, "missing registration " + i
    assert reg[i]["author"] == "c1a00001", "author changed for " + i
    assert reg[i]["content_hash"] == hashes[i], "registration edited for " + i

res = {}
for r in d["resolutions"]:
    res.setdefault(r["id"], []).append(r)
for i in ids:
    rows = res.get(i, [])
    assert len(rows) == 1, "expected exactly one resolution for %s, got %d" % (i, len(rows))
    r = rows[0]
    assert r["outcome"] == "unresolved", "not unresolved: " + i
    assert r["resolver"] == "c1a0000b", "wrong resolver: " + i
    assert r["resolver"] != reg[i]["author"], "author resolved own prediction: " + i
    assert r.get("evidence_at") is None, "unresolved event was scored with evidence time: " + i
    assert (r.get("evidence_citation") or "").strip(), "missing evidence citation: " + i
    assert (r.get("reason") or "").strip(), "missing reason: " + i
    assert int(r["resolved_at"]) >= 1794700800, "resolved before due date: " + i
    assert "withdraw" in r["reason"].lower() or "withdraw" in r["evidence_citation"].lower(), \
        "reason/citation does not name the withdrawal: " + i
    assert "act25" in (r["reason"] + r["evidence_citation"]).lower() or \
        "Act 25" in (r["reason"] + r["evidence_citation"]), \
        "citation does not guard against Act 25 substitution: " + i
# Due registration 4 (2026-11-25) must not be resolved in this window.
assert "act24-validation-and-record-correction-act-registration-4" not in res
PY

VICHE_PREDICT_LEDGER=$ledger \
VICHE_PREDICT_CALIBRATION=$tmp/calibration.json \
    python3 "$root/government/predict-scorer.py" >/dev/null
python3 - "$tmp/calibration.json" <<'PY'
import json, sys
x = json.load(open(sys.argv[1]))
assert x["integrity"]["clean"] is True
scored = {r["id"] for r in x["brier"]["per_prediction"]}
ids = {
    "act24-validation-and-record-correction-act-registration-1",
    "act24-validation-and-record-correction-act-registration-2",
    "act24-validation-and-record-correction-act-registration-3",
}
assert not (scored & ids), "unresolved Act 24 forecasts leaked into Brier score"
assert x["counts"]["unresolved"] >= 3, "unresolved resolutions not counted in coverage"
PY

echo 'act22-act24-due-resolution-smoke: passed'
