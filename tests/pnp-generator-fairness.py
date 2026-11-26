"""Exercise a real scheduling tick with all lower-bound slots occupied."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class Fairness(unittest.TestCase):
    def test_independent_lanes(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{"PNP_STATE_ROOT":d}):
            from missions.pnp.lbcert import autosolve as a
            from missions.pnp import cli, fastlane
            from missions.pnp.lbcert import ready
            import plugins
            work=Path(d)/"lbcert";cands=work/"cands";cands.mkdir(parents=True,exist_ok=True)
            gaps=[dict(id="L-meta-"+str(i),statement="lower",module="M") for i in range(1,9)]
            gaps+= [dict(id="L-meta-100",statement="constructive",module="M"),
                     dict(id="L-meta-101",statement="prepared",module="M")]
            (cands/"L-meta-101.lean").write_text("dummy")
            pools=[]
            class Pool:
                def __init__(self,n):
                    self.limit=n;self.jobs=[];pools.append(self)
                def submit(self,fn,*args):
                    self.jobs.append((fn.__name__,args[0]["id"]))
                    f=Mock();f.done.return_value=False
                    return f
                def shutdown(self,**kwargs):pass
            def stop(_): (work/"STOP").touch()
            with patch.multiple(a, WORK=str(work), CANDS=str(cands), QUEUED=set(),
                               ThreadPoolExecutor=Pool), \
                 patch.object(a,"ensure_engines",return_value=[]), \
                 patch.object(a.threading,"Thread"), \
                 patch.object(a,"source_changed",return_value=False), \
                 patch.object(a,"get",return_value=json.dumps({"gaps":gaps}).encode()), \
                 patch.object(a.lbparse,"family",side_effect=lambda s:"lb" if s=="lower" else None), \
                 patch.object(a,"status",side_effect=lambda g:"generated test" if g=="L-meta-101" else None), \
                 patch.object(cli,"held_records",return_value=[]), \
                 patch.object(ready,"verified",return_value=None), \
                 patch.object(plugins,"discover",return_value={"x":1}), \
                 patch.object(plugins,"family_of",side_effect=lambda s,_:("x","v1") if s=="constructive" else None), \
                 patch.object(a.time,"sleep",side_effect=stop), \
                 patch.object(a.managed_process,"stop_all"):
                self.assertEqual(a.main(),0)
            self.assertEqual([p.limit for p in pools],[3,2,1])
            self.assertEqual(len(pools[0].jobs),3)
            self.assertEqual(pools[1].jobs,[("gen_plugin","L-meta-100")])
            self.assertEqual(pools[2].jobs,[("check_prepared","L-meta-101")])

if __name__=="__main__":unittest.main()
