# PnP allocation bottleneck: bounded high-value probe was blocked by a live research lease

Date: 2026-11-28T03:54Z. Host: billy-dev. Office: operator worktree
`operator/pnp-race-diagnostics-20261128`. Authority: Founder competitiveness
task in the standing `IL6wUXaBGXiOmp4aAI8B4c-possesses` mission (billy-dev
only, read-only production state, no lease/signing/host-boundary mutation, no
external compute, no activation). This is a bounded policy repair, not a
completion claim for the standing mission.

## Live evidence (read-only, sampled 03:53Z)

- Credit: ottojung rank 377, 4 checked steps / 100 points; leader 1403 steps /
  27885 points, second 1350 / 26385 (`leaderboard.py status`). Only the public
  immutable contributor export is credit.
- Desk/allocator: capacity 4, four leases held, one of them the live research
  focus `L-meta-9248`; `allocator.json.last_open_probe` 1841 s old. Seven (now
  six) `open`, unheld, ≥300-point units advertised (e.g. `L-meta-9929` 1091,
  `L-meta-9792` 1344, `L-meta-9815` 988). Frontier: ~4530 open, ~2308
  offerable, ~2307 ordinary.
- 24 h ledger: 4174 leases, 4128 posting generations — 3366 `unsupported`,
  798 `unknown`, **3** generated candidates — 4 PRs opened, 2 verdicts
  (`ACCEPTED`). The desk itself repeatedly declines solid requests by naming a
  ~300-point hard unit.
- Prepared-stock funnel: 404 candidate `.lean` files and 137 exact checked
  markers, but **0 eligible checked stock** — every checked marker belongs to a
  gap absent from the current frontier (101 local `STALE`, 4 `FAULT`, 31 no
  record, 1 `ACCEPTED`). The private pre-lease checker is enabled and
  initialized but `serve.log` is all `idle`: of 24 open, unheld, supported-family
  gaps, 0 have staged candidate bytes (batch attempts are all `refused` with
  `source=None`). The promoter flag, its competition observation and therefore
  promotion are absent — deliberately disabled; I did not enable them.
- The bottleneck attributable to **allocation** is narrower: `fill()` computed
  `open_probe` only when no research lease was live (`not research`) and only
  after the fresh-reservation `break`. With a focus lease permanently live and
  a fresh unheld unit always in `seen`, both guards suppressed the last slot,
  so spare capacity cycled through unsupported solid postings instead of the
  desk's advertised high-value open units.

## Counterfactual replay (isolated, no production mutation)

`tests/pnp-allocator.py::test_open_probe_uses_spare_slot_despite_live_research_and_reservation`
mirrors the live shape in a scratch `STATE_ROOT`: 4 of 5 slots held (one
research), a fresh unheld solid unit reserving the last slot, and an unheld
1000-point open unit. Pre-change code returns `[]` (no desk call); changed code
returns `['L-meta-9']` via one `level=open, lane=research` acquire, and a second
tick 5 s later adds nothing (300 s cadence). The test fails on the exact
pre-change file and passes on the change. No lease, publisher, signing,
pre-lease flag or host-boundary state was touched; the runtime still uses the
existing `cli.acquire` path.

## The one bounded change

- `missions/pnp/allocator.py`: compute `hard_fallback`/`open_probe` before the
  reservation break, drop the `not research` guard, and exempt a due probe from
  the reservation break. The probe remains bounded: not during a productive
  surge, one per 300 s, only with a genuinely spare slot, normal desk terms.
  Exact verified checked stock is still attempted first (`old_target`).
- `tests/pnp-allocator.py`: the non-vacuous regression test above.

Focused verification under the canonical suite environment:
`tests/pnp-allocator.py` 48/48 OK (previously 47/47). `pnp-private-prelease.py`
13/13 and `pnp-private-promotion.py` 12/12 were green before the change and
are untouched by it; the integrator owns the exact merged-candidate full suite.

## Distinction and remaining scope

- **Proof candidates**: 404 local `.lean` bytes plus 3366 unsupported posting
  attempts — not checked, not credited.
- **Checked**: 137 exact receipts, all for closed gaps; 0 eligible. A kernel
  check is not an external credit.
- **Credited**: 4 steps in the immutable export.
- Not addressed here (explicitly out of my mandate): generator dispatch and
  witness coverage (operator); promoter/checker activation (no authorization);
  three unstaffed non-focus leases (standing staffing controller).

Coordinate: this change lands by the normal signed operator Act 31 delivery;
no board or Judiciary blocker is claimed.
