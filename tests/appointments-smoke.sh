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
  printf '{"state":"%s","model":"opencode-go/longcat-2.5-preview-free","variant":"low"}\n' "$status"
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
printf failed > "$MOCK/$c"
x=$(/bin/sh "$script" ensure a1)
[ "$x" = fresh-3 ] || exit 1
y=$(/bin/sh "$script" replace a1)
[ "$y" = fresh-4 ] || exit 1
e=$(/bin/sh "$script" ensure executive)
[ "$e" = fresh-5 ] || exit 1
[ "$(wc -l < "$tmp/state/appointments/appointments.tsv")" -eq 2 ] || exit 1
# No secret powers granted by supplying an unknown role key.
if /bin/sh "$script" ensure a2 >/dev/null 2>&1; then exit 1; fi
printf 'a1\tbad-1\na1\tbad-2\n' > "$tmp/state/appointments/appointments.tsv"
if /bin/sh "$script" ensure a1 >/dev/null 2>&1; then echo 'duplicate appointee accepted' >&2; exit 1; fi
echo 'appointment recovery tests passed'
