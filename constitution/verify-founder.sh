#!/usr/bin/env bash
# Founder-controlled verifier for an entire GPG clear-signed Antonina comment.
# Input plaintext MUST begin:
# VICHE-FOUNDER-DIRECTIVE/1
# issue: <Town Hall issue number>
# sequence: <strictly increasing positive integer>
# issued-at: <ISO-8601 timestamp>
# [blank line]
# <directive text>
set -euo pipefail
[[ "$#" == 1 ]] || { echo "Usage: verify-founder.sh SIGNED_COMMENT.asc" >&2; exit 2; }
signed="$1"
[[ -f "$signed" ]] || exit 1
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
key="${VICHE_FOUNDER_PUBLIC_KEY:-/founder/public.asc}"
fingerprint_file="${VICHE_FOUNDER_FINGERPRINT_FILE:-/founder/fingerprint}"
state_dir="${VICHE_FOUNDER_VERIFIER_STATE:-/var/lib/lubko/wd/viche-state/founder-verification}"
: "${VICHE_TOWNHALL_ID:?Set the designated Town Hall issue number}"
[[ -r "$key" && -r "$fingerprint_file" ]] || { echo "Missing trusted Founder public key or fingerprint" >&2; exit 1; }
fingerprint="$(tr -d '[:space:]' < "$fingerprint_file" | tr '[:lower:]' '[:upper:]')"
[[ "$fingerprint" =~ ^[0-9A-F]{40}$|^[0-9A-F]{64}$ ]] || { echo "Malformed Founder fingerprint" >&2; exit 1; }
temp="$(mktemp -d)"
trap 'rm -rf "$temp"' EXIT
chmod 700 "$temp"
gpg --homedir "$temp" --batch --quiet --import "$key" >/dev/null 2>&1
if ! gpg --homedir "$temp" --batch --status-fd 3 --output "$temp/plaintext" --decrypt "$signed" 3>"$temp/status" 2>"$temp/errors"; then
  echo "Invalid Founder signature" >&2; exit 1
fi
grep -Fqx "[GNUPG:] VALIDSIG $fingerprint" "$temp/status" || \
  grep -Eq "^\[GNUPG:\] VALIDSIG $fingerprint( |$)" "$temp/status" || { echo "Signer is not the Founder" >&2; exit 1; }
[[ "$(sed -n '1p' "$temp/plaintext")" == "VICHE-FOUNDER-DIRECTIVE/1" ]] || { echo "Wrong directive type" >&2; exit 1; }
issue="$(sed -n '2s/^issue: //p' "$temp/plaintext")"
sequence="$(sed -n '3s/^sequence: //p' "$temp/plaintext")"
issued="$(sed -n '4s/^issued-at: //p' "$temp/plaintext")"
[[ "$issue" == "$VICHE_TOWNHALL_ID" ]] || { echo "Directive is for another issue" >&2; exit 1; }
[[ "$sequence" =~ ^[1-9][0-9]*$ && "${#sequence}" -lt 16 ]] || { echo "Invalid sequence" >&2; exit 1; }
[[ "$issued" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] || { echo "Invalid issued-at timestamp" >&2; exit 1; }
[[ -z "$(sed -n '5p' "$temp/plaintext")" ]] || { echo "Missing directive separator" >&2; exit 1; }
[[ -n "$(sed -n '6p' "$temp/plaintext")" ]] || { echo "Empty directive" >&2; exit 1; }

# Best-effort durable anti-replay tracking. This state must be kept outside the
# parliament's Git tree. Unix-user separation is necessary for robust enforcement;
# when agents share its UID, they can tamper with the state and this is not a
# security boundary. This verifier MUST NOT be replaced with writable town code.
mkdir -p "$state_dir"
exec 9>"$state_dir/lock"
flock -x 9
last=0
[[ ! -f "$state_dir/last-sequence" ]] || last="$(cat "$state_dir/last-sequence")"
[[ "$last" =~ ^[0-9]+$ ]] || { echo "Corrupt replay state" >&2; exit 1; }
(( 10#$sequence > 10#$last )) || { echo "Replay or out-of-order Founder instruction" >&2; exit 1; }
printf '%s\n' "$sequence" > "$state_dir/last-sequence.new"
mv -f "$state_dir/last-sequence.new" "$state_dir/last-sequence"
echo "Verified Founder directive sequence $sequence for Town Hall #$issue"
