"""Family radar: where the credited work is, what we cover, and what the tool team should build next.

Families = desk steps and recent upstream merges grouped by statement skeleton (numerals -> #).
For each: open, unclaimed (pr_open == 0), merged in the last 6 h and by whom, our coverage (a built-in
generator family, a generator plugin, merged siblings for the sweep), our statuses.
Writes PNP_STATE_ROOT/radar/radar.json and radar.md, and the tool team's backlog
PNP_STATE_ROOT/swarm/independent/tool/BACKLOG.md (+ method/BACKLOG.md): the best uncovered families,
each with example statements, the newest merged proofs to learn from and the plugin contract.

run: python3 -m missions.pnp.radar      (autosolve's sweep thread refreshes it every 10 minutes)
"""
import collections
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

from . import config, gitctl
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lbcert'))
import lbparse  # noqa: E402
import plugins  # noqa: E402
import sibling  # noqa: E402

DESK = 'https://data.pequalnp.com/data/desk/gaps.json'
OUT = os.path.join(config.STATE_ROOT, 'radar')
CANDS = os.path.join(config.STATE_ROOT, 'lbcert', 'cands')
SWARM = os.path.join(config.STATE_ROOT, 'swarm', 'independent')
HOURS = 6


def label(g):
    t = g.get('title') or ''
    return re.sub(r'\d+', '#', t)[:90] if t else sibling.skeleton(g['statement'])[:90]


def recent_merges(hours=HOURS):
    """[(module, author, unix time)] of upstream commits touching Outside/L_meta_*.lean."""
    git = ['git', '--git-dir=' + gitctl.MIRROR]
    p = subprocess.run(git + ['log', '--since=%d hours ago' % hours, '--format=@%an|%at', '--name-only',
                              'refs/remotes/upstream/main', '--', 'lean/PEqualNP/Outside/'],
                       capture_output=True, text=True, timeout=120)
    out, who, at = [], None, 0
    for line in p.stdout.splitlines():
        if line.startswith('@'):
            who, at = line[1:].rsplit('|', 1)
            at = int(at)
        else:
            m = re.fullmatch(r'lean/PEqualNP/Outside/(L_meta_\d+)\.lean', line.strip())
            if m:
                out.append(('PEqualNP.Outside.' + m.group(1), who, at))
    return out


def status(gid):
    try:
        return open(os.path.join(CANDS, gid + '.status')).read().split()[0]
    except OSError:
        return None


def build():
    r = urllib.request.Request(DESK, headers={'User-Agent': 'viche-town'})
    gaps = [g for g in json.loads(urllib.request.urlopen(r, timeout=60).read())['gaps']
            if isinstance(g.get('statement'), str)]
    head, idx = sibling.index(gitctl.MIRROR, os.path.join(config.STATE_ROOT, 'lbcert'))
    mod_sk = {m: sk for sk, ms in idx.items() for m in ms}
    found = plugins.discover()
    fams = {}
    for g in gaps:
        sk = sibling.skeleton(g['statement'])
        f = fams.setdefault(sk, {'label': label(g), 'open': 0, 'unclaimed': 0, 'examples': [],
                                 'merged_6h': 0, 'authors': collections.Counter(), 'newest_merged': [],
                                 'statuses': collections.Counter(), 'coverage': None})
        f['open'] += 1
        f['unclaimed'] += not g.get('pr_open')
        if len(f['examples']) < 3:
            f['examples'].append({'id': g['id'], 'statement': g['statement'][:1500], 'sketch': (g.get('sketch') or '')[:400]})
        st = status(g['id'])
        if st:
            f['statuses'][st] += 1
        if f['coverage'] is None:
            fam = lbparse.family(g['statement'])
            hit = None if fam else plugins.family_of(g['statement'], found)
            f['coverage'] = fam or (hit and 'plugin:' + hit[0]) or ''
    for mod, who, at in recent_merges():
        f = fams.get(mod_sk.get(mod))
        if f:
            f['merged_6h'] += 1
            f['authors'][who] += 1
            if len(f['newest_merged']) < 3:
                f['newest_merged'].append(mod)
    for sk, f in fams.items():
        f['siblings'] = len(idx.get(sk, []))
        if not f['newest_merged'] and f['siblings']:
            f['newest_merged'] = sorted(idx[sk], key=lambda m: -int(m.rsplit('_', 1)[1]))[:3]
        # value of a generator: what is open for us now plus the recent pace of the family
        f['score'] = f['unclaimed'] + 0.5 * f['merged_6h']
        if sk.startswith('¬') and not f['merged_6h']:
            f['score'] = 0      # twins of statements expected true: "none is expected" (desk sketch)
        f['authors'] = dict(f['authors'].most_common(5))
        f['statuses'] = dict(f['statuses'])
    ranked = sorted(fams.values(), key=lambda f: -f['score'])
    return {'at': time.time(), 'corpus': head, 'families': ranked}


CONTRACT = """## How to deliver a generator (plugin contract)

Create `missions/pnp/lbcert/generators/NAME/gen.py` (read missions/pnp/lbcert/plugins.py):
- `MATCH = r'...'` (re.match against the normalized statement) or `def matches(statement)`;
- `python3 gen.py GID STATEMENT_FILE OUT.lean` -> exit 0 with a complete Lean file, 3 when this
  instance is beyond the generator; pure Python on billy-dev, <= 600 s.
- Learn the proof shape from the newest merged files of the family (git show HEAD:lean/PEqualNP/Outside/L_meta_N.lean
  in your checkout; Apache-2.0, credit the source module in a comment). Most families are one generic library +
  per-instance data (a witness circuit, sampled rows, a certificate): compute the data, keep the library.
- Test: `PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.lbcert.plugtest NAME --holdout 3 --open 2`
  (generates, applies the town validator, compiles on marceline-dev; PASS = ready).
- Deliver it through the normal delivery/integration queue. Once on main, autosolve runs it on every unclaimed
  matching step within a minute and the bulk lane opens the PRs; a new gen.py version retries refused instances.
Worked example of the method: missions/pnp/lbcert/onenot (one-NOT family; runs on marceline-dev).
"""


def write(r):
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, 'radar.json.tmp')
    json.dump(r, open(tmp, 'w'), indent=1)
    os.replace(tmp, os.path.join(OUT, 'radar.json'))
    lines = ['# PnP family radar (%s, corpus %s)' % (time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(r['at'])), r['corpus'][:12]),
             '', 'score = unclaimed open steps + 0.5 x merges in the last %d h. coverage: built-in family, plugin, or none.' % HOURS,
             '', '| score | unclaimed | open | merged %dh | top authors | coverage | our statuses | family |' % HOURS,
             '|---|---|---|---|---|---|---|---|']
    for f in r['families'][:30]:
        lines.append('| %.1f | %d | %d | %d | %s | %s | %s | %s |' % (
            f['score'], f['unclaimed'], f['open'], f['merged_6h'],
            ', '.join('%s %d' % kv for kv in f['authors'].items()) or '-', f['coverage'] or '**none**',
            ', '.join('%s %d' % kv for kv in f['statuses'].items()) or '-', f['label'].replace('|', '/')))
    open(os.path.join(OUT, 'radar.md'), 'w').write('\n'.join(lines) + '\n')
    todo = [f for f in r['families'] if not f['coverage'] and f['score'] >= 2][:5]
    hard = [f for f in r['families'] if f['coverage'] and
            sum(v for k, v in f['statuses'].items() if k in ('unsupported', 'failed', 'toobig')) >= 3][:3]
    b = ['# Generator backlog (written by missions/pnp/radar.py; refreshed every 10 minutes)', '',
         'Credits go to the first accepted PR. Competitors win batches with per-family generators that open a PR',
         'seconds after a step is posted. Build the generator for the top family below that nobody in the town',
         'is already building (claim it by creating its generators/NAME directory in your delivery).', '']
    for i, f in enumerate(todo, 1):
        b += ['## %d. %s' % (i, f['label']),
              '', 'unclaimed %d, open %d, merged in %d h: %d (%s)' % (
                  f['unclaimed'], f['open'], HOURS, f['merged_6h'], ', '.join(f['authors']) or '-'),
              'newest merged proofs to study: %s' % (', '.join(f['newest_merged']) or 'none yet: derive the method'), '']
        for e in f['examples'][:2]:
            b += ['- %s: `%s`' % (e['id'], e['statement'][:700].replace('`', "'"))]
            if e['sketch']:
                b += ['  desk sketch: %s' % e['sketch'][:300]]
        b.append('')
    b.append(CONTRACT)
    _put(os.path.join(SWARM, 'tool', 'BACKLOG.md'), '\n'.join(b))
    m = ['# Method backlog (missions/pnp/radar.py)', '',
         'Families where the town has a generator but it refuses many instances: a stronger argument',
         'turns refusals into credits. Write the argument as a checked lemma plus what the generator must compute.', '']
    for f in hard:
        m += ['## %s' % f['label'], 'statuses: %s; unclaimed %d; newest merged: %s' % (
            f['statuses'], f['unclaimed'], ', '.join(f['newest_merged']) or '-'), '']
    m += ['One-NOT family: monotone size >= 12 needs the gate-elimination proof of the merged L-meta-14412',
          '(library from L-meta-9266); the live-set template of L-meta-14150 takes > 1 h of kernel time there.']
    _put(os.path.join(SWARM, 'method', 'BACKLOG.md'), '\n'.join(m) + '\n')


def _put(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    open(tmp, 'w').write(text)
    os.replace(tmp, path)


def main():
    r = build()
    write(r)
    print(open(os.path.join(OUT, 'radar.md')).read())


if __name__ == '__main__':
    main()
