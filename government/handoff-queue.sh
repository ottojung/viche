#!/bin/sh
# Act 19 §3.2 — durable handoff queue POSIX wrapper (single source of truth).
#
# The queue at records/handoffs/ is the dispatch's ONLY input. AGENDA.md and
# MANDATES.md reference queue entries by id; they never duplicate status.
#
#   handoff_open <office>                     -> print open handoff JSON lines (none if empty)
#   handoff_append <office> <work> <evidence> <authority>   -> echo new open id
#   handoff_done <id> <evidence>
#   handoff_supersede <id>
set -eu
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
py=$town/government/handoff-queue.py
[ -f "$py" ] || { echo "handoff-queue: missing $py" >&2; exit 1; }

case "${1:-}" in
open) shift; python3 "$py" open "$@" ;;
append) shift; python3 "$py" append "$@" ;;
done) shift; python3 "$py" done "$@" ;;
supersede) shift; python3 "$py" supersede "$@" ;;
*) echo "handoff-queue: unknown command" >&2; exit 2 ;;
esac
