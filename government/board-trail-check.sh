#!/bin/sh
# Act 18 §5 — board-trail completeness cross-check (POSIX /bin/sh; no Bash).
#
# For each board-originated work item recorded in Git, this script confirms
# whether its originating Antonina issue carries a post-completion update that
# reaches a terminal state and/or a stage marker, and counts automated
# ("chatter") lines. Deterministic: the same board + Git inputs always yield
# the same output. It reports facts only; the independent Judiciary interprets
# them (Act 15 §2 — no reform proposals). Same-model / measurement-reliability
# limits are reported by the caller, not hidden.
#
# Output: one JSON object per line (JSONL) on stdout, one per originating
# issue, with classified fields. The caller (government/judiciary-measurements.py)
# aggregates the §5 metrics and records the honest limitations.
#
# Input mapping: records/board-trail/originating.tsv (Git). When the Executive's
# generated records/board-trail/index.json (Act 18 §3.8) exists it is the
# preferred input; this mapping is the fallback.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
map=$town/records/board-trail/originating.tsv
sep=$(printf '\t')
if [ ! -f "$map" ]; then
    echo "board-trail-check: no cross-check mapping at $map" >&2
    exit 1
fi

while IFS="$sep" read -r issue work act epoch type; do
    case "$issue" in ''|'#'*) continue ;; esac
    case "$epoch" in ''|*[!0-9]*) epoch=0 ;; esac
    page=1
    all='[]'
    while :; do
        data=$(antonina board show --id "$issue" --page "$page" --json) || {
            echo "board-trail-check: board query failed for #$issue" >&2
            exit 1
        }
        msgs=$(printf '%s' "$data" | jq -c '.messages // []')
        all=$(jq -n --argjson a "$all" --argjson b "$msgs" '$a + $b')
        n=$(printf '%s' "$msgs" | jq 'length')
        [ "$n" -lt 50 ] && break
        page=$((page + 1))
        [ "$page" -gt 20 ] && break
    done
    printf '%s\n' "$all" | jq -c \
        --arg issue "$issue" --arg work "$work" --arg act "$act" \
        --arg type "$type" --argjson epoch "$epoch" '
        def clean: (.createdAt // "") | sub("\\.[0-9]+Z$"; "Z");
        ($epoch | if . > 0 then todate else "" end) as $since |
        [ .[] | {a:(.author // ""), b:(.body // ""), t:clean} ] as $c |
        (if $epoch > 0 then ($c | map(select(.t > $since))) else $c end) as $p |
        ($p | map(.b)) as $pb |
        {
          issue: $issue, work: $work, act: $act, type: $type,
          enacted_epoch: $epoch,
          comments_total: ($c | length),
          post_completion: ($p | length),
          terminal: (if ([ $pb[] |
                         (test("(?i)stage\\s*marker[^\\n]{0,12}\\b(proposal|enactment|deployment|verification)\\b"))
                         and
                         (test("(?m)(^|[.:;—-]\\s*|(?i:state|status|terminal|result|outcome|transition)\\s+)(verification:confirmed|verification:blocked|enactment:not_enacted|deferred)([.\\s,;:]|$)"))
                       ] | any)
                    then 1 else 0 end),
          stage_markers: ([$pb[] | scan("(?i)stage\\s*marker[^\\n]{0,12}\\b(proposal|enactment|deployment|verification)\\b")[0]] | unique | join(",")),
          chatter: ($pb | map(select(test("\\[(scheduler-turn|terminal-handoff|progress-checkpoint)\\]"))) | length),
          latest_iso: (if ($c | length) > 0 then ($c | map(.t) | max) else "-" end)
        }'
done < "$map"
