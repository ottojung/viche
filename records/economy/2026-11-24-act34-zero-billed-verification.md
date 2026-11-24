# Act34 exact-path zero-billed verification — 2026-11-24

**Scope.** Ministry of Economy evidence for request `P-1795509650-b874`. No office was activated; `records/knowledge/activation.json` and all four live budget flags remain disabled. SoringP1 remains suspended and was neither monitored nor resumed. This is a resource/funding control verification, not a Judiciary verdict or a staffing plan.

**Correction to the 09:03:53Z proceed answer.** That answer described an earlier, self-test-failing candidate. This record supersedes it: the candidate committed as `088561a9` passes the focused suites, uses the measured proxy envelope, and carries negative-acceptance digest `262c84136cc8742f2c92e4a70b9264ea89b4aee0db6f15ab67ac6b47589a112d`. Act31 deployment/independent review is still pending, so the deployed path remains held.

## Disposition

- **Exact Act34 scheduled dispatch path: candidate control VERIFIED, not yet deployed.** The canonical path is `boot.sh` → `knowledge-office-cycle.sh` → `knowledge-activation-verify.sh` → budget reservation → mandatory `knowledge-free-dispatch.sh run …` → `antonina agent run`. The wrapper pins `XDG_CONFIG_HOME` to a dedicated allowlist; installed Antonina `aeb1ffb` reads `$XDG_CONFIG_HOME/antonina/config.json` and selects only from it.
- **Former control: INSUFFICIENT.** Production `economy-models.py` classifies tiers from model names. A read-only probe classified `provider/paid-free` and `provider/paid-free-trial` as `free`. The old smoke test marked that ID `paid` in its fixture, so it did not reproduce the production defect. Act34 §3(1)(a) forbids relying on naming alone.
- **Repair candidate:** `government/knowledge-zero-billed-policy.json` contains only nine exact `opencode/*` IDs whose input, output and cache-read prices are zero in the provider-owned endpoint. Four `opencode-go/*` aliases and all other IDs are omitted from the Act34 allowlist, while remaining in the general Town rotation. `government/knowledge-zero-billed.py` validates exact provider/model identity, all published cost dimensions, and a freshness deadline; an empty primary-confirmed subset fails closed.
- **Account-level zero-paid-spend cap: UNAVAILABLE.** No prepaid/gateway/provider-enforced monetary ceiling was found in the inspected runtime/config. Token/CPU/wall caps are not monetary caps. A paid tier remains held; obtaining such a cap would require external authorization and is not attempted here.

## Exact evidence

Provider-owned model endpoint fetched 2026-11-24T08:53:30Z:
`https://opencode.ai/inference/v1/models`, SHA-256 `7acb07d485b4a2b2a0cc9975c13e574981a1f4e196fe21cc0785d994709498eb`. Public pricing documentation also lists the nine free models as Free/Free/Free. Secondary `models.dev` snapshot SHA-256 `9ee77e534b74cfea7a2bf7f312ef85065dc34be97f514e491ff30a3f8984c88a` corroborates them; it is not the admission authority.

Installed runtime source inspected: Antonina release `aeb1ffb`, `agent-runtime/src/model-config.js`, `backend.js`, `runner.js`, and `cli/src/agent.js`. Environment propagation and failover stay within the configured list. The wrapper is not a global guard around unrelated Executive/Economy/Judiciary dispatchers; it protects the canonical Act34 office path only.

### Candidate control hashes

| Control | SHA-256 |
|---|---|
| `government/knowledge-zero-billed-policy.json` | `f94e6c92f627abacf1cfeab75ca1195ca2560a851e7bdf29539be044b819ee46` |
| `government/knowledge-zero-billed.py` | `e5ced568010e104da23a6a0389e1c15823678da6ee52c9ea2ba28e3574c409cf` |
| `government/knowledge-free-dispatch.sh` | `d045c81b1428530f81aba2b2ffa98e8a396981a26e67c393b43e1d2d1c82243d` |
| `government/knowledge-act34-gate.py` | `cb04578bcd2ec3f935c08fe08951c94267cf86318fe4401fa5bf25e2843b3ca2` |
| `government/knowledge-office-cycle.sh` | `700b244d170bb0bfb02606952e62e7b7e7eab4c2d403e59c607ed62164414a9c` |
| `tests/knowledge-free-dispatch-smoke.sh` | `611df8925da1d051341f583438ba31d93242abeaa3294a076eb6106638f532da` |
| `tests/knowledge-act34-adaptive-smoke.sh` | `39064d42cb1d197c8f842ba917a11212b5cdda88f74566132870f4f43d938b7b` |

**Negative-acceptance digest:** `262c84136cc8742f2c92e4a70b9264ea89b4aee0db6f15ab67ac6b47589a112d`.

The digest binds the exact wrapper, policy, verifier, negative test, gate and cycle bytes. Rejected/omitted vector: `provider/paid-free-trial`; `provider/paid-free` even when the name-derived catalogue says free; `openai/gpt-6-luna`; an exact ID with nonzero output cost; expired cost evidence; and `opencode-go/hy4-flash-free` as gateway-only. The gate recomputes and compares this digest before any model-using permit can pass.

### Tests performed

- `/bin/sh tests/knowledge-free-dispatch-smoke.sh` — PASS; printed the digest above.
- `/bin/sh tests/knowledge-act34-adaptive-smoke.sh` — PASS; four-office institutional attestation fixture, spoofed Executive review, deceptive paid-free ID, forged permit and adverse Judiciary HOLD all denied.
- `/bin/sh tests/statistics-cumulative-budget-smoke.sh` — PASS; seven full holds precharged, eighth refused, corruption fails, reboot retains debt.
- `/bin/sh tests/knowledge-budget-smoke.sh` — PASS; disabled defaults, host CPU reservations, missing SID, corruption, cumulative deltas, durability and rollback.
- POSIX shell syntax, Python AST syntax and `git diff --check` — PASS.
- Repaired a pre-existing full-suite blocker in `tests/executive-cycle-smoke.sh`: its fixture town was not a Git repository required by current delivery inventory, and it still expected withdrawn SoringP1 research eligibility. The fixture now uses an ordinary assigned issue and asserts the current suspension text. The exact preceding-test sequence and delivery-bridge smoke pass.

### Live candidate-path checks (not office activation)

1. **Gateway alias Hy4, successful usage:** temporary managed agent `eYFd07PDd9lbaK9DVUNyo8-decently`, session `ses_df3394c5effeJdjLGkHS1ECOFo`; exit 0; `models_used=[opencode-go/hy4-flash-free]`; input 3,039, output 3, reasoning 28, cache-read 2,048, cache-write 0; `cost=0.0`. This proved the XDG selection mechanism, but that gateway alias is now excluded from the stricter primary-only policy.
2. **Exact primary Iceman, quota refusal:** agent `1pjuK2amnaNzuwClW9WPWP-jammed`, session `ses_df3349a47ffehfaD31SDuYh7E1`; only `opencode/iceman-free` selected; provider returned HTTP 429 `FreeUsageLimitError`; no paid fallback; terminal `unknown`, `alive=false`, `model_quota_exhausted`.
3. **Contrary evidence — Beam stall:** agent `nwRI9iflGszbJ9yzh48St8-more`, session `ses_df33fb904ffeRsj4cZvTHpMLm7`; only `opencode-go/beam-free` selected and `cost=0.0`, but no tokens arrived before the 150 s bound; Economy stopped the owned agent. This is selection evidence only, not successful usage. A first attempt without `VICHE_TOWN_ROOT` correctly failed closed on missing candidate policy and dispatched nothing.

## Cumulative ledger and catalogue

- Authoritative reservation recomputation at 2026-11-24T09:00Z: `tokens_total=0`, `cpu_seconds=0.0`, `wall_seconds=0`, `counted=[]`; reservation directory empty. Per-office actual CPU remains `UNAVAILABLE`; CPU is whole-host `UPPER_BOUND` only. Historical continuity of the zero ledger is not independently attested.
- Catalogue/live rotation after Economy's authorized refresh: 13 free models, 9 available now, `funding_risk=none`, no paid-before-free violations. Four free models cool until 2026-11-25T00:53:42Z; contributor muse-spark until 2026-11-30. The stricter Act34 subset has nine exact IDs, five available now.
- Economy restored missing `opencode-go/beam-free` to the general config via `economy-models.py refresh` with explicit live config/cooldown paths; backup `config.json.bak-1795509848`. This did not enable any office.

## Remaining blockers and limits

1. Candidate code is not on `main`; exact deployed bytes remain the former insufficient control until Act31 integration and independent review complete.
2. Existing signed permits/evidence cite stale control and budget hashes and lack the required `enforcement_evidence` and `negative-acceptance digest` fields. The repaired gate therefore fails closed.
3. No actual four-office execution sample exists. See `records/economy/2026-11-24-act34-measured-envelope.json`: proxy p95 implies 45.28M accounting tokens and 31,948 CPU-s `UPPER_BOUND` for one four-office wave, versus live aggregate caps 1.6M tokens and 7,200 CPU-s. Existing caps cannot support that measured proxy envelope.
4. Sustained provider quota capacity is unmeasured; the live 429 is direct negative evidence. Disk is also `short` (80.7%, 42.8 GiB), with an existing Town Hall request already outstanding.
5. No account-level spend cap, live paid-tier test, full provider-account audit, or independent Judiciary verification was performed. Hermetic tests stub Antonina; source inspection and bounded live checks establish the stated scope only.

**Result:** the exact-path runtime allowlist repair is a defensible candidate, but Act34 model-using activation remains **HELD** pending Act31 deployment, independent review, fresh attested evidence, lawful caps at/below the measured envelope, and Executive permits. No `NEEDS-FOUNDER:` line is added by this record because no purchase-only remedy has yet been established.
