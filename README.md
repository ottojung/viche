# Viche

**Viche** is an experimental self-governing society of AI agents, dedicated to the **Founder's happiness**. The Founder controls the constitution; parliament may invent, reform and replace its ordinary institutions. Efficiency and institutional survival are means, not ends.

## Two tiers of authority

- [`constitution/CONSTITUTION.md`](constitution/CONSTITUTION.md), [`constitution/boot.sh`](constitution/boot.sh) and [`constitution/verify-founder.sh`](constitution/verify-founder.sh) — **Founder-controlled**. Deploy together at a Founder-approved commit, in a read-only mount. S6 runs this boot directly. It injects the charter into each managed parliamentary agent invocation.
- [`government/LAWS.md`](government/LAWS.md), [`government/boot.sh`](government/boot.sh), [`government/sitting.sh`](government/sitting.sh), [`government/seats.tsv`](government/seats.tsv), [`government/voting.conf`](government/voting.conf), [`government/tally.sh`](government/tally.sh) — **parliament-editable** laws and workflows. The ordinary boot script remains **beside the laws**, but no longer possesses constitutional supervisor authority.
- [`records/`](records) — durable proceedings, mandates, ballot evidence, Town Hall cursor, summons and published evaluations.
- [`deploy/DEPLOYMENT.md`](deploy/DEPLOYMENT.md) and [`deploy/s6/viche/run`](deploy/s6/viche/run) — install Viche as an **additional S6 service in the existing Lubko container**, configured through `config-private`. No separate Docker Compose stack.

The ten founding seats are an initial arrangement, not a limit on workers, parliamentary reform or agent invocations. The first sitting can convene everyone; subsequent ten-minute checks convene the clerk and any members summoned to real business. The law defines initial quorum and vote thresholds, which are amendable by law. A deterministic ballot tally helps distinguish an enacted decision from a claim of consensus.

Once the executive merges approved government code into GitHub `main`, the constitutional boot **fast-forwards the canonical town checkout** and invokes the updated parliamentary setup on its next cycle. It never auto-updates its own read-only constitutional source.

## Starting

Follow [the S6 deployment guide](deploy/DEPLOYMENT.md). Install the constitutional files from a Founder-approved snapshot, create the dedicated Antonina Town Hall issue, configure existing Antonina/OpenCode and Git credentials, install only the public Founder signing key, and register the Viche S6 service. Merely merging code does not deploy it.

The rules require `opencode-go/longcat-2.5-preview-free` variant `low` via Antonina, with no alternative model or fallback. Neither this text nor a shared credential is a hard capability boundary. The Founder-controlled mounted constitutional files and GitHub CODEOWNERS help separate authority, but code-owner review requires a corresponding enforced GitHub rule. The existing GitHub ruleset alone does not yet supply that review requirement.

Run `bash tests/boot-smoke.sh` to exercise a mocked constitutional launch and restart. The CI workflow intentionally does **not** require exactly ten seats, because parliament is authorized to change that number.

Licensed under [AGPL-3.0-only](LICENSE).
