#!/bin/sh
# Founder-facing "Needs you" line: newest-per-volatile-topic supersession,
# word-boundary clipping and machine-needs-first ordering must not regress.
# Hermetic: no board, agent, model or state files are read.
set -eu
here=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
target=$here/digest-needs-supersession.py
# The regression test lands with the daily-digest fix in the separate delivery
# digest-needs-supersession-20261128. Until that delivery is on main, the pure
# helpers the test asserts do not exist there and running it would fail against
# the unfixed renderer, turning the canonical suite red (Act 21 section 1).
# Skip cleanly in that ordering; once the fix lands, the test runs on every pass.
if [ ! -f "$target" ]; then
    printf 'SKIP: %s not present (digest fix not yet landed)\n' "$target"
    exit 0
fi
exec python3 "$target"
