"""Instantiate a public, general PM3 lower bound for exact negative prefix gaps."""
import hashlib
import re
import sys
from functools import lru_cache
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE="PEqualNP.Outside.L_meta_27460"
SOURCE_SHA="048bc115db296b128cd4c7630049e996ce0e20710f9aa37e09aa69080c6510b5"
MARKER="\ntheorem "+SOURCE+" :"


def unwrap(s):
    s=" ".join(s.split())
    while s.startswith("(") and s.endswith(")"):
        depth=0
        for i,c in enumerate(s):
            if c=="(":depth+=1
            elif c==")":depth-=1
            if depth==0:break
        if i!=len(s)-1:break
        s=s[1:-1].strip()
    return s


@lru_cache(maxsize=1)
def template():
    raw=(HERE/"template.lean").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError("unreviewed lower-bound template")
    helpers,tail=raw.decode().split(MARKER,1)
    statement=tail.split(" := by",1)[0]
    return helpers,unwrap(statement)


@lru_cache(maxsize=1)
def matcher():
    _,s=template()
    # The exact three mathematical hypotheses and all normal-form conjuncts
    # must be unchanged. The general lower bound is independent of the prefix.
    pattern=re.escape(s)
    pattern=pattern.replace(re.escape("C.size ≤ 12"),r"C\.size\ ≤\ (?P<bound>[0-9]{1,2})")
    for example in ("and, [0, 4]","or, [2, 9]"):
        old=re.escape("GateOp."+example)
        pattern=pattern.replace(old,r"GateOp\.(?:and|or|not),\ \[[0-9, ]+\]")
    return re.compile(pattern)


def matches(statement):
    m=matcher().fullmatch(unwrap(statement))
    return m is not None and int(m["bound"])<13


def generate(gid,statement):
    if not re.fullmatch(r"L-meta-[0-9]+",gid) or not matches(statement):
        return None
    module="PEqualNP.Outside."+gid.replace("-","_")
    helpers,_=template()
    helpers=re.sub(r"(?m)^theorem ","lemma ",helpers).replace(SOURCE,module)
    attribution=("\n-- Derived from merged PEqualNP L-meta-27460, Apache-2.0.\n"
                 "-- General PM3 lower bound; adapted for the exact target prefix.\n")
    return (helpers+attribution+"\ntheorem "+module+" : "+statement.strip()
            +" := by\n  rintro ⟨C, fan, small, computes, _⟩\n  have large := "
            +module+".pm3_lower C fan computes\n  omega\n")


def main():
    gid,sf,out=sys.argv[1:]
    text=generate(gid,Path(sf).read_text())
    if text is None:return 3
    Path(out).write_text(text)
    return 0


if __name__=="__main__":sys.exit(main())
