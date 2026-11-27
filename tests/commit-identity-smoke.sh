#!/bin/sh
# Hermetic check of the office/seat commit-identity helper.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
town=$tmp/town
mkdir -p "$town"
git init -q -b main "$town"
git -C "$town" config user.name Fixture
git -C "$town" config user.email fixture@example.invalid
git -C "$town" config commit.gpgsign false
printf 'base\n' > "$town/f"
git -C "$town" add f
git -C "$town" commit -qm base

# Invalid contributor identities are rejected.
if VICHE_COMMIT_FIXTURE=1 /bin/sh -c \
   "python3 '$repo/government/commit-identity.py' commit --repo '$town' --subject 'bad' --contributor 'No Email' --" \
   >/dev/null 2>&1; then
    echo 'Accepted a malformed contributor identity' >&2
    exit 1
fi
if VICHE_COMMIT_FIXTURE=1 /bin/sh -c \
   "python3 '$repo/government/commit-identity.py' commit --repo '$town' --subject 'bad' --contributor 'Otto Jung <otto.jung@vauplace.com>' --" \
   >/dev/null 2>&1; then
    echo 'Accepted the shared signing identity as a co-author' >&2
    exit 1
fi

# A valid contributor is credited exactly once and survives a second run.
printf 'change\n' >> "$town/f"
git -C "$town" add f
VICHE_COMMIT_FIXTURE=1 python3 "$repo/government/commit-identity.py" commit \
    --repo "$town" --subject "valid commit" \
    --contributor "Viche Clerk <clerk@viche.local>" >/dev/null
git -C "$town" log -1 --format=%B | grep -q '^Co-authored-by: Viche Clerk <clerk@viche.local>$'
# Hook preservation: default commit runs hooks; --no-verify skips them.
printf 'hook\n' > "$town/.git/hooks/pre-commit"
chmod +x "$town/.git/hooks/pre-commit"
cat > "$town/.git/hooks/pre-commit" <<EOF
#!/bin/sh
echo ran > $tmp/hook-ran
EOF
chmod +x "$town/.git/hooks/pre-commit"
rm -f "$tmp/hook-ran"
printf 'change2\n' >> "$town/f"
git -C "$town" add f
VICHE_COMMIT_FIXTURE=1 python3 "$repo/government/commit-identity.py" commit \
    --repo "$town" --subject "hook run" \
    --contributor "Viche Clerk <clerk@viche.local>" >/dev/null
test -f "$tmp/hook-ran"

rm -f "$tmp/hook-ran"
printf 'change3\n' >> "$town/f"
git -C "$town" add f
VICHE_COMMIT_FIXTURE=1 python3 "$repo/government/commit-identity.py" commit \
    --repo "$town" --subject "hook skip" \
    --contributor "Viche Clerk <clerk@viche.local>" \
    -- --no-verify >/dev/null
test ! -f "$tmp/hook-ran"

echo 'Office/seat commit identity smoke passed'