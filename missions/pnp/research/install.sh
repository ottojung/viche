#!/bin/sh
set -eu
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root="$HOME/.local/share/viche/pnp-research"
mkdir -p "$root/releases" "$HOME/.local/bin"
chmod 700 "$root" "$root/releases"
# A running command always sees a complete, immutable release. Do not replace
# its modules one at a time during deployment.
version=$(cd "$src" && sha256sum ./*.py README.md | sha256sum | cut -c1-32)
dest="$root/releases/$version"
if [ ! -d "$dest/research" ]; then
  tmp=$(mktemp -d "$root/releases/.install-XXXXXX")
  trap 'rm -rf "$tmp"' EXIT HUP INT TERM
  mkdir -m 700 "$tmp/research"
  for f in "$src"/*.py "$src/README.md"; do
    install -m 600 "$f" "$tmp/research/$(basename "$f")"
  done
  mv -T "$tmp" "$dest" || [ -d "$dest/research" ]
fi
ln -s "$dest" "$root/.current-$$"
mv -Tf "$root/.current-$$" "$root/current"
cat > "$HOME/.local/bin/pnp-research.tmp-$$" <<'EOF'
#!/bin/sh
exec "$HOME/.local/bin/python3" "$HOME/.local/share/viche/pnp-research/current/research/entry.py" "$@"
EOF
chmod 700 "$HOME/.local/bin/pnp-research.tmp-$$"
mv -f "$HOME/.local/bin/pnp-research.tmp-$$" "$HOME/.local/bin/pnp-research"
printf '%s\n' "$version"
