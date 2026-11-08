#!/bin/sh
# Hermetic scope/ordering tests for the enactment delivery route.
# Local bare origin; no network, no canonical state, nothing published for real.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
town=$tmp/town
remote=$tmp/origin.git
state=$tmp/state
mkdir -p "$town" "$state"
git init --bare -q "$remote"
git -C "$town" init -q -b main
git -C "$town" config user.name Fixture
git -C "$town" config user.email fixture@example.invalid
git -C "$town" config commit.gpgsign false
git -C "$town" remote add origin "$remote"
mkdir -p "$town/government" "$town/tests" "$town/records/enactment" \
         "$town/records/bills" "$town/records/ballots"
cp "$repo/government/suite-status.sh" "$town/government/suite-status.sh"
cp "$repo/government/enactment-merge.sh" "$town/government/enactment-merge.sh"
printf '#!/bin/sh\nexit 0\n' > "$town/tests/records-smoke.sh"
printf '#!/bin/sh\nexit 0\n' > "$town/tests/run-all.sh"
chmod +x "$town/tests/records-smoke.sh" "$town/tests/run-all.sh"
printf 'How Viche works\n' > "$town/AGENTS.md"
printf 'Operative law v1\n' > "$town/government/LAWS.md"
printf 'old bill\n' > "$town/records/bills/sample-act.md"
printf 'enactment record\n' > "$town/records/enactment/sample-act-ENACTMENT.md"
git -C "$town" add -A
git -C "$town" commit -qm 'main baseline'
git -C "$town" push -q -u origin main
base=$(git -C "$town" rev-parse HEAD)

# A delivery branch that is a fast-forward of main.
mk_delivery() {
    name=$1; shift
    d=$tmp/$name
    git -C "$town" worktree add -q -b "delivery/$name" "$d" main
    "$@" "$d"
    git -C "$d" add -A
    git -C "$d" commit -qm "delivery $name"
    git -C "$d" push -q origin "HEAD:refs/heads/delivery/$name"
}

write_manifest() { # dir bill paths(modes as "path mode" pairs on stdin)
    d=$1; bill=$2
    {
        printf '# bill: %s\n' "$bill"
        printf '# authority: records/enactment/sample-act-ENACTMENT.md\n'
        cat
    } > "$d/records/enactment/$bill.allowlist"
}

fails=0
expect_fail() {
    label=$1; shift
    if out=$(run "$@" 2>&1); then
        echo "FAIL (expected refusal): $label" >&2
        printf '%s\n' "$out" | sed 's/^/    /' >&2
        fails=$((fails+1))
    else
        printf 'ok   refused: %s\n' "$label"
    fi
}
expect_ok() {
    label=$1; shift
    if out=$(run "$@" 2>&1); then
        printf 'ok   accepted: %s\n' "$label"
    else
        echo "FAIL (expected success): $label" >&2
        printf '%s\n' "$out" | sed 's/^/    /' >&2
        fails=$((fails+1))
    fi
}
run() {
    VICHE_TOWN_ROOT=$town VICHE_STATE_ROOT=$state \
        /bin/sh "$town/government/enactment-merge.sh" "$@"
}

tab=$(printf '\t')

# --- 1. A correct declaration is accepted -------------------------------
mk_delivery good sh -c "printf 'Operative law v2\n' > \"\$0/government/LAWS.md\""
d=$tmp/good
printf 'government/LAWS.md\tmodify\n' | write_manifest "$d" good-act
git -C "$d" add -A; git -C "$d" commit -qm 'add manifest'
git -C "$d" push -q origin "HEAD:refs/heads/delivery/good"
expect_ok 'exact allowlist matches delta' \
    delivery/good --manifest records/enactment/good-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 2. Unlisted path ---------------------------------------------------
mk_delivery extra sh -c "printf 'Operative law v2\n' > \"\$0/government/LAWS.md\"; printf 'sneak\n' > \"\$0/README.md\""
d=$tmp/extra
printf 'government/LAWS.md\tmodify\n' | write_manifest "$d" extra-act
git -C "$d" add -A; git -C "$d" commit -qm 'manifest omits one path'
git -C "$d" push -q origin "HEAD:refs/heads/delivery/extra"
expect_fail 'path changed but not declared' \
    delivery/extra --manifest records/enactment/extra-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 3. Manifest lists an unchanged path --------------------------------
mk_delivery over sh -c "printf 'Operative law v2\n' > \"\$0/government/LAWS.md\""
d=$tmp/over
{ printf 'government/LAWS.md\tmodify\n'; printf 'records/bills/sample-act.md\tmodify\n'; } |
    write_manifest "$d" over-act
git -C "$d" add -A; git -C "$d" commit -qm 'manifest over-declares'
git -C "$d" push -q origin "HEAD:refs/heads/delivery/over"
expect_fail 'declared path did not change' \
    delivery/over --manifest records/enactment/over-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 4. Ballot ROW edit refused ----------------------------------------
# Baseline ballot file on main first, so the delivery can only be a row edit.
git -C "$town" checkout -q main
mkdir -p "$town/records/ballots"
printf 'a\tyes\tcafebabe\n' > "$town/records/ballots/sample.tsv"
git -C "$town" add -A; git -C "$town" commit -qm 'add ballot baseline'
git -C "$town" push -q origin main

d2=$tmp/ballotmod2
git -C "$town" worktree add -q -b delivery/ballotmod2 "$d2" main
printf 'a\tyes\tdeadbeef\n' > "$d2/records/ballots/sample.tsv"
printf 'records/ballots/sample.tsv\tmodify\n' | write_manifest "$d2" bm2-act
git -C "$d2" add -A; git -C "$d2" commit -qm 'edit ballot rows on new base'
git -C "$d2" push -q origin "HEAD:refs/heads/delivery/ballotmod2"
expect_fail 'ballot row edit refused' \
    delivery/ballotmod2 --manifest records/enactment/bm2-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 5. New ballot file (add) allowed only as add -----------------------
d3=$tmp/ballotadd
git -C "$town" worktree add -q -b delivery/ballotadd "$d3" main
printf 'b\tyes\tf00d\n' > "$d3/records/ballots/new-act.tsv"
printf 'records/ballots/new-act.tsv\tadd\n' | write_manifest "$d3" ba-act
git -C "$d3" add -A; git -C "$d3" commit -qm 'add a new ballot file'
git -C "$d3" push -q origin "HEAD:refs/heads/delivery/ballotadd"
expect_ok 'new ballot file accepted as add' \
    delivery/ballotadd --manifest records/enactment/ba-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 6. Actor gate: Clerk may not verify -------------------------------
expect_fail 'Clerk as verifier' \
    delivery/good --manifest records/enactment/good-act.allowlist \
    --sponsor c1a00004 --verified-by c1a00001 --reviewed-by c1a00007 --check
expect_fail 'Clerk as reviewer' \
    delivery/good --manifest records/enactment/good-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00001 --check
expect_fail 'sponsor as verifier' \
    delivery/good --manifest records/enactment/good-act.allowlist \
    --sponsor c1a00004 --verified-by c1a00004 --reviewed-by c1a00007 --check
expect_fail 'verifier equals reviewer' \
    delivery/good --manifest records/enactment/good-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1e00008 --check

# --- 7. Paths outside the permitted set --------------------------------
d4=$tmp/outside
git -C "$town" worktree add -q -b delivery/outside "$d4" main
printf 'x\n' > "$d4/README.md"
printf 'README.md\tmodify\n' | write_manifest "$d4" out-act
git -C "$d4" add -A; git -C "$d4" commit -qm 'touch a non-records path'
git -C "$d4" push -q origin "HEAD:refs/heads/delivery/outside"
expect_fail 'path outside permitted set' \
    delivery/outside --manifest records/enactment/out-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 8. Ambiguous path --------------------------------------------------
d5=$tmp/ambig
git -C "$town" worktree add -q -b delivery/ambig "$d5" main
printf 'y\n' > "$d5/records/bills/glob.md"
printf 'records/bills/*.md\tadd\n' | write_manifest "$d5" amb-act
git -C "$d5" add -A; git -C "$d5" commit -qm 'glob in manifest'
git -C "$d5" push -q origin "HEAD:refs/heads/delivery/ambig"
expect_fail 'glob path refused' \
    delivery/ambig --manifest records/enactment/amb-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 9. Ordering: non-fast-forward delivery refused --------------------
d6=$tmp/behind
git -C "$town" worktree add -q -b delivery/behind "$d6" main
printf 'z\n' > "$d6/records/bills/behind.md"
printf 'records/bills/behind.md\tadd\n' | write_manifest "$d6" behind-act
git -C "$d6" add -A; git -C "$d6" commit -qm 'delivery based on old main'
git -C "$d6" push -q origin "HEAD:refs/heads/delivery/behind"
# advance main afterwards so the delivery is no longer a fast-forward
git -C "$town" checkout -q main
printf 'further law\n' >> "$town/government/LAWS.md"
git -C "$town" add -A
git -C "$town" commit -qm 'main moves ahead'
git -C "$town" push -q origin main
expect_fail 'stale delivery (not fast-forward)' \
    delivery/behind --manifest records/enactment/behind-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --check

# --- 10. Verification precedes landing; then fast-forward land ---------
d7=$tmp/land
git -C "$town" worktree add -q -b delivery/land "$d7" main
printf 'final law\n' > "$d7/government/LAWS.md"
printf 'government/LAWS.md\tmodify\n' | write_manifest "$d7" land-act
git -C "$d7" add -A; git -C "$d7" commit -qm 'enactment delivery'
git -C "$d7" push -q origin "HEAD:refs/heads/delivery/land"
cand=$(git -C "$town" rev-parse refs/remotes/origin/delivery/land)
expect_ok 'verify exact candidate without publishing' \
    delivery/land --manifest records/enactment/land-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007
[ -f "$state/delivery/enactment-$cand.json" ] ||
    { echo "FAIL: no receipt for $cand" >&2; fails=$((fails+1)); }
main_before=$(git -C "$remote" rev-parse main)
[ "$main_before" != "$cand" ] ||
    { echo 'FAIL: main moved without --publish' >&2; fails=$((fails+1)); }
git -C "$town" fetch -q origin '+refs/heads/main:refs/remotes/origin/main'
expect_ok 'publish fast-forwards main to the verified commit' \
    delivery/land --manifest records/enactment/land-act.allowlist \
    --sponsor c1a00004 --verified-by c1e00008 --reviewed-by c1a00007 --publish
main_after=$(git -C "$remote" rev-parse main)
[ "$main_after" = "$cand" ] ||
    { echo "FAIL: main is $main_after, expected $cand" >&2; fails=$((fails+1)); }

if [ "$fails" -ne 0 ]; then
    echo "enactment-merge smoke FAILED ($fails)" >&2
    exit 1
fi
echo 'enactment-merge scope and ordering smoke passed'
