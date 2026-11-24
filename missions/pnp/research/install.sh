#!/bin/sh
set -eu
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
dest="$HOME/.local/share/viche/pnp-research/research"
mkdir -p "$dest" "$HOME/.local/bin"
chmod 700 "$dest"
for f in "$src"/*.py; do
  name=$(basename "$f")
  install -m 600 "$f" "$dest/$name.tmp"
  mv "$dest/$name.tmp" "$dest/$name"
done
cat > "$HOME/.local/bin/pnp-research.tmp" <<'EOF'
#!/bin/sh
exec "$HOME/.local/bin/python3" "$HOME/.local/share/viche/pnp-research/research/entry.py" "$@"
EOF
chmod 700 "$HOME/.local/bin/pnp-research.tmp"
mv "$HOME/.local/bin/pnp-research.tmp" "$HOME/.local/bin/pnp-research"
