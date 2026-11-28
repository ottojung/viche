"""Six-input monotone-vs-general family proof generator (stronger core-search).

Plugin interface for missions.pnp.lbcert.plugins: defines MATCH and runs as
    python3 gen.py GID STATEMENT_FILE OUT.lean
exit 0: candidate written; exit 3: beyond method; other: bug.
"""
import sys, os, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import engine

MATCH = r'^∀ s : ℕ, PEqualNP\.MetaComplexity\.HasCircuitSize 6 \(fun x : Fin 6 → Bool => Nat\.testBit .*'

TEMPLATE_SHA = None
try:
    import hashlib as _h
    TEMPLATE_SHA = _h.sha256(open(os.path.join(HERE, 'ref_40311.lean'), 'rb').read()).hexdigest()
except Exception:
    pass


def matches(statement):
    return engine.matches(statement)


def generate(gid, statement):
    text, why = engine.solve(gid, statement)
    if text is None:
        return None, why
    return text, None


def main():
    gid, sf, out = sys.argv[1:4]
    stmt = open(sf, encoding='utf-8').read().strip()
    text, why = engine.solve(gid, stmt)
    if text is None:
        print(json.dumps({'status': 'fail', 'why': why}))
        sys.exit(3)
    open(out, 'w', encoding='utf-8').write(text)
    print(json.dumps({'status': 'ok'}))


if __name__ == '__main__':
    sys.exit(main())