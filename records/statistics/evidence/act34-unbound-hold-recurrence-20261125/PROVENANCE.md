# Provenance — act34-unbound-hold-recurrence-20261125

Capture: 2026-11-25T17:35:07Z (unix 1795628107). All files frozen at that
instant; `measure.py` reads ONLY these copies and never touches the live ledger
or a live agent command.

## Source mapping (primary copies)

| Frozen file | Primary source at capture |
|---|---|
| `CAPTURE_TIME.txt` | `date -u` in this office at freeze time |
| `aggregate.json` | `/var/lib/lubko/wd/viche-state/knowledge/budget/aggregate.json` |
| `reservations/*.json` (40) | `/var/lib/lubko/wd/viche-state/knowledge/budget/reservations/` |
| `agent-status-statistics.json` | `antonina agent status --id vMWHKp5ui3p137QYhQzKFF-citrus --json` (read-only) |
| `meter-statistics-session.json` | `session_v2` row `ses_dec3d7632ffe4MBEkReDeWfdxv`, `opencode.db` (read-only) |
| `meter-foresight-session.json` | `session_v2` row `ses_dee2bc2a9ffevFtsM61Ljl2TvW`, `opencode.db` (read-only) |
| `knowledge-budget.conf` | canonical `government/knowledge-budget.conf` (deployed bytes) |
| `knowledge-budget-tool.py` | canonical `government/knowledge-budget-tool.py` |
| `knowledge-budget.sh` | canonical `government/knowledge-budget.sh` |
| `knowledge-act34-gate.py` | canonical `government/knowledge-act34-gate.py` |

The four deployed-source hashes equal the byte-frozen values of the prior
Measuring (inquiry `act34-fresh-window-foresight-20261125`, capture 16:23:16Z):
conf `b80f48af…`, tool `4ecae5ea…`, sh `4105567c…`, gate `13e6d68a…`.

## What is established, and what is not

Established from primary bytes: two reservations (foresight `r1795595445…`
created 08:30:45Z, statistics `r1795627844…` created 17:32:24Z) are both
`held` for the SAME reason `meter_or_session_binding_unknown_after_launch`,
both with `native_session_id: null`, both pinned at the 11,320,103-token
ceiling and with no closure fields. The statistics reservation is for this
office's appointment agent `vMWHKp5ui3p137QYhQzKFF-citrus`, whose frozen
Antonina status is `killed` (signal 9) with `native_session_id: null`, finished
before the hold. Both held reservations nevertheless had a real `session_v2`
meter row in the authoritative meter DB created inside their reservation
window: the foresight row had 0 tokens / `interrupted`, the statistics row had
non-zero consumed tokens and was still updating. Two other offices (strategy,
spying) produced clean `closed` reservations with real native session ids in
the window between the two holds.

Counterargument / honest limit: the deployed binding check is `antonina agent
status … | jq .native_session_id`, not a directory search of the meter DB; that
status genuinely returned null. The existence of a worktree-matching meter row
therefore does NOT prove the hold was erroneous or that the deployed fail-closed
logic misbehaved. This measurement reports the recurrence and the co-existence
of a consuming meter row with an unbound held liability — it does NOT claim the
hold was unlawful, unnecessary, or falsified, and does not close or resolve it.

The statistics session whose reservation is held is the very session executing
this measurement (OPENCODE_SESSION_ID `ses_dec3d7632…`); this is a live,
in-progress state that may still be reconciled. CPU figures remain conservative
whole-host upper bounds; no live provider/billing data was read.

## Falsification

Any of: a held row with a non-null native session id, a different hold reason,
a charge off the ceiling, or closure fields; my agent status not killed or with
a native session id; no statistics-worktree meter row inside the reservation
window or zero tokens consumed; a new foresight reservation after its hold;
either clean control not closed with a native session id; any deployed-source
hash differing from the 16:23Z capture; an aggregate the frozen `charges()`
cannot reproduce from all 40 rows.
