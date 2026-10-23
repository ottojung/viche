#!/bin/sh
# Judiciary investigates outcomes without Clerk or Executive summons.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/oversight
charter=${VICHE_CONSTITUTION:?authoritative Founder charter required}
now=${VICHE_OVERSIGHT_NOW:-$(date +%s)}
mkdir -p "$root"
if [ "${VICHE_AUDIT_CHECKS:-1}" = 1 ]; then
  python3 "$town/government/audit-accountability.py" check > "$root/random-check.log" || exit 1
fi
id=$(/bin/sh "$town/government/appointments.sh" ensure judiciary)
[ -s "$charter" ] && [ -d "$seats/branches/judiciary" ] || exit 1
[ -f "$root/observations.tsv" ] || exit 0
# The Judiciary has its own durable officer; parliamentary summons never gate it.
meta=$(antonina agent status --id "$id" --json)
kind=$(printf '%s\n' "$meta" | jq -r '.state')
case "$kind" in running) exit 0;; failed) echo 'Judiciary: failed agent, independent recovery required' >&2; exit 1;; idle|succeeded) :;; *) exit 1;; esac

# Investigate an incident at least every half hour; also run independent
# broad audits at least once every six hours when there is no incident.
incident=no
cadence=21600
if [ -s "$root/incident.json" ] || [ -s "$root/random/incident.json" ]; then incident=yes; cadence=1800; fi
last=0
if [ -s "$root/last-audit-dispatch" ]; then last=$(cat "$root/last-audit-dispatch"); fi
case "$last" in ''|*[!0-9]*) last=0;; esac
[ $((now-last)) -ge "$cadence" ] || exit 0

evidence='No ordinary incident.'
[ ! -s "$root/incident.json" ] || evidence=$(cat "$root/incident.json")
[ ! -s "$root/random/incident.json" ] || evidence="$evidence $(cat "$root/random/incident.json")"
selection='Test-only no sample'
if [ "${VICHE_AUDIT_SELECTION:-1}" = 1 ]; then
  if [ "$incident" = yes ] && [ -s "$root/random/latest.json" ]; then
    selection=$(cat "$root/random/latest.json")
  else
    selection=$(python3 "$town/government/audit-selection.py") || exit 1
  fi
fi
prompt=$(cat <<EOF
You are the independent Viche Judiciary under Act 4, accountable to
Parliament and the Founder, not to the Executive or Clerk. Your sole role is
fact-finding, adjudication of sampled evidence, and reporting measurements
to the Legislature. Independently audit
whether Viche is making the Founder happier: quality of assigned work,
timeliness, and conservation of Founder attention (Acts 8 and 9). Examine
actual Git changes, tests, merges, deployment, live owners and board issues.
The sample is drawn from the board without executive cooperation. Auditing an
unassigned issue is not acquiring it for productive work.
For host compliance, distinguish Viche agent execution from GitHub Actions
verification. GitHub-hosted CI, including Lean and tests, is explicitly allowed.
Treat disabling CI solely due to agent host assignment as a policy mistake.
An agent being alive or writing a report is NOT evidence of useful delivery.
Do not equate number of commits or a stale local main checkout with success.
Separate verified evidence, uncertainty, and mere leading indicators.

=== AUTHORITATIVE CONSTITUTION ===
$(cat "$charter")
=== END AUTHORITATIVE CONSTITUTION ===

Current deterministic watchdog evidence:
$evidence
Randomized audit cases (bounded deep review):
$selection

For each sampled open issue, verify actual host assignment from its description
and latest Founder comments, then investigate unjustified neglect if assigned.
For sampled completed work verify delivery; for government decisions check
lawfulness and effect. Submit an evidence-backed verdict for EVERY sampled case
using $town/government/audit-accountability.py report with --case, --verdict
(verified, not_assigned, finding, inconclusive) and --evidence. Record a
finding for neglect or false delivery, not for a mere absence of information.
Use verified_fixed with new evidence only for later independent correction.

Inspect the complete, current ordinary laws at $town/government/LAWS.md and
oversight guidance at $town/government/OVERSIGHT.md.
Independently investigate adverse signals and limitations, publish reproducible
findings and measurement limitations for legislative consideration. Present findings, methods, sampling uncertainty, false positives, missing
measurements and the effectiveness of the Judiciary's OWN operations to the
Legislature. In particular distinguish lack of evidence from a clean result.
The Judiciary may request a parliamentary inquiry and may describe an
observed measurement weakness, but MUST NOT propose, sponsor, ratify or
implement reforms to measurement systems, audit algorithms, institutional
rules or its own operation. Reform proposals and ratification belong ONLY to
the Legislature; authorized implementation belongs to the Executive.
The Clerk MUST consider judicial evidence at every sitting.
Independently measure the effects of previously ratified corrections and report
the evidence, including failures of judicial measurement, to Parliament. Do not merely ask the executive whether
it thinks it is effective. Use Antonina-managed agents; model selection is Antonina's responsibility. Never perform unrelated projects. This is a judicial evidence review, not a legislative vote.
EOF
)
antonina agent run --id "$id" --cwd "$seats/branches/judiciary" --prompt "$prompt" --detach
printf '%s\n' "$now" > "$root/last-audit-dispatch"
printf '%s\t%s\taccepted_not_verified\n' "$now" "$incident" >> "$root/audit-dispatches.tsv"
