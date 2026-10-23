#!/bin/sh
# Regression: a legal seat survives deletion and terminal failure of its appointee.
set -eu
town=${1:-$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
mkdir -p "$tmp/bin" "$tmp/town/government" "$tmp/seats/a1" "$tmp/seats/branches/executive" "$tmp/state" "$tmp/mock"
printf 'a1\tClerk\tFounder intake\n' > "$tmp/town/government/seats.tsv"
cat > "$tmp/bin/antonina" <<'EOF'
#!/bin/sh
set -eu
if [ "$1" = agent ] && [ "$2" = new ]; then
  num=0; [ ! -f "$MOCK/counter" ] || num=$(cat "$MOCK/counter")
  num=$((num+1)); printf '%s\n' "$num" > "$MOCK/counter"
  id="fresh-$num"; printf idle > "$MOCK/$id"
  printf '%s\n' "$id"
elif [ "$1" = agent ] && [ "$2" = status ]; then
  id=$4
  [ -f "$MOCK/$id" ] || exit 1
  status=$(cat "$MOCK/$id")
  if [ "$status" = failed ]; then
    printf '{"state":"failed","finished_at":1792775220.5,"prompts":2,"backend_error":{"classification":"upstream_endpoint_unavailable","transient":true,"automatic_retry_safe":false}}\n'
  elif [ "$status" = failed-permanent ]; then
    printf '{"state":"failed","finished_at":1792775230.25,"prompts":3,"backend_error":{"classification":"invalid_api_key","transient":false,"automatic_retry_safe":false}}\n'
  else
    printf '{"state":"%s","model":null,"variant":"low"}\n' "$status"
  fi
else
  echo 'unexpected mocked command' >&2; exit 7
fi
EOF
chmod +x "$tmp/bin/antonina"
export MOCK=$tmp/mock
export VICHE_TOWN_ROOT=$tmp/town
export VICHE_SEATS_ROOT=$tmp/seats
export VICHE_STATE_ROOT=$tmp/state
PATH=$tmp/bin:$PATH; export PATH
script=$town/government/appointments.sh
a=$(/bin/sh "$script" ensure a1)
[ "$a" = fresh-1 ] || exit 1
b=$(/bin/sh "$script" ensure a1)
[ "$a" = "$b" ] || exit 1
r=$(/bin/sh "$script" resolve a1)
[ "$r" = "$a" ] || exit 1
rm "$MOCK/$a"
if /bin/sh "$script" resolve a1 >/dev/null 2>&1; then echo 'resolve invented missing agent' >&2; exit 1; fi
c=$(/bin/sh "$script" ensure a1)
[ "$c" = fresh-2 ] || exit 1
# A deleted prior appointment is preserved as UNREADABLE, not falsely failed.
jq -e '.state=="unreadable" and .agent_id=="fresh-1"' \
  "$tmp/state/appointments/terminal-evidence/fresh-1/event.json" >/dev/null
printf failed > "$MOCK/$c"
x=$(/bin/sh "$script" ensure a1)
[ "$x" = fresh-3 ] || exit 1
# Preserve the real failed status, no duplicate observation of this invocation.
jq -e '.state=="failed" and .agent_id=="fresh-2" and .office=="a1" and
       .finished_at==1792775220.5 and .prompts==2 and
       .failure_class=="upstream_endpoint_unavailable" and
       .transient==true and .automatic_retry_safe==false' \
  "$tmp/state/appointments/terminal-evidence/fresh-2/event.json" >/dev/null
[ -s "$tmp/state/appointments/terminal-evidence/fresh-2/status.json" ]
[ "$(wc -l < "$tmp/state/appointments/terminal-events.jsonl")" -eq 2 ]
[ "$(/bin/sh "$script" ensure a1)" = fresh-3 ]
[ "$(wc -l < "$tmp/state/appointments/terminal-events.jsonl")" -eq 2 ]
y=$(/bin/sh "$script" replace a1)
[ "$y" = fresh-4 ] || exit 1
e=$(/bin/sh "$script" ensure executive)
[ "$e" = fresh-5 ] || exit 1
# A confirmed nontransient terminal failure must retain false, not be erased
# into null by jq's alternative operator (false // null is null).
printf failed-permanent > "$MOCK/$e"
f=$(/bin/sh "$script" ensure executive)
[ "$f" = fresh-6 ] || exit 1
jq -e '.state=="failed" and .failure_class=="invalid_api_key" and
        .transient==false and .automatic_retry_safe==false and
        .prompts==3 and .finished_at==1792775230.25' \
  "$tmp/state/appointments/terminal-evidence/fresh-5/event.json" >/dev/null
[ "$(wc -l < "$tmp/state/appointments/appointments.tsv")" -eq 2 ] || exit 1
# No secret powers granted by supplying an unknown role key.
if /bin/sh "$script" ensure a2 >/dev/null 2>&1; then exit 1; fi
printf 'a1\tbad-1\na1\tbad-2\n' > "$tmp/state/appointments/appointments.tsv"
if /bin/sh "$script" ensure a1 >/dev/null 2>&1; then echo 'duplicate appointee accepted' >&2; exit 1; fi
echo 'appointment recovery tests passed'
