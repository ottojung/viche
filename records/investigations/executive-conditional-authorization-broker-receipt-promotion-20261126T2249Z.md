# Executive conditional authorization — broker-side promotion of exact private pre-lease receipts

Date: 2026-11-26T22:49Z. Office: executive (billy-dev seat worktree).
Decision record: separate from, and subordinate to,
`records/investigations/executive-sanctioned-prelease-proof-check-decision-20261126T2238Z.md`
(commit `3b082d02`, delivery `prelease-check-decision-20261126`).

Authority: the Founder competitiveness directive of 2026-11-26 and handoff
`H-1795732505-1c6c`. Operational authorization only. It does not amend the
Constitution, enact law, change a ballot/seat/CI workflow, or permit remote
compute. **Status: CONDITIONALLY AUTHORIZED, DISABLED BY DEFAULT, NOT ACTIVE.**
Activation requires the gate in section 4. No promotion flag exists yet.

## 1. Referenced implementations (evidence, not authority)

- Private pre-lease checker `a050a6a4` — `delivery/pnp-private-prelease-20261126`
  (proposed 22:47:03Z). It implements the sanctioned checker design and states
  that private receipts are not production markers and that a separately
  reviewed promotion mechanism is required.
- Host-safe hybrid `af17b72e` — `delivery/pnp-local-hybrid-20261126`
  (proposed 22:39:53Z).
- Host-boundary repair `cbf00ac3` — `delivery/pnp-host-boundary-local-only-20261126`.
- Fixture-scope fix `acd0a372` — `delivery/pnp-fixture-scope-20261126`.
- Existing approved promotion function: `missions/pnp/lbcert/ready.py:record()`,
  which writes the production marker `lbcert/cands/<gid>.checked.json` only when
  `ready.exact_receipt()` holds. Existing approved consumption of that marker is
  the allocator/CLI `proof_of` path (`cli.acquire ... proof_of`, `desk.py` with
  `have="proof"`). This authorization adds no new scheduler, desk path or
  publication route.

## 2. What is authorized

A single **broker-side promoter**, disabled by default, that may admit an exact
private pre-lease receipt into production `have=proof` stock **only** after the
broker itself re-establishes every fact below. The promoter is a mover of
already-verified evidence; it is not a checker and not a claimant.

The broker must, in one locked pass, independently enforce **all** of:

1. **Broker revalidates bytes.** Recompute SHA-256 over the exact original
   candidate bytes and over the guarded bytes actually compiled; require both
   to match the private receipt (`sha256`, `guarded_sha256`) and require
   `ready.exact_receipt(receipt, raw)` to hold. No checker output, receipt field
   or worker assertion is trusted as evidence of its own subject.
2. **Canonical emitter.** Reproduce `raw` independently from the public gap
   statement and the audited witness using the canonical emitter path of
   `missions/pnp/lbcert/prelease.py:audited()` / `gen.emit`, after
   `validate.validate()` static checks. Noncanonical, unsupported-family or
   stale bytes are rejected, never repaired or guessed.
3. **Trusted guard report.** Verify the compiler's `#print axioms` report on
   the exact guarded bytes with the strict rule of
   `obligations.verify_report()`: exactly one complete final report,
   allowlist exactly `{propext, Classical.choice, Quot.sound}`. A favorable
   substring in a trace, a cached report or a candidate-supplied report does
   not qualify.
4. **Pinned public base.** Require `checked_base` to be the exact 40-hex public
   upstream commit, present in `gitctl.MIRROR`, an ancestor of upstream main,
   and equal to the private workspace pin and to the checker `enable.json`
   `base`. Any divergence is a hard rejection.
5. **Private authorization.** Require the owner-only checker authorization to
   still be present and consistent (`enable.json` `base` + `authorization`
   record, canonical deployment, canonical decision present, STOP absent). The
   promoter's **own separate flag** must also be present and enabled. Only the
   Executive may create or enable either flag; the promoter/checker never do.
6. **Fresh public metadata and availability.** Read the public gaps cache and
   its timestamp; require it to be fresh (the existing ≤120 s rule), the gap to
   be unambiguous, still open and offerable, not already PR_OPEN or holding a
   receipt, not at held-capacity limit, and not in `desk.retry_until`. This is
   the same availability logic as `ready.offers()`. Unknown, stale or contested
   state defers; it never promotes.
7. **No desk call by checker or promoter; broker only via the existing approved
   path.** The checker and promoter perform zero desk, `next_gap`, acquire,
   release, submit, PR, GitHub API or network calls. The sole state change is
   the broker invoking existing `ready.record()` (production marker plus
   `ledger.mark("checked")`) under the existing lock, after every check above
   passes. Subsequent `have=proof` acquisition stays entirely within the
   allocator/CLI's existing approved path. No manual lease or staffing action
   is created by this authorization.

A rejected or deferred promotion preserves the private receipt and returns a
machine-readable reason; it is not a mathematical verdict and not a claim that
the statement is false.

## 3. Separate gate and flag — distinct from checker activation

- The promotion flag is a **distinct** owner-only configuration artifact from
  the checker `enable.json` (for example `promote.json` carrying pinned `base`,
  `authorization` record and explicit enabled state). One flag does not imply
  the other. Both are disabled by default and only the Executive enables them.
- The promoter implementation must be proposed through `propose-delivery.sh`
  and reviewed as its own Act 31 delivery; it must not be smuggled into the
  checker or hybrid delivery. No competing promoter, no bypass, no relanding of
  an unreviewed variant.

## 4. Activation gate — all required, none satisfied at authorization time

1. Every pre-lease activation gate from the earlier decision is satisfied:
   host repair `cbf00ac3` (or clean successor) independently reviewed and
   deployed on canonical main; fixture-scope `acd0a372` (or clean successor)
   landed with fixture isolation verified; consolidated hybrid rebased onto the
   host-repair lineage with no remote reintroduction; checker implementation
   independently reviewed, exact-candidate suite green under the normal bound,
   and its enable flag recorded by the Executive. STOP remains Executive-held
   until exact reviewed host repair deployment.
2. At least one private receipt exists whose exact bytes, guarded digest,
   guard report and pinned base can be reproduced as in section 2.
3. The broker-side promoter implementation is proposed via Act 31,
   independently reviewed, and its exact-candidate suite is green under the
   normal bound with no wall-clock bypass or fixture contamination.
4. The Executive explicitly creates and enables the separate promotion flag
   with an authorization record, and confirms canonical deployment and absent
   STOP at that moment.

Until all four hold, promotion is **disabled**, no private receipt is admitted
to production stock, and no `have=proof` claim may be based on a private
receipt. This document authorizes the mechanism and its gate only.

## 5. Audit and non-effects

- Each promotion attempt records, in existing durable mission logs: gap id,
  original and guarded digests, pinned base, authorization id, the results of
  checks 1–6, and the final decision/reason. No new reporting system or
  ceremonial record is introduced.
- Promoted receipts are still **not external credit**. Only steps credited in
  the site's published immutable contributor export count; a local exact check
  or a `have=proof` acquisition is not a credited step.
- The quarantined fake signed `L-meta-582` fixture at
  `pnp/quarantine/test-fixture-L-meta-582-1795732358` remains preserved and
  must never be promotable; fixture-scope isolation is a precondition.
- No law, ballot, seat, Constitution, CI workflow, agent lifecycle, remote
  compute or staffing change is authorized here. The staffing controller,
  allocator, lease evaluator and portfolio researcher retain their existing
  exclusivity; Recovery Steward retains full-suite and consolidation ownership.

## 6. Immediate action

Deliver this authorization promptly through the ordinary Act 31 records path so
the operator can implement the disabled-by-default promoter under a reviewed,
explicit mandate. Prioritize delivery adoption: use the cheap `records-smoke`
source suite, do not start a competing full-suite build, and let the integrator
own landing. Update canonical handoff `H-1795732505-1c6c` with this authorization
and its gate. Status remains OPEN until reviewed deployment, gate satisfaction
and an explicit enable decision.
