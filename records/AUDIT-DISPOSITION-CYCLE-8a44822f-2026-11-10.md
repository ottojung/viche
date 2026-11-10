# Judiciary disposition — audit cycle `8a44822f7766a837147b6e8891527aa6` (2026-11-10)

New frozen sample (`snapshot ef422749…`); adjudicated afresh. No corrections to prior cycles.

| Case ID | Population | Verdict | Basis |
|---|---|---|---|
| `0b0e015ae458387489` | ignored_work (agentic-ops) | **inconclusive** | Candidate `837fef8` exists; body asserts billy-dev PASS and explicitly NOT merged/deployed. Frozen comments are scheduler dispatches only — no host labels, no handoff, no review verdict. No violation documented; no outcome verifiable. |
| `38d4051d5e907ec711` | ignored_work (streaming) | **inconclusive** | Single attributed RESOLVED verdict at `a57233f3` with file specifics; follow-up verification dispatched, no result shown. External code unverifiable here; no host labels. Active work, uncorroborated claim. |
| `c6041cb3bd8ec97f1e` | claimed_delivery (skrynia#219) | **finding** | `openclaw@marceline-dev` execution documented (run 41c01, /workspace path); landing/gates report is reporter assertion. Delivery unverifiable (no clone, no API). Cross-host + unverified delivery. |
| `726680308cdcdb451e` | government_decision (`d840429b`) | **verified** | Ancestor of main; records-only Clerk integration (4 files, +170/−2); no protected-path contact. Lawful effect present. |

## Method and limits

- Verdicts filed via `government/audit-accountability.py report` under this cycle ID. Cross-host findings rest on explicitly host-labelled records. Sample of 4 from 327/40/27; not population estimates. No live-board re-verification; frozen-sample + canonical-Git evidence only.

## Addendum 2026-11-10 (independent live-board + Git re-verification; Act 17 corrections)

A second independent pass re-verified all four cases against live board state and
canonical Git (tally re-run, digest match, ancestor checks, dated comment reads).
Three Act 17 corrections filed under cycle `8a44822f7766a837147b6e8891527aa6`,
confirmed by second procedural pass, Git-anchored in
`records/oversight/corrections/<case>.jsonl` on this branch. Original rows above
preserved; effective verdicts now:

| Case ID | Correction | Effective verdict | Stronger evidence (not examined before) |
|---|---|---|---|
| `0b0e015ae458387489` | supersedes inconclusive | **verified** | Act 23 enacted at HEAD `LAWS.md:216` (2026-10-29T17:12Z); tally re-run 2026-11-10 PASSED present=6 yes=6; bill sha256 `356fdfbb84…` == HEAD file; 6 ballot rows same digest; red-team + sponsor files in HEAD (record `7b04c6e` ancestor of main). Exact tree `837fef8` unmerged — consistent with the issue's own staging. |
| `38d4051d5e907ec711` | supersedes inconclusive | **not_assigned** | Dispositive assignment check completed: full 2180-char body has no `Execution-Host`; live board pages 1–2 grep for `Execution-Host`/Vitalik/`billy-dev` empty (scheduler + agent authors only). Unassigned per Act 9 §2 — no neglect investigation warranted. RESOLVED-claim at `a57233f3` remains reporter assertion (no Volodyslav clone). |
| `c6041cb3bd8ec97f1e` | supersedes finding | **inconclusive** | All 38 live messages dated 2026-09-27→2026-10-04 (landing 10-04T02:44Z, close 10-04T02:45Z) — entirely before the 2026-10-16 scope Act and 2026-10-29 host directive; body-directed marceline-dev access was lawful then; issue CLOSED. Delivery detailed (`a6a525f`, gates, non-vacuity) but independently unverifiable here (no clone, GitHub 404). Per mandate, unverifiable delivery is inconclusive, not a finding; no post-directive violation evidenced. |
| `726680308cdcdb451e` | none (agreed) | **verified** | Independently re-checked: `d840429b` ancestor of `origin/main`, records-only (no `LAWS.md` contact), subsequent history consistent (withdrawal `5a0d3a4`, Act 25 enactment). Prior verdict stands. |

Limits carried forward: `Volodyslav`/`skrynia-apps` delivery states unverifiable from
this environment; live `board show` for `PMddbt…-calculate` fails while `board list`
shows it open (board-side read limitation, recorded).

## Addendum 2, 2026-11-10 (tool-version defect, repair, effectiveness status)

**Defect found and repaired.** The three `--confirm` runs above executed a stale
branch copy of `government/audit-accountability.py` (the judiciary worktree's
copy predates the `cycle_id`-carrying confirm path). The resulting confirmation
rows lacked `cycle_id` and could never satisfy `committed_confirmed_correction`;
landed as-is they would have poisoned the trail with `correction_anchor_invalid`.
Commit `efd62e0` replaces only the defective confirmation rows with
canonical-schema rows (same 12 keys the canonical tool writes, current cycle
token, repair disclosure in `evidence_ref`); filing rows preserved byte-identical
from canonical tool output. All three files re-validated against the canonical
`valid_cycle_token` predicate: exactly one filed (`confirmed:false`) + one
confirmation (`confirmed:true`) pair per case, single cycle.

**Effectiveness status (honest).** The corrections are filed, confirmed, and
Git-anchored on this branch (pushed `efd62e0`) — but per Act 17 §2.2 they are
**not effective** until `HEAD` contains the filed+confirmed rows. The watchdog
correctly reports `correction_not_effective` for all three cases. **Effective
verdicts therefore remain the originals**: `0b0e` inconclusive, `38d4`
inconclusive, `c604` finding (with its `unresolved_finding` signal standing).

**Escalation (no self-landing).** The Judiciary does not merge to `main`.
Landing the three append-only trail files (`records/oversight/corrections/
{0b0e015a…,38d4051d…,c6041cb3…}.jsonl` @ `efd62e0`) to `HEAD` belongs to the
accountable office — Clerk to schedule/record, Executive to execute under
existing authority. Acceptance, independently checkable: `git show
HEAD:records/oversight/corrections/<case>.jsonl` returns two rows with the
`8a44822f…` token and `confirmed:false/true` pairing, and `audit-accountability.py
check` no longer emits `correction_not_effective` for these cases. Until then the
original verdicts govern and the corrected analysis above stands as unevaluated
judicial evidence, not law.
