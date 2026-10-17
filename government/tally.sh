#!/bin/sh
# Vote tally using POSIX shell and awk, without associative arrays.
set -eu
[ "$#" -eq 1 ] || { echo "Usage: tally.sh BILL_ID" >&2; exit 2; }
case "$1" in ''|*[!a-zA-Z0-9_-]*) echo "Invalid bill ID" >&2; exit 2;; esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
roster=$town/government/seats.tsv
ballots=$town/records/ballots/$1.tsv
proposal=$town/records/bills/$1.md
rules=$town/government/voting.conf
[ -s "$roster" ] && [ -s "$ballots" ] && [ -s "$proposal" ] && [ -f "$rules" ] || {
    echo "Missing roster, ballots, proposed text, or voting rules" >&2; exit 2;
}
quorum=$(sed -n 's/^quorum=//p' "$rules")
required=$(sed -n 's/^ayes=//p' "$rules")
for n in "$quorum" "$required"; do
    case "$n" in ''|0|*[!0-9]*) echo "Invalid voting threshold" >&2; exit 2;; esac
done
digest=$(sha256sum "$proposal" | cut -d ' ' -f 1)
tab=$(printf '\t')
# Build set of all seats that have ever been in the roster (historical + current).
historical_seats=$(git -C "$town" log --all --format=%H -- government/seats.tsv 2>/dev/null | while read -r commit; do
    git -C "$town" show "$commit:government/seats.tsv" 2>/dev/null || true
done | cut -f1 | sort -u)
awk -F "$tab" -v quorum="$quorum" -v required="$required" -v digest="$digest" -v bill="$1" -v hist="$historical_seats" '
BEGIN {
    n = split(hist, arr, "\n")
    for (i = 1; i <= n; i++) if (arr[i]) hist_seats[arr[i]] = 1
}
FNR == NR {
    if (NF != 3 || $1 !~ /^[0-9a-f]+$/ || seen[$1]++) {
        bad=1; print "Invalid seat roster"; exit 2
    }
    seats++
    next
}
{
    if (NF != 3 || !($1 in hist_seats) || voted[$1]++ ||
        $3 != digest || ($2 != "yes" && $2 != "no" && $2 != "abstain")) {
        bad=1; print "Invalid, duplicate or mismatched ballot"; exit 2
    }
    counts[$2]++
    present++
}
END {
    if (bad) exit 2
    if (seats == 0 || quorum > seats || required > seats) {
        print "Invalid voting thresholds for roster"
        exit 2
    }
    printf "Bill %s: present=%d yes=%d no=%d abstain=%d (quorum=%d, required_yes=%d)\n", bill, present, counts["yes"], counts["no"], counts["abstain"], quorum, required
    if (present >= quorum && counts["yes"] >= required) {
        print "PASSED"
        exit 0
    }
    print "NOT PASSED"
    exit 1
}
' "$roster" "$ballots"
