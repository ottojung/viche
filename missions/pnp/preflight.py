"""Cheap, attempt-scoped proof generators; no leases, agents, builds or publication."""
import argparse
import hashlib
import json
from pathlib import Path

from . import assignment, state, support, tools, validate
from .proofs import circuit, synthesis


def paths(rec):
    d=support.directory(rec)/"preflight"
    return d, d/"report.json"


def read(rec):
    if not support.active(rec):
        return None
    d,p=paths(rec)
    try:
        report=json.loads(p.read_text())
        if report.get("attempt")!=support.attempt(rec):
            return None
        if report.get("result")=="candidate":
            f=d/"candidate.lean"
            if hashlib.sha256(f.read_bytes()).hexdigest()!=report.get("sha256"):
                return None
        return report
    except (OSError,ValueError,AttributeError):
        return None


def run(rec, revision):
    if not support.active(rec):
        return None
    previous=read(rec)
    if previous and previous.get("tools_revision")==revision:
        return previous
    meta={"id":rec["gap_id"],"file":rec["path"],"module":rec["module"],
          "statement":rec["statement"],"imports":rec["imports"]}
    result={"attempt":support.attempt(rec),"tools_revision":revision,
            "result":"not_recognized","local_lean_checked":False}
    source=None
    try:
        r=circuit.explicit_circuit(meta)
        if r is not None:
            result.update(generator="explicit",details=r,result="no_candidate")
            if r.get("verified"):
                source=circuit.render(meta,"decide")
        else:
            r=synthesis.candidate(meta)
            if r is not None:
                source=r.pop("candidate",None)
                result.update(generator="synthesis",details=r,result="no_candidate")
        if source:
            validate.validate(meta,source.encode())
            result.update(result="candidate",sha256=hashlib.sha256(source.encode()).hexdigest(),
                          candidate=str(paths(rec)[0]/"candidate.lean"))
    except (ValueError,TypeError,KeyError,validate.InvalidCandidate) as exc:
        result.update(result="generator_error",error=str(exc)[:500])
        source=None
    with state.lock(rec["gap_id"]):
        latest=state.load(rec["gap_id"])
        if not support.active(latest) or support.attempt(latest)!=result["attempt"]:
            return None
        d,p=paths(latest)
        if source:
            state.atomic_write(str(d/"candidate.lean"),source)
        state.atomic_write(str(p),json.dumps(result,ensure_ascii=False)+"\n")
    return result


def scan():
    revision=tools.snapshot()["revision"]
    rows=[]
    for gap in state.all_gaps():
        rec=state.load(gap)
        if support.active(rec):
            r=run(rec,revision)
            if r:
                rows.append({"gap":gap,**r})
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scan",action="store_true")
    ns=p.parse_args()
    if ns.scan:
        print(json.dumps(scan(),ensure_ascii=False,indent=2))
        return
    tools.record("preflight")
    gap,lease=assignment.resolve()
    rec=state.load(gap)
    if not support.active(rec) or rec["lease"]!=lease:
        p.error("live bound assignment required")
    print(json.dumps(run(rec,tools.snapshot()["revision"]),ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
