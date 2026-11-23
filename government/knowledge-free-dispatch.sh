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
policy="$state/economy/model-policy.json"
allow_dir="$state/knowledge/free-allowlist"
allow_cfg="$allow_dir/antonina/config.json"

log() { printf 'knowledge-free-dispatch: %s\n' "$*" >&2; }
die() { log "$*"; exit 1; }

[ -s "$policy" ] || die "Economy model policy missing: $policy"
[ -f "$town/government/knowledge-practical-bounds.py" ] || die "practical-bounds module missing"

# Build the allowlist from Economy's audited, source-attested free tier only.
# Every id must carry a '-free' component and appear in model-policy.json 'prefer'.
# This is ALLOWLIST CONSTRUCTION from an authoritative record, not a billing
# enforcement check here: enforcement is Antonina's config on the dispatch path.
python3 - "$policy" "$allow_dir" "$allow_cfg" <<'PY'
import json, os, sys, tempfile
policy, allow_dir, allow_cfg = sys.argv[1:4]
p = json.load(open(policy, encoding="utf-8"))
prefer = p.get("prefer") or []
if not prefer:
    raise SystemExit("empty free-tier prefer list")
for mid in prefer:
    if not isinstance(mid, str) or "-free" not in mid:
        raise SystemExit("non-free id in policy prefer: %s" % mid)
entries = [{"model": mid, "comment": "Economy audited free tier 2026-11-23; source-attested in model-policy.json"} for mid in prefer]
os.makedirs(os.path.dirname(allow_cfg), mode=0o700, exist_ok=True)
os.chmod(allow_dir, 0o700)
fd, tmp = tempfile.mkstemp(prefix=".free-allow-", dir=os.path.dirname(allow_cfg))
with os.fdopen(fd, "w", encoding="utf-8") as fh:
    json.dump({"models": entries}, fh, indent=2)
    fh.write("\n")
os.chmod(tmp, 0o600)
os.replace(tmp, allow_cfg)
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
