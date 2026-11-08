#!/bin/sh
# Narrow, ordered enactment route for protected records.
#
# WHY THIS EXISTS: government/reviewed-merge.sh correctly refuses
# constitution/*, records/ballots/*, records/bills/*, government/LAWS.md and
# government/seats.tsv, so an enacted bill that must write those paths had no
# reviewed delivery route. In practice such changes reached main as direct
# commits, which lands the change BEFORE any exact-commit verification can run
# -- the wrong order under Act 21 §§1-2.
#
# This route fixes the ORDER: it verifies the exact candidate commit and tree
# while the change is still only on a delivery ref, then lands that same commit
# by fast-forward. The candidate is never rewritten, so verification is about
# exactly the bytes that land.
#
# THIS SCRIPT DOES NOT GRANT LEGAL AUTHORITY. It is a delivery mechanism. A real
# enactment still requires Parliament to have enacted the bill authorising those
# exact record changes. The script only refuses to deliver anything not declared
# in an exact allowlist and not verified by offices other than sponsor/Clerk.
#
# Usage:
#   enactment-merge.sh delivery/BRANCH --manifest PATH --sponsor SEAT \
#       --verified-by OFFICE --reviewed-by OFFICE [--publish] [--check]
#
#   --check    validate ref shape, scope and actors; print the accepted scope
#   --publish  verify the exact candidate, then fast-forward main to it
#
# Manifest (committed on the delivery branch, under records/enactment/):
#   # bill: <bill-id>
#   # authority: <path to the committed enactment record>
#   <path><TAB>add|modify
# The manifest must match the delivery delta EXACTLY: every changed path listed
# once, nothing listed that did not change, nothing changed outside the set.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
tab=$(printf '\t')

usage() {
    cat >&2 <<'U'
usage: enactment-merge.sh delivery/BRANCH --manifest PATH --sponsor SEAT \
           --verified-by OFFICE --reviewed-by OFFICE [--publish] [--check]
U
    exit 2
}

[ "$#" -ge 1 ] || usage
branch=$1; shift
case "$branch" in
    delivery/*) : ;;
    *) echo 'Only the delivery/ namespace may be integrated' >&2; exit 2 ;;
esac
case "$branch" in
    *[!a-zA-Z0-9_/-]*|*../*|*//*|'delivery/') exit 2 ;;
esac

manifest=
sponsor=
verified_by=
reviewed_by=
publish=false
check_only=false
while [ "$#" -gt 0 ]; do
    case "$1" in
        --manifest) manifest=$2; shift 2 ;;
        --sponsor) sponsor=$2; shift 2 ;;
        --verified-by) verified_by=$2; shift 2 ;;
        --reviewed-by) reviewed_by=$2; shift 2 ;;
        --publish) publish=true; shift ;;
        --check) check_only=true; shift ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done
[ -n "$manifest" ] && [ -n "$sponsor" ] && [ -n "$verified_by" ] && [ -n "$reviewed_by" ] || usage
case "$manifest" in
    records/enactment/*.allowlist) : ;;
    *) echo 'Manifest must be a committed records/enactment/*.allowlist path' >&2; exit 2 ;;
esac

# --- Actors: non-Clerk, non-sponsor, mutually distinct -----------------------
is_clerk() {
    case "$1" in
        clerk|Clerk|'Viche Clerk c1a00001'|c1a00001) return 0 ;;
        *) return 1 ;;
    esac
}
is_clerk "$verified_by" && { echo 'Verifier may not be the Clerk (custodian)' >&2; exit 2; }
is_clerk "$reviewed_by" && { echo 'Reviewer may not be the Clerk (custodian)' >&2; exit 2; }
[ "$verified_by" != "$reviewed_by" ] || { echo 'Reviewer must differ from verifier' >&2; exit 2; }
[ "$verified_by" != "$sponsor" ] || { echo 'Sponsor may not verify their own enactment' >&2; exit 2; }
[ "$reviewed_by" != "$sponsor" ] || { echo 'Sponsor may not review their own enactment' >&2; exit 2; }

# --- Pin refs; a later main update makes the publish fail rather than clobber --
git -C "$town" fetch -q origin \
    "+refs/heads/main:refs/remotes/origin/main" \
    "+refs/heads/$branch:refs/remotes/origin/$branch" ||
    { echo 'Cannot fetch canonical main and delivery ref' >&2; exit 1; }
base=$(git -C "$town" rev-parse refs/remotes/origin/main)
candidate=$(git -C "$town" rev-parse "refs/remotes/origin/$branch")
[ "$base" != "$candidate" ] || { echo 'No delivery delta' >&2; exit 1; }

# --- Ordering, part 1: the candidate must already contain main --------------
# Refusing rather than merging keeps the verified bytes identical to the landed
# bytes. The author rebases their delivery branch onto main; we never rewrite.
git -C "$town" merge-base --is-ancestor "$base" "$candidate" || {
    echo 'Delivery branch is not a fast-forward of main.' >&2
    echo 'Rebase it onto main and re-run; this route never rewrites a candidate.' >&2
    exit 1
}

tree=$(git -C "$town" rev-parse "$candidate^{tree}")
delta=$(git -C "$town" diff --name-only "$base" "$candidate")
[ -n "$delta" ] || { echo 'No delivery delta' >&2; exit 1; }

# --- Manifest, read from the candidate itself -------------------------------
git -C "$town" cat-file -e "$candidate:$manifest" 2>/dev/null ||
    { echo "Manifest missing at delivery commit: $manifest" >&2; exit 1; }
man=$(git -C "$town" show "$candidate:$manifest")

bill=$(printf '%s\n' "$man" | sed -n 's/^# bill:[[:space:]]*//p' | head -n 1)
authority=$(printf '%s\n' "$man" | sed -n 's/^# authority:[[:space:]]*//p' | head -n 1)
[ -n "$bill" ] || { echo 'Manifest lacks "# bill: <id>"' >&2; exit 1; }
[ -n "$authority" ] || { echo 'Manifest lacks "# authority: <path>"' >&2; exit 1; }
case "$authority" in
    records/*) : ;;
    *) echo 'Authority must name a committed records/ enactment record' >&2; exit 1 ;;
esac
git -C "$town" cat-file -e "$base:$authority" 2>/dev/null ||
    { echo "Authority record not present at base: $authority" >&2; exit 1; }

entries=$(printf '%s\n' "$man" | grep -v '^#' | grep -v '^$' || :)

# --- Exact bijection between manifest and delta -----------------------------
# The manifest is committed on the delivery branch, so it appears in the delta;
# it is metadata about the change, not one of the declared paths, and is exempt.
listed=$(printf '%s\n' "$entries" | cut -f1 | grep -vx "$manifest" | sort)
changed=$(printf '%s\n' "$delta" | grep -vx "$manifest" | sort)
[ "$listed" = "$changed" ] || {
    echo 'Manifest does not match the delivery delta exactly.' >&2
    echo '  manifest:' >&2; printf '%s\n' "$listed" | sed 's/^/    /' >&2
    echo '  delta:' >&2; printf '%s\n' "$changed" | sed 's/^/    /' >&2
    exit 1
}

# --- Per-entry rules --------------------------------------------------------
# Written to a file and read with redirection: a piped loop would run in a
# subshell (so "exit 1" would not stop the script) and its final failing read
# would trip set -e.
entriesfile=$(mktemp) || exit 1
trap 'rm -f "$entriesfile"' 0 1 2 3 15
printf '%s\n' "$entries" > "$entriesfile"
while IFS="$tab" read -r path mode; do
    [ -n "$path" ] || continue
    case "$path" in
        *'*'*|*'?'*|*'['*|../*|/*|*'//'*)
            echo "Ambiguous or absolute path refused: $path" >&2; exit 1 ;;
        constitution/*|government/seats.tsv)
            echo "Path may never be delivered by this route: $path" >&2; exit 1 ;;
        records/*|government/LAWS.md) : ;;
        *) echo "Path outside the permitted enactment set: $path" >&2; exit 1 ;;
    esac
    case "$mode" in
        add|modify) : ;;
        *) echo "Mode must be add or modify: $path -> $mode" >&2; exit 1 ;;
    esac
    present=no
    git -C "$town" cat-file -e "$base:$path" 2>/dev/null && present=yes
    [ "$mode" = add ] && [ "$present" = yes ] &&
        { echo "Manifest says add but path exists at base: $path" >&2; exit 1; }
    [ "$mode" = modify ] && [ "$present" = no ] &&
        { echo "Manifest says modify but path is absent at base: $path" >&2; exit 1; }
    case "$path" in
        records/ballots/*)
            [ "$mode" = modify ] &&
                { echo "Ballot row edits are refused by design: $path" >&2; exit 1; } ;;
    esac
done < "$entriesfile"
rm -f "$entriesfile"

if [ "$check_only" = true ]; then
    echo "SCOPE OK bill=$bill authority=$authority sponsor=$sponsor verifier=$verified_by reviewer=$reviewed_by"
    echo "candidate=$candidate tree=$tree base=$base"
    printf '%s\n' "$entries" | sed 's/^/  /'
    echo 'Checked only; nothing verified against a suite and nothing pushed.'
    exit 0
fi

# --- Ordering, part 2: verify the exact candidate BEFORE it can land --------
suite=tests/records-smoke.sh
while IFS= read -r file; do
    case "$file" in
        government/*|tests/*) suite=tests/run-all.sh ;;
    esac
done <<EOF
$delta
EOF

mkdir -p "$state/delivery"
scratch=$(mktemp -d "$state/delivery/enactment.XXXXXXXX") || exit 1
cwd=$scratch/checkout
cleanup() {
    if [ -d "$cwd" ]; then
        git -C "$town" worktree remove --force "$cwd" >/dev/null 2>&1 || :
    fi
    rm -rf "$scratch"
}
trap cleanup 0
trap 'exit 130' 1 2 3 15

# Exact-commit checkout of the candidate itself (not the canonical dirt).
git -C "$town" worktree add --quiet --detach "$cwd" "$candidate"
[ "$(git -C "$cwd" rev-parse HEAD)" = "$candidate" ] ||
    { echo 'Could not check out the exact candidate commit' >&2; exit 1; }
[ "$(git -C "$cwd" rev-parse HEAD^{tree})" = "$tree" ] ||
    { echo 'Candidate tree mismatch during checkout' >&2; exit 1; }

VICHE_TOWN_ROOT="$cwd" /bin/sh "$cwd/government/suite-status.sh" \
    --commit "$candidate" --suite "$suite" > "$scratch/suite.log" 2>&1 ||
    { echo "Exact enactment candidate $candidate failed $suite" >&2; tail -n 15 "$scratch/suite.log" >&2; exit 1; }
jq -e --arg sha "$candidate" --arg tree "$tree" \
    '.result=="green" and .commit==$sha and .tree==$tree and .incident==false' \
    "$cwd/records/suite-status.json" >/dev/null ||
    { echo 'Verifier did not attest the exact candidate/tree' >&2; exit 1; }

receipt="$state/delivery/enactment-$candidate.json"
jq -n --arg bill "$bill" --arg cand "$candidate" --arg tree "$tree" \
      --arg manifest "$manifest" --arg authority "$authority" \
      --arg sponsor "$sponsor" --arg verifier "$verified_by" \
      --arg reviewer "$reviewed_by" --arg suite "$suite" --arg base "$base" \
    '{bill:$bill,commit:$cand,tree:$tree,manifest:$manifest,authority:$authority,
      sponsor:$sponsor,verified_by:$verifier,reviewed_by:$reviewer,suite:$suite,
      base:$base,scope:"declared-manifest-exact",order:"verified-before-land"}' > "$receipt"

if [ "$publish" != true ]; then
    echo "VERIFIED candidate $candidate tree=$tree suite=$suite receipt=$receipt"
    echo 'Not pushed; verification precedes landing but is not enactment or review.'
    exit 0
fi

# --- Land it: fast-forward only, after canonical preflight ------------------
canonical_head=$(git -C "$town" rev-parse HEAD)
[ "$canonical_head" = "$base" ] ||
    { echo 'Canonical checkout is not at fetched main; reconcile before publish' >&2; exit 1; }
while IFS= read -r path; do
    [ -n "$path" ] || continue
    if { [ -e "$town/$path" ] || [ -L "$town/$path" ]; } &&
       ! git -C "$town" ls-files --error-unmatch -- "$path" >/dev/null 2>&1; then
        echo "Canonical untracked evidence overlaps the approved enactment: $path" >&2
        exit 1
    fi
    if ! git -C "$town" diff --quiet -- "$path" ||
       ! git -C "$town" diff --cached --quiet -- "$path"; then
        echo "Canonical working tree has uncommitted changes to: $path" >&2
        exit 1
    fi
done <<EOF
$changed
EOF

git -C "$town" push origin "$candidate:refs/heads/main" ||
    { echo 'Push refused (concurrent main update?); reconcile and re-run' >&2; exit 1; }
echo "LANDED enactment $bill commit=$candidate tree=$tree receipt=$receipt"
