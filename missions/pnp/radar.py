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

from . import config, frontier, gitctl, ledger
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lbcert'))
import lbparse  # noqa: E402
import plugins  # noqa: E402
import sibling  # noqa: E402

DESK = 'https://data.pequalnp.com/data/desk/gaps.json'
OUT = os.path.join(config.STATE_ROOT, 'radar')
CANDS = os.path.join(config.STATE_ROOT, 'lbcert', 'cands')
SWARM = os.path.join(config.STATE_ROOT, 'swarm', 'independent')
HOURS = 6


def normalize_skeleton(sk):
    # The sibling matcher deliberately retains projection-like numerals.
    # For economic family grouping, a bitmask before .testBit is data.
    return re.sub(r'(?<![\w.])\d+(?=\.testBit\b)', '#', sk)


def family_key(g):
    title = g.get('title') or ''
    if title:
        return 'title:'+re.sub(r'\d+', '#', ' '.join(title.split()))
    return 'statement:'+normalize_skeleton(sibling.skeleton(g['statement']))


def label(g):
    return family_key(g).split(':',1)[1]


def recent_merges(hours=HOURS, ref='refs/remotes/upstream/main'):
    """Advisory recent merge subjects; build() cross-checks indexed modules.

    The path-filtered git history walk times out on large proof bursts.
    Upstream squash-merge subjects name the lemma and PR. Read the pinned
    first-parent commit metadata only; ignore ambiguous subjects and count
    each lemma at most once. This is a learning signal, not a credit receipt.
    """
    git = ['git', '--git-dir=' + gitctl.MIRROR]
    p = subprocess.run(git + ['log', '--first-parent', '--since=%d hours ago' % hours,
                              '--format=%at%x00%an%x00%s', ref],
                       capture_output=True, text=True, timeout=20, check=True)
    out, seen = [], set()
    for line in p.stdout.splitlines():
        fields = line.split('\0', 2)
        if len(fields) != 3 or not fields[0].isdigit():
            continue
        at, who, subject = fields
        match = re.fullmatch(r'(?:Prove )?L-meta-(\d+)(?: \([A-Za-z0-9_-]+\))? \(#\d+\)', subject)
        if not match:
            continue
        module = 'PEqualNP.Outside.L_meta_' + match.group(1)
        if module not in seen:
            seen.add(module)
            out.append((module, who, int(at)))
    return out


def status(gid):
    try:
        return open(os.path.join(CANDS, gid + '.status')).read().split()[0]
    except OSError:
        return None


def posting_evidence(events):
    """Count actual attempts and retain the latest observed outcome per unit.

    Candidate generation is not proof acceptance. Unknown means the bounded
    posting attempt found no candidate, not that a unit is mathematically false.
    """
    latest = {}
    counts = collections.defaultdict(collections.Counter)
    for e in events:
        if e.get("stage") != "posting_generated":
            continue
        gid, outcome, at = e.get("gid"), e.get("result"), e.get("t")
        if not isinstance(gid, str) or outcome not in ("generated", "unsupported", "unknown") or not isinstance(at, (float, int)):
            continue
        counts[gid][outcome] += 1
        if gid not in latest or at >= latest[gid][0]:
            latest[gid] = (at, outcome)
    return counts, {g: e[1] for g, e in latest.items()}


def build():
    from .lbcert import live
    rows = json.loads(live.gaps_bytes(timeout=60))['gaps']
    gaps = [g for g in rows if isinstance(g.get('statement'), str)]
    head, idx = sibling.index(gitctl.MIRROR, os.path.join(config.STATE_ROOT, 'lbcert'))
    mod_sk = {m: normalize_skeleton(sk) for sk, ms in idx.items() for m in ms}
    sk_mods = collections.defaultdict(set)
    for m,sk in mod_sk.items():sk_mods[sk].add(m)
    sk_families=collections.defaultdict(set)
    found = plugins.discover()
    # gaps.json also lists closed steps and cut-of-cut sub-steps nobody can take (2359 vs 1820 open on
    # 2026-11-26); the live desk status says which are open, their points and how many hold them.
    from .lbcert import live
    now=time.time()
    snap=frontier.load(now)
    if not snap.get('complete') or not 0<=now-snap.get('observed',0)<=90:
        raise RuntimeError('fresh complete frontier unavailable; preserve prior radar')
    lg=snap['gaps']
    levels=frontier.cached_offer_levels(snap,now)
    offers_known=levels is not None and levels==frontier.offer_levels(snap,rows)
    attempts, latest = posting_evidence(ledger.read(HOURS))
    fams = {}
    for g in gaps:
        if lg is not None and g['id'] not in lg:
            continue
        sk = normalize_skeleton(sibling.skeleton(g['statement']))
        key = family_key(g)
        sk_families[sk].add(key)
        f = fams.setdefault(key, {'label': label(g), 'open': 0, 'unclaimed': 0, 'examples': [],
                                 'merged_6h': 0, 'authors': collections.Counter(), 'newest_merged': [],
                                 'statuses': collections.Counter(), 'coverage': None,
                                 'points': 0, 'free_points': 0, 'offerable':0, 'uncovered_offerable':0, 'uncovered_points':0, 'refused_offerable':0, 'refused_points':0, 'posting_attempts':collections.Counter(), '_skeletons':set(), '_coverage':collections.Counter()})
        f['_skeletons'].add(sk)
        f['open'] += 1
        f['unclaimed'] += not g.get('pr_open')
        s = (lg or {}).get(g['id']) or {}
        pts = s.get('points') or 0
        f['points'] += pts
        offered=offers_known and g.get("offerable_now") is True and not g.get("pr_open")
        if offered:
            f["offerable"]+=1
            f["free_points"] += pts * (0.3 if s.get("level")=="open" else 1)
        st = status(g['id'])
        if st:
            f['statuses'][st] += 1
        fam = lbparse.family(g['statement'])
        hit = None if fam else plugins.family_of(g['statement'], found)
        coverage = fam or (hit and 'plugin:' + hit[0]) or ''
        f['_coverage'][coverage]+=1
        f['posting_attempts'].update(attempts.get(g['id'], {}))
        # Prefer recent direct posting evidence over an older candidate status.
        result = latest.get(g['id'])
        refused = (result in ('unsupported', 'unknown') if result is not None
                   else st in ('unsupported', 'failed', 'toobig'))
        weight = pts * (0.3 if s.get("level")=="open" else 1)
        if offered and not coverage:
            f["uncovered_offerable"] += 1
            f["uncovered_points"] += weight
        if offered and coverage and refused:
            f["refused_offerable"] += 1
            f["refused_points"] += weight
        example={"id":g["id"],"statement":g["statement"][:1500],
                 "sketch":(g.get("sketch") or "")[:400],"offered":bool(offered),
                 "coverage":coverage, "refused":refused}
        f["examples"].append(example)
        f["examples"].sort(key=lambda x:(not x["offered"],bool(x["coverage"]),not x["refused"],-int(re.sub(r"\D","",x["id"]) or 0)))
        del f["examples"][3:]
    for mod, who, at in recent_merges(ref=head):
        keys=sk_families.get(mod_sk.get(mod),set())
        f = fams.get(next(iter(keys))) if len(keys)==1 else None
        if f:
            f['merged_6h'] += 1
            f['authors'][who] += 1
            if len(f['newest_merged']) < 3:
                f['newest_merged'].append(mod)
    for sk, f in fams.items():
        siblings=set().union(*(sk_mods[x] for x in f.pop('_skeletons')))
        f['siblings'] = len(siblings)
        cov=f.pop('_coverage')
        f['coverage_counts']=dict(cov)
        f['coverage']=next(iter(cov)) if len(cov)==1 else 'partial: '+', '.join(k for k in cov if k)
        if not f['newest_merged'] and f['siblings']:
            f['newest_merged'] = sorted(siblings, key=lambda m: -int(m.rsplit('_', 1)[1]))[:3]
        # value of a generator: what is open for us now plus the recent pace of the family
        # Desk points differ 100-fold between families (warmups ~10, open rows ~1000): weigh by the points
        # still takeable (open, no PR, a free parallel slot), in units of 100.
        f['score'] = (f['free_points'] / 100.0 if lg is not None else f['unclaimed']) + 0.5 * f['merged_6h']
        if (sk.startswith('statement:¬') or f['label'].startswith('It is false that:')) and not f['merged_6h']:
            f['score'] = 0      # twins of statements expected true: "none is expected" (desk sketch)
        f['authors'] = dict(f['authors'].most_common(5))
        f['statuses'] = dict(f['statuses'])
        f['posting_attempts'] = dict(f['posting_attempts'])
    ranked = sorted(fams.values(), key=lambda f: -f['score'])
    return {'at': time.time(), 'corpus': head, 'history_evidence': 'first-parent subjects matched to indexed proof modules', 'offers_known':offers_known,'families': ranked}


CONTRACT = """## How to deliver a generator (plugin contract)

Create `missions/pnp/lbcert/generators/NAME/gen.py` (read missions/pnp/lbcert/plugins.py):
- `MATCH = r'...'` (re.match against the normalized statement) or `def matches(statement)`;
- `python3 gen.py GID STATEMENT_FILE OUT.lean` -> exit 0 with a complete Lean file, 3 when this
  instance is beyond the generator; pure Python on billy-dev, <= 600 s.
- Learn the proof shape from the newest merged files of the family (git show HEAD:lean/PEqualNP/Outside/L_meta_N.lean
  in your checkout; Apache-2.0, credit the source module in a comment). Most families are one generic library +
  per-instance data (a witness circuit, sampled rows, a certificate): compute the data, keep the library.
- Test: `PYTHONPATH=/var/lib/lubko/wd/viche python3 -m missions.pnp.lbcert.plugtest NAME --holdout 3 --open 2`
  (local generation and static validation only; a candidate is not a compiler receipt).
- Deliver it through the normal delivery/integration queue. The broker retains responsibility for leases;
  the posting lane attempts applicable generators on legitimate assignments.
Worked example of the method: missions/pnp/lbcert/onenot (one-NOT family; local generation).
"""


def backlog_priorities(r):
    """Separate current addressable work from historical learning leads.

    Matching a plugin is only syntactic coverage, not evidence of a proof.
    If offerability is unknown, historical activity is explicitly advisory.
    """
    families = r["families"]
    uncovered = [f for f in families if f.get("uncovered_offerable", 0)]
    refused = [f for f in families if f.get("refused_offerable", 0)]
    historical = [f for f in families if
                  (not f["coverage"] or f.get("coverage_counts", {}).get("", 0))
                  and f["merged_6h"]]
    if r.get("offers_known"):
        todo = sorted(uncovered, key=lambda f: (-f["uncovered_points"], -f["uncovered_offerable"], -f["merged_6h"]))[:5]
        hard = sorted(refused, key=lambda f: (-f["refused_points"], -f["refused_offerable"], -f["merged_6h"]))[:3]
    else:
        todo, hard = [], []
    historical = sorted(historical, key=lambda f: -f["merged_6h"])[:3]
    return todo, hard, historical


def yield_leads(r):
    # Evidence on open catalog rows even when the offerability snapshots disagree.
    def failures(f):
        p = f.get('posting_attempts', {})
        return p.get('unsupported', 0) + p.get('unknown', 0)
    return sorted((f for f in r['families'] if failures(f)),
                  key=lambda f: (-failures(f), -f.get('merged_6h', 0)))[:5]


def write(r):
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, 'radar.json.tmp')
    json.dump(r, open(tmp, 'w'), indent=1)
    os.replace(tmp, os.path.join(OUT, 'radar.json'))
    lines = ['# PnP family radar (%s, corpus %s)' % (time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(r['at'])), r['corpus'][:12]),
             '', 'score = actual offerable desk points / 100 (no rival PR; verified catalog/status agreement) + 0.5 x merges in the last %d h.'
             ' coverage: built-in family, plugin, or none.' % HOURS,
             'Recent merge counts are advisory: first-parent merge subjects matched to indexed proof modules; ambiguous subjects omitted, not official credits.',
             '', '| score | free pts | unclaimed | open | merged %dh | top authors | coverage | our statuses | family |' % HOURS,
             '|---|---|---|---|---|---|---|---|---|']
    for f in r['families'][:30]:
        lines.append('| %.1f | %d | %d | %d | %d | %s | %s | %s | %s |' % (
            f['score'], f.get('free_points', 0), f['unclaimed'], f['open'], f['merged_6h'],
            ', '.join('%s %d' % kv for kv in f['authors'].items()) or '-', f['coverage'] or '**none**',
            ', '.join('%s %d' % kv for kv in f['statuses'].items()) or '-', f['label'].replace('|', '/')))
    open(os.path.join(OUT, 'radar.md'), 'w').write('\n'.join(lines) + '\n')
    todo, hard, historical = backlog_priorities(r)
    b = ['# Generator backlog (written by missions/pnp/radar.py; refreshed every 10 minutes)', '',
         'Actual offers are cross-checked against the public catalog/status; unknown offerability is not zero work.',
         'Credits go to the first accepted PR. Competitors win batches with per-family generators that open a PR',
         'seconds after a step is posted. Build the generator for the top family below that nobody in the town',
         'is already building (claim it by creating its generators/NAME directory in your delivery).', '']
    for i, f in enumerate(todo, 1):
        b += ['## %d. %s' % (i, f['label']),
              '', 'offerable points %d, offerable rows %d, no-PR rows %d, open %d, merged in %d h: %d (%s)' % (
                  f.get('free_points', 0),f.get('offerable',0), f['unclaimed'], f['open'], HOURS, f['merged_6h'],
                  ', '.join(f['authors']) or '-'),
              'newest merged proofs to study: %s' % (', '.join(f['newest_merged']) or 'none yet: derive the method'), '']
        for e in f['examples'][:2]:
            b += ['- %s: `%s`' % (e['id'], e['statement'][:700].replace('`', "'"))]
            if e['sketch']:
                b += ['  desk sketch: %s' % e['sketch'][:300]]
        b.append('')
    if not todo:
        b += ['No verified currently offerable uncovered family. Do not interpret this as a solved frontier.', '']
    b += ['## Historical learning leads (not current offers)', '']
    for f in historical:
        b += ['- %s: %d recent merges; %s' % (f['label'], f['merged_6h'], ', '.join(f['newest_merged']) or '-')]
    b += ['', CONTRACT]
    _put(os.path.join(SWARM, 'tool', 'BACKLOG.md'), '\n'.join(b))
    m = ['# Method backlog (missions/pnp/radar.py)', '',
         'Families where the town has a generator but it refuses many instances: a stronger argument',
         'turns refusals into credits. Preserve exact lemma source and independent semantic tests; kernel checks require a bound lease.', '']
    for f in hard:
        m += ['## %s' % f['label'], 'currently offerable refusals: %d (%d weighted points); statuses: %s; newest merged: %s' % (
            f['refused_offerable'], f['refused_points'], f['statuses'], ', '.join(f['newest_merged']) or '-'), '']
    if not hard:
        m += ['No verified offerable generator refusals; use the historical leads or exact held work.', '']
    m += ['', '## Recent direct posting evidence (not credits or guaranteed current offers)', '']
    for f in yield_leads(r):
        a = f['posting_attempts']
        m += ['- %s: %d generated candidates, %d unsupported, %d bounded unknown attempts in %dh; %d upstream merges in the matched family.' % (
            f['label'], a.get('generated', 0), a.get('unsupported', 0), a.get('unknown', 0), HOURS, f['merged_6h'])]
    m += ['','Use these counts to diagnose a failing method, not to infer truth or claim a lease.','']
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
