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
  "agent status")
    if [ "$MODE" = failed ]; then
      printf '{"state":"failed","model":"%s","variant":"%s","backend_error":{"classification":"upstream_endpoint_unavailable"}}\n' "$MODEL" "$VARIANT"
    else
      printf '{"state":"%s","model":"%s","variant":"%s"}\n' "$MODE" "$MODEL" "$VARIANT"
    fi
    ;;
  "agent run") case "$*" in *"Founder charter fixture"*) :;; *) exit 9;; esac; printf "accepted\n" >> "$OUTPUT" ;;
  "agent log") echo 'Endpoint is unavailable' ;;
  "agent delete") echo "delete" >> "$LIVENESS_ACTIONS" ;;
  "agent new") echo "new" >> "$LIVENESS_ACTIONS"; printf '{"state":"idle"}\n' > "$MOCK_STATUS" ;;
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
LIVENESS_ACTIONS=$scratch/liveness-actions
MOCK_STATUS=$scratch/mock-status
export PATH VICHE_TOWN_ROOT VICHE_SEATS_ROOT VICHE_STATE_ROOT VICHE_CONSTITUTION MODE MODEL VARIANT OUTPUT LIVENESS_ACTIONS MOCK_STATUS
: > "$LIVENESS_ACTIONS"
printf '{"state":"idle"}\n' > "$MOCK_STATUS"
cp "$repo/government/seat-liveness.sh" "$scratch/town/government/seat-liveness.sh"
git -C "$scratch/seats/b2000002" init -q
git -C "$scratch/seats/b2000002" -c user.name=test -c user.email=test@example.test commit --allow-empty -qm baseline
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
[ "$(wc -l < "$LIVENESS_ACTIONS")" -eq 2 ]
MODE=idle MODEL=not-approved; export MODEL MODE
if /bin/sh "$repo/government/executive-cycle.sh"; then exit 1; fi
[ "$(wc -l < "$OUTPUT")" -eq 1 ]
MODEL=opencode-go/longcat-2.5-preview-free; export MODEL
printf "b2000002\n" > "$scratch/town/records/SUMMONED.txt"
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 1 ]
: > "$scratch/town/records/SUMMONED.txt"
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 2 ]
MODE=failed; export MODE
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$OUTPUT")" -eq 2 ]
[ "$(wc -l < "$LIVENESS_ACTIONS")" -eq 2 ]
printf '%s\n' "$(date +%s)" > "$scratch/state/liveness/last-reset-b2000002"
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$LIVENESS_ACTIONS")" -eq 2 ]
printf '0\n' > "$scratch/state/liveness/last-reset-b2000002"
/bin/sh "$repo/government/executive-cycle.sh"
[ "$(wc -l < "$LIVENESS_ACTIONS")" -eq 4 ]
echo 'Executive cycle smoke checks passed'
