#!/bin/sh
# Act 18 (Board Reporting Act) §7 — the board-trail index is GENERATED from the
# curated records/board-trail/originating.tsv mapping (NOT parsed from bill/LAWS
# prose, which mis-maps issues that bills cite as examples) plus the board's
# terminal-update check. Hermetic: mock board, scratch town.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
town=$scratch/town
mkdir -p "$town/government" "$town/records/board-trail" "$town/records/bills" "$scratch/bin"
cp "$repo/government/board-trail-index.py" "$town/government/"
cp "$repo/records/board-trail/originating.tsv" "$town/records/board-trail/"
cp "$repo/government/LAWS.md" "$town/government/"
cp "$repo"/records/bills/judiciary-independence.md "$repo"/records/bills/board-reporting-act.md "$town/records/bills/"

# Mock board: titles per issue; #312 has a terminal verification update, others do not.
# #303 carries a stage marker plus a PROSE MENTION of the terminal token: the §7
# declaration-position rule must reject it (regression for the §5/§7 false positive).
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
"board show")
  case "$*" in
    *"303"*) printf '{"title":"Three-branch legislation","messages":[{"author":"agent","body":"Stage marker: verification. We must not claim verification:confirmed in this prose sentence."}]}' ;;
    *"307"*) printf '{"title":"Innovation Centre","messages":[]}' ;;
    *"308"*) printf '{"title":"Epistemic Adversarialism","messages":[]}' ;;
    *"310"*) printf '{"title":"Detector Calibration Act","messages":[]}' ;;
    *"312"*) printf '{"title":"Board Reporting Act","messages":[{"author":"c1e00002","body":"Stage marker: verification. Terminal state verification:confirmed. Evidence records/ballots/board-reporting-act.tsv"}]}' ;;
    *) printf '{"title":"unknown","messages":[]}' ;;
  esac ;;
*) echo "unexpected mock: $*" >&2; exit 90 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
PATH="$scratch/bin:$PATH"
VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$scratch/state" python3 "$town/government/board-trail-index.py" >/dev/null

idx="$town/records/board-trail/index.json"
[ -s "$idx" ]

# Mapping comes from originating.tsv, not prose: #303 -> Act 15, #312 -> Act 18.
jq -e '.issues[] | select(.issue==303) | .work | test("Act 15")' "$idx" >/dev/null
jq -e '.issues[] | select(.issue==312) | .work | test("Act 18")' "$idx" >/dev/null
jq -e '.issues[] | select(.issue==308) | .work | test("Act 16")' "$idx" >/dev/null
# #310 is a draft: not enacted, terminal not_enacted, no git_only_gap.
jq -e '.issues[] | select(.issue==310) | .terminal_status=="enactment:not_enacted" and .git_only_gap==false' "$idx" >/dev/null
# Enacted laws without a terminal board update are git_only_gap (303/307/308).
jq -e '.issues[] | select(.issue==303) | .git_only_gap==true and .stage=="enactment"' "$idx" >/dev/null
jq -e '.issues[] | select(.issue==307) | .git_only_gap==true' "$idx" >/dev/null
# #312 has a terminal verification update -> not a gap, terminal confirmed.
jq -e '.issues[] | select(.issue==312) | .git_only_gap==false and .terminal_status=="verification:confirmed"' "$idx" >/dev/null
# Owning office: legislative items are Clerk-owned.
jq -e '.issues[] | select(.issue==303) | .owning_office=="Clerk"' "$idx" >/dev/null
# Titles come from the board.
jq -e '.issues[] | select(.issue==303) | .title=="Three-branch legislation"' "$idx" >/dev/null

echo 'Act 18 board-trail index smoke passed'
