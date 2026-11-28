import sys
import unittest
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from missions.pnp.lbcert import autosolve as auto

class Recovery(unittest.TestCase):
    def test_fresh_stalled_only(self):
        for rec,now,expected in [
            ({},1000,"normal"),
            (dict(active=True,recovery=False,observed=1000),1000,"posting-only"),
            (dict(active=True,recovery=True,observed=1000),1000,"held-only"),
            (dict(active=True,recovery=True,observed=1000),1061,"posting-only"),
            (dict(active=True,recovery=True,observed=1000),2201,"normal"),
        ]:
            with patch.object(auto.surge,"load",return_value=rec):
                self.assertEqual(auto.generation_mode(now),expected)
    def test_exact_held_scope(self):
        q=dict(id="L-meta-1",statement="True",module="PEqualNP.Outside.L_meta_1",
               file="lean/PEqualNP/Outside/L_meta_1.lean",imports=["PEqualNP.Defs"])
        r=dict(gap_id=q["id"],statement=q["statement"],module=q["module"],
               path=q["file"],imports=q["imports"],work_lane="research",
               state="LEASED",lease="fixture",lease_expires_at=2000)
        with patch("missions.pnp.support.active",return_value=True):
            self.assertEqual(auto.exact_held_research([q],[r],1000),[q])
            for k,v in (("work_lane","posting"),("statement","False"),
                         ("module","Other"),("path","Other"),("imports",[]),
                         ("queued_lease","fixture"),("candidate_digest","x"),
                         ("intent","x"),("pr_number",1)):
                self.assertEqual(auto.exact_held_research([q],[{**r,k:v}],1000),[])
            self.assertEqual(auto.exact_held_research([q],[],1000),[])
        with patch("missions.pnp.support.active",return_value=False):
            self.assertEqual(auto.exact_held_research([q],[r],1000),[])

    def test_bounded_timeout_is_deferred_not_permanent_failure(self):
        from missions.pnp import ledger
        import plugins
        q=dict(id="L-meta-1",statement="True",module="M",file="M.lean",imports=[])
        with tempfile.TemporaryDirectory() as d, patch.object(auto,"WORK",d), \
             patch.object(auto,"CANDS",d), patch.object(plugins,"run",return_value=(124,"timeout")) as run, \
             patch.object(ledger,"mark"):
            auto.gen_plugin(q,"fixture","abcdef",auto.RECOVERY_TIMEOUT)
            self.assertGreater(run.call_args.kwargs["timeout"], 0)
            self.assertLessEqual(run.call_args.kwargs["timeout"], auto.RECOVERY_TIMEOUT)
            self.assertTrue(auto.status(q["id"]).startswith("deferred plugin "))
            self.assertFalse(auto.fresh(q["id"],"abcdef"))
            old=time.time()-auto.RETRY_DELAY-1
            os.utime(Path(d)/(q["id"]+".status"),(old,old))
            self.assertTrue(auto.fresh(q["id"],"abcdef"))


if __name__=="__main__":unittest.main()
