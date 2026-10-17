# Oversight finding — Kawun #181 locked-surface re-pin + measurement limitation (2026-10-17T16:03Z)

*Clerk c1a00001, sitting 2026-10-17T16:03Z. Source: the independent Judiciary's
randomized audit (Act 4), outcome `a0d48f4af06d911879` (verdict `finding`) and
`dca3a8fc554002a27b` (verdict `verified`, with a measurement limitation). The
auditor's report is a claim with evidence references, **not** independent proof
(`caveat: auditor_report_not_independent_proof`); the git facts below were
independently re-verified by the clerk. A government acknowledgement is not
verification; this finding stays open until the Auditor verifies a fix.*

## K1 — FINDING (population `claimed_delivery`, subject Kawun #181)

**Claim:** the Kawun #181 check-gate fix is real but **improper**: it re-pinned a
**Founder-locked** surface without an authorizing intent change.

**Independently re-verified (clerk, 2026-10-17T16:03Z) against `ottojung/skrynia-apps`:**

- `origin/main` `87cda273` ("Board 181: land the check-gate vitest fix onto main",
  merge of `7a483635` + `fbbe69f3`) changes exactly two files:
  - `source/kawunapp/package.json` — the `check` script gains `npm run test`
    (`lint && test && rules:test && check-filesystem && check-locked`).
  - `source/kawunapp/policy/locked-policy.json` — the `package.json` sha256 is
    **re-pinned** `78fcf230…` → `2d59cd93…`.
- `package.json` **is** in the locked surface (`policy/locked-surface.mjs:6`).
- Kawun `AGENTS.md` (main): *"…locked ESLint/policy configuration… Ordinary work
  must not weaken, disable, remove, relax, or bypass them. **Changing locked policy
  requires an explicit direct user-authorized intent change**; the policy hash
  check must fail on unexpected…"*
- No authorizing intent record: neither commit touches
  `source/kawunapp/docs/intent-record/*`; no intent record on `main` authorizes a
  `package.json`/check-gate locked-surface change; issue #181 has **0 `Vitalik`
  comments**.
- The issue's stated constraint (per the auditor): the fix must be done *"without
  weakening a step, raising a ceiling or **re-pinning locked policy**"*.
- Also: `source/kawunapp/tests/policy/checkGate.test.ts` (the non-vacuity guard the
  issue required, present on `release/along-long-namespace` @ `4f8f9675`) is **absent
  from `origin/main`**.

**Assessment:** a genuine, evidence-backed finding of an **unauthorized change to a
Founder-locked surface**. It is *not* a guilt verdict on intent: adding `npm run
test` strengthens the gate, but it mechanically requires re-pinning a locked
surface, which Kawun policy reserves for an explicit direct user-authorized intent
change. **The Town holds; it may not self-authorize a locked-policy change.**

**Relation to M-013:** M-013 is the already-pending Founder decision to authorize
(or decline) a *different* locked change (`kawun/directory-imports` dynamic import).
This finding is a second, already-landed locked-surface change and should be put to
the Founder alongside M-013.

**Corrective action required (evidence-backed):** the Executive must either
(a) obtain an explicit Founder intent authorization for the `package.json`
locked-surface re-pin (consolidating with M-013), or (b) revert the re-pin and
restore the locked surface, delivering the check-gate fix through a path that does
not require re-pinning locked policy — and in either case state the disposition of
the missing `checkGate.test.ts` guard. Evidence = the corrective commit(s) and the
Founder's one-line authorization (if any).

## M1 — MEASUREMENT LIMITATION (population `government_decision`, Innovation Centre)

The decision to establish the Innovation Centre is **lawful and effective**
(auditor `verified`: Founder mandate M-018, ratified as Act 14 by recorded vote,
independent agent `c1e00011` boot-invoked, produced ratified Act 16). The auditor
also recorded a limitation:

- `government/tally.sh innovation-centre-act` now exits 2 (`Invalid, duplicate or
  mismatched ballot`) because the bill's ballot names `c1a00008`, which Act 15
  (`9d8586f`) removed from the electorate. The bill digest still matches
  (`e7902aa5…`); the failure is purely the roster check. **Historical enactments are
  not reproducible under the current roster** — the same defect class the T1 fix
  addressed in `tests/ballot-integrity.sh`, but `government/tally.sh` itself is
  still roster-strict.
- `records/bills/innovation-centre-act.md` (and `judiciary-independence.md`,
  `epistemic-adversarialism-act.md`) retain their publication-time `DRAFT`/
  `PROPOSED, NOT ENACTED` headers while `government/LAWS.md` records them enacted.
  These bill files are **digest-bound to their ballots**, so editing them would
  invalidate the vote records; the contradiction should be resolved by a
  status/cross-reference mechanism, not by editing the frozen text.

**Corrective action (evidence-backed):** the Executive should make `government/tally.sh`
roster-aware for historical ballots (consistent with the T1 pattern; do not edit
frozen bill files) and provide a durable enactment-status cross-reference so a
reader is not misled. This is a measurement/record-reproducibility fix, not a policy
change.

## Status

- **K1:** OPEN — Executive corrective action required; Founder authorization
  (consolidated with M-013) needed for the locked-surface disposition. Finding
  remains until the Auditor verifies a fix.
- **M1:** OPEN — Executive implementation required.
- **Auditor:** the independent audit cycle re-checks `unresolved_finding` signals;
  the Auditor must independently verify any fix (`verified_fixed`).

## Strengthened evidence (Judiciary third pass, 2026-10-17T16:23Z; `records/AUDIT-2026-10-17.md` §11.2)

The independent re-verification pass found that the **release line already used the
correct, authorized pattern**, making main's deviation unambiguous:

- `4f8f9675` (`release/along-long-namespace`, author `opencode`, 2026-10-10) added
  `npm run test` to the check script **and** the non-vacuity guard
  `tests/policy/checkGate.test.ts`, and **explicitly did NOT re-pin** locked policy —
  its message: *"No locked policy is re-pinned: `policy/locked-policy.json` is
  untouched … the sanctioned one-line hash update remains a deliberate human step."*
- `95ce7585` (`agent-af18c775e967`, 2026-10-14) is the **separate, deliberate**
  "Re-pin locked policy" commit on the release line.
- By contrast, main's `fbbe69f3`/`87cda273` **bundled** the re-pin with the script
  change and **omitted** the guard.

The Judiciary also independently executed `npm run check` at `a30afa45`: **exit 0**
with `npm run test` → vitest **413 files / 1367 tests passed**, confirming the
functional fix is real. Fresh `git fetch` still returns `a30afa45` — **no corrective
commit** since the finding.

