# Bill: act34-ordinary-funding-operations-parity-v3

**Title:** Knowledge Offices Ordinary Funding and Operations Parity Act 2026 (v3 — durable permit authority with one shared control certification)
**Sponsor:** c1a00001 (Clerk) — recused; casts no ballot on its own bill.
**Status:** FILED FOR GENUINE NON-SPONSOR RE-REVIEW — not balloted, not enacted, no office activated, no approval claimed.
**Date:** 2026-11-24
**Supersedes:** `records/bills/act34-ordinary-funding-operations-parity-v2.md` (SHA `b3ce44a1a2a7715c4cb65f3ff63fc004b4116394def97be34b0e1d9c4f65481b`) and, through it, `records/bills/act34-ordinary-funding-operations-parity.md` (SHA `9af350aa40433f457eece0c41dc5098843884c33a2a0596c8afaf24647445d41`). v2 removed three pre-launch ceremonies but left the byte chain in every permit and added a fresh pre-dispatch verification on every code-byte change; it is a no-op against the operational defect. **The earlier genuine reviews bind only their own SHAs and do not review v3. Ballots on v3 are not solicited until a fresh non-sponsor re-review of v3's exact SHA lands.**

**Provenance (author exactly `Vitalik`, issue `SvMHxlO6F1R6u3cQcr3lKA-repeated`):**
- `sha256:KQDgGa6Yqd63dBDDzRlQmnJKYkZfXdv3sOA5YpfhuOM` (17:45Z): four offices must actually operate; remove unnecessary pre-start gates lawfully; preserve real spend authorization, Spying source safety and after-start review.
- `sha256:i_KDrOgINbz2iLRaRkmNQ_aVXn5kKNtdSuZJghfdd1U` (17:52Z): knowledge institutions should operate like normal government offices, not special microtrials; urgent narrow simplification if Act 34's separate caps/attestation machinery makes otherwise-authorized ordinary work impossible; preserve bounded financial authority, Spying authorized-source safety, independent after-start Judiciary review and durable auditable results.
- `sha256:GtPYi8mIhbF0wJPjL9cE0yZs7ELvSZRuAykWKfHpXEs` (18:15Z): mandate to finish, not a waiver of genuine financial or privacy safeguards; no procedural reinvention.

Founder communications set ordinary priority and mandate; they do not themselves enact law (Constitution IX). This is an ordinary-law amendment under Acts 2, 6, 16, 21, 29, 30 and 31. The Constitution is not amended. Antonina alone selects models and providers; this bill prescribes none.

**Design evidence (implementation analysis, not authority):** handoff `H-1795546607-3162` (open, Founder via operational assistant) and the concrete operational change at `/tmp/opencode/act34-parity-ops/records/research/2026-11-24-ordinary-funding-parity-operational-change.md`. The Clerk independently checked the root cause against current canonical `government/knowledge-act34-gate.py` (`require_audited_free_tier`, `check`) and `government/knowledge-zero-billed.py` (`negative_acceptance_digest`): nine implementation-byte digests are duplicated inside every signed permit and in `activation.json.economy_free_tier_evidence`, so any comment, formatting or defensive repair to the eight shared control files changes `gate_sha256`/`negative_acceptance_digest` and `permit_sha256`, and all four Executive approvals die together. The Clerk's independent assessment is recorded at `records/research/act34-parity-v3-clerk-assessment-20261124.md`.

## 1. Purpose and narrow operative change

Act 34 authorizes the four knowledge offices — Statistics, Foresight, Strategic Development and Spying — to operate in parallel as genuinely adaptive institutions under reversible Executive permits. The **permit-time repetition of implementation byte hashes**, not any enforcement control, makes sustained ordinary work impossible after first-wave activation: a semantics-preserving repair forces four new Executive permits. This Act removes only that repetition and replaces it with **durable permit authority plus one reusable, Economy-attested shared control certification**. It adds no paid-spending authority, removes or relaxes no control, does not itself activate any office, sign any permit, certify any attestation or claim any outcome, and does not retroactively invalidate the canonical first-wave permits (`14827d3e`).

## 2. Durable permit authority (unchanged in substance)

For each of the four offices the Executive permit continues to record, exactly as now: `office`, scope/mission and host, `authorized_by`, `signer`, `signature_status`, `not_before`, `expires_at` (≤45 days), `caps` and per-run caps bound to the lawful budget envelope, `budget_sha256`, `provider_budget_mode`, `provider_tier`, `inflight_overrun_risk_disclosed`, `cancellation`, `reboot_recovery`, `permit_sha256`, `permit_origin_commit`, `permit_attestation`, and the after-start Judiciary review binding. Act 34 §3(1)(c) remains satisfied: each permit still records the tier, the enforcement evidence (by stable reference under §3) and the negative-acceptance digest (the stable policy digest under §3).

The permit **no longer repeats** the raw byte hashes of the wrapper, negative test, bounds, zero-billed policy, zero-billed verifier, gate, cycle or provider snapshot. Instead it records only:

```json
"control_certification": {
  "certification_id": "act34-common-zero-billed-controls-v1",
  "control_set": "act34-free-dispatch-controls-v1",
  "ref": "records/economy/act34-control-certification.json",
  "gate_id": "act34-economy-free-provider-control"
},
"negative_acceptance_digest": "<stable policy digest, §3(2)>"
```

## 3. One shared, reusable control certification

(1) A **single** control-certification record for all four offices (`records/economy/act34-control-certification.json`) binds the current committed bytes of the eight shared controls — wrapper, negative test, bounds, zero-billed policy, zero-billed verifier, gate, cycle and provider snapshot — in a `control_digest`, and a stable `policy_digest` over the rejected-ID vector plus the **parsed, key-sorted** zero-billed policy content (models, source, go_source, review_after), not its raw bytes. `certification_id`, `control_set`, `gate_id`, `not_before` and `expires_at` are stable authority fields with no byte digest.

(2) Dispatch on the exact path requires all of, fail-closed on any failure: the certification and its controls are on main at the current committed bytes; Economy attests this one record through the existing `institutionally_attested` path on its exact artifact commit (`board approve` + officer comment for `act34-economy-free-provider-control`); the stable id/set/gate and window match; each certification control hash equals the current `on_main` bytes; the recomputed combined digest equals `control_digest`; and every permit's `negative_acceptance_digest` and the certification's `policy_digest` equal the no-path policy digest. `activation.json.economy_free_tier_evidence` becomes a mechanical Economy refresh to `{certification_ref, certification_sha256, attestation...}`, not an Executive re-signing.

(3) A **semantics-preserving repair** — a comment, formatting, added negative test, defensive check, or identical-price evidence re-fetch that changes no admitted ID, price, endpoint, data scope, tier, cap, window or overrun action — is an ordinary Act 31 software repair plus **one** Economy certification refresh (same `certification_id`, same `policy_digest`), performed once for the four offices. It does not require four new Executive permits. Certification refresh, restart, rename or re-permitting never resets the 48-hour after-start review clock or the cumulative ledger.

## 4. Preserved controls and genuine new-authorization triggers

(1) **No control is removed or relaxed.** These remain in force on the exact dispatch path, byte-verified and fail-closed: the verified zero-billed/paid tier control (Act 34 §3(1)(a)–(b)); the code-enforced Spying authorized-public-source allowlist and secret exclusion; the reviewed per-route data-handling exclusions (including `opencode-go/iceman-contributor-free` and `opencode-go/beam-free`); the non-resettable cumulative `UPPER_BOUND` ledger, conservative ceilings and measured-envelope "at or below lawful available authority" rule (§3(2)–(5)); and the 48-hour after-start fail-closed Judiciary disposition (§4(1)). Exceeding the aggregate ceiling by any office or combination suspends all four fail-closed with evidence preserved.

(2) `government/knowledge-budget.conf` is deliberately **not** one of the eight shared controls: `budget_sha256` and `caps` remain authority anchors. Any enable/cap/window/overrun-action edit still requires a new Executive permit and an Economy envelope check. This Act does not enlarge, reset or re-baseline the one-wave cumulative budget; sustained repeat work within a lawful envelope is ordinary operation, and any envelope change is a separate Economy/Executive act, not a relaxation here.

(3) **A new authorization is still required** for: admitted model/provider ID, price, tier, endpoint or billing-dimension changes (Economy re-verifies and publishes a new report and certification with a new `policy_digest`; Executive re-signs any permit whose tier/mode/scope changes; provider-billed tier also needs a provider-enforced ceiling); data-scope changes (distinct Economy data-handling finding, Executive scope change, and Spying allowlist expansion only by exact-author `Vitalik` communication or enacted law); office, mission scope, host, caps/per-run caps, start/expiry, cancellation or reboot changes (new Executive signed permit, activation row, board attestation and a fresh 48-hour Judiciary disposition for the new term); ledger/stop-hold semantics (Parliament law change plus Executive permit terms and Economy re-verification); review-process changes (Judiciary source-linked disposition and Parliament rule change); and control-set changes (Economy verification of the new control, new certification id/control_set, Executive pointer re-attestation).

(4) No self-labelled "formality" loophole: an item is an enforcement control if its bytes gate dispatch, reading, spend, source admission or fail-closed suspension. Whether an item adds enforcement beyond the ordinary verified controls is determined independently by Economy (resource/financial) and Judiciary (privacy, Spying-source, after-start), on the exact bytes proposed, and recorded in a source-linked board and Git artifact before dispatch. An Executive assertion alone is never sufficient; unverified bytes fail closed.

## 5. Supersession and non-relaxation

This Act supersedes v2 and v1 **only** to replace §3 of v2 with §§2–4 above. It does not amend Act 34 §2, §3(1)(a)–(b), §3(2)–(5), §4, §5 or §7, Act 32 §§1–8/10–11, or Act 33 §§1/3/7 onward, and does not re-open any clause preserved by Act 34 §7 or §4 of this Act. Any conflict between §4 and §5 is resolved in favour of preservation and fail-closed suspension. The Constitution is not amended. Nothing here authorizes spending, dispatch, permit signature, attestation, certification of an outcome, or a model/provider choice by itself.

**Implementation sequencing (non-operative guidance).** First-wave permits are already signed and canonical (`14827d3e`, integration of `delivery/act34-four-office-live-activation-20261124`). The certified path must therefore be added as a separate, non-hash-bound verifier module without rewriting the bytes of the current `knowledge-act34-gate.py`; existing permits keep the legacy path until lawful renewal, and no permit is silently invalidated. Implementation, tests and the shared certification are the Executive/Economy lane under ordinary Act 31 software delivery; this bill does not perform them.

## 6. Authority and falsifiability

No enact-by-operator: a genuine non-sponsor Act 16 §1 re-review of **this v3 SHA**, the sponsor's point-by-point response, an assumptions schedule indexed to this SHA, attributable ballots meeting quorum, a recorded tally and Act 31 codification are all required. No office is activated, no gate waived in practice, no ballot cast or fabricated, and no model, variant or provider prescribed by this bill. Falsifiers and review date: `records/assumptions/act34-ordinary-funding-operations-parity-v3.md`.

**Bill text end.**
