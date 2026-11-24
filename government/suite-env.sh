#!/bin/sh
# Isolate ordinary suite execution from production agent/model configuration.
# This is an accidental-side-effect barrier, not an OS security sandbox.
set -eu
[ "$#" -gt 0 ] || exit 2
scratch=$(mktemp -d "${TMPDIR:-/tmp}/viche-test-env.XXXXXXXX")
trap 'rm -rf "$scratch"' 0
trap 'exit 130' 1 2 3 15
mkdir -p "$scratch/home" "$scratch/bin" "$scratch/config" "$scratch/state" "$scratch/data" "$scratch/cache" "$scratch/town-state" "$scratch/seats"
# Never fall through to the real model provider or agent service. Fixtures
# that need these commands must put their own mocks ahead of this directory.
for cmd in antonina opencode; do
    printf '#!/bin/sh\nprintf "Unmocked live agent/provider command refused in test suite\\n" >&2\nexit 126\n' > "$scratch/bin/$cmd"
    chmod +x "$scratch/bin/$cmd"
done
HOME=$scratch/home
XDG_CONFIG_HOME=$scratch/config
XDG_STATE_HOME=$scratch/state
XDG_DATA_HOME=$scratch/data
XDG_CACHE_HOME=$scratch/cache
VICHE_STATE_ROOT=$scratch/town-state
VICHE_SEATS_ROOT=$scratch/seats
PATH=$scratch/bin:$PATH
export HOME XDG_CONFIG_HOME XDG_STATE_HOME XDG_DATA_HOME XDG_CACHE_HOME
export VICHE_STATE_ROOT VICHE_SEATS_ROOT PATH
unset ANTONINA_HOST_XDG_CONFIG_HOME ANTONINA_HOST_XDG_STATE_HOME ANTONINA_HOST_XDG_DATA_HOME
unset ANTONINA_OPENCODE_XDG_CONFIG_HOME ANTONINA_OPENCODE_XDG_STATE_HOME ANTONINA_OPENCODE_XDG_DATA_HOME
unset VICHE_ANTONINA_CONFIG VICHE_ANTONINA_COOLDOWNS VICHE_ANTONINA_MODEL_HEALTH VICHE_OPENCODE_MODELS
"$@"
