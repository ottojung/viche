#!/usr/bin/env python3
"""Compile a finished candidate file on marceline-dev against current upstream (relay op `lb-cert`,
check mode: the handler only runs `lake env lean` in its pinned tree, inside the shared compile slots).

usage: checkremote.py FILE.lean MODULE [--timeout SECONDS]
exit: 0 compiles (no error, no sorry), 1 does not compile, 2 relay trouble.  One JSON line on stdout
(with the compiler's last lines in `log`).  Any agent may use it; it needs no lease or workspace binding.
"""
import base64, gzip, json, os, subprocess, sys, tempfile

try:
    from . import process as managed_process
except ImportError:
    import process as managed_process

REQ = os.path.expanduser('~/.local/bin/marceline-request')


def check(path, module, timeout=900):
    data = open(path, 'rb').read()
    if not data or len(data)>512*1024:
        return 2, {'status':'invalid_proof_size'}
    req = {'statement': 'check', 'module': module, 'maxstates': 1, 'chunks': 1, 'timeout': timeout,
           'check_file_gz_b64': base64.b64encode(gzip.compress(data, 9)).decode()}
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
        json.dump(req, f)
        rf = f.name
    try:
        sub = managed_process.run([REQ, 'submit', 'lb-cert', rf], capture_output=True, text=True, timeout=60)
        rid = sub.stdout.strip().split('\n')[-1]
        if sub.returncode != 0 or len(rid) != 36:
            return 2, {'status': 'relay_error', 'detail': sub.stderr[-300:]}
        w = managed_process.run([REQ, 'wait', rid, str(timeout + 300)], capture_output=True, text=True, timeout=timeout + 360)
    finally:
        os.unlink(rf)
    try:
        r = (json.loads(w.stdout.strip().split('\n')[-1]).get('result') or {})
    except Exception:
        return 2, {'status': 'relay_error', 'id': rid, 'detail': w.stderr[-300:]}
    out = {k: r.get(k) for k in ('status', 'bytes', 'sha256', 'log', 'checked_base')}
    out['id'] = rid
    if r.get('engine') != 'check':
        return 2, dict(out, status='handler_without_check_mode')
    return (0 if r.get('status') == 'ok' else 1), out


def main():
    path, module = sys.argv[1:3]
    t = int(sys.argv[sys.argv.index('--timeout') + 1]) if '--timeout' in sys.argv else 900
    rc, out = check(path, module, t)
    print(json.dumps(out))
    return rc


if __name__ == '__main__':
    sys.exit(main())
