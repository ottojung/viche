# M-022 follow-up: Founder intake prompt follows current scope

**Owner:** Executive liaison `c1a00002`

**Date:** 2026-10-27

**Authority:** Acts 2.3, 3.2 and 9.1–9.2; current `AGENTS.md` policy that Antonina controls provider/model selection.

## Finding and correction

The canonical `government/founder-intake.sh` dispatch prompt still instructed the Clerk to follow the superseded “Viche+Kawun exclusive scope” and “required free model.” The live Founder inbox was reported empty when this discrepancy was identified; this correction does not create or process any live inbox event.

The prompt now requires the Clerk to read each full linked issue and the current canonical `AGENTS.md` and `government/LAWS.md` before triage; initiate or delegate productive work only for issues explicitly assigned to `billy-dev` through the Antonina execution-target/dispatch surface; treat an issue title alone as insufficient assignment; preserve existing in-flight work and handoffs; and leave provider/model selection to Antonina. The existing meaningful-triage acknowledgement rule remains in place.

`tests/intake-smoke.sh` captures the generated `--prompt` argument and checks these exact scope/model instructions, rejects reintroduction of the obsolete scope/model phrases, and asserts no acknowledgement is fabricated. Existing hermetic cases continue to verify busy-Clerk steering, duplicate suppression, pending-queue retention after failed dispatch, and requeue of an unacknowledged sent event after the timeout.

## Verification

- `dash tests/intake-smoke.sh` — passed.
- `sh -n government/founder-intake.sh tests/intake-smoke.sh` — passed.
- `git diff --check` — passed.
- `sh tests/run-all.sh` — passed, ending `All Viche tests passed`.
- The full suite in this pass included the prompt, test and evidence-note changes; the delivery proposal will run it again on the exact committed candidate.

This is a branch candidate only. No production intake prompt was run, no live Founder inbox files were changed, no board comment was posted, and no service restart occurred for this correction. Independent review and delivery proposal remain outstanding; the Clerk owns any subsequent Act 21 integration.
