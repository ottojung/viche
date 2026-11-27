"""Screened residual gate-elimination candidates; static source, not kernel receipts."""
import hashlib
import importlib.util
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE_SHA="61b1b5b087d946295c7e8faf526877dc978afde91126203befb5724c5d5211df"
SEED_SHA="9d181b9ef383c39124a79eeb4c36ac21f085ea5f116a4483fef293cd73b09a1f"
LIB_SHA="048bc115db296b128cd4c7630049e996ce0e20710f9aa37e09aa69080c6510b5"

def read(path,digest):
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=digest:
        raise ValueError("unreviewed residual library data")
    return data

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

@lru_cache(maxsize=1)
def seeds():
    return json.loads(read(HERE/"seeds.json",SEED_SHA))

@lru_cache(maxsize=1)
def shape():
    return module("residualgate_shape",HERE.parent/"gateelim/gen.py")

def matches(s):
    g=shape()
    e=g.parse(s)
    return e is not None and g.key(e) in seeds()

def generate(gid,s):
    if not re.fullmatch(r"L-meta-[0-9]+",gid) or not matches(s):return None
    g=module("residualgate_emitter",HERE.parent/"gateelim/gen.py")
    refined=module("residualgate_refined",HERE/"refined.py")
    data=json.loads(read(HERE/"bases.json",BASE_SHA))
    ref=refined.Refinement(g.bounds,data)
    g.bounds.lower=ref.lower
    row=seeds()[g.key(g.parse(s))]
    f=g.bounds.normalize((1<<a)|(1<<b) for a,b in g.parse(s))
    if ref.lower(f)[0]!=row["bound"]:return None
    orig=g.Emitter
    class Emitter(orig):
        def emit(self,f):
            if f in self.names:return self.names[f]
            B,plan=ref.lower(f)
            if plan[0]!="base":return super().emit(f)
            base,p=ref.find(f)
            def remap(m):return sum(1<<v for i,v in enumerate(p) if m>>i&1)
            zs=[remap(z) for a,z in base["pairs"]]
            os=[remap(a) for a,z in base["pairs"]]
            if not zs or not all(not g.truth(f,z) for z in zs) or not all(g.truth(f,a) for a in os):
                raise ValueError("invalid residual samples")
            v="v"+str(len(self.names)+1)
            self.names[f]=v
            self.say("def "+v+" : BF 8 := fun x => "+g.expression(f)+"\n")
            proof=f"base {v} {zs[0]} {zs[1:]} {os} 1 {B-2} (by decide) (by decide +kernel) (by decide +kernel) (by decide +kernel) (by\n    intro i hi\n    interval_cases i\n    decide +kernel)"
            self.dec(v+"_lb : LB "+v+" "+str(B),proof)
            return v
    g.Emitter=Emitter
    w=[(a,b,{int(k):v for k,v in t.items()}) for a,b,t in row["witness"]]
    text=g.generate(gid,s,witness=w)
    if text is None:return None
    lib=read(HERE.parent/"pm3lower/template.lean",LIB_SHA).decode()
    if lib.count("end Compile")!=1:raise ValueError("library structure changed")
    src=lib.split("end Compile")[0]+"end Compile\n"
    src=re.sub(r"(?m)^theorem ","lemma ",src.replace(g.SOURCE,"PEqualNP.Outside."+gid.replace("-","_")))
    marker="-- Gate elimination rules from merged PEqualNP L-meta-27460 (Apache-2.0)."
    return src+"\n"+text[text.index(marker):]

def main():
    gid,sf,out=sys.argv[1:]
    text=generate(gid,Path(sf).read_text())
    if text is None:return 3
    Path(out).write_text(text)
    return 0

if __name__=="__main__":sys.exit(main())
