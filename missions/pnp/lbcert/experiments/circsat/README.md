# Bounded SAT circuit synthesis experiment (2026-11-26)

This is intentionally outside generator discovery. It encodes each gate's operation,
earlier input wires, and truth-table values, and bounds SAT work by conflicts and
wall time. Independent exhaustive truth-table evaluation audits returned circuits.
The monotone-factor and one-inversion heuristics are also implemented.

Live evaluation: 11 matching open truth-table circuit problems, zero generated
witnesses within the bounded search; no exact historical matches in the 4,000
most recent numbered merged theorem files scanned. Refusal means unknown, not
unsatisfiable. Do not install this as a production generator without a positive
real holdout and evidence that it beats the deployed generator.
