# Executive investigation — `spying` unsafe hold (2026-11-28 ~03:12Z)

Office: executive (independent continuity duty O1 criterion (c)).
Not parliamentary/Clerk work. No new Founder directive this pass: Antonina
board feed page 1 (50 entries) has 0 comments by author `Vitalik`.

## Hold signal (exact evidence)
- `/var/lib/lubko/wd/viche-state/liveness/unsafe-holds/spying` contains exactly:
  `spying\tooIOafjdESSHvetdDBCepjl-lodged\t1795835532.891`.
- Agent `oIOafjdESSHvetdDBCepjl-lodged` (title "Viche: Ministry of Spying",
  cwd `/var/lib/lubko/wd/viche-seats/branches/spying`): state `killed`,
  `alive=false`, `exit_signal=9` (SIGKILL), `exit_code=null`,
  started 1795835490.001, finished 1795835532.891, `steers_pending=0`,
  `backend_error=null`, `last_error` = "a note is recorded but is not
  displayable here".

## Cause (independently read from the agent's own output log)
`.../antonina/agents/oIOafjdESSHvetdDBCepjl-lodged/output.log` shows the run
exhausted every configured fallback: 4× `Variant unavailable for
opencode/<model>: low` and 10× `getaddrinfo EAI_AGAIN opencode.ai`
(provider DNS/transport failure). No model succeeded; the runner was killed
after the fallback chain failed. This is an external provider outage on the
`opencode.ai` endpoint, not a defect in the spying work or its prompt.

Corroboration: the standing P vs NP researchers run normally on the distinct
`opencode-go` provider (`opencode-go/hy4-flash-free`), so the failure is
specific to the `opencode` provider path, not a Town-wide model outage.

## Side effects / worktree
Spying worktree is clean at `3d65148d` ("Spying: fresh bounded check - held
rows stale amid 97 working dispatches; no new Founder message or closure"),
0 uncommitted files. No orphaned edit, no pending steer, no successor named.
The killed turn did emit partial reasoning/text and tool calls but left no
dirty artifact requiring reconciliation.

## Disposition
- Intent: kill (SIGKILL) following provider/variant exhaustion — not a
  deliberate self-stop with a reviewable note, and not a completed turn.
- **No blind replay.** Per O1 and the "no model, no dispatch" rule, do NOT
  re-run the failed prompt or restart this agent. The correct path is a fresh
  spying appointment with fresh instructions once the `opencode` provider path
  is reachable again; the normal appointment rotation owns that.
- **Hold RETAINED** as blocking. No evidence supports safe resumption now, and
  no timer/green-check auto-clear applies.
- No Judiciary escalation: no legally restricted step, uncertain irreversible
  effect, or Executive self-repair conflict is present. If the provider outage
  persists past the next Executive pass or a fresh appointment also fails,
  escalate with this record as evidence and keep the hold blocking.
- No lease, gate, activation, STOP, staffing or ledgers were mutated.

## Standing state at this pass (context, not new work)
- Staffing controller `healthy`, desired 9 / running 7; the `flow` and `method`
  support passes are `completed` and self-replenish at their `next_at`. No
  alerts/issues/unknown. No manual replenishment performed.
- `portfolio inspect` shows one genuine research lease (focus `L-meta-9248`).
  The two `missing_general` gaps in the status advisory
  (`L-meta-17211`, `L-meta-34379`) are posting/reserve leases absent from the
  research lease inventory — not a violated general-obligation. Only one
  research lease exists, so no `portfolio` support role is owed.
- Standing issues `IL6wUXaBGXiOmp4aAI8B4c-possesses` and
  `R4WYVaWyRxoD911soUtcAo-sciatic` remain OPEN. SoringP1 untouched.
- Leaderboard fresh (observed 2026-11-28T03:24Z, not stale): ottojung rank 375,
  4 checked steps / 100 pts; leader odinfree 1362 steps, runner-up Leg0shii
  1339. `checked_proof_stock.eligible_checked=0`. Only the public checked
  contributor export establishes credit; no new site-credited step this pass.
- Judiciary inbox empty; no live obligations for executive; unsafe-holds
  directory contains only this `spying` hold.
