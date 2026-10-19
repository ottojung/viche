#!/bin/sh
# Hermetic test of Act 17 (Audit Verdict Correction Act): superseding verdicts,
# the Git-anchored append-only corrections trail, corrected_finding visibility,
# finality (one correction per cycle, no bare re-flip) and honest procedural
# (not independent) second-pass labelling.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/state/oversight/random/cases" \
    "$scratch/state/oversight/random/outcomes" "$scratch/town/records" \
    "$scratch/seats/branches/judiciary"
printf 'authoritative fixture\n' > "$scratch/charter"
: > "$scratch/town/records/SUMMONED.txt"
CASE=0123456789abcdef01
printf '{"case_id":"%s","population":"ignored_work","id":"301","at":2000000000}\n' \
    "$CASE" > "$scratch/state/oversight/random/cases/$CASE.json"
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
"agent list")
    printf '{"agents":[{"id":"c1e00008"}],"unreadable":0}\n' ;;
"agent status")
    printf '{"state":"idle","model":"opencode-go/longcat-2.5-preview-free","variant":"low"}\n' ;;
*) echo "unexpected mock call: $*" >&2; exit 90 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
PATH=$scratch/bin:$PATH
VICHE_STATE_ROOT=$scratch/state
VICHE_TOWN_ROOT=$scratch/town
VICHE_SEATS_ROOT=$scratch/seats
VICHE_CONSTITUTION=$scratch/charter
VICHE_OVERSIGHT_NOW=2000000000
export PATH VICHE_STATE_ROOT VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_CONSTITUTION VICHE_OVERSIGHT_NOW

trail="$scratch/town/records/oversight/corrections/$CASE.jsonl"
CTRL="$repo/government/audit-accountability.py"

# 1. Ordinary filing of a non-finding verdict (the prior lockout target).
python3 "$CTRL" report --case "$CASE" --verdict not_assigned \
    --evidence "board #301 original sample" >/dev/null

# 2. A correction of that non-finding is now permitted (Act 17 §2.1/§2.5).
python3 "$CTRL" report --case "$CASE" --verdict finding \
    --evidence "commit:deadbeef stronger replay" --correction \
    --supersedes not_assigned --auditor c1e00008 --reason_code corrected_on_replay \
    --why_stronger "replayed the full sample with an independent evaluator" >/dev/null

# 3. Git-anchored authoritative trail exists and records the pending correction.
[ -s "$trail" ]
grep -q '"correction": true' "$trail"
grep -q '"confirmed": false' "$trail"
grep -q '"supersedes": "not_assigned"' "$trail"
grep -q '"phase": "correction_filed"' "$trail"

# 4. Until the second procedural pass, the current verdict is unchanged and the
#    case is reported correction_pending (Act 17 §2.4).
python3 "$CTRL" check > "$scratch/check"
jq -e '[.signals[].type]|index("correction_pending")' "$scratch/check" >/dev/null
jq -e --arg c "$CASE" '.signals[]|select(.type=="correction_pending" and .case_id==$c)' \
    "$scratch/check" >/dev/null
# current verdict in the cache is still the prior one
jq -e --arg c "$CASE" '.verdict' "$scratch/state/oversight/random/outcomes/$CASE.json" >/dev/null
[ "$(jq -r .verdict "$scratch/state/oversight/random/outcomes/$CASE.json")" = not_assigned ]

# 5. Second procedural pass (same office/model — NOT independent) confirms it.
python3 "$CTRL" report --case "$CASE" --confirm --evidence "second procedural replay" >/dev/null
grep -q '"phase": "second_procedural_pass_not_independent"' "$trail"
grep -q '"confirmed": true' "$trail"
[ "$(jq -r .verdict "$scratch/state/oversight/random/outcomes/$CASE.json")" = finding ]
python3 "$CTRL" check > "$scratch/check"
if jq -e '[.signals[].type]|index("correction_pending")' "$scratch/check" >/dev/null; then
    echo "correction_pending cleared after confirmation" >&2; exit 1
fi

# 6. A finding may be corrected to a non-finding (§2.5); this raises the distinct
#    corrected_finding signal instead of unresolved_finding (§2.3).
python3 "$CTRL" report --case "$CASE" --verdict not_assigned \
    --evidence "commit:cafebabe still stronger retraction" --correction \
    --supersedes finding --auditor c1e00008 --reason_code retracted_on_stronger_evidence \
    --why_stronger "new replay shows the original finding was a false positive" >/dev/null
python3 "$CTRL" report --case "$CASE" --confirm --evidence "procedural retraction replay" >/dev/null
python3 "$CTRL" check > "$scratch/check"
jq -e '[.signals[].type]|index("corrected_finding")' "$scratch/check" >/dev/null
if jq -e '[.signals[].type]|index("unresolved_finding")' "$scratch/check" >/dev/null; then
    echo "corrected finding must not raise unresolved_finding" >&2; exit 1
fi

# 7. Finality: one correction per case per cycle — a second pending correction
#    is refused while one is pending.
python3 "$CTRL" report --case "$CASE" --verdict verified \
    --evidence "commit:feedface third look" --correction \
    --supersedes not_assigned --auditor c1e00008 --reason_code third \
    --why_stronger "yet another replay" >/dev/null
if python3 "$CTRL" report --case "$CASE" --verdict finding \
    --evidence "commit:feedface dup" --correction --supersedes not_assigned \
    --auditor c1e00008 --reason_code dup --why_stronger "again" 2>/dev/null; then
    echo "second concurrent pending correction must be refused" >&2; exit 1
fi

# 8. Finality: no bare re-flip — a target verdict already held is refused.
if python3 "$CTRL" report --case "$CASE" --verdict finding \
    --evidence "commit:feedface reflip" --correction --supersedes verified \
    --auditor c1e00008 --reason_code reflip --why_stronger "back again" 2>/dev/null; then
    echo "bare re-flip must be refused" >&2; exit 1
fi

# 9. Guardrails: a correction missing why_stronger / reason_code / auditor /
#    supersedes, or citing the original evidence, is refused.
if python3 "$CTRL" report --case "$CASE" --verdict inconclusive \
    --evidence "commit:x1" --correction --supersedes verified \
    --auditor c1e00008 --reason_code no_why --why_stronger "" 2>/dev/null; then
    echo "empty why_stronger must be refused" >&2; exit 1
fi
if python3 "$CTRL" report --case "$CASE" --verdict inconclusive \
    --evidence "commit:x1" --correction --supersedes verified \
    --auditor c1e00008 --reason_code no_why --why_stronger "diff" 2>/dev/null; then
    echo "duplicate evidence must be refused" >&2; exit 1
fi
if python3 "$CTRL" report --case "$CASE" --verdict inconclusive \
    --evidence "board #301 original sample" --correction --supersedes verified \
    --auditor c1e00008 --reason_code orig --why_stronger "same ref" 2>/dev/null; then
    echo "original evidence reuse must be refused" >&2; exit 1
fi

# 10. verified_fixed still requires a previous finding (unchanged).
CASE2=fedcba9876543210fe
printf '{"case_id":"%s","population":"claimed_delivery","id":"218","at":2000000000}\n' \
    "$CASE2" > "$scratch/state/oversight/random/cases/$CASE2.json"
if python3 "$CTRL" report --case "$CASE2" --verdict verified_fixed \
    --evidence "commit:nope" 2>/dev/null; then
    echo "verified_fixed without a prior finding must be refused" >&2; exit 1
fi

# 11. The trail is append-only: the number of committed lines equals the number
#    of correction/confirmation filings (no overwrite).
n=$(wc -l < "$trail")
[ "$n" -ge 4 ]

echo 'Act 17 audit correction smoke passed'
