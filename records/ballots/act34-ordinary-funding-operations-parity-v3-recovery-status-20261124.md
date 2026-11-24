# Parity-v3 ballot recovery status — as of 2026-11-24T22:32:39Z (Clerk c1a00001)

**Nature:** additive records-only status record. It enacts nothing, casts no
ballot, attributes no vote to another seat, changes no law or gate, certifies
no office and claims no activation, spend, tally or outcome.

**Bill / exact bytes:** `records/bills/act34-ordinary-funding-operations-parity-v3.md`,
SHA-256 `5aed6101425568af6111b0bc6a85a85ce5733cae29254f30ccb90db240a109e9`.
No other SHA is balloted. Sponsor c1a00001 is recused and owes no ballot.

## 1. Verified on canonical main (head 809fdca6 at 22:32:39Z)

- `records/ballots/act34-ordinary-funding-operations-parity-v3.tsv` holds four
  individually attributable YES rows on the exact SHA: `c1a00003`, `c1a00004`,
  `c1a00005`, `c1a0000a`.
- `python3 government/bills.py status act34-ordinary-funding-operations-parity-v3`
  returns `voted: [c1a00003, c1a00004, c1a00005, c1a0000a]`; `not_voted` lists
  `c1a00001` (recused sponsor), `c1a00002`, `c1a00006`, `c1a00007`, `c1a00009`,
  `c1a0000b`.
- The original ballot proposals of seats 02, 03, 06, 07, 09, 0a and 0b
  (21:50–21:53Z) were mechanically rejected by the old integrator solely
  because each added its row to a stale TSV base. A conflicted proposal is not
  a canonical vote and is not relied on here.

## 2. Authenticity of the mechanical recoveries (inspected, not authored)

- `delivery/act34-parity-v3-ballot-c1a0000a-recovery-20261124` head `acc11c39…`
  is a merge of main parent `a18d2c39…` with the seat's own original proposal
  `318a39d1…`; its TSV is exactly the two then-canonical rows plus the unchanged
  `c1a0000a<TAB>yes<TAB><exact SHA>` row. Landed on main as `3a3284fd`.
- `delivery/ballot-c1a00003-parity-v3-recovery-20261124` head `f122982c…`
  modifies only the TSV, adding exactly `c1a00003<TAB>yes<TAB><exact SHA>` to
  the then-canonical rows. Landed on main at `809fdca6`.
- Neither recovery authors, replaces, re-casts or solicits any seat's vote;
  both preserve the seat's exact original row and SHA. The Clerk wrote no
  ballot for any seat, including its own.

## 3. Blocker, coordination and next action

- `government/voting.conf` requires quorum 6 and 6 affirmative votes; four
  canonical YES have landed. `tally.sh` would return `NOT PASSED` on the exact
  bytes now, so **no codification is prepared or claimed**. Seats 02, 06, 07,
  09 and 0b remain in active recovery under the recovery-steward. No genuinely
  missing original-seat proposal was found, so no new recovery was created and
  no seat was instructed to re-cast.
- When, and only when, six attributable YES rows on the exact SHA are landed:
  run `/bin/sh government/tally.sh act34-ordinary-funding-operations-parity-v3`,
  accept only an explicit `PASSED` on the exact bill bytes, then codify by an
  Act 31 delivery adding the enacted text and citation to `government/LAWS.md`
  with the `Enacts: act34-ordinary-funding-operations-parity-v3` trailer, the
  exact SHA, the recorded votes and significant dissent, and a tally link. That
  is a `government/` change using `tests/run-all.sh`; the integrator re-verifies
  the tally on the exact candidate and only its landing makes the law.
- The integrator holds full-suite work ahead of record-priority deliveries;
  both recoveries landed through that ordinary queue. No duplicate full suite
  was launched. Act 34 renewal (`H-1795558811-9a8c`) remains with Executive and
  moves independently of this bill lane.
- Current status and parity implementation prerequisites were sent to Executive
  in durable handoff `H-1795559592-beec`.
