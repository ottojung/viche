#!/bin/sh
# Executive dispatch is autonomous, safe under blocked/running states and model-pinned.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
mkdir -p "$scratch/bin" "$scratch/town/government" "$scratch/town/records" "$scratch/seats/b2000002" "$scratch/state"
printf 'a1000001\tClerk\tintake\nb2000002\tExecutive\tdelivery\n' > "$scratch/town/government/seats.tsv"
printf "Founder charter fixture\n" > "$scratch/charter"
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
set -eu
case "$1 $2" in
  "agent status") printf '{"state":"%s","model":"%s","variant":"%s"}\n' "$MODE" "$MODEL" "$VARIANT" ;;
  "agent run") case "$*" in *"Founder charter fixture"*) :;; *) exit 9;; esac; printf "accepted\n" >> "$OUTPUT" ;;
  *) exit 7 ;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
PATH=$scratch/bin:$PATH
VICHE_TOWN_ROOT=$scratch/town
VICHE_SEATS_ROOT=$scratch/seats
VICHE_STATE_ROOT=$scratch/state
VICHE_CONSTITUTION=$scratch/charter
MODE=idle MODEL=opencode-go/longcat-2.5-preview-free VARIANT=low
OUTPUT=$scratch/runs
export PATH VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION MODE MODEL VARIANT OUTPUT
/bin/sh "$repo/government/executive-cycle.sh"
[ ! -e "$OUTPUT" ]
touch "$scratch/state/inaugurated"
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 1 ]
grep -Fq "accepted" "$OUTPUT"
MODE=running; export MODE
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 1 ]
MODE=failed; export MODE
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 1 ]
MODE=idle MODEL=not-approved; export MODE MODEL
if /bin/sh "$repo/government/executive-cycle.sh"; then exit 1; fi
[ "$(wc -l < "$OUTPUT")" -eq 1 ]
MODEL=opencode-go/longcat-2.5-preview-free; export MODEL
printf "b2000002\n" > "$scratch/town/records/SUMMONED.txt"
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 1 ]
: > "$scratch/town/records/SUMMONED.txt"
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 2 ]
echo 'Executive cycle smoke checks passed'
