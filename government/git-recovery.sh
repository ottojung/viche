#!/bin/sh
# Bounded, non-destructive recovery for a conflicted canonical checkout.
#
# Runs OUTSIDE the Founder-controlled boot loop (invoked by the parliament-controlled
# viche-git-recovery S6 service), so it keeps running while boot.sh's cycle()
# short-circuits on reconcile() failure. See
# records/CONTINUITY-BOOT-INTEGRATION-DEADLOCK-2026-10-16.md and
# records/CONTINUITY-BOOT-DEADLOCK-VERIFICATION-2026-10-16.md.
#
# Safety: a merge is aborted ONLY when every gate below proves no unique work is
# discarded. `git merge --abort` (= `git reset --merge`) silently discards staged
# changes that did not come from the merge, so staged changes beyond the merge's
# own files are refused. Unstaged modifications to merge-untouched files and
# untracked files are preserved by reset --merge (verified empirically; see
# tests/git-recovery-smoke.sh).
#
# Exit 0: no conflict, or recovery succeeded. Exit 1: conflict detected but no
# safe automatic recovery (the Sentinel's government_git_conflict signal already
# alerts Town Hall). Exit 2: usage/environment error.
set -eu

town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
log=$state/recovery/git-recovery.log
throttle=${VICHE_RECOVERY_LOG_THROTTLE_SECONDS:-300}

[ -d "$town/.git" ] || exit 0
mkdir -p "$state/recovery"
umask 077
now=$(date -u +%FT%TZ)
now_epoch=$(date -u +%s)

log() { printf '%s %s\n' "$now" "$*" >> "$log"; }

# Refusals are logged at most once per throttle window; the durable log is an
# audit record, not a high-volume channel, and the Sentinel alerts hourly anyway.
refusal_file=$state/recovery/last-refusal
refuse() {
    code=$1
    shift
    last_epoch=0
    last_code=
    if [ -s "$refusal_file" ]; then
        read -r last_epoch last_code < "$refusal_file" || {
            last_epoch=0
            last_code=
        }
    fi
    if [ "$last_code" = "$code" ] && [ "$((now_epoch - last_epoch))" -lt "$throttle" ]; then
        exit 1
    fi
    printf '%s %s\n' "$now_epoch" "$code" > "$refusal_file"
    log REFUSED "$code" "$@"
    exit 1
}

# --- Detect the conflict class ---------------------------------------------
if [ -f "$town/.git/MERGE_HEAD" ]; then
    kind=merge
elif [ -f "$town/.git/CHERRY_PICK_HEAD" ]; then
    kind=cherry-pick
elif [ -d "$town/.git/rebase-merge" ] || [ -d "$town/.git/rebase-apply" ]; then
    kind=rebase
elif [ -n "$(git -C "$town" ls-files -u 2>/dev/null)" ]; then
    kind=unmerged-index
else
    exit 0
fi

log CONFLICT_DETECTED kind=$kind

case "$kind" in
    cherry-pick | rebase | unmerged-index)
        # Different in-progress commands with different abort commands and
        # different safety proofs; do not guess. Alert only.
        refuse RECOVERY_NOT_AUTOMATED kind=$kind
        ;;
esac

# --- kind=merge: prove aborting discards no unique work --------------------
head=$(git -C "$town" rev-parse HEAD)
merge_head=$(cat "$town/.git/MERGE_HEAD")

# Evaluate the gates against a current origin/main when reachable; fall back to
# the stale remote-tracking ref if the fetch fails (the post-abort pull will
# still fail safely if origin/main moved).
git -C "$town" fetch origin main 2>/dev/null || true

# Gate 1: every commit reachable from HEAD must survive the fast-forward.
# If HEAD is an ancestor of origin/main, `git pull --ff-only` after the abort
# moves to origin/main and keeps every HEAD commit.
if ! git -C "$town" merge-base --is-ancestor HEAD origin/main 2>/dev/null; then
    refuse HEAD_NOT_ANCESTOR_OF_ORIGIN_MAIN head=$head
fi

# Gate 2: every commit the merge would bring in (HEAD..MERGE_HEAD) must remain
# reachable from a surviving ref after the abort (abort deletes no refs).
if [ "$(git -C "$town" rev-list --count "HEAD..$merge_head" --not --branches --remotes --tags 2>/dev/null)" -ne 0 ]; then
    refuse MERGE_HEAD_UNREACHABLE_AFTER_ABORT merge_head=$merge_head
fi

# Gate 3: staged changes must all come from the merge. reset --merge discards
# staged changes to files the merge did not touch (verified empirically).
staged_list=$state/recovery/staged.$$
touched_list=$state/recovery/touched.$$
trap 'rm -f "$staged_list" "$touched_list"' EXIT HUP INT TERM
git -C "$town" diff --cached --name-only HEAD >"$staged_list" 2>/dev/null || true
git -C "$town" diff --name-only HEAD "$merge_head" >"$touched_list" 2>/dev/null || true
if [ -n "$(grep -Fxv -f "$touched_list" "$staged_list" || true)" ]; then
    refuse STAGED_CHANGES_BEYOND_MERGE
fi

# Gate 4: no hand resolution in progress on conflicted files. Conflict markers
# are the default state (safe to discard); clean custom content matching no
# stage means a resolver edited the file - refuse and let an actor finish.
unmerged=$(git -C "$town" ls-files -u 2>/dev/null | awk '{print $4}' | sort -u)
for f in $unmerged; do
    if [ -f "$town/$f" ] && ! grep -q '^<<<<<<< ' "$town/$f" 2>/dev/null; then
        ours=$(git -C "$town" ls-files -u -- "$f" | awk '$3 == 2 {print $2; exit}')
        theirs=$(git -C "$town" ls-files -u -- "$f" | awk '$3 == 3 {print $2; exit}')
        wt=$(git -C "$town" hash-object "$town/$f" 2>/dev/null || echo none)
        if [ -n "$ours" ] && [ -n "$theirs" ] && [ "$wt" != "$ours" ] && [ "$wt" != "$theirs" ]; then
            refuse RESOLUTION_IN_PROGRESS file=$f
        fi
    fi
done

# --- All gates passed: abort and fast-forward ------------------------------
log SAFE_TO_ABORT head=$head merge_head=$merge_head
if ! git -C "$town" merge --abort; then
    log RECOVERY_FAILED merge_abort_failed
    exit 1
fi
log MERGE_ABORTED
if ! git -C "$town" pull --ff-only; then
    log RECOVERY_FAILED pull_after_abort
    exit 1
fi
new_head=$(git -C "$town" rev-parse HEAD)
if ! git -C "$town" merge-base --is-ancestor "$head" "$new_head" 2>/dev/null; then
    log RECOVERY_FAILED postverify_old_head_unreachable
    exit 1
fi
log RECOVERY_SUCCEEDED new_head=$new_head
exit 0
