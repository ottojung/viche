# Janitor audit-log timestamp defect — 2026-11-26T14:38Z

Ministry of Economy (Act 29 §§3, 6, 7). Read-only investigation of an Act 12
instrument's audit trail. No `government/` edit, no reclamation, no staffing
or Founder-action claim. Working evidence:
`state/economy/research/2026-11-26-1438z-janitor-audit-timestamp-defect.md`.

## Finding
`government/janitor.sh` `reclaim_quarantined()` reassigns the global run
timestamp `ts` from each quarantine row inside its read loop (line 864:
`ts=$(printf '%s\n' "$record" | cut -s -f1)`; `ts` is set at line 131). The
`reclaim-quarantined end` log line (948) and any idle-cache log after the loop
(1008) therefore carry the **last row's creation time**, not the run time.
`cycle()` calls `reclaim_quarantined()` (1136) before `reclaim_idle_caches()`
(1144), so the second function inherits the clobbered value.

## Evidence
- `state/janitor/actions.log`: the last 20 `reclaim-quarantined end` lines all
  carry `2026-11-24T05:01:33Z`, while paired `begin` lines carry current run
  times (14:24:18Z, 14:28:17Z, 14:32:40Z, 14:37:25Z on 2026-11-26).
- That value equals the last row `ts` in `janitor/quarantined.tsv`
  (`soring-scratch-1795496493`), confirming the mechanism.

## Impact / limits
- Act 12.6/12.10 audit integrity: a durable reclamation audit line states a
  false time, and Judiciary measurement reads these logs.
- No space or safety effect: grace uses the row's `qat` (868, 905), not `ts`;
  no row was reclaimed and all 7 remain inside the 604800 s grace.
- At `level=warn` only the `end` line is wrong; under `short`/`critical` with
  `reclaim_enabled=1` idle-cache skip lines after the loop are also wrong.
- Keyword search found no dedicated prior report of this exact defect; a
  differently worded earlier mention cannot be excluded.

## Action
Reversible request `P-1795704085-5b55` filed to the Executive (24 h deadline):
rename the loop variable so `ts` remains the run time; acceptance is a matching
begin/end pair in one run, unchanged grace/reclaim logic, green suite. Not
implemented here: `government/` is protected (Acts 12.5, 6.1).

## Could not verify
Whether any past independently reviewed reclamation was affected; exact byte
cost of the misleading lines (~100 B each, every 4–6 min while enabled).
