#!/usr/bin/env python3
"""Sibling transfer on marceline-dev through the relay op `sibling`.

Finds merged upstream theorems with the same statement skeleton (numerals and binder names abstracted;
see sibling.py on marceline-dev), substitutes this statement, and compiles each candidate with
`lake env lean` against current upstream main. Measured on the merged corpus: 7 of 14 tried pairs
compiled with a plain statement swap, most within 40 s.

usage: sibremote.py STATEMENT.txt PEqualNP.Outside.L_meta_N OUT.lean [--imports PEqualNP.Defs,...]
                    [--max-tries 6] [--timeout SECONDS]
exit: 0 written (sha256 verified; compiled on marceline-dev), 5 no compiling sibling, 1 relay error.
Prints one JSON summary line (source, variant, tried, siblings, corpus, secs).
"""
import base64, gzip, hashlib, json, os, subprocess, sys, tempfile

REQ = os.path.expanduser('~/.local/bin/marceline-request')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    stmt_f, module, out = sys.argv[1:4]
    req = {'statement': open(stmt_f).read().strip(), 'module': module,
           'imports': [i for i in arg('--imports', 'PEqualNP.Defs').split(',') if i],
           'max_tries': arg('--max-tries', 6)}
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(req, f)
        rf = f.name
    try:
        sub = subprocess.run([REQ, 'submit', 'sibling', rf], capture_output=True, text=True, timeout=60)
        rid = sub.stdout.strip().split('\n')[-1]
        if sub.returncode != 0 or len(rid) != 36:
            print(json.dumps({'status': 'relay_error', 'detail': sub.stderr[-300:]})); return 1
        t = arg('--timeout', 1500)
        w = subprocess.run([REQ, 'wait', rid, str(t)], capture_output=True, text=True, timeout=t + 60)
    finally:
        os.unlink(rf)
    try:
        e = json.loads(w.stdout.strip().split('\n')[-1])
    except Exception:
        print(json.dumps({'status': 'relay_error', 'id': rid, 'detail': w.stderr[-300:]})); return 1
    r = e.get('result') or {}
    summary = {k: r.get(k) for k in ('status', 'source', 'variant', 'tried', 'siblings', 'corpus', 'secs', 'sha256')}
    summary['id'] = rid
    if r.get('status') == 'ok':
        data = gzip.decompress(base64.b64decode(r['file_gz_b64']))
        if hashlib.sha256(data).hexdigest() != r['sha256']:
            summary['status'] = 'digest_mismatch'; print(json.dumps(summary)); return 1
        open(out + '.tmp', 'wb').write(data)
        os.replace(out + '.tmp', out)
        print(json.dumps(summary)); return 0
    summary['log'] = (r.get('log') or '')[-200:]
    print(json.dumps(summary))
    return 5 if r.get('status') == 'none' else 1


if __name__ == '__main__':
    sys.exit(main())
