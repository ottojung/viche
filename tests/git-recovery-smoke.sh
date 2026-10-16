#!/bin/sh
# Smoke test for git-recovery.sh: bounded, non-destructive conflict recovery.
# POSIX /bin/sh only. Runs entirely in scratch clones; never touches a real
# canonical checkout. See records/CONTINUITY-BOOT-DEADLOCK-VERIFICATION-2026-10-16.md.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
failures=0
check() {
    if [ "$1" -eq 0 ]; then
        echo "ok: $2"
    else
        echo "FAIL: $2"
        failures=$((failures + 1))
    fi
}

# setup_safe <dir>: origin/main = M (with L as ancestor); local main = L; a
# conflicted `git merge feature` on f.txt. HEAD (L) is an ancestor of
# origin/main, so recovery is provably safe.
setup_safe() {
    d=$1
    rm -rf "$d"
    mkdir -p "$d"
    git init -q --bare "$d/remote.git"
    git init -q -b main "$d/town"
    git -C "$d/town" config user.name t
    git -C "$d/town" config user.email t@e.st
    git -C "$d/town" remote add origin "$d/remote.git"
    echo base >"$d/town/f.txt"
    echo kbase >"$d/town/k.txt"
    git -C "$d/town" add . && git -C "$d/town" commit -qm base
    git -C "$d/town" checkout -q -b feature
    echo feature >"$d/town/f.txt"
    git -C "$d/town" commit -qam feat
    git -C "$d/town" push -q origin feature
    git -C "$d/town" checkout -q main
    echo local >"$d/town/f.txt"
    echo L >"$d/town/g.txt"
    git -C "$d/town" add . && git -C "$d/town" commit -qm L
    git -C "$d/town" push -q origin HEAD:main
    git -C "$d/town" branch --set-upstream-to=origin/main main
    echo M >"$d/town/m.txt"
    git -C "$d/town" add . && git -C "$d/town" commit -qm M
    git -C "$d/town" push -q origin HEAD:main
    git -C "$d/town" branch --set-upstream-to=origin/main main
    git -C "$d/town" reset -q --hard HEAD~1
    git -C "$d/town" merge feature >/dev/null 2>&1 || true
}

# setup_local_only <dir>: origin/main = B; local main = L (unpushed); conflicted
# merge. HEAD (L) is NOT an ancestor of origin/main -> recovery must refuse.
setup_local_only() {
    d=$1
    rm -rf "$d"
    mkdir -p "$d"
    git init -q --bare "$d/remote.git"
    git init -q -b main "$d/town"
    git -C "$d/town" config user.name t
    git -C "$d/town" config user.email t@e.st
    git -C "$d/town" remote add origin "$d/remote.git"
    echo base >"$d/town/f.txt"
    echo kbase >"$d/town/k.txt"
    git -C "$d/town" add . && git -C "$d/town" commit -qm base
    git -C "$d/town" push -q origin HEAD:main
    git -C "$d/town" branch --set-upstream-to=origin/main main
    git -C "$d/town" checkout -q -b feature
    echo feature >"$d/town/f.txt"
    git -C "$d/town" commit -qam feat
    git -C "$d/town" push -q origin feature
    git -C "$d/town" checkout -q main
    echo local >"$d/town/f.txt"
    echo L >"$d/town/g.txt"
    git -C "$d/town" add . && git -C "$d/town" commit -qm L
    git -C "$d/town" merge feature >/dev/null 2>&1 || true
}

# setup_rebase <dir>: a conflicted rebase in progress.
setup_rebase() {
    d=$1
    rm -rf "$d"
    mkdir -p "$d"
    git init -q --bare "$d/remote.git"
    git init -q -b main "$d/town"
    git -C "$d/town" config user.name t
    git -C "$d/town" config user.email t@e.st
    git -C "$d/town" remote add origin "$d/remote.git"
    echo base >"$d/town/f.txt"
    git -C "$d/town" add . && git -C "$d/town" commit -qm base
    git -C "$d/town" push -q origin HEAD:main
    git -C "$d/town" branch --set-upstream-to=origin/main main
    git -C "$d/town" checkout -q -b topic
    echo topic >"$d/town/f.txt"
    git -C "$d/town" commit -qam topic
    git -C "$d/town" checkout -q main
    echo main2 >"$d/town/f.txt"
    git -C "$d/town" commit -qam main2
    git -C "$d/town" checkout -q topic
    git -C "$d/town" rebase main >/dev/null 2>&1 || true
}

run_recovery() {
    VICHE_TOWN_ROOT="$1/town" VICHE_STATE_ROOT="$1/state" /bin/sh "$repo/government/git-recovery.sh"
}

echo "=== 1. no conflict: exit 0, no log ==="
d=$scratch/s1
mkdir -p "$d"
git init -q --bare "$d/remote.git"
git init -q -b main "$d/town"
git -C "$d/town" config user.name t
git -C "$d/town" config user.email t@e.st
git -C "$d/town" remote add origin "$d/remote.git"
echo x >"$d/town/f.txt"
git -C "$d/town" add . && git -C "$d/town" commit -qm x
git -C "$d/town" push -q origin HEAD:main
    git -C "$d/town" branch --set-upstream-to=origin/main main
run_recovery "$d"
check $? "no-conflict exit 0"
[ ! -e "$d/state/recovery/git-recovery.log" ]
check $? "no-conflict writes no log"

echo "=== 2. safe conflict: recovery succeeds, deadlock broken ==="
d=$scratch/s2
setup_safe "$d"
test -f "$d/town/.git/MERGE_HEAD"
check $? "precondition: conflicted"
run_recovery "$d"
check $? "safe recovery exit 0"
[ ! -f "$d/town/.git/MERGE_HEAD" ]
check $? "MERGE_HEAD cleared"
git -C "$d/town" pull --ff-only >/dev/null 2>&1
check $? "boot reconcile (pull --ff-only) now succeeds"
grep -q RECOVERY_SUCCEEDED "$d/state/recovery/git-recovery.log"
check $? "RECOVERY_SUCCEEDED logged"
old_head=$(git -C "$d/town" rev-parse HEAD)
run_recovery "$d"
check $? "idempotent second run exits 0"

echo "=== 3. local-only commits: refused, conflict preserved ==="
d=$scratch/s3
setup_local_only "$d"
run_recovery "$d" && rc=0 || rc=1
[ "$rc" -eq 1 ]
check $? "local-only refused (exit 1)"
test -f "$d/town/.git/MERGE_HEAD"
check $? "MERGE_HEAD preserved on refusal"
grep -q HEAD_NOT_ANCESTOR_OF_ORIGIN_MAIN "$d/state/recovery/git-recovery.log"
check $? "HEAD_NOT_ANCESTOR_OF_ORIGIN_MAIN logged"

echo "=== 4. staged change beyond merge: refused, staged file preserved ==="
d=$scratch/s4
setup_safe "$d"
echo extra >"$d/town/extra.txt"
git -C "$d/town" add extra.txt
run_recovery "$d" && rc=0 || rc=1
[ "$rc" -eq 1 ]
check $? "staged-beyond-merge refused (exit 1)"
test -f "$d/town/extra.txt"
check $? "staged extra.txt preserved"
grep -q STAGED_CHANGES_BEYOND_MERGE "$d/state/recovery/git-recovery.log"
check $? "STAGED_CHANGES_BEYOND_MERGE logged"

echo "=== 5. hand resolution in progress: refused ==="
d=$scratch/s5
setup_safe "$d"
echo custom-resolution >"$d/town/f.txt"
run_recovery "$d" && rc=0 || rc=1
[ "$rc" -eq 1 ]
check $? "resolution-in-progress refused (exit 1)"
grep -q RESOLUTION_IN_PROGRESS "$d/state/recovery/git-recovery.log"
check $? "RESOLUTION_IN_PROGRESS logged"

echo "=== 6. unstaged mod to merge-untouched file: preserved ==="
d=$scratch/s6
setup_safe "$d"
echo kmod >>"$d/town/k.txt"
run_recovery "$d"
check $? "recovery with unstaged mod exit 0"
grep -q kmod "$d/town/k.txt"
check $? "unstaged k.txt mod preserved"

echo "=== 7. untracked file: preserved ==="
d=$scratch/s7
setup_safe "$d"
echo u >"$d/town/u.txt"
run_recovery "$d"
check $? "recovery with untracked file exit 0"
test -f "$d/town/u.txt"
check $? "untracked u.txt preserved"

echo "=== 8. rebase conflict: not automated, state intact ==="
d=$scratch/s8
setup_rebase "$d"
test -d "$d/town/.git/rebase-merge" -o -d "$d/town/.git/rebase-apply"
check $? "precondition: rebase in progress"
run_recovery "$d" && rc=0 || rc=1
[ "$rc" -eq 1 ]
check $? "rebase not automated (exit 1)"
test -d "$d/town/.git/rebase-merge" -o -d "$d/town/.git/rebase-apply"
check $? "rebase state intact"
grep -q RECOVERY_NOT_AUTOMATED "$d/state/recovery/git-recovery.log"
check $? "RECOVERY_NOT_AUTOMATED logged"

echo "=== 9. end-to-end: boot cycle() short-circuits on conflict, resumes after recovery ==="
d=$scratch/s9
setup_safe "$d"
town=$d/town
cat >"$d/cycle.sh" <<EOF
#!/bin/sh
town=$town
reconcile() { git -C "\$town" pull --ff-only || return 1; }
sitting() { echo SITTING_RAN; }
cycle() {
    reconcile || { echo "Viche: government integration/reconciliation failed" >&2; return 1; }
    sitting
}
cycle
EOF
out=$(/bin/sh "$d/cycle.sh" 2>/dev/null) && rc=0 || rc=1
[ "$rc" -eq 1 ]
check $? "cycle short-circuits on conflict"
printf '%s' "$out" | grep -q SITTING_RAN && check 1 "sitting not invoked during conflict" || check 0 "sitting not invoked during conflict"
run_recovery "$d"
check $? "recovery in e2e scenario"
out=$(/bin/sh "$d/cycle.sh" 2>/dev/null) && rc=0 || rc=1
[ "$rc" -eq 0 ]
check $? "cycle succeeds after recovery"
printf '%s' "$out" | grep -q SITTING_RAN
check $? "sitting resumes after recovery"

echo
if [ "$failures" -ne 0 ]; then
    echo "Git recovery smoke checks FAILED ($failures)"
    exit 1
fi
echo "Git recovery smoke checks passed"
