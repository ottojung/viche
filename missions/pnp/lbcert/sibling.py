"""Statement skeletons and the merged-corpus skeleton index (billy-dev side of sibling transfer).

skeleton(s) = normalized statement, binder names x1.. -> x, every numeral -> '#' (identical to
marceline-dev /home/lubko/pnp-infra/lbgen/sibling.py, which builds and compiles the candidates).
index(mirror) = {skeleton: [module, ...]} of the merged upstream Outside files at upstream/main.
Incremental: skeletons are cached per blob sha, so a new commit costs only its new files.
"""
import json
import os
import re
import subprocess

import lbparse

NUM = re.compile(r'(?<![\w.])\d+(?![\w.])')


def skeleton(s):
    s = lbparse.norm(s)
    s = re.sub(r'\bx\d+\b', 'x', s)
    return NUM.sub('#', s)


def final_theorem(text, module):
    return re.search(r'(?ms)^theorem %s\s*:\s*(.*?)\s*:=' % re.escape(module), text)


def index(mirror, cache_dir, ref='refs/remotes/upstream/main'):
    git = ['git', '--git-dir=' + mirror]
    head = subprocess.run(git + ['rev-parse', ref], capture_output=True, text=True, check=True).stdout.strip()
    blobs_f = os.path.join(cache_dir, 'sibblobs.json')
    try:
        blobs = json.load(open(blobs_f))
    except (OSError, ValueError):
        blobs = {}
    ls = subprocess.run(git + ['ls-tree', '-l', head, 'lean/PEqualNP/Outside/'], capture_output=True,
                        text=True, check=True).stdout
    files = []
    for line in ls.splitlines():
        meta, path = line.split('\t', 1)
        _, _, sha, size = meta.split()
        m = re.fullmatch(r'lean/PEqualNP/Outside/(L_meta_\d+)\.lean', path)
        if m and size.isdigit() and int(size) <= 300000:
            files.append((sha, 'PEqualNP.Outside.' + m.group(1)))
    new = [(s, mod) for s, mod in files if s not in blobs]
    if new:
        p = subprocess.Popen(git + ['cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        for sha, mod in new:
            p.stdin.write((sha + '\n').encode())
            p.stdin.flush()
            hdr = p.stdout.readline().split()
            n = int(hdr[2])
            text = p.stdout.read(n).decode('utf-8', 'replace')
            p.stdout.read(1)
            m = final_theorem(text, mod)
            blobs[sha] = skeleton(m.group(1)) if m else None
        p.stdin.close()
        p.wait()
        tmp = blobs_f + '.tmp'
        json.dump(blobs, open(tmp, 'w'))
        os.replace(tmp, blobs_f)
    idx = {}
    for sha, mod in files:
        if blobs.get(sha):
            idx.setdefault(blobs[sha], []).append(mod)
    return head, idx
