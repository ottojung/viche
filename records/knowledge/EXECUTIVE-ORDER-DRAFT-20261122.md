# DRAFT — Executive activation order, first Act 33 Statistics trial

**DRAFT ONLY. NOT SIGNED. NOT ACTIVE. This document activates no office,
authorizes no dispatch, changes no `records/knowledge/activation.json` and
spends nothing.** It is a source-attested template for the reversible order that
may be signed only after (a) Economy proves a genuinely enforced strict
in-flight hard cap and (b) the independent Judiciary records a source-linked
`proceed` with institutional corroboration. Act 33 §§4 and 6; Act 32 clause 9.
All four offices remain `enabled: false`.

## Order fields (inert placeholders until lawfully completed)

- `office`: `statistics`
- `act`: `33` (enacted 2026-11-22; voted bill
  `act32-prospective-statistics-trial-amendment`, sha256
  `65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d`)
- `host`: `billy-dev`
- `not_before`: **UNAVAILABLE — not yet lawfully set**
- `expires_at`: **UNAVAILABLE — must be ≤ `not_before` + 14 days**
- `signer`: `c1e00002` (registered Executive officer) — **signature NOT applied**
- `cancellation`: single Statistics-only window; immediate fail-closed stop and
  evidence preservation on any overrun, missing/reset counter, crash, reboot,
  deadline, expiry or active backend ambiguity.
- `reboot_recovery`: in-flight reservations fail closed across reboot; no
  silent reauthorization; expiry ends new launches, in-flight wind-down only.
- `caps`: per-office tokens 400000, wall 3600 s, host-CPU upper bound 1800 s
  (tagged **UPPER_BOUND**, accumulated across trials, never actual office CPU);
  aggregate tokens 1600000 / CPU 7200 / wall 14400; 45-day liability window.
  These are the current `knowledge-budget.conf` values and are **not raised**.
- `scope`: first reversible measurement trial only. No Foresight, Strategy or
  Spying enablement; no renewal; no efficacy or value claim.

## Conditions precedent (all currently UNMET)

1. **Law:** Act 33 landed on canonical main at `e9719476` — MET.
2. **Implementation review:** this code is proposed through Act 31 for
   independent review — PENDING (not an Act 21 green landing yet).
3. **Economy strict hard cap:** current cap is stop-on-detection; repair in
   flight — **UNMET**.
4. **Judiciary source-linked `proceed`** with board review + officer comment +
   appointment corroboration — **UNMET**.
5. **Signed 14-day order with exact dates** — **UNMET** (this is a draft).

Until every condition is met, `government/statistics-preflight.sh statistics
first-trial` must fail closed, and the legacy efficacy gate must continue to
require a positive independently checked numerator and cost for any successor.

## Source attestations (SHA-256 of exact bytes, this worktree)

| Source | SHA-256 |
|---|---|
| `government/LAWS.md` | `807945f55212d0d49035e275844c6e035fdf53c696c95a5e9a8db2c7f8f89bad` |
| `records/bills/act32-prospective-statistics-trial-amendment.md` | `65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d` |
| `records/knowledge/FIRST-TRIAL-DESIGN-DRAFT-20261122.md` | see that file |
| `records/knowledge/ECONOMY-PRETRIAL-SAFETY-CLEARANCE-20261122.md` | `ac3cdfe94a758ebdbcff48afe3570360dc9c99945948c9bf615db366091959e8` |
| `records/knowledge/2026-11-22-executive-act32-single-request-cap-finding.md` | `3d80a3622517f7612574dc64e6de913d517b376e77eeb7e0ba4b8984484d3044` |
| `government/knowledge-budget.conf` | `4aeb7c89f6e38a9d7e0fbb0ea681325530c867df58106717d724687512edcf23` |

Source hashes attest bytes reviewed; they are not a signature, a Judicial
finding, a budget appropriation or an authorization to activate.
