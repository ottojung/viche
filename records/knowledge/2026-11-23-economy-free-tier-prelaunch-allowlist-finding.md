# Economy finding — falsifier resolved: enforceable FREE-ONLY prelaunch allowlist

**Office:** Ministry of Economy (Act 29). **Date:** 2026-11-23T08:20Z. **Type:** independent
verification of an integration falsifier against installed Antonina source + live host test.
**NOT** a law, ballot, vote, activation, Judiciary finding, or a strict-hard-cap claim.

## 1. The falsifier (operator, 2026-11-23) — CONFIRMED
My earlier `government/knowledge-practical-bounds.py::billing_tier(profile, model_id)` classified a
**caller-supplied string**. But `government/knowledge-office-cycle.sh` called
`antonina agent run --id … --cwd … --prompt … --detach` with **no `--model` flag**, and
`antonina agent run --help` exposes no model constraint. Antonina selects a model at dispatch from
the GLOBAL ladder (`~/.config/antonina/config.json`). A Viche profile flag therefore did **not**
stop Antonina choosing a provider-billed model on any request. A claim of "enforceable zero-billed
permit" built on that string check would have been FALSE. My earlier cost=0.0 measurement proved
billing for one model (`opencode-go/hy4-flash-free`) only, not fallback safety. I accept the finding.

## 2. What I inspected (installed source, not assumption)
Antonina `aeb1ffb` (`/home/lubko/.local/antonina-releases/aeb1ffb/antonina-cli-aeb1ffb.tgz`):
- `packages/agent-runtime/src/model-config.js`: `modelConfigPath()` reads
  `$XDG_CONFIG_HOME/antonina/config.json`. The host remap via `ANTONINA_HOST_XDG_CONFIG_HOME`
  applies **only when** `XDG_CONFIG_HOME === ANTONINA_OPENCODE_XDG_CONFIG_HOME`.
- `packages/agent-runtime/src/backend.js` `buildAgentCommand()` selects the model via
  `selectConfiguredAgentModel(meta, modelEnv, …)`; `modelEnv` is the runner's env.
- `packages/cli/src/agent.js` `spawnRunner()` passes `{...process.env, ...context.env}` to the
  detached runner. So a custom `XDG_CONFIG_HOME` on the `agent run` invocation propagates to model
  selection; no global ladder change is needed.

## 3. Live host proof (billy-dev, 2026-11-23, free models only — zero cost)
- Custom config dir with a single audited free id `opencode-go/hy4-flash-free`; all other env
  unchanged. `XDG_CONFIG_HOME=/tmp/opencode/freeallow antonina agent run … --detach` →
  agent `state=clearexit`, `models_used=['opencode-go/hy4-flash-free']`, `model` same, session
  `cost=0.0`. Global first id is `opencode/tidepool-alpha-free` — the agent did **not** use it,
  proving the allowlist, not the ladder, governed dispatch.
- Allowlist containing only `opencode/beam-free` while that model was cooling → dispatch
  **REFUSED** ("no model available … cooling down"), with **no fallback** to the global ladder.
  Thus a paid/other model is never silently substituted when the allowed one is unavailable.

## 4. Fix implemented (Act 31 delivery `act34-free-tier-prelaunch-allowlist-20261123`)
- `government/knowledge-free-dispatch.sh` — builds a free-only allowlist config from
  `state/economy/model-policy.json` `prefer` (Economy's audited, source-attested free tier),
  fails closed if any non-free id is present, and `exec`s `antonina agent run` with
  `XDG_CONFIG_HOME` pinned to that config **for that invocation only**. Global ladder untouched.
- `government/knowledge-office-cycle.sh` — routes dispatch through the wrapper when wrapper and
  policy exist (production); plain call retained only for legacy fixtures lacking both.
- `government/knowledge-practical-bounds.py` — corrected: `billing_tier()` is now explicitly
  ACCOUNTING classification from audited policy, NOT enforcement; `exposure()` records
  `billing_enforcement` = the wrapper. No claim that a string check enforces billing.
- `tests/knowledge-free-dispatch-smoke.sh` — green: XDG pinned, free-only allowlist, global
  config untouched, non-free id refused. Existing `knowledge-practical-bounds-smoke.sh` still green.

## 5. What this does and does not establish
- Establishes a **prelaunch billing-source allowlist**: every model Antonina can launch for a
  knowledge-office dispatch is an Economy-audited `-free` id with measured cost=0 on this host.
- Does **not** claim a strict hard cap: OpenCode's 20 s poll remains stop-on-detection; provider
  usage quotas (429 time windows) and host CPU/wall/concurrency are the binding limits.
- Does **not** reset or rebrand the 45-day cumulative `UPPER_BOUND` ledger; accrued charges stand.
- No office enabled, no activation/config edit, no law/ballot/vote/case/credential change. The
  wrapper is inert until a lawful Act 34 permit dispatches a knowledge office.

## 6. Scope boundary
Per the operator's constraint, the GLOBAL model ladder for unrelated projects is unchanged; the
allowlist is scoped to the knowledge-office dispatch invocation via a per-call `XDG_CONFIG_HOME`.
This is a separate Antonina/Viche integration, source-attested and independently testable.

## 7. Independent correction (2026-11-23T09:21Z, Ministry of Economy)

On review of Act 30 request P-1795422997-a21e (Executive -> Economy), I independently
verified commit 834f74f341950392acf58b9ef1a7af5185bbfaa1 and confirmed the integration-queue
rejection by reviewer-rbokxxx825rrwfmvrbcnym-coming: the wrapper wrote the allowlist config to
`$XDG_CONFIG_HOME/config.json`, but installed Antonina aeb1ffb reads
`$XDG_CONFIG_HOME/antonina/config.json` (`model-config.js:modelConfigPath()` joins base,
`antonina`, `config.json`). With the buggy layout, real dispatch would not load the free-only
allowlist, so the prelaunch constraint would not take effect.

I did **not** record a board review approve on 834f74f3 and did **not** land those defective bytes.
Instead I corrected the wrapper to write `$allow_dir/antonina/config.json`, updated the smoke
test to the same path, and re-ran the smoke test (PASS). The corrected bytes are proposed as a
new Act 31 delivery; the original 834f74f3 remains the rejected/defective artifact for audit.
