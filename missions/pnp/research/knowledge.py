"""Durable mathematical research objects, independent of lease lifetimes."""
import argparse
from contextlib import closing
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import time

from .. import config, state

KINDS = ("lemma", "technique", "obstruction", "counterexample", "reduction",
         "certificate", "obligation", "finding", "fragment")
MAX_ARTIFACT = 512 * 1024
def digest(x):
    return hashlib.sha256(x).hexdigest()

def canon(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def root():
    p = Path(config.STATE_ROOT) / "research"
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    return p

def db():
    c = sqlite3.connect(root() / "knowledge.sqlite", timeout=5)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS object(
      id TEXT PRIMARY KEY, kind TEXT NOT NULL, family TEXT NOT NULL,
      statement TEXT NOT NULL, detail TEXT NOT NULL, provenance TEXT NOT NULL,
      artifact TEXT, base TEXT, created REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS edge(
      source TEXT REFERENCES object(id), target TEXT REFERENCES object(id),
      relation TEXT NOT NULL, PRIMARY KEY(source,target,relation)
    );
    CREATE TABLE IF NOT EXISTS proof(
      node TEXT REFERENCES object(id), base TEXT, artifact TEXT,
      source_digest TEXT, result TEXT, checked REAL,
      PRIMARY KEY(node,base,artifact)
    );
    CREATE TABLE IF NOT EXISTS assignment(
      node TEXT REFERENCES object(id), attempt TEXT, worker TEXT, at REAL,
      PRIMARY KEY(node,attempt)
    );
    CREATE INDEX IF NOT EXISTS object_family ON object(family,kind);
    CREATE INDEX IF NOT EXISTS edge_target ON edge(target);
    """)
    return c

def family(text):
    s = text.lower()
    for label, patterns in (
        ("petersen", ("petersen",)),
        ("projective-plane", ("plane of order", "order-3 plane", "order 3 plane", "projective plane", "point-line")),
        ("c4-free-incidence", ("4-cycle-free", "4-cycle", "c4-free", "haslinedegree")),
        ("graph-circuit", ("graphfun", "edgegraph", "monotone", "circuit")),
    ):
        if any(p in s for p in patterns):
            return label
    return "unclassified"

def store_artifact(path):
    if path is None:
        return None
    p = Path(path)
    with p.open("rb") as f:
        data = f.read(MAX_ARTIFACT+1)
    if not data or len(data)>MAX_ARTIFACT:
        raise ValueError("artifact empty or exceeds 512 KiB")
    h = digest(data)
    dest = root()/"artifacts"/h
    if not dest.exists():
        dest.parent.mkdir(exist_ok=True,mode=0o700)
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=dest.parent)
        try:
            with os.fdopen(fd,"wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp,dest)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return h

def artifact(h):
    if not re.fullmatch(r"[0-9a-f]{64}",h or ""):
        raise ValueError("invalid artifact digest")
    p=root()/"artifacts"/h
    if digest(p.read_bytes())!=h:
        raise ValueError("artifact digest mismatch")
    return p

def add(c, kind, fam, statement, detail, provenance, file=None, base=None, deps=()):
    if kind not in KINDS or not statement.strip() or len(statement)>30000 or not provenance.strip():
        raise ValueError("kind, exact statement/description and provenance required")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}",fam):
        raise ValueError("invalid family")
    deps=tuple(sorted(set(deps)))
    if kind=="obligation" and not re.fullmatch(r"[0-9a-f]{40}",base or ""):
        raise ValueError("obligation requires exact upstream base")
    h=store_artifact(file)
    identity=[kind,fam,statement,detail,provenance,h,base,deps]
    oid=digest(canon(identity).encode())[:32]
    with c:
        for dep in deps:
            row=c.execute("SELECT kind,base FROM object WHERE id=?",(dep,)).fetchone()
            if not row:raise ValueError("unknown dependency "+dep)
            if kind=="obligation" and (row["kind"]!="obligation" or row["base"]!=base):
                raise ValueError("Lean obligations require same-base obligation dependencies")
        c.execute("INSERT OR IGNORE INTO object VALUES(?,?,?,?,?,?,?,?,?)",
                  (oid,kind,fam,statement,detail,provenance,h,base,time.time()))
        for dep in deps:
            c.execute("INSERT OR IGNORE INTO edge VALUES(?,?,?)",(oid,dep,"requires"))
    return oid

def get(c, oid):
    row=c.execute("SELECT * FROM object WHERE id=?",(oid,)).fetchone()
    if not row:raise ValueError("unknown object "+oid)
    obj=dict(row)
    obj["dependencies"]=[r[0] for r in c.execute("SELECT target FROM edge WHERE source=? AND relation='requires' ORDER BY target",(oid,))]
    obj["links"]=[dict(r) for r in c.execute("SELECT source,target,relation FROM edge WHERE source=? OR target=?",(oid,oid))]
    obj["checks"]=[dict(r) for r in c.execute("SELECT base,artifact,source_digest,result,checked FROM proof WHERE node=?",(oid,))]
    obj["assignments"]=[dict(r) for r in c.execute("SELECT attempt,worker,at FROM assignment WHERE node=?",(oid,))]
    if obj["artifact"]:obj["artifact_path"]=str(artifact(obj["artifact"]))
    return obj

def words(s):
    return set(re.findall(r"[a-z0-9_]+",s.lower()))

def search(c, query="", fam=None, kinds=None, limit=12):
    q=words(query)
    rows=[]
    for row in c.execute("SELECT id,kind,family,statement,detail,provenance,created FROM object"):
        if fam and row["family"]!=fam:continue
        if kinds and row["kind"] not in kinds:continue
        overlap=q & words(" ".join(str(row[k]) for k in ("statement","detail","provenance","family")))
        if q and not overlap:continue
        score=len(overlap)/(len(q) or 1)
        rows.append((score,row["created"],dict(row)))
    rows.sort(key=lambda x:(x[0],x[1]),reverse=True)
    return [dict(row,score=round(score,3)) for score,_,row in rows[:limit]]

def record_finding(rec, d):
    fam=family((rec.get("gap_title") or "")+" "+(rec.get("statement") or ""))
    with closing(db()) as c:
        return add(c,"finding",fam,d["message"],d["evidence"],
                   f"{rec['gap_id']} / {d.get('attempt')} / {d.get('worker')} / {d.get('id')}")

def record_fragment(rec, info, path):
    fam=family((rec.get("gap_title") or "")+" "+(rec.get("statement") or ""))
    with closing(db()) as c:
        return add(c,"fragment",fam,info["message"],"Imported fragment: reported status only; independently recheck.",
                   f"{rec['gap_id']} / {info.get('attempt')} / {info['digest']}",path,info.get("base"))

def relevant(rec):
    # Cheap bounded advisory output, no corpus refresh or compiler work.
    if not (Path(config.STATE_ROOT)/"research/knowledge.sqlite").exists():return {}
    fam=family((rec.get("gap_title") or "")+" "+(rec.get("statement") or ""))
    with closing(db()) as c:
        rows=search(c,rec.get("gap_title") or rec.get("statement") or "",fam,limit=6)
        result=[{"id":r["id"],"kind":r["kind"],"statement":r["statement"][:500]} for r in rows]
        # Exact-target obligations plus family knowledge are separately visible.
        nodes=[dict(r) for r in c.execute("SELECT id,statement,base FROM object WHERE kind='obligation' AND provenance LIKE ?",
                                        (rec["gap_id"]+" / %",))]
        for node in nodes:
            node["statement"]=node["statement"][:600]
            node["verified"] = any(json.loads(x[0]).get("status")=="kernel_checked" for x in
                                    c.execute("SELECT result FROM proof WHERE node=?",(node["id"],)))
        return {"family":fam,"knowledge":result,"obligations":nodes[:20],
                "command":"pnp-research knowledge find --family "+fam,
                "obligation_command":"pnp-research obligations ready --family "+fam}

def link(c, source, target, relation):
    if relation not in ("supports","blocks","counterexample_to","instantiates","reduces_to"):
        raise ValueError("invalid relationship")
    if source==target:raise ValueError("self link")
    with c:
        c.execute("INSERT OR IGNORE INTO edge VALUES(?,?,?)",(source,target,relation))
    return {"source":source,"target":target,"relation":relation}


def histories():
    """Current and quarantined gap histories, never arbitrary workspace files."""
    archive=Path(config.STATE_ROOT).parent/"quarantine"
    folders=list(Path(config.GAPS_DIR).glob("L-*"))+list(archive.glob("L-*-??????????????"))
    for folder in sorted(folders):
        try:
            rec=json.loads((folder/"state.json").read_text())
            if not config.GAP_ID_RE.fullmatch(rec["gap_id"]):continue
            if folder.parent==archive and not folder.name.startswith(rec["gap_id"]+"-"):continue
            if folder.parent!=archive and folder.name!=rec["gap_id"]:continue
            yield rec,folder
        except (OSError,ValueError,TypeError,KeyError):continue


def ingest(c):
    """Replay append-only historical findings and hashed fragments idempotently."""
    n=collections.Counter()
    for rec,folder in histories():
        gap=rec["gap_id"]
        fam=family((rec.get("gap_title") or "")+" "+(rec.get("statement") or ""))
        try:
            with (folder/"events.jsonl").open() as f:
                for line in f:
                    try:
                        e=json.loads(line)
                        d=e.get("detail",{})
                        if e.get("kind")!="research_finding":continue
                        msg=d.get("message","")
                        if not msg.strip():continue
                        add(c,"finding",fam,msg,d.get("evidence",""),
                            f"{gap} / {d.get('attempt')} / {d.get('worker')} / {d.get('id')}")
                        n["findings"]+=1
                    except (ValueError,TypeError,KeyError):continue
        except OSError:pass
        for p in (folder/"support").glob("*/fragments/*.json"):
            try:
                m=json.loads(p.read_text())
                f=p.with_suffix(".lean")
                if digest(f.read_bytes())!=p.stem:continue
                add(c,"fragment",fam,m["message"],"Imported fragment: reported status only; independently recheck.",
                    f"{gap} / {m.get('attempt')} / {p.stem}",f,m.get("base"))
                n["fragments"]+=1
            except (OSError,ValueError,KeyError,TypeError):continue
    return dict(n)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("add");a.add_argument("kind",choices=KINDS);a.add_argument("--family",required=True)
    a.add_argument("--statement",required=True);a.add_argument("--detail",default="")
    a.add_argument("--provenance",required=True);a.add_argument("--file");a.add_argument("--base")
    a.add_argument("--requires",action="append",default=[])
    a=sub.add_parser("find");a.add_argument("query",nargs="?",default="");a.add_argument("--family")
    a.add_argument("--kind",action="append",choices=KINDS);a.add_argument("--limit",type=int,default=12)
    a=sub.add_parser("show");a.add_argument("id")
    a=sub.add_parser("link");a.add_argument("source");a.add_argument("target");a.add_argument("relation")
    sub.add_parser("ingest");sub.add_parser("stats")
    args=p.parse_args()
    with closing(db()) as c:
        if args.cmd=="add":
            out={"id":add(c,args.kind,args.family,args.statement,args.detail,args.provenance,args.file,args.base,args.requires)}
        elif args.cmd=="find":out=search(c,args.query,args.family,args.kind,max(1,min(100,args.limit)))
        elif args.cmd=="show":out=get(c,args.id)
        elif args.cmd=="link":out=link(c,args.source,args.target,args.relation)
        elif args.cmd=="ingest":out=ingest(c)
        else:out={"objects":dict(c.execute("SELECT kind,count(*) FROM object GROUP BY kind")),
                  "families":dict(c.execute("SELECT family,count(*) FROM object GROUP BY family")),
                  "dependencies":c.execute("SELECT count(*) FROM edge").fetchone()[0],
                  "checks":c.execute("SELECT count(*) FROM proof").fetchone()[0]}
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=="__main__":main()
