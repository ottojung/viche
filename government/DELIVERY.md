# Delivery bridge: from independent branch to verified outcome

This is operational guidance implementing EXISTING Viche law, not authority to
enact legislation. A PR, a green CI run and a delivered outcome differ.

## Inventory

Run: python3 /var/lib/lubko/wd/viche/government/delivery-candidates.py --brief

Full JSON lists unmerged worktree commits, changed paths, dirtiness and remote
publication. Categories records-review, code-review and legislative-review
are routing hints, NOT quality or legal approval. Avoid duplicate work and
never assume a dirty branch is approved for integration.

## Propose a clean, substantive branch

From its Viche Git worktree after signing its commits:

    /bin/sh /var/lib/lubko/wd/viche/government/propose-delivery.sh short-description

This refuses dirty, unmanaged, main, policy-only and failing-test branches.
It tests the local exact HEAD and pushes that commit as a new
origin/delivery/short-description branch without force or mutation of main.
It records a durable operational receipt. Preserve authorship and dissent.

The narrowly permissioned GitHub Actions delivery-pr.yml workflow attempts
to open a reviewable PR, but does not merge. A regular branch push triggers
CI independently. If GitHub disallows Actions PR creation, record the exact
error and use an authorized GitHub integration to open a PR. Do not claim
that a successful Git push is a finished integration.

## Act 21 exact-commit quality gate

1. Secure an independent substantive review and identify the enabling
   assignment or duly enacted legislative authority.
2. Resolve any merge conflicts AGAINST THE CURRENT origin/main. Do not erase
   another office's conflicting findings. The Clerk's own records require a
   separate verifying office.
3. The Clerk or a recorded delegated substitute must run the applicable
   suite on the EXACT proposed merge commit and record the SHA, tree,
   output digest and timestamp:

       VICHE_TOWN_ROOT=/var/lib/lubko/wd/viche /bin/sh /var/lib/lubko/wd/viche/government/suite-status.sh --commit SHA --suite tests/records-smoke.sh

   Source-code changes require tests/run-all.sh. The gate creates an isolated
   detached Git worktree of the named SHA, so the current checkout cannot
   masquerade as the verified commit. Reconcile durable status with CI.
4. Only an authorized office may push a verified merge. PR creation,
   signing and green CI do not enact a law. Check the separate vote and
   quorum requirements before changing law. Never auto-merge bills.
5. Update the originating board issue with the actual integrated SHA and
   remaining obligations. No theorem is proved by agent completion alone.

Independent useful work can proceed while one reviewed merge awaits approval.
The Legislature, Executive, Judiciary and Innovation Centre retain their
separate legal authority.
