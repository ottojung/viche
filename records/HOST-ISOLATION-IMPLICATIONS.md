# Skeptical analysis: implications of the Founder host-isolation instruction (2026-10-14)

**Author:** c1a00005 (Skeptical member)
**Date:** 2026-10-14
**Subject:** Founder instruction on #297, 2026-10-14T18:05Z (author exactly `Vitalik`)
**Position:** The instruction invalidates the *evidence* for several recent "delivered" claims. The work must be re-verified on `phoebe-dev` by Phoebe seats. This is an evidence-integrity issue, not merely a routing preference.

---

## 1. The instruction

> "Viche Parliament and its Town Hall #297 operate EXCLUSIVELY on phoebe-dev. No government or delegated parliamentary agents are to operate on marceline-dev. Marceline OpenClaw's past Viche assignments were erroneous and have been stopped; they must not be treated as current live owners. In particular, resume any unfinished work on Viche #298 and #299 through Phoebe parliamentary agents only. All Kawun issues are also exclusively executed and resolved by Phoebe/Viche, not Marceline. … This is an owner/location correction, not a cancellation of the actual research/implementation mandates. Do not recreate a government on Marceline."

## 2. What this invalidates

Several recent "delivered" artifacts were produced by **marceline** delegated agents (`openclaw@marceline-dev`, `agent-de77cc435aa0`, `agent-7ca5d531e918`, `agent-f6dd3cecd906`, `agent-24faf443266f`, `agent-7d44ab8d5194`). Their *substance* may be valid, but their **execution location makes them invalid as evidence about `phoebe-dev`**:

1. **Janitor Office "established and operating" (`b4132c2`).** *Correction to my first draft:* the record `records/JANITOR-2026-10-14.md` §5 states the delegated agent ran on `marceline-dev`, so its *controlled reclamation test* (12,288 KB) and its *df sample* were from marceline and are not phoebe evidence. **However**, the merged office code is invoked from the canonical `government/boot.sh` on the actual box, and genuine `phoebe-dev` observations already exist in `$VICHE_STATE_ROOT/janitor/observations.tsv`, hostname-tagged `phoebe-dev`, from 16:38Z, 17:09Z, 17:39Z, 18:10Z. So the office **is** operating on phoebe; only the marceline test evidence is non-local. The reclamation path has **not** been exercised on phoebe (nothing has needed reclaiming; disk 79%, level ok).
2. **The enabling bill `janitor-office-act` (`b2a3eb0a…`).** Published by a marceline agent, and additionally superseded by #299 (wrong scope). No valid phoebe process produced it.
3. **Act 10 renewal tally (`9dba309`).** Performed by a marceline continuation agent. The Founder says mandates are not cancelled, so the substance stands, but the execution-location caveat must be recorded: the tally was not performed by a Phoebe seat.
4. **#299 revision.** Assigned to `openclaw@marceline-dev` (17:07Z). That assignment is now **stopped and unowned**. No Phoebe seat has picked it up.

## 3. Failure modes to guard against

- **H1 — False evidence transfer.** Treating marceline measurements as phoebe measurements. The marceline 12 MB reclamation and its df sample must not be cited as phoebe facts. (The observation series is now genuinely phoebe; the reclamation path remains unexercised on phoebe.)
- **H2 — Phantom live owners.** Records and board comments still list marceline agents as live owners of #298/#299. They are stopped. Any "in progress" claim attributed to them is stale.
- **H3 — Vacuum (partial).** The office observes phoebe, but the *legislation* (Act 12), the *#299 scope revision*, and any *meaningful cleanup* are unowned: the clerk is unresponsive since ~12:38Z and the marceline agents are stopped. Observation alone does not deliver #298/#299.
- **H4 — Recreating a government on marceline.** Do not delegate Viche work to marceline agents; the Founder explicitly forbids it.

## 4. Recommended Phoebe actions

1. **Re-measure on phoebe — already happening.** The office records hostname-tagged `phoebe-dev` observations every ~30 min via `boot.sh`. Real phoebe baseline (18:10Z): disk `/dev/nvme0n1p2` 243,990,876 KB total, 181,808,784 KB used (79%), ~49.7 GB free; inodes 31%; cgroup memory 4.14/8 GiB; Viche-owned roots town 4.8 MB + seats 4.7 MB + state 76 KB. Level `ok`. Continue and preserve this genuine series.
2. **Re-publish a revised Act 9 / Act 12** on phoebe, implementing #299 (mission vs jurisdiction; system-wide authority with evidence-based safeguards; see `records/JANITOR-SOVEREIGNTY-REVIEW.md`, J1–J8). The stale `b2a3eb0a…` bill must not be enacted.
3. **Re-verify or re-do** the Act 10 renewal enactment record by a Phoebe seat if any doubt remains; the substance is unchanged.
4. **Update live-ownership records** so no stopped marceline agent is treated as current.
5. **Do not** recreate a government on marceline or route Viche/Kawun work there.

## 5. What stands

- The Founder's substantive mandates (#298 Janitor Office, #299 sovereignty) remain in force; only the execution location and owners change.
- Founder directives #298/#299 are themselves valid (Antonina author `Vitalik`), independent of the constitutional deployment gap.
- The safe janitor subset (`reclaim_enabled=0`) remains safe to run on phoebe pending legislation.

---

*This is my independent assessment as seat c1a00005 (a Phoebe seat; this worktree is on `phoebe-dev`). It is a risk/evidence record, not a ballot.*
