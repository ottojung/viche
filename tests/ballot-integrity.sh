#!/bin/sh
# Durable ballot-record integrity guard (POSIX /bin/sh, no network).
# Every non-quarantined records/ballots/<bill>.tsv must bind to an existing
# records/bills/<bill>.md by exact SHA-256 digest, name only seats from the
# current roster, cast only yes/no/abstain, and not duplicate a seat.
# Guards the durable vote record against stale, forged, mismatched or orphaned
# ballots -- a record-integrity defect class not covered by records-smoke.sh.
set -eu
root=$(git rev-parse --show-toplevel)
roster=$root/government/seats.tsv
bills=$root/records/bills
ballots=$root/records/ballots
tab=$(printf '\t')
failed=0

[ -s "$roster" ] || { echo "Missing seat roster" >&2; exit 1; }

for f in "$ballots"/*.tsv; do
    [ -f "$f" ] || continue
    case "$f" in "$ballots"/quarantine/*) continue ;; esac
    id=$(basename "$f" .tsv)
    bill=$bills/$id.md
    if [ ! -s "$bill" ]; then
        echo "Orphan ballot file without a bill: $f" >&2
        failed=1
        continue
    fi
    digest=$(sha256sum "$bill" | cut -d ' ' -f1)
    awk -F "$tab" -v digest="$digest" -v file="$f" '
        FNR == NR {
            if (NF != 3 || $1 !~ /^[0-9a-f]+$/ || seen[$1]++) {
                print "Invalid seat roster"; exit 2
            }
            seats[$1] = 1
            next
        }
        NF != 3 { print "Malformed ballot line in " file ": " $0; bad = 1; next }
        !($1 in seats) { print "Unknown seat in " file ": " $1; bad = 1 }
        voted[$1]++ { print "Duplicate seat in " file ": " $1; bad = 1 }
        $3 != digest { print "Digest mismatch in " file ": " $0; bad = 1 }
        ($2 != "yes" && $2 != "no" && $2 != "abstain") {
            print "Invalid vote value in " file ": " $2; bad = 1
        }
        END { if (bad) exit 1 }
    ' "$roster" "$f" || failed=1
done

if [ "$failed" -ne 0 ]; then
    echo "Ballot integrity check FAILED" >&2
    exit 1
fi
echo "Viche: durable ballot files bind to their bills and use only roster seats"
