"""Bounded root-pair search with sharing-aware DAG cost.

Formula costs double-count common subexpressions. Enumerate semantic root
operands, then count the union of actual gates and independently audit the
compacted DAG. Failure is only a bounded search refusal.
"""
from functools import lru_cache
import time
from . import gen


@lru_cache(maxsize=180000)
def gates(expr):
    if isinstance(expr,int):return frozenset()
    return frozenset((expr,)).union(*(gates(a) for a in expr[1:]))


@lru_cache(maxsize=3)
def library(n,rows,allow,depth):
    table,_,_=gen.formula_library(n,rows,allow,depth)
    return table,{x:gates(e) for x,e in table.items()}


def search(problem,seconds=.65):
    kind,_,_,k,_,pred=problem
    n,rows,t=gen.domain(problem)
    if kind!="two" or not 5<=n<=6 or k>12:return None
    allow=pred=="FanInTwo"
    table,nodes=library(n,tuple(rows),allow,7 if n==5 else 6)
    full=(1<<len(rows))-1
    deadline=time.monotonic()+seconds
    for outer in ((False,True) if allow else (False,)):
        target=full^t if outer else t
        cap=k-int(outer)
        for op in ("or","and"):
            flip=0 if op=="or" else full
            aim=target^flip
            opts={x^flip:x for x in table if len(nodes[x])<cap and (x^flip)&~aim==0}
            for a,x in sorted(opts.items(),key=lambda z:(len(nodes[z[1]]),-z[0].bit_count())):
                if time.monotonic()>deadline:return None
                need=aim^a
                if 1<<a.bit_count()<len(opts):
                    def iterb():
                        sub=a
                        while True:
                            b=opts.get(need|sub)
                            if b is not None:yield b
                            if sub==0:break
                            sub=(sub-1)&a
                    bs=iterb()
                else:bs=(y for b,y in opts.items() if a|b==aim)
                for y in bs:
                    if y<x or len(nodes[x]|nodes[y])>cap+1:continue
                    e=gen.combine(op,table[x],table[y])
                    if outer:e=("not",e)
                    sol=gen.compact(problem,*gen.compile_expr(n,e))
                    if sol and gen.valid(problem,sol):return sol
    return None
