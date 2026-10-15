#!/bin/sh
# The independent Audit Member investigates outcomes without Clerk or executive summons.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
root=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}/oversight
charter=${VICHE_CONSTITUTION:?authoritative Founder charter required}
now=${VICHE_OVERSIGHT_NOW:-$(date +%s)}
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
if [ -s "$root/incident.json" ]; then incident=yes; cadence=1800; fi
last=0
if [ -s "$root/last-audit-dispatch" ]; then last=$(cat "$root/last-audit-dispatch"); fi
case "$last" in ''|*[!0-9]*) last=0;; esac
[ $((now-last)) -ge "$cadence" ] || exit 0

evidence='No active incident; review sampled observations and seek blind spots.'
if [ "$incident" = yes ]; then evidence=$(cat "$root/incident.json"); fi
prompt=$(cat <<EOF
You are the independent Viche Audit Member under Act 4, accountable to
Parliament and the Founder, not to the executive or Clerk. Independently audit
whether Viche is making the Founder happier: quality of finished Kawun work,
timeliness, and conservation of Founder attention (Acts 8 and 9). Examine
actual Git changes, tests, merges, deployment, live owners and board issues.
An agent being alive or writing a report is NOT evidence of useful delivery.
Do not equate number of commits or a stale local main checkout with success.
Separate verified evidence, uncertainty, and mere leading indicators.

=== AUTHORITATIVE CONSTITUTION ===
$(cat "$charter")
=== END AUTHORITATIVE CONSTITUTION ===

Current deterministic watchdog evidence:
$evidence

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
