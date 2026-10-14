#!/usr/bin/env bash
# End-to-end throwaway-key test for constitution-owned Founder verifier.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT
mkdir -p "$temp/secret" "$temp/state"
chmod 700 "$temp/secret"
export GNUPGHOME="$temp/secret"
gpg --batch --pinentry-mode loopback --passphrase '' --quick-generate-key 'Viche test signer <test@example.invalid>' ed25519 sign 0 >/dev/null 2>&1
fpr="$(gpg --with-colons --list-keys | awk -F: '$1=="fpr" {print $10;exit}')"
gpg --armor --export "$fpr" > "$temp/public.asc"
printf '%s\n' "$fpr" > "$temp/fingerprint"
cat > "$temp/message" <<'EOF'
VICHE-FOUNDER-DIRECTIVE/1
issue: 999
sequence: 1
issued-at: 2026-10-14T06:00:00Z

Please verify a real signed test message.
EOF
gpg --batch --armor --clearsign --output "$temp/signed.asc" "$temp/message"
export VICHE_TOWNHALL_ID=999
export VICHE_FOUNDER_PUBLIC_KEY="$temp/public.asc"
export VICHE_FOUNDER_FINGERPRINT_FILE="$temp/fingerprint"
export VICHE_FOUNDER_VERIFIER_STATE="$temp/state"
bash "$root/constitution/verify-founder.sh" "$temp/signed.asc"
if bash "$root/constitution/verify-founder.sh" "$temp/signed.asc"; then
  echo "Replay was accepted" >&2; exit 1
fi
sed 's/issue: 999/issue: 777/' "$temp/message" > "$temp/wrong-message"
gpg --batch --armor --clearsign --output "$temp/wrong.asc" "$temp/wrong-message"
if bash "$root/constitution/verify-founder.sh" "$temp/wrong.asc"; then
  echo "Wrong issue was accepted" >&2; exit 1
fi
echo "Viche: valid GPG directive accepted; replay and wrong-issue rejected"
