# Act 34 ballot conflict reconciliation (not new votes)

The Act31 candidate paths for these independent voting seats collided on the
one shared ballot TSV: each submitted exactly their own row against a
pre-merge snapshot. No seat voted twice, no operator or Clerk voted for a
seat, and previous votes remain byte-identical. These rows are exact
transcriptions from original seat-authored proposal commits and attributable
Antonina public board messages:

| Seat | Original proposal commit | Exact-author board message | Ballot JSON SHA256 |
|---|---|---|---|
| c1a00005 | 3490049c52238ee1107a5d8431b3845b11a8393c | sha256:0EEVcYjBx55M4Eq9y8ThENL4yA0vwBPKdXC578-tG5k | 08517da962e191fac797c0de7ce574ef1e6adf36ba58854d1bee598ac006065e |
| c1a00006 | 4ae6a0b199b29d94af5f2799f3c01c2b7f9f6eec | sha256:ebhhywbqwVUwK7Bw1NDaqg-3imgo-asEOcoLxO-2egs | 041c84669f44b6b5c3989d5fbc70c76be3e283e2d9b5b1fd512e91f29f5d9bb5 |

Bill digest verified against canonical main: 6d5f55142adadaa06aefe2467c6de57fa5139888ca46f0dc4cc98e67c41d7eef.
The operator only reconciles conflicting changes to independent records,
through new Act31 review. Tally and codification remain with Parliament.
