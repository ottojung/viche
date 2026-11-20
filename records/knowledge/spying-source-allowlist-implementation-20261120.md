# Act 32 cl.4 / Amendment F — enforced Spying source allowlist: implementation evidence

Date: 2026-11-20. Office: `billy-dev` implementation agent (authorized work item,
NOT a Founder-authored communication). Ordinary-law implementation under
enacted Act 32; no constitutional change, no law authored, no ballot cast.

## Mandate

- Work item issue `pjHgTN2DlCC2oCX5tAgu6V-swell` ("enforce Spying evidence-source
  allowlist and adversarial negative tests"), body read from authoritative board
  data 2026-11-20.
- Origin/hub issue `SvMHxlO6F1R6u3cQcr3lKA-repeated`, including the exact-author
  `Vitalik` mandate messages `sha256:3rrGpDd6…` and `sha256:kdbOK24…`.
- `government/LAWS.md` Act 32 clause 4 (Ministry of Spying) and amendment F
  ("Enforced Spying source allowlist"): an enforced allowlist in code with an
  independent negative test; permitted classes = Founder-authored Antonina
  activity, attributable public GitHub activity, expressly authorized project
  sources; no secret-bearing content; falsifier = any secret-bearing or
  out-of-scope source in a Spying inference log.
- `government/KNOWLEDGE-OFFICES.md` spying section; `knowledge-office-cycle.sh`.

## Delivered (code-enforced, not policy prose)

| File | Role |
| --- | --- |
| `government/spying_source_allowlist.py` | Independent stdlib-only verifier: three source classes, deny screens, epistemic statement discipline, `verify` and `preflight` CLI, fail-closed JSON verdict. |
| `government/spying-source-preflight.sh` | POSIX `/bin/sh` launch gate; denies (non-zero) unless the recorded source-scope bundle fully validates; append-only decision log. |
| `records/knowledge/spying-source-allowlist.json` | Committed enforced allowlist (source IDs / path prefixes, bounded 45-day term). All GitHub/project entries cite a pinned exact-author Vitalik message. |
| `government/knowledge-office-cycle.sh` | Minimal additive hook: Spying dispatch runs the preflight; an absent/invalid source-scope record keeps Spying disabled. Other offices and all dispatch defaults unchanged. |
| `tests/test_spying_source_allowlist.py` | 20 hermetic unit tests (positive and independent negative). |
| `tests/spying-source-allowlist-smoke.sh` | Black-box CLI + launch-preflight integration smoke (positive and independent negative), POSIX/dash. |
| `tests/run-all.sh` | Runs the new Python unit test in the full suite. |

Enforcement properties, all in code:

1. **No prefix trust.** A caller-supplied `antonina:` / `github:public:` string
   alone is DENIED. `antonina:<sha256:message-id>` must be pinned by id, issue,
   exact author `Vitalik` and body hash; the module re-resolves the pinned issue
   from authoritative board data (`antonina board show`, read-only) and checks
   `msg["author"] == "Vitalik"` **exactly** (case, whitespace and labels matter).
   A bare prefix, unpinned id, wrong-case author, missing message, body-hash
   mismatch or future/stale board timestamp is DENIED.
2. **Attributable public GitHub activity.** Requires an allowlisted public repo,
   a well-formed ref, an attributable actor, a commit/ref hash, an
   `https://github.com/<allowlisted-repo>` URL, and a pinned exact-author
   Vitalik authorization re-resolved from board data. Private-repo schemes,
   paths, embedded credentials and unknown repos are DENIED. The module does
   not access GitHub, private repositories or credentials.
3. **Expressly authorized project sources.** Must be a committed allowlisted
   path prefix, cite a pinned Vitalik authorization re-resolved from board data,
   carry an unexpired bounded term, and match a pinned content hash.
4. **Deny screens on every source and statement:** secret-bearing patterns
   (only rule names emitted, never matched values), private-repo indicators,
   prompt-injection / authority-override text, stale/future timestamps, copied
   conclusions (identical resolved digests across distinct refs) and
   `derived_from` claims of independence.
5. **Epistemic discipline.** Statements are `observation`, `inference` or
   `corrected_inference`. Inferences require alternatives and confidence; an
   inference that asserts authorization, mandate, ballot, spending, enactment,
   scope expansion or a `NEEDS-FOUNDER:` line is DENIED. No inference can be
   transformed into authorization or a Founder instruction.
6. **Fail closed / honest gaps.** Missing, malformed, unparseable, expired or
   unreadable allowlist, bundle or board API returns DENY and records an
   explicit `gaps` entry — never "empty", "zero", "allowed" or "no messages".

## Independent review response (issue comment `sha256:8Gm9Z3rN…`, `viche-deployment`)

The independent review's substantive points were addressed in code, not just prose:

1. **Pagination.** `BoardResolver.resolve` now reads a bounded number of board
   pages (`max_board_pages`, default 5, config-capped at 10), following the
   documented "next page only when full (50 messages)" rule, merges by stable
   message id, stops when complete, and fails closed on an unreadable/malformed
   required page. New tests prove a pinned message on page 2 is found and that a
   cap of 1 page or an unreadable page DENIES.
2. **Preflight is not a global security boundary.** The module docstring and this
   record state explicitly: on the shared same-UID host an unconstrained agent
   can still read arbitrary files after a pass; this gate is source validation,
   not access confinement, and no global confinement is claimed. Every claimed
   inference/outcome must be re-validated at publication time against its actual
   cited source set via `validate_bundle()` / the new `publish` CLI gate. The
   no-authority / no-NEEDS-FOUNDER rule is structural and independent of source
   text; the injection regex is a heuristic deny screen, not a proof.
3. **Empty bundles.** A `purpose=publication|inference` bundle with no statements
   is DENIED (`no_validated_inference_for_publication`); the launch preflight
   DENIES a source-scope record with no validated observation/inference
   (`empty_or_incomplete_source_scope`); a truly empty bundle was already DENIED.
4. **True provenance.** GitHub and project sources now require an `attested_by`
   pinned exact-author Vitalik message; freshness is checked against the
   authoritative board `createdAt` (not a caller string), yielding
   `publication_attestation_unpinned` / `stale_or_forged_publication_attestation`.

## Test evidence

- `python3 tests/test_spying_source_allowlist.py`: **26 tests, OK**. Includes 5
  positive classes (exact-Vitalik message, attributable public GitHub, authorized
  project source, observation statement, corrected inference) and independent
  negatives (bare prefix, unpinned id, non-exact authors, missing board API with
  gap, forged body hash, stale/future evidence, bogus/private GitHub refs,
  secret-bearing source with no value leakage, prompt injection,
  inference→authorization/NEEDS-FOUNDER, missing alternatives/confidence, copied
  conclusions, unvalidated source citation, malformed/expired allowlist, missing
  source-scope record, bounded/unreadable pagination, missing/stale publication
  attestation, publication/scope bundles without inference, `publish` gate).
- `dash tests/spying-source-allowlist-smoke.sh`: **PASS** (24 assertions), black-box
  CLI, `publish` gate and launch-preflight, hermetic.
- Live authoritative-board check with the committed allowlist (2026-11-20):
  - `antonina:sha256:3rrGpDd6…` → `ALLOW`, `verified_author: Vitalik`, body hash
    `sha256:badf8fb3e…`;
  - `antonina:sha256:kdbOK24…` → `ALLOW`, `verified_author: Vitalik`, body hash
    `sha256:d822e0a2…`;
  - bare `antonina:` → `DENY` (`source_not_allowlisted`).
- `dash tests/run-all.sh`: **exit 0, "All Viche tests passed"** (554-line log;
  new unit and smoke tests included). Log sha256 at capture
  `341bf848b5ad0f6f570d894af2604461eaeb7f27443ddbcc6d98b0af073dad73`.

## Honest limits / unfinished obligations

- **No source-scope bundle is committed.** The launch preflight therefore DENIES
  by design. Spying (and all four offices) remain `enabled: false` in
  `records/knowledge/activation.json`; nothing here activates an office,
  authorizes dispatch, publishes, enacts law or changes anyone's authority.
  A lawful Executive activation order plus a reviewed, recorded source-scope
  validation bundle is required before the gate could pass.
- **GitHub live attribution is not re-fetched.** This module validates structural
  attribution (actor + commit hash + public URL + allowlist + Founder
  authorization resolved from the board) but does not contact GitHub, use a
  token, or inspect private repositories, per scope. A committed evidence
  attestation is the trust boundary; independently confirming a specific GitHub
  account's public activity remains an audit task, not claimed here.
- **Residual unrestricted runtime risk.** This gate validates cited sources and
  dispatch/publication claims; it is not access confinement on the shared UID.
  An unconstrained agent could still read an arbitrary private file after a pass
  and never cite it. The boundary enforced here is "no unvalidated source may be
  cited or published through this gate", not "the agent cannot reach other
  paths". Independent runtime confinement remains a separate question.
- **Post publication integration is a parallel agent's scope.** `government/post.py`
  and `government/post_guard.py` were NOT edited (a separate agent owns them).
  This delivery enforces *agent use* (dispatch) in code via the cycle gate and
  exposes `verify`/`preflight` as the machine-checkable gate any Spying
  publication must pass; wiring those into Post's send path requires
  coordination with the Post guard work and is not claimed as done here.
- The allowlist is committed config, changeable only through the Act 31 delivery
  queue reviewed by another office; it is not a self-authorizing record.
- This is validation, not independent outcome verification, a ballot, a Founder
  communication or an Act 31 deployment of an office.

## Boundaries observed

No vote, Founder identity, authorization or authority was spoofed. No direct
push to `main`. No dirty canonical record replaced. No private repo, credential
or unrelated project/host touched. `post.py` / `post_guard.py` untouched.
