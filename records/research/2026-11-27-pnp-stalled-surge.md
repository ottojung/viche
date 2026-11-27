# Recovery lane for a stalled raw-supply surge

Observed on billy-dev 2026-11-27 16:50 UTC: 125 distinct unsuccessful posting
assignments in the preceding 15 minutes, no generated candidate or opened PR,
1,168 ordinary offers, zero new witness arrivals according to the surge
telemetry. Ordinary supply alone is not a productive competition burst.
Earlier 30-minute sample: 248 assignments, 237 unsupported, 11 bounded
search refusals. No inference that these propositions are false.

Proposed policy: preserve the raw surge classification, its hysteresis,
the broker's cooldown and lease ceiling, and the existing suppression of
speculative certificate compilation. Only after at least 40 distinct
unsupported/unknown posting outcomes across at least 600 s within the last
900 s, zero successful candidate generation/PR publication, fresh telemetry
and no new burst of 50 witnesses, let the existing allocator retain one
already-held uncontested assignment for research and let the existing
staffing controller start at most one general and one tool slot. Keep the
other slots in the posting lane. A successful generation or new witness
burst restores the original full surge priority. A stale, truncated or
unreadable ledger does not enable recovery. Operator pause still wins.
No new desk request, proof-of claim, direct PR or agent lifecycle override.

This is a proposed, independently reviewable policy refinement, not a change
to the live policy before Act 31. The measured thresholds are experimental
and should be checked against actual credited points, not agent counts.
