#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
git -C "$tmp" init -q -b main
git -C "$tmp" config user.name test
git -C "$tmp" config user.email test@example.invalid
mkdir -p "$tmp/government" "$tmp/tests" "$tmp/records"
printf 'fixture\n' > "$tmp/government/base"
git -C "$tmp" add . && git -C "$tmp" commit -qm base
base=$(git -C "$tmp" rev-parse HEAD)
# Record a green verification of main, then introduce a change. The record
# precedes the change but its tree necessarily differs from the resulting tree.
main_base=$(git -C "$tmp" rev-parse HEAD)
base_tree=$(git -C "$tmp" rev-parse HEAD^{tree})
printf '{"result":"green","commit":"%s","tree":"%s"}\n' "$main_base" "$base_tree" > "$tmp/records/suite-status.json"
git -C "$tmp" add . && git -C "$tmp" commit -qm green-record
# This change has prior green evidence, but cannot satisfy Act 21's exact-tree
# requirement under the in-tree status-record design; it must remain unreadable.
git -C "$tmp" checkout -qb main-candidate HEAD
printf 'changed\n' > "$tmp/government/base"
git -C "$tmp" add . && git -C "$tmp" commit -qm candidate
green_change=$(git -C "$tmp" rev-parse HEAD)
green_tree=$(git -C "$tmp" rev-parse HEAD^{tree})
git -C "$tmp" checkout -q main
git -C "$tmp" merge --ff-only -q main-candidate
# A main change with no matching prior verification is unreadable.
printf 'unverified\n' > "$tmp/tests/unverified"
git -C "$tmp" add . && git -C "$tmp" commit -qm unverified-change
# Store a red result for the exact changed commit; this is a genuine violation.
printf 'red\n' > "$tmp/tests/red"
git -C "$tmp" add . && git -C "$tmp" commit -qm red-change
red_commit=$(git -C "$tmp" rev-parse HEAD)
red_tree=$(git -C "$tmp" rev-parse HEAD^{tree})
printf '{"result":"red","commit":"%s","tree":"%s"}\n' "$red_commit" "$red_tree" > "$tmp/records/suite-status.json"
git -C "$tmp" add . && git -C "$tmp" commit -qm red-record
out=$(/bin/sh "$root/government/suite-compliance-check.sh" "$tmp")
printf '%s' "$out" | python3 -c 'import json,sys;x=json.load(sys.stdin); assert x["status"]=="measured"; assert x["compliant"]==0; assert x["unreadable"]>0; assert x["main_red_episodes"]==1; assert x["violations"]==1'
echo 'suite-compliance-smoke: passed (green exact-tree limitation reported unreadable)'
