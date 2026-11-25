"""Test a generator plugin end to end: generate, validate (town rules), compile on marceline-dev.

python3 -m missions.pnp.lbcert.plugtest NAME --holdout 3     newest merged statements it matches
python3 -m missions.pnp.lbcert.plugtest NAME --open 3        newest open desk steps it matches
python3 -m missions.pnp.lbcert.plugtest NAME --statement-file F --module PEqualNP.Outside.L_meta_N
Prints one JSON line per instance and a summary; exit 0 iff every instance passed or was refused (3).
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

from missions.pnp import gitctl, validate
from missions.pnp.lbcert import plugins, checkremote

DESK = 'https://data.pequalnp.com/data/desk/gaps.json'


def merged(fn, n, scan=4000):
    git = ['git', '--git-dir=' + gitctl.MIRROR]
    ls = subprocess.run(git + ['ls-tree', 'refs/remotes/upstream/main', 'lean/PEqualNP/Outside/'],
                        capture_output=True, text=True, check=True).stdout
    files = []
    for line in ls.splitlines():
        meta, path = line.split('\t', 1)
        m = re.fullmatch(r'lean/PEqualNP/Outside/L_meta_(\d+)\.lean', path)
        if m:
            files.append((int(m.group(1)), meta.split()[2]))
    files.sort(reverse=True)
    out = []
    p = subprocess.Popen(git + ['cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for num, sha in files[:scan]:
        p.stdin.write((sha + '\n').encode()); p.stdin.flush()
        k = int(p.stdout.readline().split()[2])
        text = p.stdout.read(k).decode('utf-8', 'replace'); p.stdout.read(1)
        mod = 'PEqualNP.Outside.L_meta_%d' % num
        m = re.search(r'(?ms)^theorem %s\s*:\s*(.*?)\s*:=\s*by\b' % re.escape(mod), text)
        if m and fn(m.group(1)):
            out.append({'id': 'L-meta-%d' % num, 'module': mod, 'statement': m.group(1).strip(),
                        'file': 'lean/PEqualNP/Outside/L_meta_%d.lean' % num, 'imports': ['PEqualNP.Defs']})
            if len(out) >= n:
                break
    p.stdin.close(); p.wait()
    return out


def desk_open(fn, n):
    r = urllib.request.Request(DESK, headers={'User-Agent': 'viche-town'})
    gaps = json.loads(urllib.request.urlopen(r, timeout=60).read())['gaps']
    gs = [g for g in gaps if isinstance(g.get('statement'), str) and fn(g['statement'])]
    gs.sort(key=lambda g: -int(re.sub(r'\D', '', g['id']) or 0))
    return gs[:n]


def one(name, g):
    t0 = time.time()
    res = {'id': g['id']}
    with tempfile.TemporaryDirectory() as d:
        sf, out = os.path.join(d, 's.txt'), os.path.join(d, 'out.lean')
        open(sf, 'w').write(g['statement'])
        rc, log = plugins.run(name, g['id'], sf, out)
        res.update(gen_rc=rc, gen_secs=round(time.time() - t0, 1))
        if rc != 0:
            res['result'] = 'refused' if rc == 3 else 'generator_error'
            res['log'] = log
            return res
        data = open(out, 'rb').read()
        res['bytes'] = len(data)
        try:
            validate.validate(g, data)
        except validate.InvalidCandidate as e:
            res.update(result='invalid', log=str(e))
            return res
        t1 = time.time()
        crc, cres = checkremote.check(out, g['module'])
        res.update(compile_secs=round(time.time() - t1), result={0: 'PASS', 1: 'compile_error'}.get(crc, 'relay_error'))
        if crc:
            res['log'] = (cres.get('log') or cres.get('detail') or '')[-600:]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name')
    ap.add_argument('--holdout', type=int, default=0)
    ap.add_argument('--open', type=int, default=0)
    ap.add_argument('--statement-file')
    ap.add_argument('--module')
    a = ap.parse_args()
    found = plugins.discover()
    if a.name not in found:
        sys.exit('plugin %s not found or not loadable (see stderr)' % a.name)
    fn = found[a.name][2]
    cases = []
    if a.holdout:
        cases += merged(fn, a.holdout)
    if a.open:
        cases += desk_open(fn, a.open)
    if a.statement_file:
        num = a.module.rsplit('_', 1)[1]
        cases.append({'id': 'L-meta-' + num, 'module': a.module, 'statement': open(a.statement_file).read().strip(),
                      'file': 'lean/PEqualNP/Outside/L_meta_%s.lean' % num, 'imports': ['PEqualNP.Defs']})
    if not cases:
        sys.exit('no matching statements found')
    results = [one(a.name, g) for g in cases]
    for r in results:
        print(json.dumps(r))
    ok = all(r['result'] in ('PASS', 'refused') for r in results)
    print(json.dumps({'plugin': a.name, 'cases': len(results),
                      'pass': sum(r['result'] == 'PASS' for r in results),
                      'refused': sum(r['result'] == 'refused' for r in results), 'ok': ok}))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
