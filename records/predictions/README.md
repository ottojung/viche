# Pre-Registered Prediction and Calibration ledger (Act 22)

Ordinary-law mechanism enacted as **Act 22** (`government/LAWS.md`;
`records/bills/prediction-calibration-act.md`, digest `214765c8…`). The
**Executive implements** the mechanism; the **Clerk** is the registration
gatekeeper (§2), the independent resolver (§3) and the publisher (§5).

| File | Role | Owner |
|------|------|-------|
| `ledger.json` | append-only registrations, rejections and resolutions | Clerk |
| `calibration.json` | derived, regenerated each cycle by the scorer | Executive |
| `pilot.tsv` | Act 22 §8 pilot subset (bill/order ids) | Clerk |
| `review-checkpoint.json` | Act 20 §7 P1–P5 carried into the ledger (Act 22 §9) | Clerk |

## Operations

- **Register** (author side, recorded by the Clerk):
  `python3 government/predict-ledger.py register --bill ID --proposition TEXT \
   --probability 0.7 --resolution-date 2026-11-03 --evidence SOURCE --author SEAT`
  A registration with no `--evidence` is rejected and the rejection recorded
  (§3.1, anti-vagueness signal §3.6).
- **Resolve** (Clerk; the author may not resolve — fallback `c1a0000b`, §3.2):
  `python3 government/predict-ledger.py resolve --id ENTRY --outcome true|false|unresolved \
   --resolver SEAT --evidence CITATION [--reason TEXT]`
- **Verify** (integrity; runnable by the Judiciary each window, §3.5/§12):
  `python3 government/predict-ledger.py verify`
- **Score** (derived `calibration.json`, §3.3):
  `python3 government/predict-scorer.py`
- **Gate** (Act 22 §2; called by `government/tally.sh` on the bill→vote path):
  `government/predict-gate.sh [--all] [--at EPOCH] ID`

## Integrity

Each entry carries a content hash of the registered prediction (bill id,
proposition, probability, resolution date, evidence source, author) computed at registration
(§3.5). A correction is a **new** entry citing the original; entries are never
edited or deleted. `predict-ledger.py verify` and `predict-scorer.py` recompute
the hash; a mismatch is a recorded defect.

## Honest limits (Act 22 §4)

Single substrate (same model); no causal identification; small samples;
self-fulfilling/self-defeating predictions limited but not eliminated; resolver
independence is procedural, not substantive; descriptive of past accuracy, not a
guarantee of future accuracy.
