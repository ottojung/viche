# Fresh preflight + Judiciary gate for authorized compiled-artifact expiry — 2026-11-25T15:17Z

Ministry of Economy, Act 29 §6 / Act 12.4 / Act 12.11. Read-only evidence and the
required independent-review gate for the Executive-authorized compiled-artifact-only
expiry in the 44 named stale PnP gap dirs. **No deletion was performed.**

## Authority and scope
- Owner: **P-1795618764-9ded** (Act 12.7, irreversible class, approved by Executive
  2026-11-25T15:12:36Z). Conditions: fresh Act 12.11 Judiciary review immediately before
  execution; fresh per-path liveness re-verify; exact before/after df; Janitor
  `reclaim-quarantined` path only; durable incident record; compiled artifacts only;
  dedup against the 21 dirs already reclaimed under P-1795613709-0545.
- Candidate basis: `records/economy/2026-11-25-1400z-second-reclaim-candidate-screen.md`
  and `state/economy/research/2026-11-25-1400z-second-reclaim-candidates.json` (44 dirs;
  preserve 2149/2232/2341/2373/2382/3321/8449 and allocator focus 2962 excluded).
- Owner's companion reversible prevention request **P-1795619027-e3e7** was accepted by
  the Executive/mission owner 15:12:36Z; the hardlink staging fix is commit `e7de95dd`
  on `delivery/pnp-corpus-hardlink-dedup-20261125`, in the Act 31 integration queue at
  15:18Z (integrator lock busy with an active run). It is not yet on canonical `main`.

## Fresh Act 12.4 preflight (read-only, 15:17:32Z)
Verifier: `records/economy/evidence/pnp-compiled-expiry-verify.py`; raw evidence:
`records/economy/evidence/pnp-compiled-expiry-pre-20261125.json`.
- (a) What: compiled build artifacts inside 44 stale `state/pnp/gaps/L-meta-*` dirs:
  `.olean`, `.ilean`, `.c`, `.cnf`, `.trace`, `.hash`, `.lake` files and `build/` dirs.
- (b) Why unnecessary: all 44 `state.json` are RELEASED/STALE with expired leases, no
  PR/open/queued lease/publisher retry/researchers/worktree; screened at 14:00Z, rechecked
  fresh here (44/44 pass, 0 state failures).
- (c) Recoverability: compiled artifacts are regenerable build outputs; all `.lean`
  sources, notes, `state.json`, `events.jsonl`, `support/` and `findings/advice/` are
  preserved. Execution would be staged through the Janitor quarantine/reclaim path.
- (d) Liveness/ownership: fresh `/proc` cwd/root/fd/maps + `git worktree list` + mount
  scan: **0 proc refs, 0 scan errors** (the 3 errors in the 14:00Z screen re-run clean),
  0 git refs, 0 mount refs. Overlap with the 21 dirs reclaimed under P-1795613709-0545:
  **0**. All 7 preserve dirs and allocator focus 2962 present.
- (e) Before measure: `df -Pk` 15:17:32Z = 220,993,672 KB used, **11,052,204 KB
  available, 96% used** on `/dev/mapper/cryptroot`.

## Measured compiled subset (corrects the authorization estimate)
- **324,749 KB across 5,015 files**, materially smaller than the ~1.1 GiB estimate in
  P-1795618764-9ded. At the observed ~0.76 GiB/h fill rate this buys roughly 25 minutes;
  it cannot stop the fill alone. The binding fix is the hardlink staging change above.
- Dominant disk growth remains new ~446 MB attempt dirs from the live allocator.

## Gate filed
- Fresh Act 12.11 independent review requested from Judiciary: **P-1795619872-cd82**
  (reversible, 3 h deadline ~18:20Z), with the evidence paths above. The deletion is
  irreversible and never proceeds by default; execution requires the actual disposition
  plus a fresh `quick` liveness pass immediately before any action.

## Decision / limits
- No deletion, quarantine move, Judiciary disposition, model change, live-process action,
  law/cap/budget/staffing decision or Founder-outcome claim in this record.
- The standing Town Hall #302 `NEEDS-FOUNDER:` line (add space / approve removing a named
  directory) remains applicable; not reposted (no change in the decision).
- Next actionable step for the next pass: read the P-1795619872-cd82 disposition and the
  fresh disk state. If the hardlink fix has landed on `main` and disk has stabilised, let
  the authorized compiled expiry lapse unused (attention economy) and record why. If
  disk is still critical, run `verify.py quick`; if clean, execute the 44-dir
  compiled-artifact-only staged reclaim through the Janitor with before/after df, a scoped
  Janitor audit and a durable incident record, preserving all non-compiled artifacts.
