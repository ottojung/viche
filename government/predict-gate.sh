#!/bin/sh
# Act 22 §2 — pre-registration gate (POSIX /bin/sh; no Bash).
#
# No bill may reach the Act 16 §1 ballot gate, and no consequential order may
# take effect, unless the Clerk has recorded >=1 registered, evidence-linked
# prediction whose registration timestamp precedes the ballot/order timestamp.
# This is the deterministic gate the bill->vote path calls; it reports facts and
# exits non-zero on a refusal. It does not change quorum or voting rules.
#
# Scope (Act 22 §8 pilot): for the first measurement window the Act applies only
# to a named pilot subset — bills sponsored by the Innovation Centre and the
# Clerk, and the consequential orders the Clerk lists. The Clerk-owned list
# records/predictions/pilot.tsv names that subset. A bill not in the pilot list
# is out of scope and the gate passes ("not_exercised"); --all enforces the gate
# universally (for the post-pilot decision). If pilot.tsv is absent the gate
# fails closed (enforces every bill) so an unlisted bill cannot silently bypass
# the Act.
#
# Usage: predict-gate.sh [--all] [--at EPOCH] ID
#   --all       enforce for every bill/order, ignoring the pilot list
#   --at EPOCH  use EPOCH as the ballot/order timestamp (for consequential
#               orders with no ballots/<id>.tsv); default derives it from the
#               first commit that added records/ballots/ID.tsv, else now
#
# Exit: 0 pass (registered prediction precedes the ballot/order, or out of
#       pilot scope); 1 refuse (no qualifying prediction); 2 usage error.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
ledger=${VICHE_PREDICT_LEDGER:-$town/records/predictions/ledger.json}
pilot=$town/records/predictions/pilot.tsv

all=0
at=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --all) all=1; shift ;;
        --at) [ "$#" -ge 2 ] || { echo "predict-gate: --at needs a value" >&2; exit 2; }; at=$2; shift 2 ;;
        -h|--help) echo "usage: predict-gate.sh [--all] [--at EPOCH] ID" >&2; exit 0 ;;
        --) shift; break ;;
        -*) echo "predict-gate: unknown option: $1" >&2; exit 2 ;;
        *) break ;;
    esac
done
[ "$#" -eq 1 ] || { echo "usage: predict-gate.sh [--all] [--at EPOCH] ID" >&2; exit 2; }
id=$1
case "$id" in ''|*[!a-zA-Z0-9_.-]*) echo "predict-gate: invalid id: $id" >&2; exit 2 ;; esac

# --- pilot scope ---------------------------------------------------------
if [ "$all" -eq 0 ] && [ -f "$pilot" ]; then
    if ! awk -v want="$id" '!/^[[:space:]]*#/ && $0==want { found=1 } END { exit found?0:1 }' "$pilot"; then
        echo "predict-gate: PASS (not_exercised) $id — outside Act 22 §8 pilot scope"
        exit 0
    fi
fi
if [ "$all" -eq 0 ] && [ ! -f "$pilot" ]; then
    echo "predict-gate: REFUSE $id — pilot scope list missing" >&2
    exit 1
fi

# --- ballot/order timestamp ---------------------------------------------
if [ -n "$at" ]; then
    case "$at" in ''|*[!0-9]*) echo "predict-gate: invalid --at: $at" >&2; exit 2 ;; esac
    ballot_ts=$at
elif [ -f "$town/records/ballots/$id.tsv" ]; then
    ballot_ts=$(git -C "$town" log --diff-filter=A --format=%ct -- "records/ballots/$id.tsv" 2>/dev/null | awk 'NR==1 { print; exit }')
    case "$ballot_ts" in ''|*[!0-9]*) ballot_ts=$(date +%s) ;; esac
else
    ballot_ts=$(date +%s)
fi

[ -f "$ledger" ] || {
    echo "predict-gate: REFUSE $id — no ledger ($ledger); 0 registered predictions" >&2
    exit 1
}

# --- qualifying registered predictions ----------------------------------
# A qualifying prediction is a registration with a named evidence source and a
# registration timestamp strictly before the ballot/order timestamp.
count=$(jq --arg id "$id" --argjson ts "$ballot_ts" '
    [ .entries[]
      | select(.kind=="registration")
      | select(.status=="registered")
      | select(.bill_id==$id)
      | select((.evidence_source // "") != "")
      | select((.registered_at // 0) < $ts)
    ] | length' "$ledger" 2>/dev/null) || {
    echo "predict-gate: REFUSE $id — ledger unreadable" >&2; exit 1
}
case "$count" in ''|*[!0-9]*) echo "predict-gate: REFUSE $id — ledger unreadable" >&2; exit 1 ;; esac

if [ "$count" -ge 1 ]; then
    echo "predict-gate: PASS $id — $count registered evidence-linked prediction(s) precede $ballot_ts"
    exit 0
fi
echo "predict-gate: REFUSE $id — 0 registered evidence-linked predictions precede the ballot/order ($ballot_ts)" >&2
exit 1
