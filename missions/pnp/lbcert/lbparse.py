#!/usr/bin/env python3
"""Robust statement classifier for HasCircuitSize lower bounds (any pretty-printing style).

classify(stmt) -> dict(kind, n, lb, fun) or None
  kind 'forall': ∀ (t : ℕ), HasCircuitSize N F t → K ≤ t
  kind 'neg'   : ¬HasCircuitSize N F S            (lb = S + 1)
truth_table(n, fun_text) -> int bitmask (Python translation; marceline-dev also has a Lean #eval fallback).
"""
import os, re, subprocess, tempfile

HCS = 'PEqualNP.MetaComplexity.HasCircuitSize'
NUM = r'\(?\s*(\d+)\s*(?::\s*ℕ\s*)?\)?'


def norm(s):
    s = re.sub(r'\s+', ' ', s).strip()
    for _ in range(3):
        s = re.sub(r'\(\s*(\d+)\s*:\s*ℕ\s*\)', r'\1', s)
        s = re.sub(r'\(\s*(\d+)\s*:\s*Fin\s+\d+\s*\)', r'\1', s)
    return s


def take_group(s, i):
    assert s[i] == '('
    d = 0
    for j in range(i, len(s)):
        if s[j] == '(':
            d += 1
        elif s[j] == ')':
            d -= 1
            if d == 0:
                return j + 1
    raise ValueError('unbalanced')


def split_hcs(s):
    assert s.startswith(HCS)
    r = s[len(HCS):].lstrip()
    m = re.match(NUM, r)
    if not m:
        return None
    n = int(m.group(1))
    r = r[m.end():].lstrip()
    if not r.startswith('('):
        return None
    e = take_group(r, 0)
    fun = r[1:e - 1].strip()
    if not fun.startswith('fun'):
        return None
    return n, fun, r[e:].strip()


def classify(stmt):
    s = norm(stmt)
    m = re.match(r'∀ \(?(\w+) : ℕ\)?, ', s)
    if m:
        v = m.group(1)
        body = s[m.end():]
        if not body.startswith(HCS):
            return None
        p = split_hcs(body)
        if not p:
            return None
        n, fun, rest = p
        m2 = re.fullmatch(r'%s → (\d+) ≤ %s' % (re.escape(v), re.escape(v)), rest)
        if m2:
            return dict(kind='forall', n=n, lb=int(m2.group(1)), fun=fun)
        return None
    m = re.match(r'¬ ?\(?', s)
    if m and s[m.end():].startswith(HCS):
        body = s[m.end():]
        if body.endswith(')') and s[m.end() - 1] == '(':
            body = body[:-1]
        p = split_hcs(body)
        if not p:
            return None
        n, fun, rest = p
        m2 = re.fullmatch(r'(\d+)', rest)
        if m2:
            return dict(kind='neg', n=n, lb=int(m2.group(1)) + 1, fun=fun)
    return None


def py_truth_table(n, fun):
    m = re.match(r'fun \(?(\w+) : Fin \(?\d+\)? → Bool\)? => (.*)$', fun)
    if not m:
        raise ValueError('binder')
    var, b = m.group(1), m.group(2)
    b = re.sub(r'\b%s (\d+)' % re.escape(var), r'X[\1]', b)
    if re.search(r'\b%s\b' % re.escape(var), b):
        raise ValueError('var use')
    b = b.replace('&&', ' and ').replace('||', ' or ')
    b = re.sub(r'!(?!=)', ' not ', b)
    b = b.replace('Bool.true', 'True').replace('Bool.false', 'False')
    b = re.sub(r'\btrue\b', 'True', b)
    b = re.sub(r'\bfalse\b', 'False', b)
    if re.sub(r'\b(and|or|not|True|False|X)\b', '', b).strip(' ()[]0123456789') != '' and \
            not re.fullmatch(r'[\s()\[\]\d]*', re.sub(r'\b(and|or|not|True|False|X)\b', '', b)):
        raise ValueError('tokens')
    code = compile(b, '<body>', 'eval')
    y = 0
    for v in range(1 << n):
        X = [(v >> i) & 1 == 1 for i in range(n)]
        if eval(code, {'__builtins__': {}}, {'X': X}):
            y |= 1 << v
    return y


def truth_table(n, fun):
    return py_truth_table(n, fun), 'py'


MONO_RE = re.compile(r'^∀ (\w+) : ℕ, PEqualNP\.MetaComplexity\.HasCircuitSize \d+ \(fun .*?\) \1 → ∃ (\w+) : '
                     r'PEqualNP\.CircuitLowerBounds\.Circuit, PEqualNP\.MetaComplexity\.Monotone2 \2 ∧ \2\.size ≤ \1 ∧ ∀ ')


ONENOT_RE = re.compile(r'^∀ \(gates : List PEqualNP\.CircuitLowerBounds\.Gate\) \(o : ℕ\), .*'
                       r'GateOp\.not → \(gates\.get j\)\.op = PEqualNP\.CircuitLowerBounds\.GateOp\.not → i = j\) → '
                       r'\(∀ x : Fin [78] → Bool, .* → ∃ \(gates\' : List PEqualNP\.CircuitLowerBounds\.Gate\) ')


def family(stmt):
    """'lb' (lower bound / its ¬ form), 'mono' (monotone-equals-general, built by monofam.py on
    marceline-dev), 'onenot' ("one NOT gate saves nothing", built by onenot.py on marceline-dev)
    or None."""
    if classify(stmt):
        return 'lb'
    s = norm(stmt)
    if MONO_RE.match(s):
        return 'mono'
    if ONENOT_RE.match(s):
        return 'onenot'
    return None
