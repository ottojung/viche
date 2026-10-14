#!/usr/bin/env bash
# Deterministic, seat-aware initial legislative tally. Ballots are public evidence;
# current board/Git credentials do NOT cryptographically authenticate each voter.
set -euo pipefail
[[ "$#" == 1 && "$1" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo "Usage: tally.sh BILL_ID" >&2; exit 2; }
town="${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}"
roster="$town/government/seats.tsv"
ballots="$town/records/ballots/$1.tsv"
rules="$town/government/voting.conf"
[[ -s "$roster" && -s "$ballots" && -f "$rules" ]] || { echo "Missing voting roster, rules, or ballots" >&2; exit 2; }
quorum="$(sed -n 's/^quorum=//p' "$rules")"
required="$(sed -n 's/^ayes=//p' "$rules")"
[[ "$quorum" =~ ^[1-9][0-9]*$ && "$required" =~ ^[1-9][0-9]*$ ]] || { echo "Invalid voting rules" >&2; exit 2; }
declare -A members=() voted=()
while IFS=$'\t' read -r id _; do
  [[ -n "$id" ]] || continue
  [[ ! -v 'members[$id]' ]] || { echo "Duplicate seat: $id" >&2; exit 2; }
  members["$id"]=1
done < "$roster"
(( quorum <= ${#members[@]} && required <= ${#members[@]} )) || { echo "Thresholds incompatible with current law/roster" >&2; exit 2; }
yes=0
no=0
abstain=0
while IFS=$'\t' read -r id vote digest extra; do
  [[ -n "$id" ]] || continue
  [[ -v 'members[$id]' && ! -v 'voted[$id]' && -n "$digest" && -z "${extra:-}" ]] || { echo "Invalid/duplicate/unknown ballot: $id" >&2; exit 2; }
  voted["$id"]=1
  case "$vote" in
    yes) ((++yes));;
    no) ((++no));;
    abstain) ((++abstain));;
    *) echo "Invalid vote: $vote" >&2; exit 2;;
  esac
done < "$ballots"
present=$((yes+no+abstain))
echo "Bill $1: present=$present yes=$yes no=$no abstain=$abstain (quorum=$quorum, required_yes=$required)"
if (( present >= quorum && yes >= required )); then echo "PASSED"; exit 0; fi
echo "NOT PASSED"; exit 1
