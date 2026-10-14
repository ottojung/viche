#!/usr/bin/env bash
# Parliament-editable seat reconciliation, invoked by the constitutional s6 supervisor.
# It MUST NOT start a separate scheduler or call OpenCode directly.
set -euo pipefail
town="${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}"
seats="${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}"
test -s "$town/government/LAWS.md"
test -s "$town/government/seats.tsv"
command -v antonina >/dev/null
mkdir -p "$seats"
git -C "$town" rev-parse --is-inside-work-tree >/dev/null
ids="$(mktemp)"
trap 'rm -f "$ids"' EXIT
while IFS=$'\t' read -r agent_id title focus; do
  [[ -n "$agent_id" ]] || continue
  [[ "$agent_id" =~ ^[0-9a-f]+$ ]] || { echo "Invalid seat ID: $agent_id" >&2; exit 1; }
  [[ -n "$title" && -n "$focus" ]] || { echo "Incomplete seat: $agent_id" >&2; exit 1; }
  echo "$agent_id" >> "$ids"
done < "$town/government/seats.tsv"
[[ -s "$ids" ]] || { echo "No parliamentary seats" >&2; exit 1; }
[[ "$(sort -u "$ids" | wc -l)" -eq "$(wc -l < "$ids")" ]] || { echo "Duplicate seat IDs" >&2; exit 1; }
while IFS=$'\t' read -r agent_id title focus; do
  [[ -n "$agent_id" ]] || continue
  seat_dir="$seats/$agent_id"
  if [[ ! -e "$seat_dir/.git" ]]; then
    if [[ -e "$seat_dir" && -n "$(ls -A "$seat_dir")" ]]; then echo "Unexpected seat directory: $seat_dir" >&2; exit 1; fi
    git -C "$town" worktree add --detach "$seat_dir" HEAD
  fi
  if ! antonina agent status --id "$agent_id" --json >/dev/null 2>&1; then
    antonina agent new --id "$agent_id" --cwd "$seat_dir" --title "Viche: $title"
  fi
done < "$town/government/seats.tsv"
