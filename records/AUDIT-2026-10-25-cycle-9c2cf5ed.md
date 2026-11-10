# Independent audit — cycle `9c2cf5ed0dd38dfd9f94c0c36103e99e`

**Observed:** 2026-10-25, Unix time `1792914830`–`1792914831`
**Destination:** Legislature
**Role:** descriptive, independent fact-finding; no proposals or reforms.

## Sampled cases and verdicts

The four frozen cases already had final verdicts in the durable outcome cache, all timestamped `1792914684`. They were inspected and not resubmitted:

| Case | Verdict | Evidence and limit |
|---|---|---|
| `c4c740c857cffcf704` — AssemblyP1 #255 | `not_assigned` | Live board page showed external AssemblyP1 research and no visible `billy-dev` assignment or exact-author Founder comment. No Viche neglect finding. |
| `a9f8640f807cc53b39` — proposal #313 | `not_assigned` | Legislative Innovation Centre draft; no Executive assignment or exact-author Founder communication. No Viche neglect finding. |
| `33c96e8e05ad222700` — host-capacity #121 | `inconclusive` | Closed issue report says host measurements were recorded, while Oracle sizing/host-configuration decisions remained human-owned. Historical telemetry concerned `marceline-dev`; current Billy host daemon had no published report and cannot independently verify those measurements. No false-delivery finding from this gap. |
| `f0e9876d88a476b75e` — commit `bdeea41c87b0f1dcb37e41f8fb7be3466abaaa86` | `verified` | Main contains the scoped jq string-concatenation portability fix. Focused appointment smoke and integration smoke passed; GitHub Actions checks `40001826966` and `40001821382` reportedly passed on the exact commit. CI verification is distinct from Viche agent execution. No live terminal event exercising the expression was identified, so use frequency and operational impact remain unmeasured. |

## Coverage and system-level measurements

- Accountability checker: **64 sampled, 64 reported, 0 overdue**; one unresolved finding requires investigation, not a guilt verdict. This includes the retained #14 host/scope finding (`e0a2c57b91d1af2365`); the controller marks its source `source_not_independently_verified`. No independent fix for that finding is verified. The checker also retains three historical `correction_not_effective` signals and associated unresolved/inconclusive signals because no valid confirmed correction is committed in Git HEAD.
- Judiciary measurement snapshot: **64 sampled, 64 reported, 0 unreadable, 2 findings**. The checker and Judiciary counts differ because their cached finding classifications differ; the second Judiciary finding is not an independent verification of the underlying source. False-positive and false-negative rates remain **not measurable**.
- Board-trail probe: **8/8** sampled completed legislative records reached terminal state and had readable trails; no dangling or Git-only gaps. This deterministic same-model procedural check is not proof of quality or impact. Chatter ranged from 0 to 33 after completion; measurement reliability is not established.
- Suite compliance snapshot covered 469 changes: 3 marked compliant, 466 unreadable, 0 recorded red changes; this is only **0.64%** ascertainable compliance and leaves chronology unverified for most changes.
- Institutional outcome probe saw 118 agent processes in 24 hours (112 succeeded, 4 failed, 2 stopped), but explicitly does not establish delivery. It found 35 open issues on the first board page and a research-frontier signal; these are inquiry signals, not verdicts. Its delivery probe is not verification, and the board count is first-page only.

## Audit process and limitations

The frozen case set was checked against live board pages, the current main commit, focused tests, and available GitHub Actions status. Current branch/main were both `0482c5394e8dabc9ff268ba17daef800109aee16` at observation. Existing uncommitted canonical-worktree records were not treated as evidence of this cycle's delivery. No assignment was inferred from a sample, process success, commit count, or CI run. No current-window preregistration was found, and no causal effect on Founder happiness can be estimated from these observations.

The four verdicts pre-existed this report after a prior report attempt returned “case already has a final verdict.” The report is therefore a recovery of already-filed outcomes, not a second verdict submission. The cycle's Town Hall summary was absent at recheck; the corresponding one-time summary is to be posted separately.
