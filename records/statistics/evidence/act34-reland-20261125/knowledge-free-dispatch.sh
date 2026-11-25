#!/bin/sh
# Ministry of Economy — enforceable per-invocation FREE-ONLY model allowlist.
#
# Problem this fixes (Founder/operator falsifier, 2026-11-23):
#   `antonina agent run` has NO --model flag; Antonina chooses a model from the
#   GLOBAL ladder (~/.config/antonina/config.json) at dispatch. A caller-supplied
#   model_id string in a Viche profile does NOT constrain what Antonina launches,
#   so a "zero-billed permit" built on that string check would be FALSE.
#
# Mechanism (verified from installed Antonina aeb1ffb source and by live test):
#   agent-runtime/model-config.js resolves models from
#     $XDG_CONFIG_HOME/antonina/config.json
#   (the host remap via ANTONINA_HOST_XDG_CONFIG_HOME applies ONLY when
#   XDG_CONFIG_HOME == ANTONINA_OPENCODE_XDG_CONFIG_HOME). cli/agent.js
#   spawnRunner passes process.env to the runner, and backend.js selects the
#   model from that env via configuredModels(). Setting XDG_CONFIG_HOME to a
#   dedicated free-only directory on THIS invocation therefore pins model
#   selection at prelaunch, without touching the global ladder for any other
#   project. Live test 2026-11-23: allowlist {opencode-go/hy4-flash-free} ->
#   agent models_used=[opencode-go/hy4-flash-free], session cost=0.0; an
#   allowlist whose sole model was cooling REFUSED dispatch (no paid fallback).
#
# This script does NOT enable any office, edit activation.json, reset the 45-day
# UPPER_BOUND ledger, or spend money. It is inert until a lawful permit dispatches
# a knowledge office. It is NOT a claim of a strict hard cap: Antonina's 20 s
# poll remains stop-on-detection. It is a PRELAUNCH billing-source allowlist.
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
billing="$town/government/knowledge-zero-billed-policy.json"
billing_module="$town/government/knowledge-zero-billed.py"
allow_dir="$state/knowledge/free-allowlist"
allow_cfg="$allow_dir/antonina/config.json"

log() { printf 'knowledge-free-dispatch: %s\n' "$*" >&2; }
die() { log "$*"; exit 1; }

[ -s "$billing" ] || die "Economy exact-ID zero-cost policy missing; no paid fallback"
[ -f "$billing_module" ] || die "zero-cost policy verifier missing"
[ -f "$town/government/knowledge-practical-bounds.py" ] || die "practical-bounds module missing"

# Build the allowlist from exact provider/model IDs with reviewed zero-cost
# metadata. A -free name is necessary for the rotation but NEVER billing proof.
python3 - "$billing_module" "$billing" "$allow_cfg" "$town" <<'PY'
import importlib.util, json, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
module, billing, output, town = sys.argv[1:5]
spec = importlib.util.spec_from_file_location("zero_billed", module)
if spec is None or spec.loader is None:
    raise SystemExit("zero-cost policy verifier unavailable")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ref = json.loads(Path(billing).read_text()).get("snapshot_ref")
if not isinstance(ref, str) or not re.fullmatch(r"records/economy/evidence/[A-Za-z0-9_.-]+[.]json", ref):
    raise SystemExit("invalid reviewed provider snapshot reference")
mod.build_allowlist(billing, mod.global_config_path(), output, Path(town) / ref)
PY
[ -s "$allow_cfg" ] || die "failed to build allowlist config"

# The wrapper's only job after building the config is to exec the requested
# Antonina command with XDG_CONFIG_HOME pinned to the free-only config. All
# other environment (including state root) is preserved.
case "${1:-}" in
  run)
    shift
    XDG_CONFIG_HOME="$allow_dir" exec antonina agent run "$@"
    ;;
  *)
    die "usage: knowledge-free-dispatch.sh run <antonina agent run args...>"
    ;;
esac
