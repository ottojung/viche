#!/usr/bin/env python3
"""Build an lb_cert candidate on marceline-dev (32 cores) through the relay op `lb-cert`.

usage: lbremote.py STATEMENT_FILE MODULE OUT.lean [--maxstates N] [--chunks K] [--timeout SECONDS]
exit: 0 written (sha256 verified), 3 bound false (a smaller circuit exists), 4 too big,
      2 unsupported statement, 1 relay/handler error (fall back to local lbassemble.py).
Prints one JSON summary line on stdout.
"""
import base64, gzip, hashlib, json, os, subprocess, sys, tempfile

REQ = os.path.expanduser('~/.local/bin/marceline-request')


def arg(name, default):
    return type(default)(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def main():
    stmt_f, module, out = sys.argv[1:4]
    req = {'statement': open(stmt_f).read().strip(), 'module': module,
           'maxstates': arg('--maxstates', 60000), 'chunks': arg('--chunks', 40)}
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(req, f)
        rf = f.name
    try:
        sub = subprocess.run([REQ, 'submit', 'lb-cert', rf], capture_output=True, text=True, timeout=60)
        rid = sub.stdout.strip().split('\n')[-1]
        if sub.returncode != 0 or len(rid) != 36:
            print(json.dumps({'status': 'relay_error', 'detail': sub.stderr[-300:]})); return 1
        w = subprocess.run([REQ, 'wait', rid, str(arg('--timeout', 1500))], capture_output=True, text=True,
                           timeout=arg('--timeout', 1500) + 60)
    finally:
        os.unlink(rf)
    try:
        e = json.loads(w.stdout.strip().split('\n')[-1])
    except Exception:
        print(json.dumps({'status': 'relay_error', 'id': rid, 'detail': w.stderr[-300:]})); return 1
    r = e.get('result') or {}
    st = r.get('status', 'error')
    summary = {k: r.get(k) for k in ('status', 'engine', 'states', 'bytes', 'sha256')}
    summary['id'] = rid
    if st == 'ok':
        data = gzip.decompress(base64.b64decode(r['file_gz_b64']))
        if hashlib.sha256(data).hexdigest() != r['sha256']:
            summary['status'] = 'digest_mismatch'; print(json.dumps(summary)); return 1
        tmp = out + '.tmp'
        open(tmp, 'wb').write(data)
        os.replace(tmp, out)
        print(json.dumps(summary)); return 0
    summary['log'] = (r.get('log') or e.get('events', [{}])[-1].get('message', ''))[-200:]
    print(json.dumps(summary))
    return {'false': 3, 'toobig': 4, 'unsupported': 2}.get(st, 1)


if __name__ == '__main__':
    sys.exit(main())
