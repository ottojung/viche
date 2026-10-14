#!/usr/bin/env bash
# End-to-end mocked S6 constitutional boot, without network or real models.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
scratch="$(mktemp -d)"
cleanup() {
  if [[ -d "$scratch/seats" ]]; then
    for dir in "$scratch"/seats/*; do
      [[ -e "$dir/.git" ]] && git -C "$root" worktree remove --force "$dir" >/dev/null 2>&1 || true
    done
  fi
  rm -rf "$scratch"
}
trap cleanup EXIT
mkdir -p "$scratch/bin" "$scratch/seats" "$scratch/state" "$scratch/mock"
cat > "$scratch/bin/antonina" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
[[ "$1" == agent ]] || exit 91
command="$2"; shift 2
id='' prompt=''
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --id) id="$2"; shift 2;;
    --cwd|--title) shift 2;;
    --prompt) prompt="$2"; shift 2;;
    --json|--detach) shift;;
    *) echo "Unexpected Antonina flag $1" >&2; exit 92;;
  esac
done
[[ -n "$id" ]] || exit 93
case "$command" in
  status) [[ -e "$MOCK_STATE/$id" ]] || exit 3; echo '{"state":"idle"}';;
  new) [[ ! -e "$MOCK_STATE/$id" ]] || exit 4; touch "$MOCK_STATE/$id"; echo "$id" >> "$MOCK_STATE/created";;
  run)
    [[ -e "$MOCK_STATE/$id" ]] || exit 5
    [[ "$prompt" == *"=== AUTHORITATIVE CONSTITUTION ==="* ]] || exit 6
    [[ "$prompt" == *"opencode-go/longcat-2.5-preview-free"* ]] || exit 7
    echo "$id" >> "$MOCK_STATE/ran";;
  *) exit 94;;
esac
MOCK
chmod +x "$scratch/bin/antonina"
export MOCK_STATE="$scratch/mock"
export PATH="$scratch/bin:$PATH"
export VICHE_TOWN_ROOT="$root"
export VICHE_SEATS_ROOT="$scratch/seats"
export VICHE_STATE_ROOT="$scratch/state"
export VICHE_TEST_NO_SYNC=1
export VICHE_TOWNHALL_ID=999
seat_count="$(grep -Ec '^[0-9a-f]+[[:space:]]' "$root/government/seats.tsv")"
(( seat_count >= 1 ))
bash "$root/constitution/boot.sh" --once
[[ "$(wc -l < "$scratch/mock/created")" -eq "$seat_count" ]]
[[ "$(wc -l < "$scratch/mock/ran")" -eq "$seat_count" ]]
bash "$root/constitution/boot.sh" --once
[[ "$(wc -l < "$scratch/mock/created")" -eq "$seat_count" ]]
[[ "$(wc -l < "$scratch/mock/ran")" -eq $((seat_count + 1)) ]]
echo "Viche: $seat_count seats initialized, constitutional prompt injected, subsequent sitting summons clerk only"
