"""Pure desired-state derivation; no agent or desk mutations."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
from contextlib import closing

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
                from ..research import knowledge, obligations
                if (Path(config.STATE_ROOT)/"research/knowledge.sqlite").exists():
                    with closing(knowledge.db()) as c:
                        nodes = [n for n in obligations.ready(c) if n["status"] == "ready"
                                 and knowledge.belongs(c, n["id"], selected["gap_id"]+" / ")]
                    # Keep currently running ready fronts before allocating new ones.
                    paths = {a.get("cwd") for a in running}
                    nodes.sort(key=lambda n: (bound(selected,"ob-"+n["id"],"",2).path not in paths,n["id"]))
                    for n in nodes[:p["focus_obligations"]]:
                        slots.append(bound(selected, "ob-"+n["id"],
                            "Solve exact obligation "+n["id"]+
                            ". Inspect it, submit a proof body, collect the check, and share the result. Preserve exact blockers.", 2,n["base"]))
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
        # A policy explicitly removes extra positions; existing checked
        # obligation specialists may finish without preemption.
        if label and label.startswith("extra-"):
            return str(path) not in {s.path for s in slots}
    return False
