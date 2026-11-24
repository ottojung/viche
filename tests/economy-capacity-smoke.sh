#!/bin/sh
# Test the Ministry measurement and safe expansion signal with no host dependency.
set -eu
cd "$(dirname "$0")/.."
python3 - <<'PY_TEST'
import importlib.util
from pathlib import Path
from unittest.mock import patch
import tempfile
import copy
spec = importlib.util.spec_from_file_location("economy", "government/economy-resources.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
r = {"disk:state":{"status":"short"}, "memory":{"status":"ok","headroom_gib":11,"oom_kills":5},
     "load":{"status":"ok"}, "model_funding":{"status":"ok","free_available_now":8}}
cpu = {"usage_usec":120_000_000,"cpus":4.0,"identity":"a"}
old = {"capacity":{"cpu_sample":dict(cpu,usage_usec=0,epoch=1000)}, "resources":copy.deepcopy(r)}
def assess(resources=r, counter=cpu, previous=old, current=1600):
    return m.capacity_assessment(resources,counter,previous,current,m.DEFAULT_POLICY)
x = assess()
assert x['status']=='underused' and x['cpu_used_cores']==.2 and x['cpu_spare_cores']==3.8, x
assert x['memory_spare_gib']==8 and x['disk_mode']=='disk-light-only', x
assert assess(counter=dict(cpu,usage_usec=2_250_000_000))['status']=='no_clear_spare_capacity'
assert assess(current=1100+3600)['status']=='unmeasured'
assert assess(counter=dict(cpu,identity='new'))['status']=='unmeasured'
assert assess(counter=None)['status']=='unmeasured'
assert assess(previous={})['status']=='unmeasured'
for key, change in [('memory',{'status':'critical','headroom_gib':1}), ('memory',{'oom_kills':6}), ('model_funding',{'free_available_now':0}), ('disk:state',{'status':'critical'})]:
    constrained=copy.deepcopy(r);constrained[key].update(change)
    assert assess(resources=constrained)['status']=='constrained', key
with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp)
    (d/'cpu.stat').write_text('usage_usec 2000000\n')
    (d/'cpu.max').write_text('150000 100000\n')
    (d/'cpuset.cpus.effective').write_text('0-3\n')
    with patch.object(m,'CGROUP',d),patch.object(m.os,'sched_getaffinity',return_value={0,1,2,3}):
        assert m.cpu_counter()['cpus']==1.5
        assert m.cpu_counter()['usage_usec']==2_000_000
print('Economy capacity: measured underuse, quotas, stale counters and safety constraints passed')
PY_TEST
