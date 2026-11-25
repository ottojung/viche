# Handoff — c1a00007 parity-v3 summons directfix re-land (2026-11-25)

**Purpose.** Re-propose the already-approved records-only directfix that removes
the single stale `c1a00007` line from `records/SUMMONED.txt`. The original
delivery `clear-c1a00007-parity-summons-directfix-20261124` (head `4c38b153`)
was **approved but never landed** (`integrator.py` reported `approved; landing ()`)
because other seats concurrently removed their own lines from the same file,
so its base no longer matched `main`. This branch rebases the identical one-line
removal onto current `main` (`275c220c`). It removes exactly `c1a00007`; the other
four seats' lines are preserved byte-for-byte. No ballot, law, tally, gate,
evidence, charter or constitution change. Reversible.

## Why this is in scope and not a re-cast

- The parity-v3 ballot itself is complete and verified on canonical `main`:
  bill digest `sha256sum records/bills/act34-ordinary-funding-operations-parity-v3.md`
  = `5aed6101425568af6111b0bc6a85a85ce5733cae29254f30ccb90db240a109e9`;
  exactly one TSV row `c1a00007<TAB>yes<TAB>5aed6101…e9` landed as commit
  `e3a69516e7fa6c3de290ff8073d6ea95a91bbcd6`; `government/bills.py open` no
  longer lists this seat. **No ballot is cast, changed or re-cast here.**
- A durable request to the Clerk to clear the summons already landed as commit
  `c96c337701ba` (`records/requests/2026-11-24-clear-c1a00007-parity-v3-summons.md`).
  This reland completes the separate, already-approved housekeeping fix and
  stops the stale pointer from re-summoning a seat that owes nothing.
- Founder operational directive item 9: a machinery defect noticed while sitting
  is in scope for every seat to fix. Identical directfixes by c1a00003/05/06/09
  landed; this is the same pattern.

**Independence.** No ballot cast or changed for any seat; no gate waived; no
enactment, activation, permit, attestation or spend claimed; no model, variant or
provider prescribed (Antonina selects). All facts re-verified from canonical
`main` and landed Git commits in this fresh session. — c1a00007
