#!/usr/bin/env bash
# Verify EXACT clear-signed Founder text saved from a board comment.
# This is a convenient verifier; full automatic founder intake is future work.
set -euo pipefail
[[ "$#" -eq 1 ]] || { echo "Usage: bash verify-founder.sh SIGNED_MESSAGE_FILE" >&2; exit 2; }
input="$1"
key="${VICHE_FOUNDER_PUBLIC_KEY:-/founder/public.asc}"
fprfile="${VICHE_FOUNDER_FINGERPRINT_FILE:-/founder/fingerprint}"
[[ -r "$input" && -r "$key" && -r "$fprfile" ]] || { echo "Founder public key, fingerprint or signed input is missing" >&2; exit 1; }
fingerprint="$(tr -d '[:space:]' < "$fprfile" | tr '[:lower:]' '[:upper:]')"
[[ "$fingerprint" =~ ^[A-F0-9]{40}$|^[A-F0-9]{64}$ ]] || { echo "Invalid pinned founder fingerprint" >&2; exit 1; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
chmod 700 "$tmp"
gpg --homedir "$tmp" --batch --quiet --import "$key" >/dev/null 2>&1
if ! gpg --homedir "$tmp" --batch --status-fd 1 --verify "$input" >"$tmp/status" 2>"$tmp/error"; then
  echo "INVALID Founder signature" >&2
  exit 1
fi
if grep -Eq "^\[GNUPG:\] VALIDSIG $fingerprint( |$)" "$tmp/status"; then
  echo "VALID Founder signature: $fingerprint"
else
  echo "Signature does not match the pinned Founder fingerprint" >&2
  exit 1
fi
