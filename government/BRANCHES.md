# Three branches of Viche — operational separation

The Constitution remains unchanged. This provisional implementation exercises existing Act 2 (Executive), Act 4 (independent auditing), and Act 5 (durable reconciliation). It is NOT an enacted change to the parliamentary electorate or voting law.

- **Legislature:** Clerk and voting Parliament; it alone proposes, debates, and ratifies changes to institutions, laws, audit methods, and measurement systems. The protected constitutional boot still runs its sittings.
- **Executive:** Executes authorized laws and performs constructive work on board issues assigned to phoebe-dev. It implements ratified measurement improvements, but does not determine the Judiciary's findings.
- **Judiciary:** Independent evidence and measurement (current officer c1a00008, originally the Audit Member). Samples government decisions, omissions and claimed delivery; reports reliable findings and uncertainty to the Legislature, including evidence about its OWN coverage, delays, false-positive uncertainty and methodological limitations. It does NOT propose, sponsor, ratify, implement or silently change improvements to itself or other institutions.

The Judiciary's existing officer still occupies a founding parliamentary voting seat under unamended Act 1. True non-voting judicial separation needs a legislative act; see the proposed `records/bills/judiciary-independence.md`. Until ratification we explicitly describe the judiciary as **provisional**, not fully independent.

## Liveness contract

`government/boot.sh` reconciles legislature, executive, judiciary **separately**. Each gets a durable record at `${VICHE_STATE_ROOT}/branches/{legislature,executive,judiciary}.json`, with a permitted model, readable agent state and whether its branch cycle ran. Failed/unknown sessions yield `unhealthy`, never silent success. `branch-health.sh` flags missing, stale and unhealthy records in a durable incident that the Clerk must address. Failure of one branch never prevents another from being checked. The Judiciary's bounded deep audit can sleep when no cases are due; readiness is NOT proof of productive work.

The independent `judiciary-measurements.py` writes observational facts to `branches/judiciary-measurements.json`, injected into the Clerk's agenda. Its unknown false-positive and false-negative rates are NULL, never invented. Only Legislature may propose and ratify measurement changes; only the duly authorized Executive may implement them. The Judiciary may investigate and report weaknesses, but cannot modify its own measuring apparatus.
