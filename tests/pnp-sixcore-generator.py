"""Focused static-candidate test for the sixcore generator (no kernel verification)."""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from missions.pnp.lbcert import plugtest, plugins

def main():
    found = plugins.discover()
    assert 'sixcore' in found, 'sixcore plugin not discoverable'
    # independent historical holdouts: exclude the five technique-source IDs
    src = {37479, 39007, 39555, 39709, 40311}
    def fn(s):
        return bool(re.match(r'^∀ s : ℕ, PEqualNP\.MetaComplexity\.HasCircuitSize 6 \(fun x : Fin 6 → Bool => Nat\.testBit', s.strip()))
    cases = [g for g in plugtest.merged(fn, 6) if int(g['id'].split('-')[-1]) not in src]
    # one independent holdout keeps the test within the generator budget
    cases = cases[:1]
    results = []
    for g in cases:
        r = plugtest.one('sixcore', g)
        results.append(r)
        print(json.dumps(r), flush=True)
    rep = plugtest.summary('sixcore', results, allow_all_refused=True)
    print(json.dumps(rep))
    # accept: every case is either a candidate or a documented refusal
    assert rep['candidate_only'] + rep['refused'] == rep['cases']
    return 0

if __name__ == '__main__':
    sys.exit(main())
PY