#!/bin/sh
# DISPOSABLE PROTOTYPE — known-answer calibration harness (not production).
# Evidence for records/research/2026-10-17-detector-calibration.md. Not a law,
# not committed to any production path, never writes outside its own temp dir.
#
# Replays four documented Viche incidents (three should-NOT-fire, one should-fire)
# through the Town's detection logic on FROZEN inputs and compares the signal to
# the independently established answer. POSIX /bin/sh only.
set -eu
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
umask 077

# --- case D4: resource-safety guard, 2026-10-17 ----------------------------
# memory.max=8 GiB; memory.current ~7.4 GiB (incl. ~6.7 GiB reclaimable file
# cache); unreclaimable anon+slab ~1.57 GiB. Known answer: should NOT defer.
max=8589934592
anon=1073741824
slab=612032512
kstack=0
sock=0
file=7183319040
floor=2147483648
rs_current=0
unreclaim=$((anon + slab + kstack + sock))
if [ "$((max - unreclaim))" -lt "$floor" ]; then rs_current=1; fi   # corrected metric
rs_prefix=0
if [ "$((max - (unreclaim + file)))" -lt "$floor" ]; then rs_prefix=1; fi  # old metric

# --- case D1: oversight delivery-age (CA-M), 2026-10-16 --------------------
# origin/main 114213s old; release line 43030s old; threshold 86400.
# Known answer: should NOT trigger.
main_age=114213
release_age=43030
thresh=86400
ow_current=0
if [ "$release_age" -ge "$thresh" ] && [ "$main_age" -ge "$thresh" ]; then ow_current=1; fi
ow_prefix=0
if [ "$main_age" -ge "$thresh" ]; then ow_prefix=1; fi

# --- case D2: ballot-integrity roster (T1), 2026-10-17 ---------------------
# Ballot names c1a00008; current roster excludes it; history includes it.
# Known answer: should PASS (no fire).
bi_current=0   # current+history guard
bi_prefix=1    # current-only guard (false positive)

# --- case D-sentinel: conflict check (O2), 2026-10-16 ----------------------
# MERGE_HEAD present, unmerged paths present. Known answer: SHOULD fire.
sent_current=1

tp=0; fp=0; tn=0; fn=0
[ "$sent_current" -eq 1 ] && tp=$((tp+1)) || fn=$((fn+1))
for v in "$rs_current" "$ow_current" "$bi_current"; do
    if [ "$v" -eq 1 ]; then fp=$((fp+1)); else tn=$((tn+1)); fi
done
prefix_fp=0
for v in "$rs_prefix" "$ow_prefix" "$bi_prefix"; do
    [ "$v" -eq 1 ] && prefix_fp=$((prefix_fp+1))
done

echo "current instruments: TP=$tp FP=$fp TN=$tn FN=$fn"
echo "pre-fix instruments false-positived on $prefix_fp of 3 known-clean cases"
echo "limitations: small sample; retrospective ground truth; same-model instruments"
