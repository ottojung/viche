# Executive P vs NP post-restart allocation — 2026-11-24T08:40Z

Owner: Viche Executive (`c1e00002`), billy-dev.
Authority: standing Founder P vs NP mandate; deployed canonical HEAD
`42020a82` (which includes the indefinite SoringP1 suspension).

## Verified starting state

- Canonical policy was refreshed into the Executive worktree; the seat's
  `AGENTS.md` now matches canonical policy.
- The current `L-meta-2138` assignment guard returned `decision: continue`.
- Live status found baseline vacancies on `L-meta-1710` and newly acquired
  `L-meta-2149`; focus `L-meta-2138` had only its general researcher.
- The former `opencode.exe` PID 10070 was absent after restart. Managed compiler
  headroom was 10,033,453,460 bytes, `legacy_compilers=[]`; the pending
  publisher build remained the only heavy build.
- Public leaderboard remained UNRANKED/0 for ottojung; leader willakone 75,
  runner-up c4ss 62. No accepted-step claim is made.

## Allocation performed

`python3 -m missions.pnp.staff --baseline` was run immediately from the canonical
checkout. It restarted the existing `L-meta-1710` general workspace and started
the new `L-meta-2149` general workspace, while adopting the other three current
general researchers:

| Lease | General researcher |
|---|---|
| L-meta-1710 | o73fQ5uIn5F5zCKv3HwiEn-refer |
| L-meta-2138 (focus) | Ag9FyganFpbC3oE0Nkb3uo-praying |
| L-meta-2149 | TgBcWqQiIOlYhjYJikj4L5-papaya |
| L-meta-2245 | C7ft4sXS7ZsObrAPrTTRAd-topic |
| L-meta-2373 | N4o03s4TQWiLuKeH6JLdOI-commonly |

Three distinct specialists were dispatched only on focus `L-meta-2138`:

- integrator `gFG8MnFqSJEXHYt4E3XfJh-enjoyment`: exact reduction integration;
- restriction `6jLOeLCDT4lWUEy9IyAMUG-sickle`: pinning/deletion consequences;
- certificate `tXtYXrN4Ods3YYvCVHY3KR-sarcastic`: bounded finite certificate.

Antonina delivered its backend-recovery prompt to two of the new specialists.
Their actual logs showed relevant proof work (reading `R_meta_1672_*` and the
peer findings), so they were not interrupted or duplicated.

Independent support/evaluator coverage was replenished in the existing scratch
workspaces:

- portfolio `GwE2Idzo4TR2yGFhw6Lybq-velocity`;
- lease-evaluation `LamCoB3CBFos73RdrwJM24-strategic`;
- knowledge `D67KVMawu7b50tbbJqlNuv-cottage`;
- methods `cXZHI45s2ZBvnBBCjk5iGA-delighted`;
- flow `x4MAHSmoxvSl3W2uV2mi12-bone`.

The two evaluators were instructed to begin with
`python3 -m missions.pnp.portfolio inspect`, base decisions primarily on each
lease's general-researcher findings and actual logs, and never release merely
because staffing is temporarily absent. Support prompts include the canonical
work-conserving policy path and deliver material findings through the existing
`missions.pnp.support advise` command.

## Handoff reconciliation

- The accidental raw `L-meta-949` acquisition incident is resolved: the live
  frontier reports `held=0` and no local lease/state record exists. No further
  Executive acquisition was attempted.
- Old `L-meta-1710` specialist handoffs are complete/superseded by the evaluator's
  evidence-based focus switch; their artifacts remain preserved.
- The evaluator appointment handoff is complete: release
  `5e453ab9755b383c5b204131` and switch
  `d3a3bb8867f404ae22a3a6ab` were applied, and both evaluators are running again.
- The pair-equivalence correction remains preserved; no current candidate relies
  on it.
- The memory-bottleneck handoff is complete: the obsolete process is gone and
  headroom recovered.
- The SoringP1 m=4 research handoff is superseded by the Founder's indefinite
  suspension. No SoringP1 frontier, issue, worker or review was touched.
- The earlier baseline and suspension handoffs are complete; the current
  allocation is recorded in `H-1795509599-c6c9`.

## Publication and acceptance evidence

- `sh tests/pnp-pipeline-smoke.sh` passed all offline publisher, real-local Git,
  watchdog, proof-tool, support and allocator tests.
- Upstream PR #4501 is OPEN, MERGEABLE, authored by `ottojung`, with exactly one
  added file `lean/PEqualNP/Outside/L_meta_2171.lean`.
- Its sole commit `171eae7bf578395bbf9a233705de21bca10016a7` has GitHub
  verification `verified=true`, reason `valid`; author and committer are Otto
  Jung <otto.jung@vauplace.com>.
- The implementation issue remains open: no real rejection-correction cycle or
  authoritative checked acceptance has occurred yet. The standing research
  issue remains open indefinitely.

## Next actionable state

Workers own the mathematics and experiments. The Executive replenishes or
retires only at meaningful evidence/lease changes: a completed candidate,
correction, valid focus decision, genuine release decision, terminal lease, or
new baseline vacancy. No polling loop or new reporting gate is authorized.
