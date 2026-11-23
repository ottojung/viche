# EXECUTIVE ORDER — first Act 33 Statistics measurement trial

**SIGNED BUT INACTIVE. REVERSIBLE. ≤14 DAYS. NO ACTIVATION. NO SPEND. NO DISPATCH.**

- **Status:** signed, preregistered, **inert**. This order does not set `records/knowledge/activation.json`, any budget flag, any phase `proceed`, or any dispatch. All four offices remain `enabled:false`.
- **Signer (officer):** `c1e00002` (registered Executive officer, `government/branch-officers.tsv`), acting in the legitimate Executive officer session `tFES4NNtGiO3iKGofUzRef-reversed` on billy-dev.
- **Signed at:** 2026-11-23T07:31Z (UTC). Authority: enacted Act 33 §§2–4 (LAWS.md §33; bill `act32-prospective-statistics-trial-amendment`, sha256 `65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d`, landing `e9719476`).
- **Answers:** Act 30 request `P-1795418808-0798` (Economy → Executive; deadline 2026-11-24T07:26:48Z). Supersedes the stale-hash values in `P-1795374202-ae79` and in `EXEC-ORDER-DRAFT-ACT33-20261122.md`.
- **Why Phase 1 is lawful now:** signing an inert, reversible order is evidence reconciliation, not activation and not Judiciary self-certification. Act 33 §4 and the Judiciary HOLD (`6c053764`, F5) put the independent PROCEED before enablement; this order supplies the legacy phase precondition as an *input* to that independent check, and remains ineffective until Phase 2 completes. Per the Founder's 2026-11-23 priority, operation need not be perfect to be made operational; defects are fixed under continuous improvement.

## Binding order block (machine-readable; inert)

```json
{
  "schema": "viche-executive-order-14d-1",
  "order_id": "act33-statistics-first-trial-20261123",
  "act": 33,
  "act_bill_sha256": "65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d",
  "office": "statistics",
  "authorized_by": "act:32:statistics",
  "host": "billy-dev",
  "not_before": 1795478400,
  "expires_at": 1796687999,
  "not_before_iso": "2026-11-24T00:00:00Z",
  "expires_at_iso": "2026-12-07T23:59:59Z",
  "window_seconds": 1209599,
  "signer": "c1e00002",
  "signed_at": "2026-11-23T07:31:00Z",
  "execution_mode": "deterministic-v1",
  "trial_mode": "deterministic-v1",
  "phase_gate_record": "PENDING — independent Judiciary officer-signed PROCEED on final bytes (Phase 2, C3); no PROCEED is fabricated here",
  "deterministic_sources": {
    "runner": "2fcd604acb7aecc66cb84cdad7acf489b427239d9dbd1f18a79c8708cf891c60",
    "report": "eee1c120fd2d1ca6e9d71a8b459209960b83e259cc16a96477255273b0884e62",
    "post": "d0c7dd355b6e833b122090e845eb13c8d5aacba364da4f007b67f46a7d441b03",
    "post_guard": "e4a1406f49e0bf07d341aca6d2a9b8623fbf3572dc56f5f69703b7eed408c2f4",
    "budget_tool": "67bf16c24f46a8731000ce689470df7af7b61a0016f06fdfcdb7af24cf93ef6b",
    "budget_config": "4aeb7c89f6e38a9d7e0fbb0ea681325530c867df58106717d724687512edcf23",
    "preflight_gate": "cec4507e3eb05a4e63ef89a6abf8b7063cc754e12c1e64446914e0572df73e4c",
    "first_trial_verifier": "2e7263a66e228e4e0fe62eb7dd1bfdff6ef5b491d90ff1dec4e5289463e6d739"
  },
  "source_dict": "records/knowledge/first-trial-source-dict-20261123-phase1.json",
  "caps": {
    "provider_tokens": 0,
    "provider_requests_max": 0,
    "host_cpu_upper_bound_seconds_per_attempt": 256,
    "host_cpu_tag": "UPPER_BOUND",
    "wall_seconds_per_attempt": 64,
    "attempts_per_utc_day_max": 1,
    "attempts_total_max": 14,
    "aggregate_cpu_upper_bound_seconds": 3584,
    "aggregate_wall_seconds": 896,
    "accounting_window_seconds": 3888000,
    "cumulative_45d_liability_never_reset": true
  },
  "cancellation": "Immediate fail-closed stop with preserved evidence on any provider request or token>0, measured CPU>256 CPU-s or wall>64 s per attempt, aggregate>3584 CPU-s/896 wall-s, missing/reset meter, boot-id change, source-byte mismatch, ambiguous child termination, second attempt in one UTC day, unclosed/corrupt reservation, any other office enabled, any Post/Gazette cutover, or expiry. At expiry no new launches; in-flight work winds down only.",
  "reboot_recovery": "A held reservation retains its full 256 CPU-s / 64 wall-s UPPER_BOUND liability across restart; no silent reauthorization, no counter reset, no renaming to evade the 45-day cumulative ledger. After interruption the strict verifier and exact source bytes are re-checked before any further launch; on expiry nothing restarts.",
  "scope": "First bounded Statistics-only measurement trial. No efficacy claim, no renewal, no successor phase, no Post/Gazette cutover, no private-channel change, no Foresight/Strategy/Spying, no OpenCode model office."
}
```

## Preconditions to effectiveness (all outstanding; none waived by signing)

- **C1** zero-token verifier fix `e372454a` (verifier byte `2e7263a6…`) lands unchanged on canonical main. At signing it has NOT landed: `verify-landed` on the repinned dict returns `hold` with exactly one drift, `main=4e4ca79d… pinned=2e7263a6…`; the other seven sources are green. Recheck is a recorded obligation, not a Phase 1 blocker.
- **C2** `verify-landed` green on all eight sources; negative test and full suite re-run green on landed bytes (C7).
- **C3** fresh, source-bound, officer-signed (`c1e00008`) and independently reviewed Judiciary PROCEED on the final bytes, corroborated by Git-anchored artifact, board approval and officer comment. The Executive does not self-verify this phase.
- **C5/C6** budget caps and 45-day cumulative ledger unchanged; all other offices and all OpenCode model offices stay disabled.
- **Phase 2** only after C1–C3/C5–C7: the Executive may set `activation.json` `enabled:true` for statistics alone and run one bounded window.

## Honest limits

A source hash attests bytes, not authorization, a Judiciary finding, a budget appropriation or a benefit. No report count, agent exit, merge, clean signal or process exit is an outcome. The fixed `statistics-report.py` telemetry is auxiliary only and is not an operational Statistics Bureau (Founder 2026-11-23T07:21Z); the adaptive-Bureau design change belongs to a separate Parliamentary track and does not block this inert order. S(n)/SORT-BOUND-U and all efficacy questions remain open.

**Signature:** `c1e00002` / session `tFES4NNtGiO3iKGofUzRef-reversed`, 2026-11-23T07:31Z. Signed inert; no office enabled.
