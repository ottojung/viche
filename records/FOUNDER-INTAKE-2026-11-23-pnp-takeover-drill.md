# Founder intake — P vs NP takeover drill and leaderboard-clarification (2026-11-23T23:35Z)

Clerk c1a00001 (Antonina agent `GSOAg3B9DxwaAOGjQiunes-spite`). Authoritative source: board issue
`IL6wUXaBGXiOmp4aAI8B4c-possesses`, full body + all 9 messages read in full (page 1), plus the
current canonical `/var/lib/lubko/wd/viche/AGENTS.md` and `government/LAWS.md`.

## Messages triaged (exact-author `Vitalik`)

| event key (receipt) | message sha256 | board id | meaning |
|---|---|---|---|
| `3d09efdfa68408bd11a30a3522abf4839bbc4f5419390e23eb23b55bb0828aa1` | `sha256:LnZ7dTuU416z2YResxY8OUa45Ubp9HD5lJPnPhcxeR0` | `sha256:LnZ7dTuU…` on `IL6wUXaBGXiOmp4aAI8B4c-possesses` (23:32:33Z) | Executive-ownership handoff drill: the Founder stopped the three externally seeded auxiliary agents; Viche Executive is the ONLY authority to start/restart research agents; inspect the issue, verify roster and artifacts, restart multiple productive fronts, record real agent IDs, why fronts are useful, lease ownership, exact math output and checker outcomes. |
| `7467abf1c472a60f11d8e5e1fab3285a2408ced2c9212451983a656e4a95799d` | `sha256:l0F4DHdY6rMCHfsNPCqVQ6VHoHYxQGhKZXMZz-vbR_E` | `sha256:l0F4DHdY…` on same issue (23:33:15Z) | Clarification: do NOT edit/commit/push/rebase or otherwise touch Founder-owned worktree `/home/lubko/viche-pnp-leaderboard-20261123`; do not spend model time on that leaderboard setup. Sole next responsibility: actually dispatch and maintain the P vs NP research workforce under Antonina; restart multiple independently useful fronts, verify real math work and lease continuity, record concrete IDs and action outcomes. Keep the mission OPEN. |

These supersede/reinforce `sha256:HpOiWgNj…` (23:30Z): the definitive objective is the **public
all-time `@ottojung` checked-step rank #1 on https://pequalnp.com/contributors, then a growing
positive lead over #2** — measured from `https://data.pequalnp.com/head.json` → `files.contributors`,
NOT agent count, PR volume, local Lean builds or unverified claims.

## Scope check (Act 9, not a title-only assumption)

The issue body's first line is `Execution-Host: billy-dev`, with `Status: STANDING / CONTINUOUS;
remains OPEN indefinitely...` and an explicit Founder authorization comment. This is the
Antonina execution-target/dispatch surface — Act 9.1 is satisfied. The live canonical
`python3 government/eligible-work.py` at 23:35Z returns `complete=true count=18` and **includes**
`IL6wUXaBGXiOmp4aAI8B4c-possesses` (source `board_description_and_founder_comments`). The prior
detection gap (hyphenated `Execution-Host:` form) was independently closed by Executive delivery
`eligible-work-hyphen-execution-host-20261123` (landed as `089fbc45…` per the continuity handoff),
so automatic post-restart rediscovery is now arranged. Work is authorized; a title alone was not
relied on.

## Independently verified current state (read-only, 23:35Z)

- **Live Antonina roster** (`antonina agent list --running --page 1 --limit 100 --json`,
  `unreadable=[]`, 5 running):
  - `GSOAg3B9DxwaAOGjQiunes-spite` — Viche: Clerk (this seat).
  - `fAdAClZ9oKh0n7XshYKpSe-spinati` — Viche: Executive, cwd
    `/var/lib/lubko/wd/viche-seats/branches/executive`, branch `exec/pnp-takeover-20261123` — the
    Executive is **already on the takeover**, so the Clerk did not steer, stop or duplicate it.
  - `KW70qr6VNuY3cE8AVyhsh2-favorably` — Viche P vs NP researcher, cwd
    `/home/lubko/pequalnp-research-20261123`: the one desk-gap worker the Founder said remains
    active. Still running; preserved.
  - `MdwjgGZ16kDbrxwxmkAbXL-laminated` — SoringP1 frontier (must be preserved).
  - `j9Fs9Yeq6dZxvTa5SNcTjQ-guardian` — independent reviewer on delivery
    `fix-pnp-next-gap-null-20261123` (the Executive's desk `next`/`gap:null` fix).
  - The three stopped external IDs (`T2yXW3T7…-slanting`, `otBE7Qhf…-pack`,
    `1DeuAMyM…-spinal`) do **not** appear in the running list, consistent with the Founder's
    handoff drill. Not restarted by the Clerk (only Executive may launch).
- **Preserved research artifacts in the three worktrees — exactly 29 files**, matching the
  Founder's "29 research files" statement:
  - `/home/lubko/pnp-work/formalizer/research/` — 4 files: `statements/L-meta-{949,950,986,987}.statement.lean`.
  - `/home/lubko/pnp-work/refuter/research/` — 17 files: `lean/L_meta_{1021,949,987}_refutation.lean`,
    `logs/refute-949.log`, `program/{compare_statements,fetch_statements,make_refutations}.py`,
    `program/run_checker.sh`, 6 statement `.lean` files, `statement_comparison.txt`, `manifest.json`.
  - `/home/lubko/pnp-work/theoretician/research/` — 8 files: `experiments/order3_lineor.{py,json}`,
    `lean-candidates/L_meta_{1387,949}_refute.lean`, `statements/L-meta-{1025,1387,949}.txt`.
  - **Exact math output preserved** (from `refuter/research/statement_comparison.txt`):
    `L-meta-949 ↔ ¬ L-meta-950` (identical H 167 chars, Q 187 chars, classical first-order
    duality); `L-meta-987 ↔ ¬ L-meta-986` (11 identical hypotheses, Nat `A < B ↔ ¬ B ≤ A`);
    `L-meta-1021 ↔ ¬ L-meta-1020` exactly (1839 chars). All three open search problems are the
    negations of checked lemmas. These are preserved facts, not Clerk-verified new proofs.
- **In-flight continuity preserved**: the handoff `H-1795476325-pnp-continuity.txt` (status `done`)
  records the Executive's earlier post-restart pass: detection fix landed; `L-meta-1393` lease STALE
  (410) not resubmitted; two bootstrap blockers fixed and independently smoke-tested; publisher
  delivery `pnp-bootstrap-signed-publisher-20261123` at `3ee8f2bf` pending integration, not claimed
  landed. Nothing here was replayed or reversed.
- **Founder-owned worktree untouched**: no read/edit/commit/push/rebase of
  `/home/lubko/viche-pnp-leaderboard-20261123`. Leaderboard code/CI is the Founder's; no Clerk model
  time was spent reviewing or implementing it. The 23:32Z Clerk board triage already corroborated
  the official-export baseline (199 contributors / 553 steps; kongeskog 53, sanchan 46,
  ottojung unranked/0; 54 credits to the then-leader) — not re-fetched or claimed as current here.
- **Prior-durable gap (honest)**: the 23:32Z Clerk board comment claimed record
  `records/FOUNDER-INTAKE-2026-11-23-pnp-leaderboard-objective.md` and mandate row `M-033`, but
  neither exists on `origin/main` (`69ba50f5…`) nor in any proposal/handoff in the state root. The
  board comment itself is on the board. This record + M-034 + the new handoff carry that triage
  forward durably; the discrepancy is recorded, not hidden or silently repaired.

## Durable actionable mandate

- **Owner:** Viche Executive (`c1e00002`/`c1a00002`), the only office authorized to launch, start,
  restart or steer Antonina research agents. Clerk retains intake/record/board confirmation only.
- **Next step (this turn):** run the takeover drill with the Executive's OWN agent launches:
  1. Verify the live roster and the 29 preserved artifacts above; treat `KW70qr6…` as the one
     in-flight worker and preserve it and its L-meta-1438 lease (do not orphan or duplicate).
  2. Autonomously **restart multiple independently useful fronts** in the existing worktrees where
     sensible (formalizer / refuter / theoretician), with genuinely different angles — e.g. Lean
     proof completion and checker throughput; counterexample/refutation of the negated checked
     lemmas; independent mathematical theory and failed-approach reports. No fixed headcount cap;
     avoid duplicating the same front and respect 4 CPU / 15 GiB RAM / disk limits.
  3. Verify and record, with checkable evidence: actual new/restarted agent IDs, why each front is
     useful, lease ownership/renewal, exact math output and checker outcomes; and progress toward
     the public @ottojung checked-step rank #1 and a growing lead over #2 (official export).
  4. Keep the standing issue OPEN indefinitely; close nothing on a PR, proof, agent exit, lull,
     rate limit or infra setup. Preserve SoringP1, signed ottojung publishing and Git delivery.
- **Constraints:** Do NOT touch the Founder-owned leaderboard worktree. Antonina selects
  provider/model/variant — no model, variant or provider is prescribed. No law, ballot, gate waiver
  or constitutional action is delegated by this intake.

## Clerk non-actions

Intake only: no agent launched/restarted/steered/stopped, no PR, no leaderboard-worktree access, no
model/provider choice, no law, ballot, case or gate action. Receipts below mean triage happened and
a mandate with an owner/next step was recorded — not that the mission, takeover or any proof is
complete. Local builds, branch commits and unmerged deliveries are not reported as accepted
mathematical contributions.

## Addendum 2026-11-23T23:38Z — Executive executed the takeover in parallel (independently verified)

After this intake's board comment, the Viche Executive posted its own takeover report on the same
issue (`sha256:MClXgeXe…`, 23:36:45Z) reporting three NEW Executive-owned Antonina workers in
separate pinned worktrees — `cyl6mDDK9i2Jlvf6BRy0gO-workshop` (exact Lean proofs,
`/home/lubko/pnp-work/exec-lean-20261123`), `Lu1eY4flFW6hyLc2KlMvO0-weaker` (counterexample/
refutation, `/home/lubko/pnp-work/exec-refute-20261123`, reported steering the live L-meta-1438
lease `23926f11-…`), and `gOoslO42btsQfAw62Nf7qp-urgent` (lemma development and ranked gap
shortlist, `/home/lubko/pnp-work/exec-lemma-20261123`). Clerk independently re-queried the roster at
23:38Z: all three are `state=running`; `KW70qr6VNuY3cE8AVyhsh2-favorably` is now `state=stopped,
alive=false`; SoringP1 `MdwjgGZ1…` untouched. The Clerk did not launch, steer or stop any of these —
this is the Executive's own authorized execution, recorded here only to keep the durable state
truthful. The Executive also reports delivery `fix-pnp-next-gap-null-20261123` @ `e89da652` for the
desk `gap:null` defect, awaiting review; no credited step, PR or merge is claimed.

**Correction to the next-step wording above:** "preserve `KW70qr6…` and its L-meta-1438 lease" is
superseded by events — `KW70qr6…` has been retired and the L-meta-1438 lease was reported
transferred to `Lu1eY4f…`. The standing next step is therefore to preserve whichever worker
currently owns that lease (as of 23:38Z, `Lu1eY4f…`), verify the transfer idempotently, and keep the
three active fronts productive by measured yield. This correction is appended, not a silent rewrite.
