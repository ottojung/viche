#!/bin/sh
# Aggregate objective branch readiness; failure mandates inquiry, not punishment.
set -eu
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
root=$state/branches
mkdir -p "$root"
now=${VICHE_BRANCH_NOW:-$(date +%s)}
max_age=${VICHE_BRANCH_MAX_AGE:-1800}
case "$now:$max_age" in *[!0-9:]*|:*|*:) exit 2;; esac
signals=
for branch in legislature executive judiciary; do
  path=$root/$branch.json
  if [ ! -s "$path" ]; then
    signals="${signals}${signals:+,}${branch}_missing"
    continue
  fi
  valid=$(jq -r --arg b "$branch" 'if .branch==$b and (.observed_at|type=="number") and
    (.readiness=="running" or .readiness=="ready" or .readiness=="unhealthy" or .readiness=="pending")
    then "yes" else "no" end' "$path" 2>/dev/null) || valid=no
  if [ "$valid" != yes ]; then
    signals="${signals}${signals:+,}${branch}_unreadable"
    continue
  fi
  at=$(jq -r '.observed_at' "$path")
  readiness=$(jq -r '.readiness' "$path")
  if [ "$at" -gt "$now" ] || [ $((now-at)) -gt "$max_age" ]; then
    signals="${signals}${signals:+,}${branch}_stale"
  elif [ "$readiness" = unhealthy ]; then
    signals="${signals}${signals:+,}${branch}_unhealthy"
  fi
done
# Mandatory legislative sub-institution. It is not a fourth government branch.
if [ -f "$state/inaugurated" ]; then
  innovation=$state/legislature/innovation-centre/health.json
  mode=legislative
  town=$(printenv VICHE_TOWN_ROOT || printf '%s\n' /var/lib/lubko/wd/viche)
  if grep -Eq '^## Act [0-9]+ — Executive Innovation Office Act \(enacted ' "$town/government/LAWS.md"; then
    innovation=$state/executive/innovation-office/health.json
    mode=executive
  fi
  if [ ! -s "$innovation" ]; then
    signals="${signals}${signals:+,}innovation_missing"
  else
    valid=$(jq -r --arg mode "$mode" '
      if .office=="innovation-centre" and .voting_seat==false and
         (($mode=="executive" and .executive_office==true and .legislative_branch==false and .controlled_by=="executive")
           or ($mode=="legislative" and .legislative_branch==true and .separate_summons==true)) and
         (.observed_at|type=="number") and (.last_dispatch_at|type=="number") and
         (.readiness=="running" or .readiness=="ready" or .readiness=="dispatched")
      then "yes" else "no" end' "$innovation" 2>/dev/null) || valid=no
    if [ "$valid" != yes ]; then
      signals="${signals}${signals:+,}innovation_unhealthy"
    else
      observed=$(jq -r '.observed_at' "$innovation")
      last=$(jq -r '.last_dispatch_at' "$innovation")
      mode=$(jq -r '.readiness' "$innovation")
      if [ "$observed" -gt "$now" ] || [ $((now-observed)) -gt "$max_age" ]; then
        signals="${signals}${signals:+,}innovation_stale"
      elif [ "$last" -eq 0 ] ||
        { [ "$mode" = ready ] && [ $((now-last)) -gt 28800 ]; }; then
        signals="${signals}${signals:+,}innovation_not_dispatched"
      fi
    fi
  fi
fi
# Monitoring is itself a fallible dependency: lack of positive evidence
# is evidence against declaring this town healthy.
evidence_age=${VICHE_EVIDENCE_MAX_AGE:-1200}
case "$evidence_age" in ''|*[!0-9]*) exit 2;; esac
fresh_evidence() {
  [ -s "$1" ] || return 1
  at=$(jq -er '.observed_at | select(type=="number" and .>=0)' "$1" 2>/dev/null) || return 1
  case "$at" in ''|*[!0-9]*) return 1;; esac
  [ "$at" -le "$now" ] && [ $((now-at)) -le "$evidence_age" ]
}
if ! command -v python3 >/dev/null 2>&1 ||
   ! python3 -c 'import json, pathlib' >/dev/null 2>&1; then
  signals="${signals}${signals:+,}python_runtime_unhealthy"
fi
for observation in "outcomes:$state/institutional-outcomes/latest.json" "institutional_cases:$state/institutional-cases/index.json" "judiciary_measurements:$state/branches/judiciary-measurements.json"; do
  evidence_name=${observation%%:*}
  evidence_path=${observation#*:}
  if ! fresh_evidence "$evidence_path"; then
    signals="${signals}${signals:+,}${evidence_name}_stale"
  fi
done
# Bind each health row to the durable evidence GENERATIONS it inspected, using
# each producer's own observation clock (key=epoch pairs). A new probe clock
# timestamp over unchanged producer observations is another check, not a new
# independent observation, so it must not close an institutional case.
# Deliberately excluded: institutional-cases/index.json, which reconciliation
# itself rewrites; including it would let our own bookkeeping manufacture a
# "new generation" without new underlying evidence.
if [ -z "$signals" ]; then
  evidence_signature=$(python3 - "$state" "${innovation:-}" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
innovation_arg = sys.argv[2] if len(sys.argv) > 2 else ""
sources = [
    ("leg", root / "branches/legislature.json"),
    ("exe", root / "branches/executive.json"),
    ("jud", root / "branches/judiciary.json"),
    ("out", root / "institutional-outcomes/latest.json"),
    ("meas", root / "branches/judiciary-measurements.json"),
]
if innovation_arg:
    sources.append(("inn", pathlib.Path(innovation_arg)))
parts = []
for key, path in sources:
    try:
        raw = path.read_bytes()
    except OSError:
        raise SystemExit(1)
    import json
    try:
        at = json.loads(raw).get("observed_at")
    except ValueError:
        raise SystemExit(1)
    if not isinstance(at, int) or at < 0:
        raise SystemExit(1)
    parts.append(f"{key}={at}")
print(",".join(parts))
PY
) || evidence_signature=
  case "$evidence_signature" in
    ''|*[!a-z0-9=,]*|*,|,*) signals="${signals}${signals:+,}health_evidence_unidentifiable" ;;
  esac
fi
# Unreviewed agent impediments are unresolved adverse evidence.
mailbox_dir="$state/oversight/judiciary-mailbox/inbox"
if [ -d "$mailbox_dir" ] &&
   [ -n "$(find "$mailbox_dir" -maxdepth 1 -type f -name '*.md' -print -quit 2>/dev/null)" ]; then
  signals="${signals}${signals:+,}judiciary_mailbox_pending"
fi
printf '%s\t%s\t%s\n' "$now" "${signals:-clear}" "${evidence_signature:-unavailable}" >> "$root/observations.tsv"
if [ -z "$signals" ]; then
  if [ -s "$root/incident.json" ]; then
    jq -c --argjson at "$now" '. + {cleared_at:$at,closure:"readiness_restored_not_delivery_verified"}' \
      "$root/incident.json" >> "$root/history.jsonl"
    rm -f "$root/incident.json"
  fi
  exit 0
fi
tmp=$(mktemp "$root/incident.XXXXXXXX")
jq -n --argjson at "$now" --arg s "$signals" \
  '{observed_at:$at,signals:($s|split(",")),
    assessment:"mandatory_branch_inquiry_not_proof_of_misconduct",
    caveat:"running_agent_not_proof_of_useful_work"}' > "$tmp"
mv -f "$tmp" "$root/incident.json"
echo "Viche: branch health inquiry: $signals" >&2
exit 1
