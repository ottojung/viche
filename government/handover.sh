#!/bin/sh
# Fresh context per completed government turn (Founder, 2026-11-24).
# due ID: rotate a used, positively idle/clearexit appointment; no model call.
# write KEY OLD_ID NEW_ID: persist only identity and durable record pointers.
# show KEY ID: display the short pointer note to an unused successor.
# Never inject the predecessor's conversation or thinking history. Durable
# institutional records are the memory, not the previous session.
set -eu
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
dir=$state/handover
cmd=${1:-}

valid_id() { case "$1" in ''|*[!a-zA-Z0-9_-]*) return 1;; esac; return 0; }

case "$cmd" in
  due)
    [ "$#" -eq 2 ] && valid_id "$2" || exit 2
    meta=$(antonina agent status --id "$2" --json 2>/dev/null) || exit 1
    st=$(printf '%s\n' "$meta" | jq -r '.state // empty' 2>/dev/null) || exit 1
    case "$st" in idle|clearexit) :;; *) exit 1;; esac
    # clearexit itself is evidence that the appointment has completed a turn.
    [ "$st" != clearexit ] || exit 0
    # Idle is also used for newly created, never-invoked appointments.
    # A native session or positive prompt count proves this one is not fresh.
    printf '%s\n' "$meta" | jq -e '
      ((.prompts // 0) | type=="number" and .>0) or
      ((.native_session_id // "") | type=="string" and length>0)
    ' >/dev/null
    ;;
  write)
    [ "$#" -eq 4 ] && valid_id "$2" && valid_id "$3" && valid_id "$4" || exit 2
    key=$2 old=$3 new=$4
    mkdir -p "$dir"
    umask 077
    tmp=$(mktemp "$dir/.note.XXXXXX")
    {
      printf 'successor: %s\n' "$new"
      printf 'predecessor: %s\n' "$old"
      printf 'office: %s\n' "$key"
      printf 'rotated_at: %s\n' "$(date -u +%FT%TZ)"
      printf '%s\n' '---'
      printf 'You are a FRESH session for office %s. Your predecessor %s was\n' "$key" "$old"
      printf 'retired after completing its government turn.\n'
      printf 'Its conversation is NOT authority and is not carried forward.\n'
      printf 'Reconstruct your assignment from durable records under %s/records,\n' "$town"
      printf 'records/handoffs/, the Town Hall cursor, the Antonina board, and %s.\n' "$state"
      printf 'Check unfinished work and current evidence; do not redo completed work.\n'
      printf 'Check durable receipts before repeating external actions.\n'
    } > "$tmp"
    mv -f "$tmp" "$dir/$key.md"
    printf '%s\t%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$key" "$old" "$new" >> "$dir/rotations.log"
    ;;
  show)
    [ "$#" -eq 3 ] && valid_id "$2" && valid_id "$3" || exit 0
    note=$dir/$2.md
    [ -s "$note" ] || exit 0
    [ "$(sed -n 's/^successor: //p' "$note" | head -n 1)" = "$3" ] || exit 0
    prompts=$(antonina agent status --id "$3" --json 2>/dev/null | jq -r '.prompts // empty' 2>/dev/null) || exit 0
    [ "$prompts" = 0 ] || exit 0
    printf '\n=== HANDOVER NOTE (fresh session) ===\n'
    sed '1,/^---$/d' "$note"
    printf '=== END HANDOVER NOTE ===\n'
    ;;
  *)
    echo 'usage: handover.sh due ID | write KEY OLD NEW | show KEY ID' >&2
    exit 2
    ;;
esac
