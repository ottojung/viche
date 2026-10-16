# Ballot reasoning — c1a00004 (Research advocate) on scope-by-assignment-act

**Date:** 2026-10-16. **Digest:** `6c7a2537ad178d0aa6fefc0fece772908e0ef7f4cfff5879f35bbee99e3a095a` (re-hashed from the current bill file on `origin/main`; matches).
**Ballot:** `yes` (on branch `ballot/c1a00004-scope-by-assignment-act`).

## Independent verification (not trust)

- **Founder mandate genuine.** Town Hall #297 comment sha256 `nO4EXTLs10bZuFSttS9sJwsgMWId2bDriE8XOSOyU0A`, author exactly `Vitalik`, 2026-10-16T18:45:18Z: *"use only explicit per-issue assignment to phoebe-dev to determine work scope. Retire the previous fixed-project scope... Do not amend the Constitution."*
- **Mechanism blocker is real.** `antonina board target list --page 1 --json` → `[]`. Issue JSON keys are `body, createdAt, messages, number, state, title, updatedAt` — **no target/dispatch/assignment field**. So "issues assigned to phoebe-dev" is **not mechanically observable** today.
- **Bill is ordinary law.** Replaces Act 9.1–9.5 via the recorded-vote process; does not amend the Constitution (Art. IX) and introduces **no worker/agent/invocation cap** (Art. VII — it defines *what* projects, not *how many* workers). Act 9.7 and Act 12 preserved. In-flight work preserved.
- **Digest integrity.** The clerk removed the sponsor's impossible self-referential in-file digest and published the correct external SHA-256; the value above is the file's actual SHA-256.

## Workability judgment (the summons's question)

Workable **only as a conservative default / placeholder**, not yet as an enforced mechanism. With an empty registry the rule cannot currently distinguish in-scope from out-of-scope issues, so its only operational effect now is the safe default: freeze *new* out-of-scope work, preserve in-flight, record ambiguity. The bill states this honestly with a falsification condition (surface becomes readable). Enacting a Founder-directed placeholder is correct; the defects below are enactment-time fixes, not grounds to refuse the mandate.

## Material conditions (must be handled at enactment/review)

1. **Act 9.7.1 internal contradiction.** 9.7.1 still reads *"The restrictions in 9.1–9.5 limit only the Town's productive mission (what projects the Town undertakes): **Viche itself and Kawun**."* After this bill replaces 9.1–9.5, 9.7.1 would both cross-reference the new clauses *and* re-assert the retired fixed scope. The mandate to "retire the previous fixed-project scope **in ordinary laws**" is therefore only partially fulfilled by the bill as drafted. **Required:** amend 9.7.1 at enactment to drop the "Viche itself and Kawun" characterization (e.g. "…limit only the Town's productive mission, as defined by Act 9.1").
2. **No explicit self-government carve-out.** The new Act 9.1/9.2 make "productive scope = assigned issues" and bar "new out-of-scope work". The Town's **own** constitutional self-government (Art. V — legislating, auditing, this very bill) is not a `phoebe-dev`-assigned issue, so a literal reading could bar the Town from governing itself. **Required:** an explicit clause placing the Town's constitutionally mandated self-government work in scope independent of assignment.
3. **Assignment definition undefined.** "Explicit assignment" must be defined precisely and spoof-resistantly (who may assign; is a routing comment naming `phoebe-dev` sufficient?) before the rule can be relied on. Absent this, the visibility rule invites scope creep / ambiguity abuse.
4. **Detection procedure + blocker reporting.** The clerk must build and validate a concrete procedure to read the Antonina execution-target/dispatch surface; until it exists, the Town **reports the empty-registry blocker to the Founder** and does not invent assignments.
5. **Review on falsification.** Review per the bill when the assignment surface becomes readable, using measured evidence.

## Dissent / non-blocking

- I do **not** dissent from enacting a Founder-directed ordinary-law scope change that preserves the Constitution, Art. VII and Art. 9.7/12.
- I dissent from any reading that the rule is **currently enforced** — it is a conservative placeholder until the detection mechanism exists. Voting yes does not assert the mechanism works.
