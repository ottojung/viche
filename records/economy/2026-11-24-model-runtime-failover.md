# Permanent model management: runtime failover, cooldown health and config writers — 2026-11-24

**Scope.** Founder-authorized independent engineering on billy-dev. The earlier hotfix
`d5b9b6e5` (additive authorization, test-checkout guard, validate-before-publish,
concurrent-write detection) was already live on `main` when this pass began; this work
rebases onto it, does not duplicate or revert it, and covers the remaining runtime
side. While this pass ran, `main` also received `889f6c58` (an independent repair of
the same stale economy-cycle mock) and `ca2fa792` (verified zero-price Go routes with
low effort); the rebase keeps both and strengthens the mock with the additional tier,
low-variant and policy-path assertions. No office was activated, no SoringP1 work was
dispatched or monitored, and no paid tier was enabled.

## Runtime failure modes identified (installed Antonina release `37ace8e`)

Evidence: `/home/lubko/.local/antonina-releases/37ace8e/node_modules/@antonina/cli/dist/packages/agent-runtime/src/`
— `model-config.js` SHA-256 `a728f683…97a97a`, `model-failover.js` `f27f6d35…8b8c`,
`model-cooldowns.js` `a9e160c8…b0c02f`, `model-health.js` `82a1442c…8c248`,
`backend.js` `6dc13841…68edffcd6`.

| Failure mode | Runtime behaviour | Consequence for the Town |
|---|---|---|
| Hard provider cooldown | `quota_exhausted` / `rate_limited` with `until <= now + 7d + 60s`, correct filename and size ≤1024 are shared exclusions; other entries are ignored | Only valid entries reduce availability; forged/soft entries must not fake a funding shortage |
| Permanent per-agent exclusion | `model_unavailable`, provider auth/billing failures get `Number.MAX_SAFE_INTEGER`; stored in **agent metadata**, not shared cooldown files | A healthy-looking ladder can still refuse a model; Economy cannot see these from shared state |
| Forced `#low` variant | `backend.js` explicitly warns that forcing a variant a model does not support yields `provider.no-route` → `model_unavailable` | A probe that answered OK once can become a permanent per-agent exclusion at launch |
| Silent stall | A model that accepts a request then emits no tokens gets a 20-minute **soft** penalty and stays in the last-resort lottery | Probe success and catalogue presence prove nothing about an actual invocation |
| Provider-wide exclusion | `excludeAgentProvider()` cools every configured model of that provider together | A one-provider free pool has no failover at all |
| All models excluded | `selectConfiguredAgentModel()` throws "No eligible configured model" | Dispatch refuses; there is no automatic paid fallback |

Live observations corroborate the soft-health path: `model-health/` held unrecognized
backend failures on `opencode-go/hy4-flash-free`, `opencode-go/hungerg-free`,
`opencode-go/iceman-contributor-free` and `openai/gpt-6-luna` from four or more distinct
agents on 2026-11-24; shared cooldown files covered 13 models. These are health signals,
not authorization decisions.

## Changes (controls)

| Control | SHA-256 |
|---|---|
| `government/economy-models.py` | `2a3dffae0f3f7a1137b40dceab1cd8dc28294a6ee3f39f294b9bd66a9dbf015c` |
| `government/MINISTRY-OF-ECONOMY.md` | `29f98205524a92afedadaf44ac6473c10f7277876a4324a6053fe655ea44dded` |
| `tests/economy-models-smoke.sh` | `c6cffb5996ba2ba45b7d506c63df6080a1e080cc18968f49e91bf44a518c2c36` |
| `tests/economy-cycle-smoke.sh` | `688b680a483be113e654b81229558424dbcf1de6bff225b838939184c3d51595` |

1. **All config writers audited.** `economy-models.py` is the only writer of the global
   ladder; the Act 34 wrapper writes an isolated `$XDG_CONFIG_HOME/antonina/config.json`
   and never touches it. The script now mirrors Antonina's accepted entry shape exactly
   (provider/model id regex, string comment, optional matching variant, no duplicates),
   repairs a missing comment or bare-string entry without changing authorization, and
   **fails closed on an invalid authorized entry** instead of silently deleting it.
   Catalogue ids containing `:`/`#` are never added. Local structural validation runs
   before the existing external validate-before-publish step, because
   `antonina agent model select` only prints the *first* model.
2. **Cooldown health separated from authorization.** `cooldown_state()` now mirrors
   `model-cooldowns.js`: only hard, bounded, correctly named, non-oversized files count;
   ignored entries are reported in `cooldown_ignored` with a reason. Two-agent
   unrecognized failures within ten minutes are reported as `soft_unhealthy` health
   evidence and never revoke a model. Added `failover_depth_now`, `free_providers_now`,
   `provider_concentration`, `failover_risk` and the runtime failure-mode list to
   `report.json`. `funding_risk` semantics are unchanged.
3. **Baseline fixture repaired.** `tests/economy-cycle-smoke.sh` still asserted an old
   prompt string (`Luna models` / `at the very bottom`) that current
   `executive-economy-cycle.sh` no longer emits, so the whole baseline economy-cycle
   smoke failed before reaching any assertion. The mock now checks the current tier
   rule, low-variant requirement and policy path.

## Verification

- `/bin/sh tests/economy-models-smoke.sh` — PASS, including new adversarial cases:
  forged/future, soft-reason, misnamed, oversized and malformed cooldowns; two-agent
  soft health; `#` catalogue ids; duplicate and malformed authorized entries; missing
  comment repair; a source-level writer invariant; the pre-existing
  additive-authorization, concurrent-change, validate-before-publish and
  test-checkout-guard cases.
- `/bin/sh tests/economy-cycle-smoke.sh` — PASS (baseline fixture repaired).
- `python3 -m py_compile government/economy-models.py`, `dash -n` on both shell tests,
  `git diff --check` — PASS.
- Full exact-head `dash tests/run-all.sh` — see suite-status update accompanying this record.

## Limits and unfinished obligations

- Per-agent permanent exclusions (unavailable model, provider credentials/billing) and
  this agent's own transient penalties live in agent metadata and are not visible to a
  deterministic Economy pass. Economy reports this explicitly; it cannot remove them.
- No live model-using dispatch was performed and no paid fallback was enabled. Act 34
  activation remains held under the existing evidence/cap/Act 31 conditions.
- The `#low` policy is unchanged: models that reject low are still authorized, but a
  runtime `provider.no-route` is now a documented failure mode rather than a hidden one.
