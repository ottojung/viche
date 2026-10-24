# Canonical checkout drift red-team increment — board #315

**Scope:** evidence check and a disposable-shell test of the draft boot-guard
mechanism. Research only; no enactment, canonical checkout access, or deployment.

## Claim check

The incident claim is supported by a contemporaneous durable record on `main`,
commit `a9405d95ff04363fbd11a47a7a3599ff318a9629`. It says the checkout was
found on three distinct `c1a00006` ballot branches on 2026-10-17, and that
Clerk commits were recovered by returning to `main` and cherry-picking. The
matching `records/TOWNHALL_CURSOR.md` entry at 12:36Z calls this the third
occurrence. Thus the recurrence/count is independently corroborated within the
repository's contemporaneous records; the underlying checkout states were not
independently observed during this review, so this does not establish raw Git
forensic proof beyond those records.

At current `origin/main` (`cddff6cf26edfeecb14989ca9ed9d007cc9a583c`),
`government/boot.sh` runs `git -C "$town" rev-parse --is-inside-work-tree`
but has no branch assertion, drift incident write, or restoration step. It
proceeds to worktree creation and then independent reconciliation hooks. The
draft's narrow premise that a branch assertion is absent therefore remains
true on this main snapshot.

## Guard mechanism test: assert-and-restore, without force reset

Tested the POSIX-shell branch-repair primitive in a temporary bare-remote plus
two disposable clones (not `/var/lib/lubko/wd/viche`). The simulated boot
sequence is: inspect current branch; if non-main, `git checkout main`; then
`git pull --ff-only`. In both cases, the assertion/checkout occurs before the
pull:

| Scenario | Before guard | After guard + ff-only reconciliation | Result |
| --- | --- | --- | --- |
| clean checkout drifted to `ballot/test` while remote `main` advanced one commit | clean ballot branch, old main ref | `main`, fast-forwarded to remote tip | pass; drift repaired and ordinary reconciliation continues |
| tracked dirty file on `ballot/test` | uncommitted edit present | `git checkout main` refused with “local changes … would be overwritten”; edit remained intact | pass for non-destructive safety; no silent cleanup |

This shows `git checkout main` provides a safe narrow restore for a clean
wrong-branch state while refusing to destroy conflicting dirty work. It does
**not** demonstrate that a dirty checkout will be back on `main` within a
cycle: a guard that merely catches/refuses must durably record and signal the
unrepaired state and arrange a later retry, or the draft's P2 guarantee is too
strong. Further, `git checkout main` itself can fail for untracked-file
conflicts or absent local `main`; those cases need explicit signal/incident
handling while allowing unrelated reconciliation to run.

## Red-team finding / next refinement

Draft §3 should distinguish (a) successful repair of a clean drift from (b)
blocked repair because the tree is dirty. Require an incident record and
`canonical_drift` signal before/irrespective of repair; on refusal preserve
the working tree and do not claim P2 success. Specify retry/measurement for
the unresolved state and how the guard avoids preventing independent seat,
Judiciary, and Executive reconciliation. The tested primitive supports the
non-destructive-checkout part only; this review did not implement or certify a
production guard.

## Reproduction details

Repository identity: `https://github.com/ottojung/viche.git`; clean isolated
clone; current `origin/main` above. POSIX `/bin/sh` script created a temporary
bare origin, cloned it into `town` and `drifter`, created/pushed
`ballot/test`, then ran the checkout-and-fast-forward sequence. For dirty
case, modified a tracked file in `drifter` before the attempted checkout.
Observed branch names and `git status --short` before/after; no force checkout,
reset, or canonical-path operation was used. Full command outputs are in the
invocation log; the assertion result is recorded here as a focused mechanism
test, not a full integration test of `government/boot.sh`.
