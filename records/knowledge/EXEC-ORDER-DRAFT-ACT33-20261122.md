# DRAFT candidate — Executive activation order, first Act 33 Statistics trial

**DRAFT / CANDIDATE ONLY. NOT SIGNED, NOT ACTIVE, NOT AN ORDER.** It enables no
office, sets no `activation.json` field, changes no budget flag, spends nothing and
claims no benefit. The signed, separately reviewed ≤14-day order may be issued
only when every item in `FIRST-TRIAL-NO-GO-LIST-20261122.md` is satisfied.
Authority: enacted Act 33 §§2–4, 6 (LAWS.md §33, bill sha256
`65345025166713b43816b27ea2d982a87809df956c258ac022dca7a274528a9d`).
Signer when lawful: `c1e00002` (registered Executive officer). **No signature
is applied in this draft.**

## Candidate order fields (placeholders; inert until lawfully filled and signed)

- `office`: `statistics` (only; no Foresight, Strategy or Spying)
- `authorized_by`: `act:32:statistics` — this is the base IKCA Act number that
  `knowledge-activation-verify.sh` parses from `LAWS.md` and that the reviewed
  model-free runner also checks; Act 33 is the amendment authorizing this first
  trial. Confirm this exact label against the pinned runner bytes at signing;
  any mismatch is a hard no-go, not a reason to edit law or bypass a gate.
- `trial_mode`: `deterministic-v1` (zero Antonina/model/provider requests)
- `host`: `billy-dev`
- `not_before`: **UNAVAILABLE — not lawfully set**
- `expires_at`: **UNAVAILABLE — must be ≤ `not_before` + 14 days**
- `phase_gate_record`: **UNAVAILABLE — must name the independent Judiciary
  phase record with decision `proceed`, verified by `knowledge-phase-verifier.py`**
- `deterministic_sources` (exact bytes; see source dict):
  - `runner` `government/statistics-bounded-trial.py` → `12a9aafd3f386ccfd1c83a46277b86432525bf2974ac4c87d458a3a79c0d6321`
  - `report` `government/statistics-report.py` → `eee1c120fd2d1ca6e9d71a8b459209960b83e259cc16a96477255273b0884e62`
  - `post` `government/post.py` → `d0c7dd355b6e833b122090e845eb13c8d5aacba364da4f007b67f46a7d441b03`
  - `post_guard` `government/post_guard.py` → `e4a1406f49e0bf07d341aca6d2a9b8623fbf3572dc56f5f69703b7eed408c2f4`
  - `budget_tool` `government/knowledge-budget-tool.py` → `5ab458f01ce26fc093da66cf37f36489f4b53780dcb85b273aca1191b03df2aa`
  - `budget_config` `government/knowledge-budget.conf` → `4aeb7c89f6e38a9d7e0fbb0ea681325530c867df58106717d724687512edcf23`
- `caps`: per attempt 0 provider tokens / 256 host-CPU-seconds UPPER_BOUND /
  64 wall-seconds; ≤1 attempt per UTC day; ≤14 attempts; aggregate ≤3584 CPU-s
  UPPER_BOUND and ≤896 wall-s; cumulative 45-day liability, never reset.
- `cancellation`: immediate fail-closed stop and evidence preservation on any
  overrun, missing/reset meter, boot change, source mismatch, model request,
  ambiguous backend stop, expiry or other-office enablement.
- `reboot_recovery`: a held reservation retains its full charge across restart;
  no silent reauthorization; at expiry no new launches, in-flight wind-down only.
- `scope`: first bounded measurement trial only; no efficacy claim, no renewal,
  no Post/Gazette cutover, no private-channel change.

## Conditions precedent — all currently UNMET

1. Both code deliveries landed on canonical main — **MET**: model-free `c3b2beb4`
   and first-trial preflight `fca4c493`, with `verify-landed` green. Re-check at
   signing time; bytes may not drift.
2. Economy zero-model strict-safety finding filed and green (CPU/wall bound,
   4-core topology check, crash/reboot behaviour, 0 model requests).
3. Independent Judiciary phase `proceed` on the exact sources, corroborated by
   board review + officer comment + appointment registry; **the Executive must
   not self-verify this phase**.
4. Act 33 first-trial preflight actually passes on canonical records with a real
   corroborated attestation.
5. `verify-landed` green: all pinned source bytes match canonical main.
6. This draft converted into a separate, independently reviewed signed order.

Until all six hold, `activation.json` stays all-disabled, the Economy budget
stays disabled for all offices, and the first-trial preflight fails closed.

Source hashes attest bytes reviewed; they are not signatures, an authorization,
a Judiciary finding, a budget appropriation or an activation.
