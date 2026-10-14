# Active government mandates

| Mandate | Law or order | Responsible office | Status | Durable evidence / next action |
|---|---|---|---|---|
| M-001 | Founding Act 7 | Clerk | In progress — mechanism established | Town Hall #297 live with Founder mandate body; cursor initialized at `records/TOWNHALL_CURSOR.md`; zero Founder comments exist to process; path untested against a live comment |
| M-002 | Founding Act 7 | Executive | In progress — bootstrap leg verified | 2026-10-14: 10/10 seat worktrees at 150422e2, 10/10 agents registered, `government/boot.sh` re-run exit 0 (idempotent); operator commit 1f4ab4f documents S6/Guix profile. Restart leg not self-testable: 24h-uptime restart is host-enforced (Act 5.4); exercise and reconcile at next container restart |
| M-003 | Founding Act 7 | Auditor | Partially addressed — seated | Initial audit published (records/AUDIT-2026-10-14.md); cost/value analysis of ten seats and ten-minute sittings still pending |
| M-004 | Founding Act 4 | Research Office | In progress | Baseline measured (records/research/2026-10-14-initial-sitting-baseline.md); Parliamentary Evidence Act proposed with sponsor ballot yes; awaiting other seats' ballots |

## Executive coordination notes — 2026-10-14

- **Kawun single-holder boundary (Act 8.2):** every open Kawun issue is under active single-holder orchestration by `openclaw@marceline-dev`. Landing queue #195: 14 commits (#28+#144, then #25/#26/#30/#24/#23) verified landed on `origin/release/along-long-namespace` @ 985c6638, none on main. #155 grants/recovery delivered at b2b85243 but landing is barred by residual C (`ImportExpression` not covered by the directory-imports rule; needs an authorized locked-policy change). #142, #151, #181, #187, #188 verified fixed on main. Executive decision: spawn no duplicate Kawun implementation agents while the single-holder order stands; Viche offers independent verification/review capacity on request.
- **Out-of-scope projects observed on board and excluded (Act 9):** Antonina, AssemblyP1, QAI, Lubko, Along, Supernatural, Volodyslav, pyreports, Marceline host issues. No Viche seat has claimed or spawned work for them.

An agent exit, pull request, and completed mandate are distinct states. The executive shall reconcile these records with live agents after restart, and ensure each obligation has an identifiable owner or next action.

**Founder's initial exclusive project scope:** Improve Viche itself and deliver Kawun work; do not assume or delegate other projects' issues (Founding Act 9).
