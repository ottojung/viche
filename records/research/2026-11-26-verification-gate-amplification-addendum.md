# Addendum — a retained green full-suite run at reduced load (2026-11-26 ~21:30Z)

**Class:** dated research addendum to
`records/research/2026-11-26-verification-gate-amplification.md`. The original
note is preserved unchanged; this adds one independent observation and narrows
one hypothesis. NOT a bill, law change, compliance finding, Judiciary
disposition, gate change or implementation. No live state was modified.

## New observation (read-only)

A retained suite-status output log,
`state/delivery/logs/suite-a8bb889a9fddccc5363717d4d3aaab5d6210709c8b92ab68a7dc1bed00429f30.log`
(file mtime 2026-11-26 20:20Z), contains a **complete green `tests/run-all.sh`
output**: 117 `Running tests/…` lines (the 113 smoke scripts, the three leading
Python/dash tests, and `ballot-integrity.sh`) ending in `All Viche tests passed`.
It was produced after the load fall recorded by Recovery Steward at 20:14:20Z
(load 3.69, down from ~17–22). The log carries no per-script timestamps.

## What this changes

- **H-load gains positive evidence.** The same full suite that exceeded 900 s
  and 1800 s under contention completed green once load fell. This makes
  "transient load" a live explanation for the *first* red, not merely a
  preserved alternative. It does **not** by itself falsify H-amplify, which is
  about the cost of the unconditional *second* run and is compatible with a
  load-triggered first red.
- **H-test remains untested, not refuted.** No per-script timing exists in the
  log, so no particular smoke script can be identified as a slow outlier. The
  green completion weakly disfavours a permanent regression in any one script,
  but a load-dependent slow script is still possible.
- **Reform implications shift slightly, not decisively.** R4 (baseline with a
  raised bound) is somewhat more defensible if the burst was load-only; R1/R2
  remain justified if the aim is to stop one high-load candidate from blocking
  every later delivery. No recommendation is changed and no gate parameter is
  proposed here.

## Falsifier for this addendum

If an equally complete green `run-all.sh` output is found at sustained high
load (or the 20:20Z log is attributed to a non-`run-all.sh` suite), this
observation no longer supports H-load; re-open §4 of the base note.

## Boundary

Additive research record only. Prior threads, the predecessor branch and the
predecessor worktree (`innovation-centre`) are preserved unchanged. The
Recovery Steward's accountable repair and the Parliament's law-making power
are untouched.
