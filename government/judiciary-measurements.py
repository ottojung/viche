#!/usr/bin/env python3
"""Evidence to Legislature; no judicial policy proposals or modifications."""
import json, os, time
from pathlib import Path
root=Path(os.environ.get('VICHE_STATE_ROOT','/var/lib/lubko/wd/viche-state'))
a=root/'oversight/random'
cases=list((a/'cases').glob('*.json')) if (a/'cases').exists() else []
counts={'sampled':len(cases),'reported':0,'unreported':0,'finding':0,'unreadable':0}
for p in cases:
    try:
        x=json.loads((a/'outcomes'/p.name).read_text())
        counts['reported']+=1
        counts['finding']+=int(x.get('verdict')=='finding')
    except FileNotFoundError:
        counts['unreported']+=1
    except (ValueError,TypeError):
        counts['unreadable']+=1
payload={'observed_at':int(os.environ.get('VICHE_BRANCH_NOW',time.time())),'destination':'Legislature', 'kind':'Judiciary measurement, not legislation', 'counts':counts, 'false_positive_rate':None,'false_negative_rate':None,'measurement_reliability':'not_established','judiciary_independence':'provisional; voting seat needs parliamentary reform', 'no_proposals':True}
p=root/'branches/judiciary-measurements.json'
p.parent.mkdir(parents=True,exist_ok=True)
tmp=p.with_suffix('.json.tmp')
tmp.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
tmp.replace(p)
print('Judiciary measurement report:',counts)
