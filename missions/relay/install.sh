#!/bin/sh
set -eu
src=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
dest="$HOME/.local/share/viche/relay"
mkdir -p "$dest" "$HOME/.local/bin"
chmod 700 "$dest"
for f in relay.mjs marceline-request README.md test.mjs lean-handler.py worker-lock.py pnp-remote-check.py; do
  cp "$src/$f" "$dest/$f.tmp"
  chmod 600 "$dest/$f.tmp"
  mv "$dest/$f.tmp" "$dest/$f"
done
chmod 700 "$dest/marceline-request"
cat > "$HOME/.local/bin/marceline-request.tmp" <<'EOF'
#!/bin/sh
exec "$HOME/.local/share/viche/relay/marceline-request" "$@"
EOF
chmod 700 "$HOME/.local/bin/marceline-request.tmp"
mv "$HOME/.local/bin/marceline-request.tmp" "$HOME/.local/bin/marceline-request"
cat > "$HOME/.local/bin/pnp-remote-check.tmp" <<'EOF'
#!/bin/sh
exec "$HOME/.local/bin/python3" "$HOME/.local/share/viche/relay/pnp-remote-check.py" "$@"
EOF
chmod 700 "$HOME/.local/bin/pnp-remote-check.tmp"
mv "$HOME/.local/bin/pnp-remote-check.tmp" "$HOME/.local/bin/pnp-remote-check"
