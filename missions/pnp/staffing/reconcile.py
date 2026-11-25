"""One slot state machine. Persist intent BEFORE any ambiguous side effect."""
import time
import subprocess
import sqlite3
from .. import gitctl
from . import backend, plan, store

ERRORS = (OSError, ValueError, TypeError, RuntimeError, subprocess.SubprocessError, gitctl.GitError, sqlite3.Error)


def update(row, phase, reason="", **kw):
    row.update(phase=phase,reason=reason,**kw)
    return row


def save(slot,row,phase,reason="",event=None,**kw):
    update(row,phase,reason,**kw)
    store.put(slot.key,row,event)
    return row


def delay(p,n):
    return min(p["retry_max"],p["retry_min"]*2**min(12,max(0,n-1)))


def failure(slot,row,p,now,reason,uncertain=False):
    n=row.get("failures",0)+1
    return save(slot,row,"unknown" if uncertain else "retry",reason,"failure",
                failures=n,next_at=now+delay(p,n))


def inspect(slot,row,roster,p,now):
    # Always consider observed running workers, even when a persisted ID exists.
    live=[a for a in roster if backend.same(a,slot.path)]
    if len(live)>1:
        exact=[backend.status(a["id"]) for a in live]
        if any(not backend.same(a,slot.path) or
               not (backend.live(a) or backend.known_terminal(a)) for a in exact):
            return save(slot,row,"unknown","duplicate identities uncertain")
        live=[a for a in exact if backend.live(a)]
        if len(live)>1:
            keep=min(live,key=lambda a:(a["id"]!=row.get("agent"),
                                         a.get("started_at") or 0,a["id"]))
            row=save(slot,row,"unknown","duplicate running identities","duplicate",
                     agent=keep["id"],duplicates=[a["id"] for a in live if a!=keep])
            if not p["paused"] and plan.current(slot):
                for a in live:
                    if a==keep:
                        continue
                    fresh=backend.status(a["id"])
                    if backend.same(fresh,slot.path) and backend.live(fresh) and plan.current(slot):
                        backend.stop(fresh["id"])
            # Confirm retirement on a new observation, never launch here.
            return row
    if live:
        found=backend.status(live[0]["id"])
        if not backend.same(found,slot.path):
            return save(slot,row,"unknown","running identity moved")
        if backend.live(found):
            changed=row.get("agent")!=found["id"] or row.get("phase")!="running"
            return save(slot,row,"running","observed live","adopted" if changed else None,
                        agent=found["id"],started=found.get("started_at",now),
                        activity=found.get("last_activity_at"),model=found.get("model"),
                        vacant_since=None,intent=None,next_at=0,duplicates=[],orphan_since=None)
        # A roster entry may have terminated since enumeration. Preserve its
        # exact identity for recovery, including an explicitly orphaned runner.
        if not row.get("agent") or not backend.known_terminal(found):
            row=save(slot,row,"unknown","reconciling observed identity",agent=found["id"])
    if not row.get("agent"):
        return row
    try:
        found=backend.status(row["agent"])
    except backend.MissingAgent:
        # Explicit authoritative not-found, not a timeout or malformed reply.
        return save(slot,row,"vacant","agent removed; rediscover workspace","identity_lost",
                    agent=None,intent=None,next_at=now+p["retry_min"],vacant_since=now)
    if not backend.same(found,slot.path):
        return save(slot,row,"unknown","stored agent no longer bound to exact workspace","binding_conflict")
    if row.get("reason") in ("duplicate running identities","duplicate identities uncertain",
                             "running identity moved","running observation not confirmed"):
        row=save(slot,row,"vacant","exact identity reconciled",duplicates=[])
    if backend.live(found):
        return save(slot,row,"running","confirmed by exact status",agent=found["id"],
                    started=found.get("started_at",now),activity=found.get("last_activity_at"),model=found.get("model"),vacant_since=None,intent=None,next_at=0,orphan_since=None)
    if not backend.known_terminal(found):
        if found.get("state")=="running" and found.get("alive") is False:
            since=row.get("orphan_since") or now
            row=save(slot,row,"unknown","running identity has no live process",orphan_since=since)
            if not p["paused"] and now-since>=p["ambiguity_grace"] and plan.current(slot):
                # Ask Antonina to repair its own orphan; never signal a PID.
                backend.stop(found["id"])
                row=save(slot,row,"unknown","orphan stop requested","orphan_stop",orphan_since=now)
            return row
        return save(slot,row,"unknown","nonterminal or inconsistent backend state")
    ended=found.get("finished_at") or 0
    started=found.get("started_at") or 0
    if row.get("phase")=="running" or ended>row.get("last_finish",0):
        short=ended-started<p["short_run"] if ended and started else True
        good=found.get("state")=="clearexit" and not short
        n=0 if good else row.get("failures",0)+1
        row=save(slot,row,"vacant","completed" if good else "short or failed invocation",
                 "finished",last_finish=ended,failures=n,finished_ok=good,
                 completed_signature=row.get("launched_signature"),vacant_since=now,
                 intent=None,next_at=now+(p["retry_min"] if good else delay(p,n)))
        if not good and n>=p["rotate_after"]:
            # A fresh agent gets the same durable workspace, not a reset
            # checkout. Do not recycle an exhausted context indefinitely.
            row=save(slot,row,"vacant","rotate repeatedly short/failed context","rotate",
                     retired_agent=found["id"],agent=None,created_after=now,
                     failures=0,next_at=now+p["retry_min"])
    return row


def reconcile(slot,p,roster,history,now=None):
    now=time.time() if now is None else now
    row=store.get(slot.key) or {"path":slot.path,"label":slot.label,"gap":slot.gap,
        "attempt":slot.attempt,"vacant_since":now,"phase":"vacant","failures":0}
    # A read failure never becomes evidence of absence.
    try:
        row=inspect(slot,row,roster,p,now)
    except ERRORS as exc:
        return save(slot,row,"unknown","status unavailable: "+type(exc).__name__)
    if row["phase"]=="running":
        return row
    if row["phase"]=="unknown" and row.get("reason") in (
            "duplicate running identities","stored agent no longer bound to exact workspace",
            "nonterminal or inconsistent backend state","running observation not confirmed",
            "duplicate identities uncertain","running identity has no live process","orphan stop requested","running identity moved"):
        return row
    if p["paused"]:
        return save(slot,row,"paused","operator pause")
    if not plan.current(slot):
        return save(slot,row,"obsolete","assignment changed")
    if row.get("next_at",0)>now:
        return row
    # A run intent can survive process death, a broken pipe or a timeout.
    # Exact status above is authoritative; wait before retrying a terminal
    # status that may predate an in-flight command.
    intent=row.get("intent")
    if intent and intent["at"]>now:
        # Rebase the conservative grace period after a wall-clock rollback.
        return save(slot,row,"unknown","clock moved backwards; renewing ambiguity grace",
                    intent={**intent,"at":now},next_at=now+p["ambiguity_grace"])
    if intent and now-intent["at"]<p["ambiguity_grace"]:
        return save(slot,row,"unknown","awaiting ambiguous operation reconciliation")
    if slot.signature and row.get("finished_ok") and row.get("completed_signature")==slot.signature:
        if now-row.get("last_finish",0)<p["support_refresh"]:
            return save(slot,row,"completed","current evidence already investigated")
    try:
        if not backend.resource_ready():
            return save(slot,row,"deferred","town resource safety guard",next_at=now+p["retry_min"])
        if not row.get("agent"):
            # History must be available and complete before creating a new ID.
            # Idle orphan creation is harmless; never launch two IDs for a slot.
            if history is None:
                return save(slot,row,"unknown","historical roster unavailable")
            candidates=[a for a in history if backend.same(a,slot.path)]
            reusable=[]
            for a in candidates:
                try:
                    exact=backend.status(a["id"])
                except backend.MissingAgent:
                    continue
                if not backend.same(exact,slot.path):
                    return save(slot,row,"unknown","historical identity changed")
                if backend.live(exact):
                    return save(slot,row,"running","adopted historical live agent","adopted",
                                agent=a["id"],intent=None,vacant_since=None,started=exact.get("started_at",now),
                                activity=exact.get("last_activity_at"),model=exact.get("model"))
                if not backend.known_terminal(exact):
                    return save(slot,row,"unknown","historical agent state uncertain")
                if (exact.get("created_at") or 0)>=row.get("created_after",0):
                    reusable.append(exact)
            if reusable:
                aid=max(reusable,key=lambda a:(a.get("created_at") or 0,a["id"]))["id"]
                row=save(slot,row,"vacant","adopted exact historical identity","identity",agent=aid,intent=None)
        backend.prepare(slot)
        if not plan.current(slot):
            return save(slot,row,"obsolete","assignment changed during preparation")
        if not row.get("agent"):
            row=save(slot,row,"unknown","new identity intent","create_intent",
                     intent={"op":"new","at":time.time()})
            aid=backend.new(slot)
            row=save(slot,row,"vacant","created identity","identity",agent=aid,intent=None)
        aid=row["agent"]
        found=backend.status(aid)
        if not backend.same(found,slot.path):
            return save(slot,row,"unknown","stored agent no longer bound to exact workspace")
        if backend.live(found):
            return save(slot,row,"running","observed before run",agent=aid,intent=None,vacant_since=None)
        if not backend.known_terminal(found):
            return save(slot,row,"unknown","nonterminal or inconsistent backend state")
        if not plan.current(slot):
            return save(slot,row,"obsolete","assignment changed before run")
        # A fresh timestamp, not the time the possibly slow preparation began.
        at=time.time()
        row=save(slot,row,"unknown","launch intent","run_intent",
                 intent={"op":"run","at":at},launched_signature=slot.signature,
                 finished_ok=False,last_finish=max(row.get("last_finish",0),found.get("finished_at") or 0))
        backend.run(slot,aid)
        # Ack is not coverage; only a subsequent exact observation is.
        return save(slot,row,"starting","launch acknowledged","ack",next_at=0)
    except ERRORS as exc:
        # No stderr/prompt/credentials in the durable controller journal.
        return failure(slot,row,p,time.time(),"operation "+type(exc).__name__,
                       uncertain=bool(row.get("intent")))
