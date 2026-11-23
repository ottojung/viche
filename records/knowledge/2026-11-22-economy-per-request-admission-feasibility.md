# Economy — per-request admission/billing-bound feasibility (Act 32/33 Statistics trial)

**This is a historical November 22 finding. The office-admission subdefect was subsequently corrected; see the dated correction below. The separate provider-level hard billing HOLD remains.**

**Office:** Ministry of Economy (Act 29). **Date:** 2026-11-22T18:4xZ. **Type:** source-level +
empirical technical evidence answering the Founder's 18:20Z assignment. **NOT** a law, ballot,
gate approval, office enablement, Judiciary finding, or claim of a verified strict cap.
**Disposition: HOLD. No strict provider-billing bound is proven for this provider.**

## 0. Authority, scope, recovery
- Founder assignment (billy-dev only): inspect the exact installed OpenCode/Antonina interface;
  produce a production-enforceable per-request admission/bound if feasible; negative-test the
  399,000-token case; prove maximum overrun quantitatively incl. crash and backend stop; if a
  strict bound is impossible, do not fake proof or relax caps — document the exact gap, offer
  concrete alternative provider/billing controls, and HOLD.
- Act 33 (codification `e9719476`) is enacted on `main`; the hard cap is not proven, so the
  "do not turn on the office" condition stands. All four offices remain `enabled: false` in
  `government/knowledge-budget.conf`; I enabled nothing.
- Recovery check: fresh isolated worktree `economy/per-request-cap-20261122` off `main`
  (`2c7fb98d`); canonical dirty records untouched; no prior artifact for this task existed, so
  no side effect was duplicated. I made two tiny free-model test calls (one 429, one ~16k tokens)
  as authorized tests; no purchases, account/credential changes, law, ballot, or main push.

## 1. Exact installed interface (not generic advice)
- `opencode` v2.2.0 at `/home/lubko/.local/antonina-v2-opencode/node_modules/@opencode/cli/bin/opencode.exe`.
- `opencode run --help`: flags are `continue, session, fork, model, agent, format, file, title,
  thinking, auto`. **There is no `--max-output-tokens`/`--max-tokens` flag.** No per-request
  output ceiling can be passed on the CLI.
- Config schema `https://opencode.ai/config.json` (fetched): no top-level `maxTokens`. A model
  override may set `providers.<id>.models.<m>.limit.{context,output,input}`. Agent `request.body`
  overlays exist but the V2 agents doc states they are **"preserved but not yet sent with model
  requests"** — so `max_tokens` cannot be injected per-agent.
- Bundled binary: `max_tokens:i.options.maxTokens` when numeric; `c=e.maxOutputTokens ||
  this.config.maxTokens || 8192`; model `limit.output` feeds `options:{maxTokens:oQ(g.limit,
  p.inputTokens)}`. So OpenCode computes each request's output cap from the model's declared
  limit minus input — but this is a *generation* cap, not an aggregate spend ceiling.
- `agent.steps` (max model steps) is settable; subagent depth defaults to 1. Viche does not set
  either for knowledge-office dispatches.
- The meter is retrospective: `knowledge-budget-tool.py snapshot()` reads cumulative columns from
  the OpenCode SQLite `session_v2`; the engine has no inline per-request callback. `monitor()`
  sleeps 20 s before it reads reservation/status/meter and kills. `finalize_locked()` says in code
  a kill is not proof the backend stopped; `stop_or_kill()` is `|| :` fire-and-forget.

## 2. Empirical test — is output actually capped? (session ses_dfb743e6affeOBILCRkWVdQDJB)
Config: project-level `opencode.jsonc` set `opencode-go/hy4-flash-free limit.output=40`;
prompt "Count from 1 to 200, one number per line, then say DONE."; run with `--format json`.

- Request 1: `step_finish reason="length" tokens={input:3293, output:0, reasoning:**40**,
  cache_read:1792}` — the provider **did** stop generation at 40 tokens.
- Request 2: `step_finish reason="length" tokens={input:304, output:0, reasoning:**40**,
  cache_read:4864}` — capped again.
- Request 3: no `step_finish`; `error type="output-limit"`, "Response still truncated after two
  output token limit continuations" — OpenCode auto-continued twice, then hard-errored.
- Session meter after: `tokens_input=4202, tokens_output=9, tokens_reasoning=243,
  tokens_cache_read=11776, cost=0`. Generation = 243+9 = **252 tokens**.
- **Overrun finding:** 2 completed requests were capped at 40 each (=80), but total generation
  was 252; the third/continuation path generated ~163 tokens, i.e. **~2.0× the nominal
  3×40=120 bound**. A configured per-request output limit therefore does **not** bound total
  generation for one prompt: OpenCode's auto-continuation bypasses/exceeds it. This is measured,
  not inferred; residual uncertainty is whether the excess is a continuation code path or
  reasoning-token accounting (both leave the gap open).
- All `opencode` (non-go) provider models returned HTTP 429 `FreeUsageLimitError`,
  `retryAfterMs≈22,902,000` (~6.4 h) — an account-level time quota, not a token cap. (Separate
  availability fact; `opencode-go` still served the test.)

## 3. Required negative test — 399,000 existing used tokens (historical behavior before cumulative office-cap correction)
Ran the engine's own deterministic `admit` with an isolated aggregate (no live state):
```
admit 399000 -> {"admit": true, "reason": "within caps"}
admit 400000 -> {"admit": true}   admit 1200000 -> {"admit": true}
```
At 399,000 used tokens the gate *at the time of this investigation* **authorized another Statistics reservation** (399k +
400k = 799k < 1.6M aggregate). The office's own 400k cap is not checked at admission at all —
only the aggregate. **Falsifier of the then-current office admission cap: achieved.** The next call was unbounded by
anything the engine enforces before launch.

## 4. Quantitative maximum overrun (current implementation)
Declared limits (models.dev, cached 2026-11-21): longcat-2.5-free 1,000,000/262,144;
tidepool-alpha-free 1,048,576/131,072; hy4-flash-free 1,048,576/65,536 (context/output).
For one admitted `opencode run` with a large-context free model:

    actual_billed - 400000 <=  (input up to ~1,048,576)
                              + (output/reasoning, with continuation bypass — measured 2.0x nominal cap)
                              + (tokens in the <=20 s poll blind window, incl. concurrency)
                              + (tokens after kill before backend actually stops)

Each term is positive and engine-unbounded. A single request can bill roughly **1.26M tokens**
(1M context + 262k output), ~3.2× the 400k cap, before any poll observes ≥400k; with the
measured continuation bypass the generation term is itself > the configured cap. The only bound
that holds is the *accounting* one: the full 400k is charged to the ledger and further dispatch
may be stopped — not that billing stopped at 400k. Crash and backend-stop cases are not
independently bounded: meter rows flush after the fact, and a fire-and-forget kill cannot reverse
provider billing. No honest strict numeric maximum can be asserted.

## 5. Feasibility of each requested control
- **model max_output_tokens:** feasible to *set* via provider model `limit.output` and the
  provider honors it per completed step — **but** auto-continuation bypasses it (§2) and it is a
  global model config, not scoped to Statistics. Not a strict aggregate bound.
- **bounded input/context:** `limit.context` is settable, but a 1M-token context means up to ~1M
  input tokens per request is *allowed*; no evidence OpenCode hard-truncates adversarial input to
  a small bound. Unproven.
- **atomic per-request precharge:** the engine reserves *before* launch (good) but charges the
  full office cap, not a computed worst-case of a request, and admits at 399k (§3). A worst-case
  precharge gate would need trustworthy bounds on input, output, continuations and steps — the
  output/continuation bound is falsified by §2, so any such gate would be a number without a
  mechanism (fake proof). Not implemented.
- **streaming/kill uncertainty:** admitted gap; kill is not proof of backend stop (source §1).
- **cumulative session+aggregate caps:** accounting accumulation works; it does not bound actual
  billing (§4). CPU `UPPER_BOUND` accumulation is preserved and was not touched.
- **concurrency:** no hard concurrency ceiling exists in the dispatch; Constitution VII forbids a
  worker-number cap as a substitute, so the control would have to be a spend/reservation bound,
  which is unproven.

## 6. Concrete alternatives requiring Founder authorization (not actioned)
A genuine strict bound needs a provider/billing control outside this interface:
1. A **provider or gateway with a hard per-key spend/token ceiling** (e.g. OpenRouter credit
   limit, Anthropic/AWS Bedrock budget, an API gateway that enforces `max_tokens` and a prepaid
   balance) with a key dedicated to the Statistics trial — requires an account/credential and, for
   paid tiers, money (Founder-reserved, Act 30 §2). Not done.
2. A **prepaid/ephemeral key with fixed credit per trial**, so maximal financial loss is capped
   by the purchased amount — requires Founder spending authorization.
3. A **local model on this box** (no external billing) — but CPU/GPU has no per-office meter
   (only a conservative whole-host upper bound) and quality/context differ; does not satisfy an
   actual-resource denominator.
None is available under my authority; I did not create accounts, hold credentials, or spend.

## 7. Disposition and role boundaries
- **HOLD** the model-driven Act 32/33 Statistics first trial. The cap is **stop-on-detection, not a strict hard
  cap**; the 399k negative test and the measured continuation bypass refute a strict-cap claim.
- No fix is submitted to Act 31 because no production-enforceable strict bound was demonstrated;
  a partial gate would be unverifiable and would violate "do not fake proof".
- No office enabled; no law, ballot, vote, case state, config, cap, dirty canonical record, or
  credential modified; no CPU UPPER_BOUND reset; no NEEDS-FOUNDER line invented for a merely
  technical fact. Judiciary reviews independently; this is Economy evidence, not its finding.

## Evidence index
- Worktree/branch: `economy/per-request-cap-20261122` @ `2c7fb98d`.
- Source: `government/knowledge-budget.{sh,conf}`, `government/knowledge-budget-tool.py` (exact
  bytes from main); `opencode run --help`; `https://opencode.ai/config.json`; agents/config docs;
  bundled binary strings.
- Empirical: session `ses_dfb743e6affeOBILCRkWVdQDJB` in the read-only Antonina `session_v2`
  meter; `admit` outputs in §3. Reproducible negative test: `tests/knowledge-budget-admit-negative-20261122.sh`.

## Dated correction — November 22, 2026 (after original measurement)

The preceding negative result and source snapshot remain HISTORICAL
evidence of the original Economy admission defect. Subsequent fix
fix/economy-cumulative-office-cap-20261122 at 40545a71
enforces BOTH cumulative per-office and aggregate caps with fail-closed
by_office accounting. The updated negative test now rejects another full
Statistics reservation after 399,000 tokens already charged to Statistics.
The test executes the CURRENT repository rather than an old worktree.
Thus section 3's original admit:true must not be described as the live state.
The source provenance of that earlier measured result remains visible.
This correction does NOT solve the independent OpenCode per-request
continuation, post-kill billing, retries, or input token overspending risks
(sections 2, 4-5). HOLD remains for model-using knowledge offices until
a provable per-provider-request admission bound is demonstrated.
The model-free Statistics trial is a separate zero-provider alternative.
