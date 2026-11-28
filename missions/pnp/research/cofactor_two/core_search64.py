"""Python port of L-meta-40976 CoreSearch (BitVec 64, 32 sample columns)."""
import itertools, re, time

M64 = (1 << 64) - 1
M32 = (1 << 32) - 1
GOAL = M32 << 32
NGOAL = M32

def sep(w): return ((w >> 32) ^ w) & M32
def cuts(ws):
    c = 0
    for w in ws: c |= sep(w)
    return c
def ops(a, b): return [a & b, a | b, a & (~b & M64), b & (~a & M64)]

class Budget(Exception): pass

def search(n, inputs, cap=400000):
    states = [0]
    def opt(k, extra, ws):
        states[0] += 1
        if states[0] > cap: raise Budget()
        if len(ws) == 1 and ws[0] in (GOAL, NGOAL): return True
        if k == 0: return False
        L = len(ws)
        for i in range(L):
            for j in range(i+1, L):
                a, b = ws[i], ws[j]
                r = [ws[t] for t in range(L) if t != i and t != j]
                base = 0
                for w in r: base |= sep(w)
                sa, sb = sep(a), sep(b)
                for z in ops(a, b):
                    v = sep(z) | base
                    if v == M32 and opt(k-1, extra, [z]+r): return True
                    if extra and ((v|sa)==M32) and opt(k-1, extra-1, [z,a]+r): return True
                    if extra and ((v|sb)==M32) and opt(k-1, extra-1, [z,b]+r): return True
                    if extra>=2 and ((v|sa|sb)==M32) and opt(k-1, extra-2, [z,a,b]+r): return True
        return False
    for mask in range(1 << len(inputs)):
        ws = [inputs[i] for i in range(len(inputs)) if (mask>>i)&1]
        if len(ws) <= n+1 and cuts(ws)==M32 and opt(n, n+1-len(ws), ws):
            return True, states[0]
    return False, states[0]

if __name__ == '__main__':
    # validate on 40976's cofactor: search 7 cols = false
    cols = [16470756647699013859, 14784806497024870156, 5941470496719636464,
            11225497327143811072, 0, 2593937604336353280]
    for n in (6, 7):
        t0=time.time()
        try:
            r, st = search(n, cols)
            print('n=%d search=%s states=%d secs=%.1f' % (n, r, st, time.time()-t0))
        except Budget:
            print('n=%d BUDGET states=%d secs=%.1f' % (n, st if 'st' in dir() else 0, time.time()-t0))
