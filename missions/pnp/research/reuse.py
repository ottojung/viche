"""Measure consumption of checked mathematical dependencies, not searches."""
import json
import time

from .. import state, support


def table(c):
    c.execute("""CREATE TABLE IF NOT EXISTS assembled_candidate(
        gap TEXT, attempt TEXT, digest TEXT, root TEXT REFERENCES object(id),
        base TEXT, dependencies TEXT, cross_attempt INTEGER, at REAL,
        PRIMARY KEY(gap,attempt,digest)
    )""")
    c.commit()


def record(c, rec, oid, base, digest):
    from . import obligations as o
    table(c)
    nodes=o.plan(c,oid)
    prefix=rec["gap_id"]+" / "+support.attempt(rec)
    # An exact checked closure, not a similarity recommendation. Count
    # previously proven dependencies with evidence from another provenance.
    deps=[n["id"] for n in nodes if n["id"]!=oid]
    reused=0
    for node in deps:
        rows=c.execute("SELECT provenance FROM origin WHERE node=?",(node,)).fetchall()
        if any(not r[0].startswith(prefix) for r in rows):reused+=1
    with c:
        c.execute("INSERT OR IGNORE INTO assembled_candidate VALUES(?,?,?,?,?,?,?,?)",
            (rec["gap_id"],support.attempt(rec),digest,oid,base,json.dumps(deps),reused,time.time()))


def report(c):
    from . import obligations as o
    table(c)
    checked={(r["node"],r["base"]) for r in c.execute(
        "SELECT node,base,artifact,source_digest,result FROM proof WHERE json_extract(result,'$.status')='kernel_checked'")
        if o.verified_record(r)}
    deps=0; consumed=set(); cross_origin=0
    for row in c.execute("""SELECT e.source,e.target,o.base FROM edge e JOIN object o ON o.id=e.source
                            WHERE e.relation='requires'"""):
        src,dst,base=row
        if (src,base) in checked and (dst,base) in checked:
            deps+=1;consumed.add(dst)
            origins=lambda n:{r[0] for r in c.execute("SELECT provenance FROM origin WHERE node=?",(n,))}
            if origins(src).isdisjoint(origins(dst)):cross_origin+=1
    rows=[dict(r) for r in c.execute("SELECT * FROM assembled_candidate")]
    published=[];accepted=[]
    for r in rows:
        rec=state.load(r["gap"])
        if rec and rec.get("candidate_digest")==r["digest"] and rec.get("pr_number"):
            published.append(r)
            if rec.get("external_verdict")=="ACCEPTED":accepted.append(r)
    return {"checked_nodes":len(checked),"checked_dependency_edges":deps,
            "distinct_consumed_dependencies":len(consumed),
            "cross_origin_checked_edges":cross_origin,
            "assembled_candidates":len(rows),"assemblies_using_prior_origins":sum(r["cross_attempt"]>0 for r in rows),
            "exact_digest_published":len(published),"exact_digest_checker_accepted":len(accepted),
            "note":"Historical dependency counts reflect checked graph closures; assembly-to-PR counts begin with instrumentation. Cross-origin is a provenance proxy, not proof of saved time. Current PR revision only."}
