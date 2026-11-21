# Act 32 host CPU budget source: conservative upper bound

## What is counted

OpenCode token totals come from authoritative session_v2 SQLite rows. The
absolute session totals are deliberately used where the exact prelaunch
token baseline cannot be proven; do not claim an exact per-run delta.
CPU accounting is NOT measured per office. The machine /proc/stat aggregate
busy ticks (user, nice, system, irq, softirq, steal; avoid duplicated guest
ticks) are sampled BEFORE detached launch and periodically thereafter.
The full positive busy-CPU delta is charged to EACH overlapping knowledge
office reservation, including unrelated activity. Thus the measured charge
is an upper bound on the office's CPU consumption. This costs more allowance
when the host is busy and can shorten sessions, never less.

The machine boot ID is checked between every sample. Reboot, counter reset,
missing native session row, missing token telemetry, unknown agent state and
corrupt reservation fail closed at full reserved liability. A request to stop
or kill a detached agent is not proof it stopped: the reservation cannot be
closed until Antonina itself reports a terminal state. No office is enabled
by this meter change alone.

This is an ADMISSION and MONITORING budget, not a mathematical guarantee
that CPU cannot overshoot a polled threshold before the next tick or when
the backend cannot be killed. The operator must not label the whole-host
upper bound as attributable per-office actual CPU, even though it suffices
for conservative spending comparisons and protects against undercounting.

All four offices remain disabled until independent Statistics baseline
evidence, Economy review, Judiciary phase check, explicit Executive order
and short unexpired office activation are established.

## Verification

Run tests/knowledge-budget-smoke.sh and tests/knowledge-host-cpu-smoke.sh.
Run python3 government/knowledge-budget-tool.py cpu-meter to see the
whole-host cumulative CPU counter and kernel boot identity.
