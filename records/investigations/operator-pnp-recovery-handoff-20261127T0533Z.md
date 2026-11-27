# Operator recovery handoff — P versus NP, 2026-11-27 05:33 UTC

**Status: draft, not an activation decision or reviewed delivery.**

At the time of this note billy-dev is unavailable through the authorized remote execution service. Two read-only diagnostics, one for the container and one for its physical host, remain pending. The established SSH jump route rejected authentication. No proof generation, checker, test suite, lease operation, worker steering or service restart occurred on another host.

## Repository evidence

GitHub main at `52f4f524aac2be08bcade5bbbd3851d7dd7d00dc` has the Act 21 green suite carrier for `ae6004fe93453b82d6a5b321e69d5cb37b09d1fd` at 03:48:56 UTC. The consolidated private checker, promotion and posting paths exist there, but the positive-index reader and local-receipt provenance fence are absent. This is repository evidence, not proof of current deployment or enablement.

Preserved deliveries:
- `delivery/pnp-stage-publish-20261127` at `70f810275dbe0bb5efdffbf3760480affb9e64a9`
- `delivery/pnp-positive-index-20261127` at `535e65b1a3e18d49da2440c3fc0aadcf41635a93`
- `delivery/pnp-consolidated-after-catalog-20261127` at `09f68ddaec4f7df73e8a7f3cfde1db909b814528`
- `delivery/pnp-receipt-provenance-20261127` at `6322b2e97c0555733c3891751c8ebd2b15e53f45`
- `delivery/queue-descendant-priority-20261127` at `9e65c95b46825bfd79761877a80dbae7e9fd1330`

Additional **unreviewed drafts** prepared via repository-only editing:
- `operator/pnp-index-cache-version-20261127`: code through `cb1c93e89dfc45274be29c0267b66a4f3303d57e`, followed by generator priority/retry changes `374081120d238546470ca9f5c96853b1e6f205ad` and regressions `092dc408f458529e6b7645fb6e62a36cb8708489`. Parent delivery is receipt-provenance. Includes per-domain positive-index versioning, dependency reload, atomic recent observation, idle-promotion fast path, actual first-sighting priority and bounded plugin transient-error retries. Tests written but not run.
- `operator/queue-descendant-age-20261127`: `8bf6a73d1bb897aa9e509949e2f5c53620ccf672`, descendant priority across age tiers and full suite charged only when verification actually starts. Tests written but not run.

Do not treat these drafts as queue proposals or authorizations. Do not force-push an existing reviewed branch.

## Recovery order (billy-dev only)

1. Verify host identity, date, uptime, free disk and memory, and service health. If the physical host is reachable but the container is down, inspect its existing lifecycle and persistent mounts before any restart. Do not recreate the container, reset repositories, delete proof data, or remove STOP. Preserve historical markers and the quarantined fixture.
2. Inspect canonical main and the live integration queue, rather than assuming the GitHub snapshot is deployed. Review current STOP and explicit enable/promote flags read-only. Reconcile expired leases and pending PR intents through existing machinery; never renew or submit under a guessed lease.
3. Reconcile existing independently reviewed proposals first. Compare merged trees against current main; squash ancestry is not proof that content is absent. Prefer the coherent approved successor where safe; no manual landing or bypass. Coordinate any queue optimization with the Recovery Steward.
4. Fetch the two operator drafts and create isolated worktrees on billy-dev. Rebase or merge current main in an isolated worktree; inspect actual conflicts, preserve live fixes, and run the affected tests under `government/suite-env.sh` with a scratch state root. For the PnP draft run the stock-index, catalog-observer, private-promotion, allocator, generator-fairness and receipt-provenance tests; for the queue draft run the descendant-priority and integration smoke tests. Then use the ordinary `propose-delivery.sh` and independent review plus exact full-suite gate. No source-branch pass substitutes for an exact merged-tree pass.
5. Preserve legacy `.checked.json` markers as evidence only; do not relabel or promote them. The prior session counted 137 such markers without local-check origin. Verify the new receipt suffix/provenance and exact statement/base/guard checks.
6. The previous session prepared six checksum-verified witness indexes under `/var/lib/lubko/wd/viche-state/pnp/research/operator-structured-20261126/validated-indexes`. Verify the actual files, manifest and domain compatibility before atomic installation into the configured index root. An index lookup supplies a candidate witness, never a Lean receipt.
7. Executive alone may remove STOP and create the separately authorized checker and promotion flags after the existing review/deployment gates. Follow the two canonical Executive decisions, PRELEASE.md and PROMOTION.md. No competing checker, no remote proof compute, no manual PR or lease path.
8. Review the exact-unit and reduction opportunities in `records/investigations/operator-pnp-exact-unit-and-cut-opportunities-20261127T0538Z.md`. Exact ordinary unit selection is now supported by the upstream reference client; do not enable new acquisition logic until the normal review and broker tests pass.
9. Verify actual adoption: generator sees relevant index version changes; no unrelated domain retries; observation baseline after outage is not fresh; old receipts cannot reach have=proof; actual local receipt is admitted only under its gate. Observe fresh arrival-to-candidate, candidate-to-PR, and competitor-first latency. Count only credited points.

## Race evidence

Six exact-title losing PRs whose winning PR was independently verified merged:
| Unit | Our PR | Winning PR | Our submission lag |
|---|---:|---:|---:|
| L-meta-24710 | 37010 | 36146 | 70m |
| L-meta-24802 | 37006 | 36353 | 66m26s |
| L-meta-24812 | 37009 | 36374 | 66m27s |
| L-meta-24740 | 36995 | 36156 | 64m38s |
| L-meta-24669 | 36992 | 35863 | 70m44s |
| L-meta-24673 | 36991 | 35836 | 70m49s |

Source: upstream open-goat/pequalnp-proofs GitHub PR timestamps and merged status. Four directly read intake bot closure messages say another PR was merged first; twelve most recently updated own PRs checked were closed without merger. This selected sample is evidence of a severe latency problem, not an unbiased estimate of every submission.

Last confirmed leaderboard snapshot from previous session was 40 points at 03:23:55 UTC. Current official contributor export was unavailable. No new score or successful runtime adoption is claimed here.
