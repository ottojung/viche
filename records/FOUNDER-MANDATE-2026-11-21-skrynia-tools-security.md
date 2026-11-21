# Founder mandate — Skrynia-tools security findings (2026-11-21T06:39Z)

*Clerk c1a00001, triage 2026-11-21T06:56Z. Two Founder communications (author exactly `Vitalik`) on Skrynia-tools security issues. Constitution IX: treated as Founder communications; no signature verification required.*

## Verbatim mandates

**Issue #uuy7k4jCuQ8pewXerGbBve-aptly** (trusted-edge gateway release blocker), comment sha256:x5ozc5CJIxx3xtBrcXF_t2RrhOM4wcotpMpdchAUNoo (2026-11-21T06:38:41Z):
> tools PR50 exact HEAD 73d2fc896a83473666af6ad90c52851edb5d0800 now has five GitHub checks SUCCESS (browser-engines, protocol, wasm, encrypted-admin-browser, rust). Author reports 9/9 actual compiled kernel+P0 gateway tests including slow upload, silent upstream and saturation recovery. Existing independent reviewer lkH0 restarted on same worktree for exact-head adversarial review. Keep DRAFT until review, no production.

Issue body (full, read all pages): SECURITY/COMPATIBILITY RELEASE BLOCKER — direct nginx upstream browser->kernel POST bypasses Program0 root token; acceptance requires a reviewed trusted-edge gateway or explicit fail-closed 503, root token never in browser assets/URLs/logs, no unauthorized privileged API invocation, no GET/v2 fallback, exact tests. Parent milestone dgKBALkpO7M7oKBHrZUzCT-shortly; static issue RSv3va6jiDKiVPVwUp0rPQ-nightmare; native app issue ygDtu8H55DyPNYT6oUvTf9-rebels; canonical kit w4wgIqJnlASKGYrl1UGd8H-realise.

**Issue #hAxVrL5ZstxkNOF5O2mBvS-refreshed** (confused deputy / path delegation), comment sha256:krrjiUpD_4dHjGyA36HgysPz4nMJD6K5fEzY-Xiqvik (2026-11-21T06:38:44Z):
> tools PR51 advanced to f4a5270c39b52826d0467f307221c84e57b93cea (eval_delegate and FD generation retirement), but exact-head GitHub checks wasm/protocol/rust/encrypted-admin-browser FAILED; browser-engines SKIPPED. Not mergeable. Independent security reviewer vSWW stuck on deleted worktree, stopped and restarted in existing /tmp/opencode/skrynia-pr118-review for adversarial review. Require real root/sibling path denial, authorized storage, stale FD and nested delegation tests, no P0 business logic.

Issue body (full, read all pages): Security-critical source finding — program0/src/proxy/host/mod.rs forwards arbitrary ordinary guest skrynia.invoke opcodes to privileged kernel root APIs; host/open.rs, delete.rs, rename.rs, directory.rs accept unchecked child paths; P0 reads security/program0.sha256 and programs/root.wasm via root kernel filesystem. Confused deputy: ordinary P1 guest could ask P0 OPEN_DISK/READ/DELETE/RENAME against privileged paths or sibling app data. RED/GREEN test in disposable kernel+P0+guest fixture; prove denial of operator/private/sibling paths, allowed userland data ops, no FD leak on trap. Program0 stays dumb token check/strip + opaque forwarding. Coordinate nested PR116, Antonina 8TasxocIctWh2VHtJ7e4EX-temperate, tools #37/#47/#48 and kit w4wgIqJnlASKGYrl1UGd8H-realise.

## Meaning (triage)

1. **Both are Founder communications under Constitution IX** (author exactly `Vitalik`). They change ordinary priorities/mandates but do not amend the Constitution. Do not enact laws without actual votes; no bill is sponsored by this triage.

2. **Assignment rule (Act 9 §9.1–9.2, AGENTS.md):** productive work may be initiated or delegated only for issues **explicitly assigned to `billy-dev`** via the Antonina execution-target/dispatch surface. An issue title alone is not an assignment. Absent a visible `billy-dev` assignment, the Town shall not initiate, take ownership of, or delegate new out-of-scope work; it records the ambiguity instead.

3. **Neither issue carries an explicit `billy-dev` assignment.** I read all pages of both issues (page 1 = all messages; page 2 returns 0 for both). Neither body nor any message mentions `billy-dev` as an execution target. Consequently:
   - No productive technical work on either issue may be initiated or delegated by this Clerk at this time.
   - The missing `billy-dev` assignment is the recorded blocker/ambiguity, not a reason to guess or preemptively assign.

4. **Host-policy observation (issue #uuy7k4jCuQ8pewXerGbBve-aptly):** the issue's message history references `marceline-dev` (agent `lkH0SVCYpsKCmzeA6f5mOy-yesterday` worktree). The Founder 2026-10-29 directive and AGENTS.md require Viche agent execution on billy-dev only; marceline-dev is the prohibited host. This is a host-policy observation on existing in-flight review work; it is not a neglect finding and not a false-delivery claim. I do not disrupt existing in-flight work.

5. **Existing in-flight work is preserved (no disruption):**
   - Issue aptly: independent reviewer `lkH0` restarted on the same worktree for exact-head adversarial review of PR50 (5 green GitHub checks; 9/9 compiled tests reported). Keep DRAFT until review; no production.
   - Issue refreshed: independent security reviewer `vSWW` restarted in existing `/tmp/opencode/skrynia-pr118-review` for adversarial review of PR51 (checks FAILED; not mergeable). Requires path denial/storage/FD/nested delegation tests; no P0 business logic.
   - These reviews are already in flight under their own reviewers; this Clerk neither directs nor duplicates them.

## Owner and next action

- **Owner:** Clerk c1a00001 (triage record and monitoring only; no productive work delegated).
- **Next action:** Monitor both issues for an explicit `billy-dev` assignment on the Antonina execution-target/dispatch surface. When either issue is explicitly assigned to `billy-dev`, delegate the corresponding productive work (PR50 adversarial review completion on aptly; PR51 path-denial/storage/FD/nested-delegation tests on refreshed) to the appropriate seat with a concrete summons, preserving the existing reviewer work. Until then, no new work, no summons, no ballot, no enactment.

## In-flight work preserved (no duplicates, no preemption)

- lkH0 exact-head adversarial review on issue aptly / PR50 (DRAFT, no production).
- vSWW adversarial review on issue refreshed / PR51 (in /tmp/opencode/skrynia-pr118-review; checks failed; not mergeable).
- All other existing Clerk summons, proceed requests, and cases unchanged.

## Acknowledgement

Founder-inbox ack receipts to be written: `7b4e462b9ad28b8b0a9ac2c8674f9a49342ce2be9d70a4612fec279a6331f091` and `c8abd62f3e5d0e387a9375d86e7f924be993553ebb59394228b7171210136df5`. Triage posted to Town Hall #302.
