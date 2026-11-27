# Private receipt admission (disabled by default)

This delivery implements the separate Executive conditional authorization
`records/investigations/executive-conditional-authorization-broker-receipt-promotion-20261126T2249Z.md`.
It does not activate the checker or promoter. Only the Executive may activate
either after the separate reviewed exact-candidate integration gates.

The allocator's existing observation process performs a bounded read-only
competition observation (five IDs maximum, at most once per 20 seconds), with
fair rotation and no probe while the global desk cooldown is active. Missing,
stale, incomplete or contested observations do not qualify. GitHub search and
catalog data remain observations, not a guarantee of exclusive availability.
The posting pass admits at most one exact receipt under the ordinary acquisition
lock, with nonblocking exclusion against the private checker. It does not
invoke a desk API or initiate publication. Every attempted admission is logged
in the existing ledger with its check results and reason.

An existing private receipt must include the exact original source, guarded
source digest and the bounded compiler transcript and transcript digest.
The promoter replays the canonical emitter audit and checks the strict final
axiom report again. Older receipts lacking the transcript are not admitted.
It independently checks local public ancestry, the pinned private checkout
HEAD, authorization, fresh catalog and complete status, direct competition,
known offerability, capacity, and retry state. It rechecks authorization
immediately before recording.

For a private proof stored only in the batch database, the existing
`ready.record` path has an optional private mode that first atomically links
the exact source into the existing candidate store, without overwriting any
source or marker. An interrupted admission can leave the source without a
checked marker, which never qualifies as an exact receipt. The marker preserves
the check time, not the promotion time. The existing fast lane understands
such a marker without requiring a generator-specific .status file.

After review and deployment, only the Executive can create the distinct
owner-only `promote.json` in the private state directory, with exact keys:
`enabled` (true), `base` (the same upstream SHA as the checker),
`checker_authorization` (matching enable.json), and `authorization` (the
Executive's separate promotion authorization ID). No code creates these flags.
Removing either flag, or STOP, disables admission. Existing stock is managed
by the normal broker; no new claim policy is introduced.
