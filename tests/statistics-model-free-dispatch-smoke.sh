#!/bin/sh
# Act 33 deterministic Statistics must not dispatch managed agents.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
mkdir -p "$d/town/government" "$d/town/records/knowledge" "$d/bin"
cp "$repo/government/knowledge-office-cycle.sh" "$d/town/government/"
printf '#!/bin/sh\n[ "$1" = statistics ]\n' > "$d/town/government/knowledge-activation-verify.sh"
printf '%s\n' '## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)' \
  '## Act 33 — Prospective Statistics Trial Clarification (enacted 2026-11-22)' > "$d/town/government/LAWS.md"
printf '%s\n' '{"offices":{"statistics":{"trial_mode":"deterministic-v1"}}}' > "$d/town/records/knowledge/activation.json"
cat > "$d/bin/antonina" <<'STUB'
#!/bin/sh
echo wrong-agent-dispatch >> "$DISPATCH_LOG"
exit 99
STUB
chmod +x "$d/bin/antonina"
export DISPATCH_LOG="$d/agent.log"
VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$d/town/government/knowledge-office-cycle.sh" statistics
test ! -e "$d/agent.log" || { echo 'FAIL: deterministic trial launched an agent' >&2; exit 1; }
# The no-agent path must only be available for the exact Act33+mode pair.
sed -i '/Act 33/d' "$d/town/government/LAWS.md"
VICHE_TOWN_ROOT="$d/town" VICHE_STATE_ROOT="$d/state" \
  PATH="$d/bin:$PATH" /bin/sh "$d/town/government/knowledge-office-cycle.sh" statistics >/dev/null 2>&1 || :
test ! -e "$d/agent.log" || { echo 'FAIL: old-law fallback called agent under missing baseline' >&2; exit 1; }
# Verify that boot dispatch includes both the bounded runner and independent
# activation guard; never rely on reporting output alone.
grep -q 'statistics-bounded-trial.py' "$repo/government/boot.sh"
grep -q 'knowledge-activation-verify.sh.*statistics' "$repo/government/boot.sh"
echo 'Act33 deterministic Statistics does not launch a model agent'
