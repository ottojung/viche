#!/bin/sh
# Local, read-only overview; the desk is not required for status reporting.
set -eu
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
python3 - "$state/pnp/gaps" <<'PY_STATUS'
import json,pathlib,sys,collections
root=pathlib.Path(sys.argv[1])
rows=[]
for path in sorted(root.glob('*/state.json')):
    try:
        d=json.loads(path.read_text())
    except (OSError,ValueError):
        continue
    rows.append({'gap':d.get('gap_id'), 'state':d.get('state'),
                 'pr_url':d.get('pr_url'), 'failure_reason':d.get('failure_reason'),
                 'updated_at':d.get('updated_at')})
print(json.dumps({'observed':len(rows),'by_state':dict(collections.Counter(
    x['state'] for x in rows)),'recent':rows[-12:],
    'caveat':'local records are not independent proof of a mathematical result'}))
PY_STATUS
