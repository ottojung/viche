#!/usr/bin/env python3
"""Conservatively drop engine declarations not (textually, transitively) reachable from the roots.
A declaration is kept if the last component of its name occurs as a token in any kept text.
usage: prune_engine.py IN.lean OUT.lean"""
import re, sys

ROOTS = {'lb_cert', 'cover', 'all_app', 'stepOK', 'BT', 'toList', 'mem', 'nd', 'lf'}
DECL = re.compile(r'^(?:@\[[^\]]*\]\s*)?(?:private |protected |noncomputable |partial )*'
                  r'(theorem|lemma|def|abbrev|inductive|structure|instance|class)\b\s*([^\s:(\[{]*)')
STRUCT = re.compile(r'^(import|namespace|end|open|section|variable|universe|set_option|--)')

src = open(sys.argv[1]).read().split('\n')
blocks = []
cur = None
for line in src:
    m = DECL.match(line)
    if m:
        cur = [m.group(1), m.group(2), [line]]
        blocks.append(cur)
    elif STRUCT.match(line) or (line.strip() == '' and cur is None):
        cur = None
        blocks.append(['struct', None, [line]])
    else:
        if cur is None:
            cur = ['struct', None, [line]]
            blocks.append(cur)
        else:
            cur[2].append(line)

tok = re.compile(r"[A-Za-z_][A-Za-z_0-9'!?]*")
last = lambda nm: nm.split('.')[-1] if nm else nm
keep = set(i for i, b in enumerate(blocks) if b[0] in ('struct', 'instance', 'class'))
need = set(ROOTS)
for i in keep:
    need |= set(tok.findall('\n'.join(blocks[i][2])))
changed = True
while changed:
    changed = False
    for i, b in enumerate(blocks):
        if i in keep:
            continue
        nm = b[1]
        if nm and (last(nm) in need or nm in need):
            keep.add(i)
            need |= set(tok.findall('\n'.join(b[2])))
            changed = True
out = []
for i, b in enumerate(blocks):
    if i in keep:
        out.extend(b[2])
res = re.sub(r'\n{3,}', '\n\n', '\n'.join(out))
open(sys.argv[2], 'w').write(res)
print('kept %d of %d decls; %d -> %d bytes' % (
    sum(1 for i in keep if blocks[i][0] != 'struct'), sum(1 for b in blocks if b[0] != 'struct'),
    len('\n'.join(src).encode()), len(res.encode())), file=sys.stderr)
