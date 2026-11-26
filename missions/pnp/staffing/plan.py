"""Pure desired-state derivation; no agent or desk mutations."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
from contextlib import closing
import sqlite3

from .. import assignment, config, continuity, focus, staff, state, support
from . import policy


@dataclass(frozen=True)
class Slot:
    path: str
    label: str
    task: str
    gap: str = ""
    attempt: str = ""
    signature: str = ""
    base: str = ""
    priority: int = 0

    @property
    def key(self):
        return hashlib.sha256(self.path.encode()).hexdigest()[:32]


def bound(rec, label, task, priority, base=""):
    path = Path(state.gap_dir(rec["gap_id"]), "attempts",
                assignment.attempt_id(rec["lease"]), "workers", label, "path")
    return Slot(str(path), label, task, rec["gap_id"], support.attempt(rec),
                base=base, priority=priority)


def current(slot):
    if not slot.gap:
        return True
    rec = state.load(slot.gap)
    return bool(rec and focus.eligible(rec) and support.attempt(rec) == slot.attempt
                and staff.current_matches(rec, slot.label == "general"))


def obligation_slots(rec, running, limit):
    """Allocate useful, unowned critical-path work, not arbitrary demo nodes."""
    from ..research import knowledge, obligations
    attempt = support.attempt(rec)
    with closing(knowledge.db()) as c:
        graph = obligations.ready(c)
        nodes = {n["id"]: n for n in graph}
        roots = [n for n in graph if n["status"] in ("ready", "blocked")
                 and knowledge.belongs(c, n["id"], rec["gap_id"]+" / "+attempt)]
        pending = set()
        if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pending_check'").fetchone():
            pending = {r[0] for r in c.execute(
                "SELECT DISTINCT node FROM pending_check WHERE state IN ('submitting','queued')")}
    impact = {}
    for root in roots:
        # Follow exact dependencies even when they originated in another family.
        stack = list(root["dependencies"])
        seen = set()
        while stack:
            oid = stack.pop()
            if oid in seen or oid not in nodes:
                continue
            seen.add(oid)
            if nodes[oid]["status"] in ("checked", "refuted"):
                continue
            impact[oid] = impact.get(oid, 0)+1
            stack.extend(nodes[oid]["dependencies"])
        if " ".join(root["statement"].split()) == " ".join(rec["statement"].split()):
            impact[root["id"]] = impact.get(root["id"], 0)+1
    paths = {a.get("invocation_cwd") or a.get("cwd") for a in running}
    ranked = []
    for oid,n in nodes.items():
        label = "ob-"+oid
        slot = bound(rec,label,"Solve exact obligation "+oid+
                     ". Inspect it, submit a proof body, collect the check, and share the result. Preserve exact blockers.",2,n["base"])
        live = slot.path in paths
        if n["status"]!="ready" or (not live and (oid not in impact or oid in pending)):
            continue
        if any(a["attempt"]==attempt and a["worker"]!=label for a in n["assignments"]):
            continue
        ranked.append((not live,-impact.get(oid,0),oid,slot))
    return [x[3] for x in sorted(ranked)[:limit]]


def desired(p, running, issues=None):
    issues = [] if issues is None else issues
    records=[]
    for gap in state.all_gaps():
        try:
            r=state.load(gap)
            if support.active(r) and not r.get("queued_lease"):
                records.append(r)
        except Exception as exc:
            issues.append(gap+": state "+type(exc).__name__)
    try:
        selected=focus.current()
    except Exception as exc:
        selected=None
        issues.append("focus: "+type(exc).__name__)
    slots = [bound(r, "general", staff.GENERAL_APPROACH, 0) for r in records]
    if selected and focus.eligible(selected):
        if focus.correction(selected):
            slots.append(bound(selected, "correction", "Repair the exact published proof using checker diagnostics.", 1))
        else:
            for label, task in continuity.FRONTS:
                slots.append(bound(selected, label, task, 1))
            try:
                if p["focus_obligations"] and (Path(config.STATE_ROOT)/"research/knowledge.sqlite").exists():
                    slots.extend(obligation_slots(selected, running, p["focus_obligations"]))
            except Exception as exc:
                issues.append("obligation planning: "+type(exc).__name__)
        for x in p["extras"]:
            if x["gap"] == selected["gap_id"] and x["attempt"] == support.attempt(selected):
                slots.append(bound(selected,x["label"],x["approach"],2))
    for role in continuity.required_support(records):
        # Stable evidence signatures, plus bounded periodic refresh. Independent
        # method/tool fronts continue even without a lease.
        try:
            sig = continuity.signature(role,records,selected)
        except Exception as exc:
            issues.append(role+": signature "+type(exc).__name__)
            continue
        if role in support.FAMILY_ROLES:
            # No dependency on the old fixed ten-minute cadence.
            sig = role
        path = continuity.support_path(role)
        slots.append(Slot(str(path),role,continuity.SUPPORT[role],signature=sig,priority=3))
    return slots


def obsolete(agent, slots):
    """Only retire exact bound workspaces, never arbitrary agents by title."""
    cwd = agent.get("invocation_cwd") or agent.get("cwd")
    if not cwd:
        return False
    path = Path(cwd)
    binding = assignment.binding(path)
    if not binding:
        return False
    rec = state.load(binding[0])
    if not rec:
        return False  # missing/corrupt authority is uncertainty
    if rec.get("lease") != binding[1]:
        return True
    if rec.get("state") in ("RELEASED", "STALE", "ACCEPTED"):
        return True
    label = assignment.worker_label(path)
    selected = focus.current()
    # Publication/correction transitions are not a license to interrupt a
    # worker mid-submit. Retire off-focus specialists only in research state.
    if support.active(rec) and label != "general" and selected:
        if focus.key(rec) != focus.key(selected):
            return True
        # A policy explicitly removes extra positions.  Exact obligation
        # specialists finish their current pass while ready; once the node is
        # checked, refuted, or blocked there is no remaining mathematical work
        # and the controller may retire the exact workspace identity.
        if label and label.startswith("extra-"):
            return str(path) not in {s.path for s in slots}
        if label and label.startswith("ob-"):
            try:
                from ..research import knowledge, obligations
                with closing(knowledge.db()) as c:
                    node=next((n for n in obligations.ready(c) if n["id"]==label[3:]),None)
                return bool(node and node["status"] in ("checked","refuted","blocked"))
            except (OSError,ValueError,KeyError,AttributeError,sqlite3.Error):
                return False
    return False
