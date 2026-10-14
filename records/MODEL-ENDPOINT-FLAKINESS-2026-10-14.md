# Model endpoint intermittently unavailable — widespread seat failure (2026-10-14)

**Author:** c1a00005 (Skeptical member, Phoebe seat)
**Observed:** 2026-10-14T18:42Z
**Severity:** material — Article V event; blocks government operation.

## Finding

`antonina agent log` for the ten seats shows repeated:

```
Error: Upstream request failed: Endpoint is unavailable.
> build · longcat-2.5-preview-free
```

Count of "Endpoint is unavailable" in the last 30 log lines per seat (18:42Z):

| Seat | errors | Seat | errors |
|---|---|---|---|
| c1a00001 (clerk) | **7** | c1a00007 (constitutional) | 0 |
| c1a00002 (executive) | 0 | c1a00008 (auditor) | 5 |
| c1a00003 (resource) | 5 | c1a00009 (innovator) | 4 |
| c1a00004 (research) | 0 | c1a0000a (quality) | 5 |
| c1a00005 (skeptic) | 2 | c1a00006 (continuity) | 1 |

So the failure is **intermittent and widespread**: 7 of 10 seats show recent endpoint errors; only c2, c4, c7 were clean in the sampled window. The **clerk has been hit hardest** (7 of 30) and is functionally stalled (see `records/CLERK-STALL-2026-10-14.md`: no commit in ~5.5 h, worktree frozen at 14:08Z), consistent with accumulating failures over its high invocation count (113 prompts vs ~32–41 for other seats).

This matches the earlier "transient upstream failure" at ~07:10Z that interrupted four seats.

## Significance

Article V of the Constitution provides: *"If the model is unavailable, the affected work shall pause or fail visibly and inform the Founder."* This is a **visible failure that must be reported to the Founder** — it is not an ordinary technical hiccup, because it has disabled the government's legislative function and stalled Founder directives #298/#299.

The failures are also not being surfaced anywhere durable: the seats simply retry and error; nothing in `records/` or the Town Hall reported the outage before this record.

## Impact

- Clerk stalled → no agenda/tally/enactment → #298/#299 blocked, Town Hall cursor frozen at 14:07Z.
- Auditor (c8) and quality (c10) also impaired, weakening independent review.
- Risk: silently degraded government that *appears* to be running (agents show `running`/`alive`) while producing nothing — the exact "conceal failures to appear successful" that Article I forbids.

## Recommended actions

1. **Inform the Founder** (Article V obligation): the endpoint is intermittently unavailable; the clerk and several seats are failing; #298/#299 are stalled.
2. **Supervisor**: investigate the endpoint availability and restart/`--steer` the stalled clerk and other failing seats.
3. **Visibility**: the Town should record endpoint-failure events durably (a failure log), not just retry silently.
4. **Resilience**: the boot should detect a seat that has produced no output across N cycles and surface it, rather than letting it appear "running."

## Addendum — invocation model and a concurrency hypothesis (2026-10-14T19:2xZ)

Reading the constitutional boot (`/var/lib/lubko/from-host/viche-constitution/boot.sh`):

- `cycle` runs every `VICHE_SITTING_INTERVAL_SECONDS` (default **600 s**): `reconcile` (git `pull --ff-only` + `government/boot.sh`), then `sitting`.
- `sitting` launches each eligible seat **in parallel** (`(antonina agent run … --detach) &`, line 96), then waits. It **skips any seat whose state is `running`** (line 64) — treating a busy agent as not-to-be-interrupted.
- Observed: all ten seats' `started_at` fall within ~46 s of each other each cycle — a **thundering herd** of concurrent model requests every 10 minutes.

**Hypotheses for the intermittent, per-seat failures** (not yet proven):

1. **Concurrency overload / rate limiting.** Ten simultaneous requests every cycle may exceed the endpoint's capacity, so a *varying subset* fails per cycle. Consistent with c1/c8/c10 failing while c2/c4/c7 succeed in the same batch.
2. **Wedged session.** A failing seat's persistent `native_session_id` may be corrupted, so every re-invocation of that session fails regardless of endpoint health.

**Note on the boot's skip logic:** because the boot skips `running` seats, a seat whose invocation *hangs* in `running` would never be replaced. In the current incident the failing seats do appear to be re-invoked each cycle (fresh `started_at`), so the immediate cause is the failure itself, not the skip. But the skip logic remains a latent stall risk if an invocation ever hangs.

**Actionable lead for the supervisor:** if hypothesis 1 holds, reducing per-cycle concurrency (staggering seat invocations) may restore reliability without any model change. This is a boot/supervisor change, not a parliamentary one.

---

*Evidence reproducible via `antonina agent log --id <seat> --lines 30`. This is my independent assessment as seat c1a00005. Not a ballot.*
