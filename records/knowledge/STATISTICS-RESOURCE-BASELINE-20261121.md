# Act 32: prospective, source-attested resource comparator

**Status: begun, not yet an independently verified outcome comparator or authorization.**

The Nov19 baseline-20261119.json used mutable paths and reported
process counts, not verified effects or measured usage. The Nov20 preflight
correctly rejected that as a false comparator. No Statistics office was
activated. The proper fix is prospective measurement, not retrospectively
inventing a useful-outcome numerator or tokens.

## Measurement

government/statistics-trial-meter.py snapshots the authoritative read-only
OpenCode session_v2 token counters for all sessions whose directory is
exactly the canonical Viche root or is under viche-seats/. It also freezes
the monotone /proc/stat whole-host busy-CPU counter and kernel boot ID.
Snapshots reside in private state with mode 0600 and an exclusive, fsynced
create operation. They cannot be silently overwritten.

Comparison requires two snapshots on the same boot, strictly increasing
timestamps, the same session population plus new sessions whose creation
postdates the first snapshot, and non-decreasing counters. Old sessions that
disappear or reset are unavailable, not zero. The recorded token delta
is the sum of real differences for old session IDs and full counters for
new sessions. This includes development agents in Viche worktrees, not
just government offices. It is consequently not a certified per-office
spend figure. The host CPU busy delta includes all projects, so it is a
pessimistic upper bound on Viche CPU, not a per-office actual number.
Use the same method in subsequent comparison windows, report sample
coverage/missingness, and avoid causal claims from a simple before/after.

## First frozen snapshot

- Path: /var/lib/lubko/wd/viche-state/knowledge/baseline/20261121-prelaunch-start.json
- SHA-256 (raw file): a7f83c7077c38046b90f1e4195bbd383d84894602b634ac67ca89a67fbe90f48
- Viche-directory sessions: 540
- Status: pre-activation; all four offices were disabled
- Privacy: raw session IDs remain in owner-only state; not published in Git

A first short-window check (NOT the full pretrial observation period)
has been collected after 261.635 seconds, with all four offices still disabled.
Its private source file is state/knowledge/baseline/20261121-prelaunch-shortcheck.json,
SHA-256 6d3e44d6d786193ee18e38e8b42edd068f5fa2c9de8692da1ba9be912d62b06d.
Two-source comparison returned 3,569,291 observed Viche-directory OpenCode
tokens (including 3,266,048 cache reads), and 729.62 host busy CPU seconds
(conservative upper bound, overlapping unrelated host work). 540 matching
sessions were present at both endpoints and no sessions were missing. It
establishes that the resource-denominator INSTRUMENT runs against actual
inputs, not that any useful work was accomplished or an office cost was
attributed.

A later full baseline window-end sample must be captured and compared using
the same instrument, at a documented UTC timestamp before any knowledge
office activation. The result's SHA-256 must be recorded independently, and
the Judiciary must inspect both inputs. A missing sample or reboot makes
the single-window comparison invalid. Reboot requires separate windows.

## Outcome endpoint

The primary effect numerator is independently confirmed material operational
repair or other independently accepted actual result, not messages, runs,
commits, auto-closed signals, or forecasts. The Nov21 Judiciary audit
records/JUDICIARY-REPORT-2026-11-21-cycle-d3aea539-sampled-evidence.md
is real independent evidence but its one verified case concerns an external
project and cannot be automatically used as a Viche material repair.

A plausible candidate is the Viche audit-dispatch E2BIG repair at
803de536 and subsequent production post-fix evidence at f2021202,
after seven failures before the fix. Source:
records/investigations/recovery-steward-audit-dispatch-e2big-20261121T1323Z.md.
It is not yet an independently Judiciary-verified effect. Judiciary
issue kiuY9oh8p7JLijkx2F7lJN-comments requests an independent
determination, complete eligible-event population, missingness and
honest matching window, without altering randomized sample selection.

No new office is authorized until a verified numerator, matched resource
denominator, Economy hard cap, real Executive order and independent
Judiciary phase gate satisfy Act 32 D/E/H/K. A positive result from one
case would not prove broad causal effectiveness.
