#!/bin/sh
# Act 32 clause 4 / amendment F -- Spying launch preflight (fail closed).
#
# Invokes the independent source-allowlist verifier and DENIES (non-zero exit)
# unless every source in the recorded Spying source-scope bundle validates.
# This gate never activates an office, publishes a message, contacts a private
# repository or reads a credential. A missing/malformed/unreadable allowlist,
# bundle or board API is a DENY, never a pass.
#
# Usage: spying-source-preflight.sh [TOWN_ROOT]
# Optional (all fail closed when absent):
#   VICHE_SPYING_ALLOWLIST  path to the committed allowlist
#   VICHE_SPYING_BOARD_JSON offline board snapshot (issue id -> board JSON)
#   VICHE_SPYING_BUNDLE     path to the source-scope bundle
#   VICHE_SPYING_NOW        fixed epoch for deterministic/replay runs
set -eu
town=${1:-${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
module=$town/government/spying_source_allowlist.py

if [ ! -s "$module" ]; then
  echo 'Spying preflight: allowlist verifier module missing' >&2
  exit 1
fi

set --
[ -z "${VICHE_SPYING_ALLOWLIST:-}" ] || set -- "$@" --allowlist "$VICHE_SPYING_ALLOWLIST"
[ -z "${VICHE_SPYING_BOARD_JSON:-}" ] || set -- "$@" --board-json "$VICHE_SPYING_BOARD_JSON"
[ -z "${VICHE_SPYING_BUNDLE:-}" ] || set -- "$@" --bundle "$VICHE_SPYING_BUNDLE"
[ -z "${VICHE_SPYING_NOW:-}" ] || set -- "$@" --now "$VICHE_SPYING_NOW"

if verdict=$(python3 "$module" preflight --town-root "$town" "$@" 2>&1); then
  denied=0
else
  denied=1
fi

# Durable, append-only audit of every preflight decision.
logdir=$state/knowledge/offices/spying
if mkdir -p "$logdir" 2>/dev/null; then
  printf '%s\n' "$verdict" >> "$logdir/source-preflight.jsonl" 2>/dev/null || :
fi

if [ "$denied" -eq 0 ]; then
  printf '%s\n' "$verdict"
  exit 0
fi
echo "Spying preflight DENIED (source scope unvalidated): $verdict" >&2
exit 1
