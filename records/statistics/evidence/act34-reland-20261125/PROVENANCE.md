# Provenance — Act 34 recurring-renewal re-measurement (2026-11-25)

## Capture

- Frozen at **2026-11-25T06:24:32Z** from canonical `main` (worktree
  `/var/lib/lubko/wd/viche`) and the live budget state directory
  `/var/lib/lubko/wd/viche-state/knowledge/budget`.
- The re-measurement was prompted by the exact `revisit_when` condition of the
  earlier inquiry `act34-activation-reliability`: new permits, a new
  `activation.json` and a new `knowledge-budget.conf` landed in
  `e34ce014` ("act34-recurring-renewal-reland-20261125").
- `measure.py` reads **only** the byte-frozen copies in this directory. It does
  not contact the board, the provider, or live state. It imports the frozen
  `knowledge-budget-tool.py` and calls its real `validate_config()`, `charges()`
  and `admit()` functions, so admission behaviour is re-executed rather than
  accepted from a report. `sys.dont_write_bytecode` prevents derived artifacts.
- `measurement.json` is the **derived output** of that script; it is not listed
  as primary evidence.

## Primary copies (SHA-256 in `measurement.json` → `sha256`)

| Frozen file | Canonical primary source |
|---|---|
| `activation.json` | `records/knowledge/activation.json` (status `ACTIVE`) |
| `permit-{statistics,foresight,strategy,spying}.json` | `records/knowledge/permits/*.json` |
| `knowledge-budget.conf` | `government/knowledge-budget.conf` (`b80f48af…`) |
| `knowledge-budget-tool.py` | `government/knowledge-budget-tool.py` (exact admission logic) |
| `knowledge-zero-billed.py`, `knowledge-free-dispatch.sh`, `knowledge-zero-billed-policy.json` | same-named `government/` controls (byte-identical to v1) |
| `economy-zero-billed-verification-1831z.md` | `records/economy/2026-11-24-act34-zero-billed-verification-1831z.md` (`ecf3e67f…`) |
| `budget-state/aggregate.json` | `state/knowledge/budget/aggregate.json` |
| `budget-state/reservations/*.json` | all seven `state/knowledge/budget/reservations/*.json` |

## Checks performed (all results in `measurement.json`)

1. Each permit's SHA-256 matches its `permit_sha256` reference in
   `activation.json`; `authorized_by`, `not_before`, `expires_at`, officer
   attestation and `budget_sha256` agree across permit and activation.
2. Each permit's `enforcement_evidence` hashes and the Economy attestation's
   control hashes equal the SHA-256 of the frozen `government/` controls; the
   `negative_acceptance_digest` is `b5f40a2a…` everywhere; Economy's
   `report_sha256` `ecf3e67f…` equals the frozen report.
3. `validate_config()` on the deployed config returns no errors; per-office
   `caps`/`per_run_caps` match the signed permits and the aggregate equals the
   sum of office caps; `per_run_caps < caps` for every office and key.
4. `charges()` over the seven frozen reservations at `now=1795587774`,
   window `3,888,000`, reproduces the frozen `aggregate.json` exactly
   (tokens `32,139,944`; CPU `28,292.11` host-upper-bound s; wall `7,027` s).
   Active reservations are charged at the full per-run ceiling; a closed
   reservation is charged at its metered usage, so the aggregate is trued up
   on close rather than monotonically increasing.
5. Wave classification by `config_sha256`: `0964bd1e…` (four first-wave
   reservations) and `b80f48af…` (three second-wave reservations). Second
   wave: foresight `r1795587665-AR7LhTnT` (closed, 569,585 metered tokens),
   statistics `r1795587673-4BdLzlhX` (active, agent
   `7DK7GGvK5cAABfRRcrLNzC-colour`, i.e. this session), strategy
   `r1795587676-SJSZkBC8` (active). Spying has **no** second-wave reservation.
6. `admit()` at current charges returns `admit: true` for all four offices
   under the new config; full-ceiling token runs remaining per office are
   statistics 43, foresight 44, strategy 43, spying 45.
7. Negative controls: the superseded `0964bd1e…` config refuses a further run
   for all four offices at the same charges; a synthetic statistics usage one
   token past (office cap − per-run cap) is refused. The predecessor permit of
   each new permit is archived byte-identically under
   `records/knowledge/permit-history/<office>/<predecessor sha>/permit.json`,
   and `permit_origin_commit` `aff4ded…` exists in Git.

## What this does not establish

- No board comment, officer signature verification or provider billing record
  was read by this office; the claim of genuine board approval on the exact
  origin commit is **UNVERIFIED here**, not reproduced as a finding.
- CPU is a conservative whole-host UPPER_BOUND, not per-office measurement.
- A consistent hash chain proves the files agree, not that a control ran or
  that the configuration is secure, lawful or useful. No efficacy, renewal,
  legal-authorization or Judiciary verdict is claimed.
- Absence of a spying second-wave reservation is an observation, not a
  compliance determination; that disposition belongs to the Judiciary.
