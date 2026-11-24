# Founder-directed incident review — 2026-11-24

## What the Town got wrong

- Economy queried the unauthenticated OpenCode CLI service, not the authenticated Antonina service. It interpreted missing providers as nonexistent models. The latter service actually listed openai/gpt-6-luna and OpenCode Go models.
- A transient or partial discovery result became a destructive policy decision: Economy removed previously authorized fallbacks and only rediscovered free models. The last historical configuration containing Luna was backed up on November 21 at 14:19:25 UTC. This left the Town unable to use its authorized fallback even when the free tier was exhausted.
- The recovery mechanism accepted the same false premise. At the live November 24 inspection there were five active PnP leases and zero researchers, despite about 10.5 GiB memory headroom. Recovery logs reported all *configured* candidates cooling down. That is not evidence that all authorized providers have exhausted their quotas. The Founder had to correct the diagnosis.
- The funding report conflated absence of free capacity with absence of any model capacity. This obscured both the actual cause and the proper remedy.
- The maintained preference order contradicted the Founder's intended policy: Luna must precede paid OpenCode fallback models. Furthermore, the Antonina backend had stopped requesting low reasoning variants while its status metadata still reported the default low label. A status label alone is not proof of what was requested.

## Corrections

Commit df535065 restored authenticated service discovery, retained authorized nonfree entries across catalogue omissions and list caps, and separated free-tier exhaustion from fallback eligibility. The live config was restored from historical entries. Catalogue presence is not proof that a request will succeed.

Founder direction, November 24: free models first, contributor-plan models next, Luna next, paid OpenCode models last. Every configured model must request low reasoning effort. Do not silently substitute another effort. A provider rejecting low must be diagnosed as such, not treated as exhausted quota or as permission to change effort. Retain base model identities for cooldown accounting. Do not automatically authorize additional paid models.

## Lessons for the Executive, Economy, recovery and Innovation Centre

1. Discovery is observation, not authorization. Partial, stale, failed and unauthenticated discovery must never erase authorization. Verify the identity and authentication scope of the service being measured.
2. An empty eligible set is a symptom, not a root cause. Compare the actual configured candidates, authorized candidates, actual backend and cooldown scope before claiming funding exhaustion. Independently verify the recovery path.
3. Test failure modes end to end: incomplete provider catalogues, lost provider visibility, free-tier exhaustion with Luna available, preservation of authorized fallbacks at the list cap, low variant on both fresh and continued invocations, and honest distinction between configured, eligible and successfully invoked.
4. The Town must recover when capacity exists, without the Founder having to diagnose the funding instrument. Assess actual staffed leases and useful deliveries, not just the existence of scheduled checks.
5. Reuse these lessons across all dependencies. A software observation or failure must not silently invalidate standing permissions or indefinitely disable institutional work. Innovation Centre should consider general improvements, not become an additional approval gate.

The initial catalogue/fallback fix is deployed. The new ordering and low-effort changes are being tested; this record does not assert that they are already deployed or that all providers accept low. The Executive must verify real execution, arrange lawful recovery of old runners, and restore research coverage. Do not launch competing agents outside Executive authority.
