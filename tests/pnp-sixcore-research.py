"""Static regression of rejected sixcore emitter. No unbound Lean."""
import importlib.util
import re
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from missions.pnp import validate
from missions.pnp.lbcert import plugins
P=ROOT/'missions/pnp/lbcert/research/sixcore/engine.py'
sp=importlib.util.spec_from_file_location('sixcore_research',P)
E=importlib.util.module_from_spec(sp);sp.loader.exec_module(E)

def stmt(m):
    body=f'Nat.testBit ({m>>32} * 2 ^ 32 + {m&0xffffffff}) (∑ i : Fin 6, if x i then 2 ^ (i : ℕ) else 0)'
    return (f'∀ s : ℕ, PEqualNP.MetaComplexity.HasCircuitSize 6 (fun x : Fin 6 → Bool => {body}) s → '
            '∃ C : PEqualNP.CircuitLowerBounds.Circuit, PEqualNP.MetaComplexity.Monotone2 C ∧ C.size ≤ s ∧ '
            f'∀ x : Fin 6 → Bool, C.eval (List.ofFn x) = {body}')

class Test(unittest.TestCase):
    def test_emits_exact_small(self):
        s=stmt(1<<63)
        text,reason=E.solve('L-meta-999999',s,budget=8)
        self.assertIsNone(reason);self.assertIsNotNone(text)
        self.assertIsNone(re.search(r'\b(?:K|N|W2|MM|NAME|BODY|STMT)\b',text.split('def target (x')[1]))
        self.assertIn('lemma bound_from_search',text)
        self.assertIn('lemma reject : search 3 rows = false',text)
        self.assertEqual(len(re.findall(r'^theorem ',text,re.M)),1)
        self.assertNotIn('L_meta_40311',text)
        self.assertNotIn('sixcore',plugins.discover())
    def test_refusal(self):
        self.assertIsNone(E.solve('bad-id',stmt(1<<63))[0])
        self.assertIsNone(E.solve('L-meta-999999','not a theorem')[0])
if __name__=='__main__':unittest.main()
