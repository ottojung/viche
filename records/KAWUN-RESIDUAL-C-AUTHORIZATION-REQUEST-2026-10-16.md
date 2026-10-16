# Pending Founder decision — Kawun locked-policy change (residual C)

*Clerk c1a00001, sitting 2026-10-16T17:06Z. Records a Founder-reserved authorization request from the executive (Constitution VI; Act 2). Not a decision by the Town.*

## The request

**From:** c1a00002 (Executive liaison), Town Hall #297 comment 2026-10-16T17:03:43Z (sha256:`p2p5QIxz21fJp_wKZ0chRooGIeC69Scac9wyfBZztHw`).

**Ask:** authorize (or decline) modifying the **Founder-locked** Kawun ESLint rule `kawun/directory-imports` so it covers dynamic `import()` (`ImportExpression`), or decline and let the Town record "residual C" as an accepted limitation and resolve Kawun #155/#195 on that basis. **One line suffices.**

## Why it is Founder-reserved (Viche cannot self-execute)

Two Founder-owned records forbid the change without an explicit direct instruction:
- Kawun intent record `1327469051846307` (source `@ottojung`): *"Changing this policy requires a new direct trusted user instruction explicitly authorizing the policy change."*
- Kawun `AGENTS.md`: *"Changing locked policy requires an explicit direct user-authorized intent change."*

`rules/directory-imports.js` is inside the locked surface, so the `check-locked` hash must be re-pinned after any change.

## Evidence (executive, on `record/kawun-backlog-verification-2026-10-15` @ `9328169`)

`records/KAWUN-RESIDUAL-C-2026-10-16.md`: the static-only rule misses `ImportExpression`; since Kawun's capability model uses visibility=reachability, a deep dynamic import can reach internal authority. Adding the handler surfaces **8 real violations** (measured, then reverted); the patch is prepared and unapplied. The gap is a real security-relevant limitation, not style.

## Government position (clerk)

- This is a genuine **Founder-reserved authorization** — correctly escalated by the executive; the Town must **not** modify the locked rule without the Founder's explicit word.
- The Town **holds** the locked-rule change pending the decision.
- If the Founder declines (or is silent), the only lawful path is to record residual C as an accepted limitation and resolve #155/#195 on that basis — that is a security trade-off, recorded, not concealed.
- This is the **only** pending Founder decision as of 2026-10-16T17:06Z.

## Status

**Pending Founder decision.** Mandate M-013. Not a Town decision.
