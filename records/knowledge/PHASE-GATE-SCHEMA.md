# Act 32 independent phase-gate record — data format and verification spec

**Status:** implementation specification for `government/knowledge-phase-verifier.py`.
This is an ordinary implementation record under Acts 4, 6, 15, 21 and 32. It is
**not** an Act, ballot, activation order, Judicial verdict or Governor approval.
No office is enabled by this file.

## 1. Purpose and separation

Act 32 clause 9 / amendment K require reversible, serial, evidence-dependent
phase gates Statistics → Foresight → Strategic Development → Spying, each with an
independently reviewer-signed `proceed|hold|stop` disposition. The shared Unix
UID cannot authenticate a sender (clause 5), so a caller-supplied `signed-by`
string is worthless on its own.

This verifier is deliberately **separate** from:

* `government/knowledge-activation-verify.sh` — gates one office's activation
  window (`activation.json`); and
* `government/knowledge-office-cycle.sh` / `boot.sh` — dispatch/runner code.

It uses its own data format, `viche-knowledge-phase-gate-v1`, stored at
`records/knowledge/phases/<gate-id>.json`. The runner integration is a later,
isolated change; this file and the verifier do not edit those shared scripts.

## 2. Record fields

| Field | Type | Meaning |
|-------|------|---------|
| `schema` | string | must be `viche-knowledge-phase-gate-v1` |
| `gate_id` | string | unique id, e.g. `statistics-initial-20261120` |
| `act` | int | parsed at runtime from canonical LAWS.md; must equal the single enacted IKCA Act number (32 today) |
| `act_bill_id` | string | must be `institutional-knowledge-and-communications-act-v4` |
| `office` | enum | `statistics\|foresight\|strategy\|spying` |
| `phase` | enum | `initial` or `renewal` |
| `host` | string | must be `billy-dev` |
| `predecessor` | object\|null | `{gate_id, office, record}`; `null` only for statistics initial |
| `next_office` | string\|null | next office in the serial order; `null` for spying |
| `not_before`, `expires_at` | int | epoch seconds; window >0, ≤14 days for `initial`, ≤45 days always |
| `created_at`, `created_epoch` | string,int | creation timestamps |
| `decision` | enum | `proceed\|hold\|stop` |
| `preconditions` | object | `baseline`, `budgets`, `executive_order`, `judiciary_check`, each `{ok: bool, ...}`; all must be `true` to proceed |
| `evidence` | array | Git-anchored source evidence: `{name, path, sha256, git:{commit,path}}` |
| `evidence_digest` | string | `sha256:` + canonical digest over `evidence` (computed by `evidence-digest` subcommand) |
| `review` | object\|null | Git-anchored, officer-attributed disposition (see §3) |
| `attestation` | object | independent institutional corroboration of `review` (see §3) |
| `day30_review` | object\|null | mandatory Judiciary review for `renewal` only (see §5) |
| `day30_attestation` | object | corroboration for `day30_review` (same shape as `attestation`) |
| `reauthorizing_act` | object | `renewal` only: a later enacted Act number in LAWS.md |

## 3. Independent reviewer — the trust anchor

A proceed requires `review` with:

* `reviewer`: an officer id present in canonical
  `government/branch-officers.tsv` (authoritative registry). Judiciary is
  `c1e00008`; Executive is `c1e00002`, etc. The role must match
  `reviewer_role`.
* Only a **`judiciary`** officer may sign `proceed` (Act 32 §9/K names the
  independent Judiciary as verifier). Other registered officers may file
  `hold`/`stop`.
* `review_artifact`: `{git_commit, git_path, sha256}`. The verifier requires the
  commit to exist, reads the blob with `git show <commit>:<path>`, recomputes its
  SHA-256 and compares to the declared digest.
* The artifact's bytes must be UTF-8 `Key: value` lines binding, exactly:
  `gate:`, `reviewer:`, `reviewer_role:`, `decision:`, `evidence_digest:` and
  `reviewed_at:`.

Any `signed_by`/`signed-by` field on the caller's record is **ignored**. A
forged or replayed artifact fails on the digest or the binding check; a review
by an unregistered officer fails the registry check. Artifact paths are read by
**exact Git tree traversal** (`git ls-tree` + `cat-file blob`); `..`, absolute
paths, symlinks and submodule/tree entries are rejected.

### 3.1 Multi-channel attestation — a Git file is not a signature

An independent trust-model review (board comment 2026-11-20T18:10Z on the
originating issue) correctly observed that any same-UID actor can commit a text
file containing a real Judiciary id. Therefore a proceed ALSO requires the
`attestation` block, which names an Antonina board `issue_id`, the expected
officer id and the officer's agent id. The verifier independently checks:

1. an institutional `antonina board review` verdict of `approve` recorded on
   the **exact Git commit** of the review artifact, with a reviewer attributable
   to the officer (read from the board via `antonina board show --json`);
2. a board comment **authored by that officer** citing the gate id and the
   artifact commit (a second independently recorded board action); and
3. the officer's agent id matching the authoritative appointment registry
   (`$VICHE_STATE_ROOT/appointments/appointments.tsv`) and having an
   attributable managed-agent session (`antonina agent status`).

`VICHE_PHASE_ATTESTATION_JSON` may point to an offline **export** of these
channels for hermetic/audited verification; hermetic tests use synthetic
exports. In production the verifier reads the live channels and fails closed if
they are unavailable or disagree.

**Residual limitation (not hidden):** the shared Unix UID cannot
cryptographically authenticate board authorship, appointment records or Git
commits (Act 32 clause 5). These are *separate institutional actions*, raising
forgery from writing one file to overriding the board review gate, the
officer's board identity and the appointment record. The verifier therefore
reports an **attested** disposition with this limitation stated; it never calls
arbitrary Git content "signed" and never fabricates a Judiciary or Governor
sign-off. No gate may proceed until genuine, independently witnessed evidence
exists.

Example artifact content (this is a *format* example, not a real sign-off):

```
gate: statistics-initial-20261120
reviewer: c1e00008
reviewer_role: judiciary
decision: proceed
evidence_digest: sha256:<...>
reviewed_at: 2026-11-21T12:00:00Z
```

## 4. Serial chain and fail-closed rules

* Expected predecessor: statistics has none for `initial`; foresight←statistics,
  strategy←foresight, spying←strategy; a `renewal` points to its own prior phase.
* The predecessor must itself verify to `proceed`, and the successor's
  `not_before` must be **≥** the predecessor's independently verified signed
  gate date (`effective_at`). This is a dependency on recorded evidence, not on
  another office remaining alive (amendment K).
* A review artifact token (commit, path, reviewer, decision) may not be reused
  across gates.
* No proceed while any precondition is false, any evidence digest mismatches,
  the act/bill/office/host is wrong, or the record is malformed. Every such
  condition returns `hold`/`invalid` with a non-zero `verify` exit.

## 5. Trial length, expiry, day-30 review, rollback

* Initial trial ≤ **14 days**; any window ≤ **45 days** absolute.
* A 30-day wait is **not** required to launch the Statistics trial — evidence
  may be collected prospectively (Founder mandate; amendment K).
* `renewal` requires (a) a filed, Git-anchored Judiciary `day30_review` with a
  `signed_epoch` no later than `root_not_before + 30 days` — missing or late
  means **automatic hold** — and (b) a later lawful reauthorizing Act present
  in LAWS.md.
* A launch is allowed only when `not_before ≤ now < expires_at`. At or after
  `expires_at`, new launches are refused; only recorded in-flight work may wind
  down (never silently reauthorised — amendment B).

## 6. Commands

```
python3 government/knowledge-phase-verifier.py --town <town> verify <record>   # exit 0 only on proceed
python3 government/knowledge-phase-verifier.py --town <town> check <record>    # always prints decision, exit 0
python3 government/knowledge-phase-verifier.py --town <town> audit             # dispatch ledger + expiry + rollback
python3 government/knowledge-phase-verifier.py --town <town> rollback --gate-id ... --reason ...
python3 government/knowledge-phase-verifier.py --town <town> evidence-digest <evidence-array.json>
```

`government/knowledge-phase-gate.sh` is a POSIX wrapper; it carries no authority.
`audit` reads `records/knowledge/phases/dispatch-ledger.jsonl` (JSONL lines with
`gate_id`, `kind`=`launch`|`in_flight_continue`, `at`, `invocation_id`) and
reports `new_invocation_after_expiry`, `in_flight_continuations`, `rollbacks`
and any `violations`. Its report is the durable proof that no new invocation
occurred after expiry.

## 7. Scope and law preservation

This mechanism implements Act 32 only. It does not amend Parliamentary law,
does not enable any office, does not forge any signature, and does not enact a
Post/Gazette cutover. Any future migration/cutover needs a separate Cutover Act
(amendment N) with separately reviewed code and independently evidenced
read/reply, plus a confidential route for material blockers. All offices remain
disabled by default until legitimate authority and evidence are filed.
