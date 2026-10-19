#!/bin/sh
# Act 18 (Board Reporting Act) §5/§7 — terminal-classifier alignment regression.
#
# A terminal update is a comment that carries a stage marker AND a DECLARED
# terminal state (§3.3/§3.4). Automated scheduler/agent status lines
# ([scheduler-turn], [terminal-handoff]) are NOT updates (§3.3.4), and a bare
# prose/quoted mention of a terminal token is not a declaration. The §5 lens
# (government/board-trail-check.sh) and the §7 generator
# (government/board-trail-index.py) MUST agree: a genuine declaration is
# terminal for both; a prose mention or an automated line is non-terminal for
# both. Hermetic: mock board + scratch town; no network, no live state.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
town=$scratch/town
mkdir -p "$town/government" "$town/records/board-trail" "$town/records/bills" "$scratch/bin"
cp "$repo/government/board-trail-check.sh" "$town/government/"
cp "$repo/government/board-trail-index.py" "$town/government/"
cp "$repo/government/LAWS.md" "$town/government/"
cp "$repo"/records/bills/judiciary-independence.md "$repo"/records/bills/board-reporting-act.md "$town/records/bills/"
cat > "$town/records/board-trail/originating.tsv" <<'MAP'
# fixture mapping
400	judiciary-independence	15	1000	law
401	innovation-centre-act	14	1000	law
402	epistemic-adversarialism-act	16	1000	law
403	board-reporting-act	18	1000	law
404	board-reporting-act	18	1000	law
MAP
# Mock board. 400 is a genuine declaration (control). 401/402 are automated
# status lines that carry a stage marker + terminal token; 403 is a prose
# mention; 404 is a prose mention with a stage marker. Only 400 may be terminal.
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
"board show")
  case "$*" in
  *"--id 400 "*) printf '%s\n' '{"title":"Three-branch legislation","messages":[{"author":"c","createdAt":"1970-01-01T00:20:00.000Z","body":"Stage marker: verification. verification:confirmed."}]}' ;;
  *"--id 401 "*) printf '%s\n' '{"title":"Innovation Centre","messages":[{"author":"openclaw","createdAt":"1970-01-01T00:20:00.000Z","body":"[terminal-handoff] Stage marker: verification. verification:confirmed."}]}' ;;
  *"--id 402 "*) printf '%s\n' '{"title":"Epistemic Adversarialism","messages":[{"author":"openclaw","createdAt":"1970-01-01T00:20:00.000Z","body":"[scheduler-turn] Stage marker: verification. verification:confirmed."}]}' ;;
  *"--id 403 "*) printf '%s\n' '{"title":"Board Reporting Act","messages":[{"author":"agent","createdAt":"1970-01-01T00:20:00.000Z","body":"We must not claim verification:confirmed in this prose sentence."}]}' ;;
  *"--id 404 "*) printf '%s\n' '{"title":"Board Reporting Act","messages":[{"author":"agent","createdAt":"1970-01-01T00:20:00.000Z","body":"Stage marker: verification. We must not claim verification:confirmed in this prose sentence."}]}' ;;
  *) printf '%s\n' '{"title":"unknown","messages":[]}' ;;
  esac ;;
*) echo "unexpected mock call: $*" >&2; exit 90 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
PATH="$scratch/bin:$PATH"
VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$scratch/state" VICHE_BRANCH_NOW=2000000000
export PATH VICHE_TOWN_ROOT VICHE_STATE_ROOT VICHE_BRANCH_NOW

sh "$town/government/board-trail-check.sh" > "$scratch/rows"
[ "$(wc -l < "$scratch/rows")" -eq 5 ]
# Control: a genuine declaration is terminal.
jq -e 'select(.issue=="400") | .terminal==1 and .stage_markers=="verification"' "$scratch/rows" >/dev/null
# Automated status lines carrying a stage marker + terminal token are NOT updates.
jq -e 'select(.issue=="401") | .terminal==0 and .chatter==1' "$scratch/rows" >/dev/null
jq -e 'select(.issue=="402") | .terminal==0 and .chatter==1' "$scratch/rows" >/dev/null
# Prose mentions are not declarations, with or without a stage marker.
jq -e 'select(.issue=="403") | .terminal==0 and .stage_markers==""' "$scratch/rows" >/dev/null
jq -e 'select(.issue=="404") | .terminal==0 and .stage_markers=="verification"' "$scratch/rows" >/dev/null

# §7 must agree with §5: only the genuine declaration is terminal; the rest are
# Git-only gaps (enacted in Git, no terminal board update).
VICHE_BOARD_TRAIL_NOW=1000 python3 "$town/government/board-trail-index.py" >/dev/null
idx="$town/records/board-trail/index.json"
[ -s "$idx" ]
jq -e '.issues[] | select(.issue==400) | .terminal_status=="verification:confirmed" and .git_only_gap==false' "$idx" >/dev/null
for n in 401 402 403 404; do
    jq -e --argjson n "$n" '.issues[] | select(.issue==$n) | .terminal_status==null and .git_only_gap==true' "$idx" >/dev/null
done

echo 'Act 18 board-trail terminal alignment smoke passed'
