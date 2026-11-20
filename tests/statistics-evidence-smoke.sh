#!/bin/sh
# Hermetic tests for the Statistics preflight evidence utilities and gate.
# Only temp fixtures are used; canonical records and state are never touched.
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
helper=$(pwd -P)/government/statistics-evidence.py
preflight=$(pwd -P)/government/statistics-preflight.sh
d=$(mktemp -d)
trap 'rm -rf "$d"' EXIT HUP INT TERM
town=$d/town
mkdir -p "$town/government" "$town/records/knowledge/statistics-preflight-20261120-sources"
cp "$helper" "$town/government/statistics-evidence.py"
src=$town/records/knowledge/statistics-preflight-20261120-sources
att=$town/records/knowledge/statistics-trial-preflight-20261120.json

printf 'frozen source alpha\n' > "$src/alpha.json"
printf 'frozen source beta\n'  > "$src/beta.json"
ha=$(sha256sum "$src/alpha.json" | cut -d' ' -f1)
hb=$(sha256sum "$src/beta.json"  | cut -d' ' -f1)
sa=$(stat -c %s "$src/alpha.json")
sb=$(stat -c %s "$src/beta.json")

write_att() {
  python3 - "$att" "$ha" "$hb" "$sa" "$sb" "$1" "$2" "$3" "$4" <<'PY'
import json, sys
path, ha, hb, sa, sb, ready, gate_status, tokens, meter = sys.argv[1:10]
gates = {k: {"status": gate_status} for k in (
    "verified_numerator", "frozen_resource_denominator",
    "executive_order", "judiciary_determination")}
json.dump({
  "schema": "viche-statistics-trial-preflight-1",
  "office": "statistics",
  "readiness": ready,
  "gates": gates,
  "candidate_outcome": "x", "numerator": "x", "denominator_statistical": "x",
  "negative_controls": ["x"], "observation_windows": "x", "comparison": "x",
  "falsifiers": ["x"], "missingness": ["x"],
  "denominator_resource": {
    "meter_available": meter == "true", "units": "usd" if meter == "true" else "unavailable",
    "tokens": None if tokens == "none" else int(tokens),
    "machine_time": None, "wall_time": None,
    "_declared_unavailable": ["machine_time", "wall_time"]},
  "sources": [
    {"snapshot": "alpha.json", "sha256": ha, "size_bytes": int(sa)},
    {"snapshot": "beta.json", "sha256": hb, "size_bytes": int(sb)}],
}, open(path, "w"), sort_keys=True)
PY
}

# --- evidence utility: stability, tamper detection, missingness -------------
m1=$(python3 "$helper" manifest "$src")
m2=$(python3 "$helper" manifest "$src")
[ "$m1" = "$m2" ] || { echo "FAIL: manifest not stable" >&2; exit 1; }
printf '%s' "$m1" | grep -q 'alpha.json' || { echo "FAIL: manifest lacks a file" >&2; exit 1; }

write_att ready green 100 true
python3 "$helper" verify "$att" "$src" | grep -q '"verified": true' || {
  echo "FAIL: verify rejected identical snapshots" >&2; exit 1; }
python3 "$helper" missingness "$att" | grep -q '"honest": true' || {
  echo "FAIL: missingness rejected metered record" >&2; exit 1; }

# Tamper: a byte change must be detected by both manifest and verify.
printf 'TAMPERED\n' > "$src/alpha.json"
python3 "$helper" verify "$att" "$src" | grep -q 'hash mismatch: alpha.json' || {
  echo "FAIL: tamper not detected" >&2; exit 1; }
m3=$(python3 "$helper" manifest "$src")
[ "$m3" != "$m1" ] || { echo "FAIL: tamper did not change manifest" >&2; exit 1; }
printf 'frozen source alpha\n' > "$src/alpha.json"

# Missing: a deleted snapshot must be reported, not treated as an empty zero.
rm "$src/beta.json"
python3 "$helper" verify "$att" "$src" | grep -q 'missing source: beta.json' || {
  echo "FAIL: missing source not detected" >&2; exit 1; }
printf 'frozen source beta\n'  > "$src/beta.json"

# Unmetered cost must not be fabricated as zero.
write_att ready green 0 false
python3 "$helper" missingness "$att" | grep -q 'unmetered tokens recorded as zero' || {
  echo "FAIL: zero-as-meter not rejected" >&2; exit 1; }

# --- preflight gate: fail closed --------------------------------------------
write_att ready green 100 true
VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" statistics || {
  echo "FAIL: ready preflight rejected an all-green record" >&2; exit 1; }

write_att not_ready green 100 true
if VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" statistics >/dev/null 2>&1; then
  echo "FAIL: not_ready passed" >&2; exit 1; fi

write_att ready hold 100 true
if VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" statistics >/dev/null 2>&1; then
  echo "FAIL: non-green gate passed" >&2; exit 1; fi

write_att ready green 100 false
if VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" statistics >/dev/null 2>&1; then
  echo "FAIL: unmetered denominator passed" >&2; exit 1; fi

# Missing attestation fails closed.
mv "$att" "$att.hidden"
if VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" statistics >/dev/null 2>&1; then
  echo "FAIL: missing attestation passed" >&2; exit 1; fi
mv "$att.hidden" "$att"

# Tampered snapshot fails the whole gate even with all flags green.
write_att ready green 100 true
printf 'TAMPERED\n' > "$src/beta.json"
if VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" statistics >/dev/null 2>&1; then
  echo "FAIL: tampered snapshot passed the gate" >&2; exit 1; fi
printf 'frozen source beta\n'  > "$src/beta.json"

# The gate is statistics-only; other offices are untouched by this change.
VICHE_TOWN_ROOT="$town" /bin/sh "$preflight" foresight || {
  echo "FAIL: non-statistics office affected" >&2; exit 1; }

echo 'statistics evidence: stable, tamper/missing detected, unmetered!=zero, preflight fail-closed'
