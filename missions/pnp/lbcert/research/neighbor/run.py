"""Replayable neighborhood search for exact six-input monotone witnesses.

Input corpus: list of records {id, mask, gates: [[op,a,b], ...]} extracted
from public accepted proofs. Catalog: the ordinary gap-cache JSON snapshot.
Output: only independently audited upper-bound witnesses, never a receipt.
"""
import argparse
import collections
import itertools
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"onenot"))
import monosix

FULL=(1<<64)-1
ROOTS=[sum(1<<r for r in range(64) if r>>i&1) for i in range(6)]

def evaluate(gates):
    w=ROOTS[:]
    if not gates:raise ValueError("missing gates")
    for a,b,o in gates:
        if not (0<=a<len(w) and 0<=b<len(w) and o in (0,1)):
            raise ValueError("invalid gate")
        w.append((w[a]|w[b]) if o else (w[a]&w[b]))
    return w[-1]

def remap(gates, order, dual):
    if sorted(order)!=list(range(6)):raise ValueError("invalid permutation")
    inv=[order.index(i) for i in range(6)]
    return [(inv[a] if a<6 else a, inv[b] if b<6 else b, o^int(dual))
            for a,b,o in gates]

def move(mask, order):
    return sum(1<<sum(((r>>i)&1)<<order[i] for i in range(6))
               for r in range(64) if mask>>r&1)

def dual(mask):
    return FULL^int(f'{mask:064b}'[::-1],2)

def tables(perm):
    for order in perm:
        dest=[sum(((r>>i)&1)<<order[i] for i in range(6)) for r in range(64)]
        yield [[sum(1<<dest[j*8+b] for b in range(8) if x>>b&1)
                for x in range(256)] for j in range(8)]

def moved(m,t):
    return (t[0][m&255]|t[1][m>>8&255]|t[2][m>>16&255]|t[3][m>>24&255]|
            t[4][m>>32&255]|t[5][m>>40&255]|t[6][m>>48&255]|t[7][m>>56&255])

def load_live(snapshot,cap=1200):
    live={}
    for g in snapshot['gaps']:
        if not g.get('offerable_now') or g.get('pr_open') or g.get('held_now'):continue
        p=monosix.parse(g.get('statement') or '')
        if not p:continue
        m=sum(v<<r for r,v in enumerate(p[2]))
        if m not in (0,FULL):live.setdefault(m,g['id'])
        if len(live)>=cap:break
    return list(live.items())

def load_seeds(corpus):
    seeds=[]
    for r in corpus:
        raw=r.get('gates') or []
        if not 0<len(raw)<=13:continue
        if any(op not in ('and','or') for op,a,b in raw):continue
        gates=[(int(a),int(b),int(op=='or')) for op,a,b in raw]
        if evaluate(gates)!=r['mask']:continue
        seeds.append((r['id'],gates))
    return seeds

def run(corpus,snapshot,out,timeout=120):
    live=load_live(snapshot);seeds=load_seeds(corpus)
    perms=list(itertools.permutations(range(6)))
    maps=list(tables(perms));orbit={}
    for i,(mask,gid) in enumerate(live):
        for j,t in enumerate(maps):
            a=moved(mask,t)
            orbit.setdefault(a,(i,2*j));orbit.setdefault(dual(a),(i,2*j+1))
    if len(orbit)>2**21:raise ValueError('orbit cap')
    with tempfile.TemporaryDirectory(prefix='pnp-neighbor-') as d:
        d=Path(d);exe=d/'search';f=d/'orbit';s=d/'seeds'
        with f.open('wb') as fd:
            for x,(i,j) in orbit.items():fd.write(struct.pack('<QII',x,i,j))
        with s.open('w') as fd:
            for i,(_,g) in enumerate(seeds):
                print(i,len(g),*(v for t in g for v in t),file=fd)
        subprocess.run(['cc','-O3','-o',str(exe),str(HERE/'search.c')],check=True,timeout=60)
        result=subprocess.run([str(exe),str(f),str(s)],check=True,capture_output=True,text=True,timeout=timeout)
    found={}
    for line in result.stdout.splitlines():
        seed,j,t,k,*raw=map(int,line.split())
        if not (0<=seed<len(seeds) and 0<=j<len(live) and 0<=t<1440 and 0<k<=13 and len(raw)==3*k):
            raise ValueError("invalid native result")
        g=list(zip(raw[::3],raw[1::3],raw[2::3]));g=remap(g,perms[t//2],t%2)
        m,gid=live[j]
        if evaluate(g)!=m:raise ValueError("native output audit failed")
        if gid not in found or len(found[gid]['gates'])>k:
            found[gid]={'id':gid,'mask':m,'gates':g,'seed':seeds[seed][0]}
    out.write_text(json.dumps({'snapshot':snapshot['updated_at'],'live':len(live),
       'seeds':len(seeds),'witnesses':list(found.values())},indent=2)+'\n')
    return collections.Counter(len(x['gates']) for x in found.values())

def main():
    p=argparse.ArgumentParser()
    p.add_argument('corpus',type=Path);p.add_argument('catalog',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--timeout',type=float,default=120)
    args=p.parse_args()
    print(run(json.loads(args.corpus.read_text()),json.loads(args.catalog.read_text()),args.output,args.timeout))

if __name__=='__main__':main()
