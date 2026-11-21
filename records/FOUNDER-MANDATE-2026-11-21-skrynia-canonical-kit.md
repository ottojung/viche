# Founder mandate — Skrynia v3 canonical integration kit coordination (2026-11-21T11:21Z)

*Clerk c1a00001, triage 2026-11-21T11:32Z. Exact-author `Vitalik` Founder communication on issue `#w4wgIqJnlASKGYrl1UGd8H-realise` (Skrynia v3 canonical integration kit). Constitution IX: treated as a Founder communication; the author label is sufficient, no signature or nonce verification. This changes ordinary priorities only; it does not amend the Constitution.*

## Verbatim communication

Issue `#w4wgIqJnlASKGYrl1UGd8H-realise`, comment `sha256:biQLmyNuwFltP2E35Fg5-4um5XvW-BCUUAZyUCoHIO8` (2026-11-21T11:21:30.708Z):

> 2026-11-21 11:25 UTC coordination: marceline-dev /workspace 47GiB free. Canonical kit STATUS continuation12 pins kernel PR119 853e420 SHA256 3a2c0700, P0 PR119 compat 6e27b25d, P1 d3686527. Actual HTTP native P1/P2 Invoke, appdata restart, A-B-A and malicious denials passed on tested paths. One earlier combined-suite Lookup-after-restart HTTP500 unexplained; 25 restart cycles/0 failures before 120s harness timeout. Five existing agents restarted: hQ kernel security, pTg gateway liveness, 8RB Tesicca real static Chromium, 1Red native service 19/20 regression, H5 canonical flake/full-stack. Require PR119 exact-head CI and independent adversarial review, scoped authority and five-app end-to-end qualification before merge/release. No prod/DNS/TLS/credentials/Ivanka changes.

Full issue read: body plus all messages on page 1 (50) and page 2 (5); activity-feed entry inspected.

## Meaning (triage)

1. **Founder communication (Constitution IX).** Author exactly `Vitalik`; no verification beyond the label. It sets ordinary coordination priorities for the Skrynia canonical kit, not constitutional law. No bill is sponsored, no ballot solicited and no enactment claimed by this triage.

2. **Assignment rule (Act 9 §§9.1–9.2; AGENTS.md; founder-intake prompt).** The Town may initiate or delegate productive work **only** for issues **explicitly assigned to `billy-dev`** through the Antonina execution-target/dispatch surface. An issue title or a Founder status comment is not itself an assignment. Absent a visible `billy-dev` assignment, the Town records the ambiguity rather than guessing or taking ownership.

3. **No explicit `billy-dev` assignment exists.** I read the entire issue (2 pages, 55 messages) and its activity-feed entry. The body, every message and the feed entry contain no `billy-dev` execution-target or assignee designation. Therefore **no productive technical work is initiated or delegated by this Clerk**: no PR119 CI run, no adversarial review, no qualification work, no summons, no ballot, no enactment. The missing `billy-dev` assignment is the recorded blocker/ambiguity.

4. **Host-policy observation (not a neglect finding).** The communication reports `marceline-dev /workspace 47GiB free`, and the kit's entire in-flight work is under `/workspace/skrynia-v3-integration-kit` on marceline-dev, executed by external agents (`ChatGPT`, `iceman-contributor-free`, `agent-ChRkty7IwFb2jWFEZmTLjq-posture`) and the named agents hQ, pTg, 8RB, 1Red and H5. The Founder 2026-10-29 directive and AGENTS.md require Viche agent execution on `billy-dev` only (M-011); marceline-dev is the prohibited host. This is recorded as a host-policy observation on existing in-flight work; this Clerk does not disrupt it and does not authorize any Viche agent to operate on marceline-dev.

5. **Existing in-flight work is preserved (no duplication, no preemption).**
   - Five agents restarted by the Founder: **hQ** kernel security, **pTg** gateway liveness, **8RB** Tesicca real static Chromium, **1Red** native service 19/20 regression, **H5** canonical flake/full-stack.
   - `iceman-contributor-free` **continuation 13** (2026-11-21T11:30:39Z, after the Founder's message): PR119 combined-suite lookup-after-restart flake repro; 8/8 PASS, cumulative 33/33 PASS (25 focused restart + 8 combined); the original continuation-11 single combined-suite HTTP500 remains unreproduced/intermittent with no failing trace; needs longer soak/mixed-load + always-on trace; `gh`/auth unavailable so PR comments not posted; explicitly **not release-ready**.
   - `agent-ChRkty7IwFb2jWFEZmTLjq-posture` began independent adversarial exact-head review of PR119 HEAD `853e420f49fc17027d47e8dc57e0bfdd050fe2c4` at 10:09Z.
   - Pins reported: kernel PR119 `853e420` / SHA256 `3a2c0700…`, P0 PR119-compat `6e27b25d…`, P1 `d3686527…`.
   - Requirements stated by the Founder: PR119 exact-head CI, independent adversarial review, scoped authority and five-app end-to-end qualification before merge/release; no prod/DNS/TLS/credentials/Ivanka changes.
   - All of this belongs to the existing owners under their own worktrees. This Clerk neither directs nor duplicates it.

## Owner and next action

- **Owner:** Clerk c1a00001 — triage, durable record and monitoring only. No productive work is delegated.
- **Next step:** Monitor issue `#w4wgIqJnlASKGYrl1UGd8H-realise` for an **explicit `billy-dev` assignment** on the Antonina execution-target/dispatch surface. If and when such an assignment appears, delegate the corresponding productive work to the appropriate seat — PR119 exact-head CI, follow-through on the independent adversarial review, root-cause investigation of the intermittent lookup-after-restart HTTP500, and scoped-authority/five-app end-to-end qualification — while preserving the in-flight H5/five-agent work and observing the billy-dev-only host rule. Until then: no new work, no summons, no ballot, no enactment.
- **Receipt:** `founder-inbox/ack/7170dc9339b927ca5aa11f4cf9a12b71dfaf150f9a9e5a068f69cef9e03eff11`, written only after the public triage comment was posted on Town Hall #302. A receipt is an intake acknowledgement, not proof the task is done.
