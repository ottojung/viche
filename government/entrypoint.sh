#!/usr/bin/env bash
# Executed when the Viche container starts. This file is parliament-editable.
set -euo pipefail
town="${VICHE_TOWN_ROOT:-/town}"
interval="${VICHE_SITTING_INTERVAL_SECONDS:-600}"
[[ "$interval" =~ ^[1-9][0-9]*$ ]] || { echo "invalid sitting interval" >&2; exit 1; }
trap 'echo "Viche: container stopping"; exit 0' TERM INT

# A failure is visible, not silently "recovered" by selecting a different model.
if ! bash "$town/government/boot.sh"; then
  echo "Viche: first bootstrap/sitting failed; will retry on next interval" >&2
fi
while :; do
  sleep "$interval" & wait "$!" || exit 0
  if ! bash "$town/government/boot.sh"; then
    echo "Viche: bootstrap/sitting failed; keeping supervisor alive for repair" >&2
  fi
done
