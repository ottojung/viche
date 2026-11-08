#!/bin/sh
# Seat registration must be all-or-nothing per seat, never per government.
#
# Root cause this guards against (reported as H-1794095844-7aa5): the old
# presence test `[ -f "$seat_dir/.git" ]` treated a DANGLING .git file as a
# registered seat, silently skipping repair, and a non-empty seat directory
# without .git hit `exit 1`, aborting reconciliation for every later seat. Eight
# of ten live seats were broken this way.
#
# The test runs government/boot.sh against a minimal hermetic town: every later
# stage of boot.sh is conditional on a script that does not exist here, so only
# seat reconciliation runs. POSIX /bin/sh only.
set -eu
root=$(git rev-parse --show-toplevel)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' 0

town=$scratch/town
seats=$scratch/seats
mkdir -p "$town/government" "$seats" "$scratch/bin" "$scratch/state"

git -C "$town" init -q
printf '# Test laws (boot.sh only requires a non-empty file)\n' > "$town/government/LAWS.md"
printf 'aaaa\tSeat A\tfirst seat\nbbbb\tSeat B\tsecond seat\n' > "$town/government/seats.tsv"
printf 'seed\n' > "$town/README"
git -C "$town" add README government/LAWS.md government/seats.tsv
git -C "$town" -c user.name='Seat Smoke' -c user.email='seat@example.invalid' \
    commit -qm 'Test: hermetic town for seat registration'

# boot.sh requires the Antonina CLI to exist; reconciliation itself must not
# call it when seat-liveness.sh is absent from this minimal town.
cat > "$scratch/bin/antonina" <<'MOCK'
#!/bin/sh
exit 0
MOCK
chmod +x "$scratch/bin/antonina"

# Seat A: dangling .git file. The old presence test skipped this seat entirely.
mkdir -p "$seats/aaaa"
printf 'gitdir: %s\n' "$scratch/vanished/worktrees/aaaa" > "$seats/aaaa/.git"
printf 'seat A work\n' > "$seats/aaaa/seat-note.txt"

# Seat B: non-empty directory with no .git. The old code exited 1 here, so no
# later seat was ever reconciled.
mkdir -p "$seats/bbbb"
printf 'seat B work\n' > "$seats/bbbb/seat-note.txt"

PATH=$scratch/bin:$PATH \
VICHE_TOWN_ROOT=$town \
VICHE_SEATS_ROOT=$seats \
VICHE_STATE_ROOT=$scratch/state \
    /bin/sh "$root/government/boot.sh"

# Both seats must now be usable Git worktrees, not just directories with a .git.
for id in aaaa bbbb; do
    git -C "$seats/$id" rev-parse --git-dir >/dev/null 2>&1 || {
        echo "FAIL: seat $id was not re-registered" >&2
        exit 1
    }
done

# Reconciliation must have continued past the first broken seat to the second:
# both are registered worktrees of the town repository.
git -C "$town" worktree list --porcelain > "$scratch/worktrees"
for id in aaaa bbbb; do
    grep -Fxq "worktree $seats/$id" "$scratch/worktrees" || {
        echo "FAIL: seat $id is not a registered worktree" >&2
        exit 1
    }
done

# Nothing may be discarded: each broken directory is preserved in a timestamped
# backup that still holds the seat's untracked work.
for id in aaaa bbbb; do
    backup=
    for candidate in "$seats/$id".backup-*; do
        [ -d "$candidate" ] && backup=$candidate
    done
    [ -n "$backup" ] || {
        echo "FAIL: no backup preserved for broken seat $id" >&2
        exit 1
    }
    [ -f "$backup/seat-note.txt" ] || {
        echo "FAIL: backup for $id lost the seat's working file" >&2
        exit 1
    }
done

printf '%s\n' 'Viche: broken seats are preserved, re-registered, and never abort later seats'
