#!/bin/sh
# Act 19 §3.3 — per-office durable-commit-age signal (a measurement, not a quota).
#
# For each office, report the age (seconds) of the last durable commit on its
# branch while the office has uncommitted work. An office that has been failing
# without committing is visibly losing work instead of looking merely "busy".
# This is a weak proxy (commit recency != work preservation); the limitation is
# named here and in the Act.
#
# Emits one TSV row per office: office <TAB> last_commit_epoch <TAB> age_seconds
#   <TAB> uncommitted_count <TAB> worktree
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
now=$(date +%s)

for office in clerk executive judiciary innovation-centre; do
    case "$office" in
        clerk) wt=$seats/c1a00001 ;;
        *) wt=$seats/branches/$office ;;
    esac
    if [ ! -d "$wt/.git" ]; then
        printf '%s\t0\t%s\t%s\t%s\n' "$office" "$now" "-" "$wt"
        continue
    fi
    epoch=$(git -C "$wt" log -1 --format=%ct 2>/dev/null || printf '0')
    case "$epoch" in ''|*[!0-9]*) epoch=0 ;; esac
    if [ "$epoch" -eq 0 ]; then
        age="never"
    else
        age=$((now - epoch))
    fi
    uncommitted=$(git -C "$wt" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
    printf '%s\t%s\t%s\t%s\t%s\n' "$office" "$epoch" "$age" "$uncommitted" "$wt"
done
