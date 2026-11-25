#!/bin/sh
# Hermetic regression for canonical/main fast-forward reconciliation (Act 31).
# Recurrence on 2026-11-25 blocked every approved delivery twice; the old
# per-incident manual push was a workaround, this proves the shared runtime
# now propagates a strict fast-forward and refuses a real divergence.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
remote=$tmp/origin.git
town=$tmp/town
state=$tmp/state
mkdir -p "$town" "$state"
git init --bare -q -b main "$remote"
git -C "$town" init -q -b main
git -C "$town" config user.name Fixture
git -C "$town" config user.email fixture@example.invalid
git -C "$town" config commit.gpgsign false
git -C "$town" remote add origin "$remote"
printf 'base\n' > "$town/f"
git -C "$town" add -A
git -C "$town" commit -qm baseline
git -C "$town" push -q -u origin main

# 1. Equal HEAD/base: no action, no note.
VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state" VICHE_GOV="$repo/government" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["VICHE_GOV"])
import integrator
town = os.environ["VICHE_TOWN_ROOT"]
base = integrator.git("rev-parse", "refs/remotes/origin/main", cwd=town)
nb, note = integrator.reconcile_canonical(base)
assert nb == base and note is None, (nb, note)
PY

# 2. Founder commits straight into canonical main: strict fast-forward is
#    propagated to origin with a non-force push and the new base is returned.
printf 'founder\n' >> "$town/f"
git -C "$town" commit -qam 'Founder (via Claude): direct canonical commit'
canonical=$(git -C "$town" rev-parse HEAD)
VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state" VICHE_GOV="$repo/government" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["VICHE_GOV"])
import integrator
town = os.environ["VICHE_TOWN_ROOT"]
base = integrator.git("rev-parse", "refs/remotes/origin/main", cwd=town)
canonical = integrator.git("rev-parse", "HEAD", cwd=town)
assert canonical != base, "fixture did not advance canonical main"
nb, note = integrator.reconcile_canonical(base)
assert note == "reconciled", (nb, note)
assert nb == canonical, (nb, canonical)
origin = integrator.git("rev-parse", "refs/remotes/origin/main", cwd=town)
assert origin == canonical, (origin, canonical)
PY

# 3. A real divergence (origin has a commit canonical lacks) must NOT be
#    auto-published; it is escalated for an agent/Judiciary to resolve.
other=$tmp/other
git clone -q "$remote" "$other"
git -C "$other" config user.name Fixture
git -C "$other" config user.email fixture@example.invalid
printf 'other\n' > "$other/g"
git -C "$other" add -A
git -C "$other" commit -qm 'independent writer'
git -C "$other" push -q origin main
VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state" VICHE_GOV="$repo/government" python3 - <<'PY'
import os, sys
sys.path.insert(0, os.environ["VICHE_GOV"])
import integrator
town = os.environ["VICHE_TOWN_ROOT"]
integrator.git("fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main", cwd=town)
base = integrator.git("rev-parse", "refs/remotes/origin/main", cwd=town)
nb, note = integrator.reconcile_canonical(base)
assert nb == base and note == "diverged", (nb, note)
PY

echo 'Canonical reconcile smoke passed'
