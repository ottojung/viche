#!/bin/sh
# The independent Audit Member investigates outcomes without Clerk or executive summons.
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
id=c1a00008
[ -s "$charter" ] && [ -d "$seats/$id" ] || exit 1
[ -f "$root/observations.tsv" ] || exit 0
# Never dispatch a second run over a parliamentary sitting.
if grep -Fxq "$id" "$town/records/SUMMONED.txt" 2>/dev/null; then exit 0; fi
meta=$(antonina agent status --id "$id" --json)
kind=$(printf '%s\n' "$meta" | jq -r '.state')
case "$kind" in running|failed) exit 0;; idle|succeeded) :;; *) exit 1;; esac
model=$(printf '%s\n' "$meta" | jq -r '.model // empty')
variant=$(printf '%s\n' "$meta" | jq -r '.variant // empty')
[ "$model" = opencode-go/longcat-2.5-preview-free ] && [ "$variant" = low ] ||
    { echo 'Auditor: unauthorized model, refusing dispatch' >&2; exit 1; }

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
You are the independent Viche Audit Member under Act 4, accountable to
Parliament and the Founder, not to the executive or Clerk. Independently audit
whether Viche is making the Founder happier: quality of assigned work,
timeliness, and conservation of Founder attention (Acts 8 and 9). Examine
actual Git changes, tests, merges, deployment, live owners and board issues.
The sample is drawn from the board without executive cooperation. Auditing an
unassigned issue is not acquiring it for productive work.
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
findings and a practical correction with an owner. If necessary, call for a
parliamentary inquiry; the Clerk MUST consider active incidents at each sitting.
Check previous corrections after subsequent evidence and hold Parliament
accountable if it ignores the issue. Do not merely ask the executive whether
it thinks it is effective. Use Antonina and only its constitutionally allowed
free model. Never perform unrelated projects. This is an audit, not a vote.
EOF
)
antonina agent run --id "$id" --cwd "$seats/$id" --prompt "$prompt" --detach
printf '%s\n' "$now" > "$root/last-audit-dispatch"
printf '%s\t%s\taccepted_not_verified\n' "$now" "$incident" >> "$root/audit-dispatches.tsv"
