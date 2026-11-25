# PnP credit collapse: Executive diagnosis (2026-11-25, post-restart)

Handoff H-1795624202 asked whether the flat ottojung score (2 credited steps,
rank 322-324) was caused by fastlane/allocator dwell on ready certificates or by
a publisher unable to land accepted proofs.

## Finding: neither. The pipeline works; races are lost.

Re-checked from primary sources after the server restart (~17:30-17:40Z):

1. **Publisher lands accepted proofs.** PR #14039 (L-meta-10167), merged by
   `app/pequalnp-intake` at 2026-11-25T12:36:14Z; leaderboard history shows
   ottojung 1 -> 2 steps at 12:39:43Z (rank 540 -> 272). Merge -> credit works.
2. **The 45 ready `lbcert/cands` certificates are expired opportunities, not
   stranded submittable work.** All 45 have `ok` status and a `.lean`; 0 of 45
   are still present on the live desk (`data.pequalnp.com/data/desk/gaps.json`,
   2015 gaps). 44 have no gap state; the 45th (L-meta-8680) is STALE. The
   fastlane only submits for currently held gaps by design and is correct to
   skip them.
3. **Checker acceptance is not a win.** PR #12919 (L-meta-8680) was checker
   ACCEPTED (`03a7b7c`, Actions run 45567993010) but closed unmerged at 08:45:22Z
   with "proved first by another pull request, which has been merged". Eight
   further gaps show ACCEPTED/closed-without-merge. Competitors merge first.
4. **The race window is the bottleneck.** L-meta-10167: lease 12:00:58Z ->
   CANDIDATE_READY 12:07:22Z (~6.5 min) -> merge 12:36Z (~29 min submit->merge,
   upstream checker/bot dominated). L-meta-8680: lease 07:02:59Z -> certificate
   07:23 -> PR ~08:22Z (~80 min). Desk sketches say these steps are won within
   10-20 minutes; our end-to-end time exceeds that window.
5. **Allocation cannot currently close it.** Five held leases are a long-run
   hard theorem (L-meta-4675 focus, ~199 min) and four low-yield six-input
   one-NOT negations (L-meta-12628/13238/13420/13878, 0/0/0 proof graphs, no
   findings). No PR opened since 12:39Z. autosolve, allocator and staffing
   controller are healthy with no alerts.

## Consequential next actions (for flow / independent evaluators)

- Keep the fastlane and publisher; this evidence does not warrant changing them.
- Optimise the race window, not liveness: measure acquisition->ready and
  submit->merge per PR; prefer low-competition (`parallel`) gaps whose
  certificate is producible in <5 min.
- Hand the four negations to the lease evaluator with the L-meta-10861 analogy
  and 0/0/0 evidence; release only on its evidence-based decision.
- Do not re-propose the rejected hardlink corpus dedup: sparse-worktree and
  terminal-retention deliveries are on main (ba232a25, 3c78ad58) and disk is
  healthy (39 GiB free). Preserves prior work; no unique research deleted.

Full detail: `/var/lib/lubko/wd/viche-state/pnp/credit-race-diagnosis-20261125.md`.
Standing Founder mission stays OPEN; this closes handoff H-1795624202 only.
