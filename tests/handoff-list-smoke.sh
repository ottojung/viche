#!/bin/sh
set -eu
cd "$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' 0
town="$scratch/town with spaces"
script="$PWD/government/handoff-queue.sh"
[ -z "$(/bin/sh "$script" list-open "$town")" ]
mkdir -p "$town/records/handoffs"
dir="$town/records/handoffs"
[ -z "$(/bin/sh "$script" list-open "$town")" ]
touch "$dir/00-empty.txt"
mkdir "$dir/01-directory.txt"
cat > "$dir/z.txt" <<'EOF'
id: z
status: open
created: 2026-11-26T10:00:00Z
work: first work
work: ignored second
status: done
EOF
cat > "$dir/a.txt" <<'EOF'
id: a
status:   open
created: 2026-11-26T09:00:00Z
work:  second work
EOF
cat > "$dir/b.txt" <<'EOF'
status: done
status: open
id: b
created: 2026-11-26T08:00:00Z
work: ignored
EOF
printf '2026-11-26T09:00:00Z\ta\tsecond work\n2026-11-26T10:00:00Z\tz\tfirst work\n' > "$scratch/want"
/bin/sh "$script" list-open "$town" > "$scratch/got"
cmp "$scratch/want" "$scratch/got"
id=$(/bin/sh "$script" add "$town" founder evidence 'new work')
/bin/sh "$script" list-open "$town" | grep -F "$id" >/dev/null
/bin/sh "$script" mark "$town" "$id" done 'finished'
/bin/sh "$script" list-open "$town" > "$scratch/got"
cmp "$scratch/want" "$scratch/got"
printf 'Single-pass handoff queue listing preserves first-header and sorted output semantics\n'
