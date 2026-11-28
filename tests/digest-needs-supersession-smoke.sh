#!/bin/sh
# Founder-facing "Needs you" line: newest-per-volatile-topic supersession,
# word-boundary clipping and machine-needs-first ordering must not regress.
# Hermetic: no board, agent, model or state files are read.
set -eu
here=$(CDPATH= cd "$(dirname "$0")" && pwd -P)
exec python3 "$here/digest-needs-supersession.py"
