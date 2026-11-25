#!/usr/bin/env python3
"""Publish a proof of the NEGATED TWIN of a step we hold (join.txt: "If you believe a step is false,
prove its negated twin, listed beside it on the desk: that is how a counterexample is sent, as an
ordinary proof in a pull request").  Uses the town's own gitctl/github/validate helpers unchanged:
same fork, same signed identity, same branch scheme and PR shape as the publisher.

usage (from /var/lib/lubko/wd/viche):
  python3 /home/lubko/pnp-work/infra/twin_publish.py HELD_GAP TWIN_GAP CANDIDATE.lean [--dry-run]
Requires: HELD_GAP is LEASED by us; TWIN_GAP's statement is exactly the negation-twin of HELD_GAP's
(one is '¬ (' + other + ')'); TWIN_GAP is open on the public desk with no open PR.
"""
import json, re, sys, time, urllib.request
sys.path.insert(0, '/var/lib/lubko/wd/viche')
from missions.pnp import config, gitctl as git, github as gh, state, validate

held, twin, cand = sys.argv[1:4]
dry = '--dry-run' in sys.argv


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


rec = state.load(held)
assert rec and rec['state'] in ('LEASED', 'RESEARCHING'), 'held gap not leased: %r' % (rec and rec['state'])
r = urllib.request.Request('https://data.pequalnp.com/data/desk/gaps.json', headers={'User-Agent': 'viche-town'})
G = {g['id']: g for g in json.loads(urllib.request.urlopen(r, timeout=40).read())['gaps']}
assert twin in G, 'twin not open on the desk'
tg = G[twin]
a, b = norm(rec['statement']), norm(tg['statement'])
assert a in ('¬ (' + b + ')', '¬(' + b + ')') or b in ('¬ (' + a + ')', '¬(' + a + ')'), 'not negation twins'
assert tg['pr_open'] == 0, 'twin already has an open PR'
data = open(cand, 'rb').read()
meta = {'id': twin, 'file': tg['file'], 'module': tg['module'], 'statement': tg['statement'],
        'imports': tg['imports']}
digest = validate.validate(meta, data)
print('validated', twin, digest, len(data), 'bytes')
if dry:
    sys.exit(0)
branch = config.branch_for(twin)
base = git.ensure_mirror()
wt = git.fresh_worktree(twin, base, branch)
git.prepare_unpublished(wt, branch, base, None)
git.pin_candidate(wt, tg['file'], data)
sha = git.signed_commit(wt, base, twin)
print('signed', sha)
pushed = git.push_branch(branch)
assert pushed == sha, 'pushed sha differs'
for _ in range(30):
    ver = gh.commit_verification(sha)
    if ver.get('verified') is True:
        break
    time.sleep(5)
assert ver.get('verified') is True and ver.get('name') == config.AUTHOR_NAME, 'signature not verified'
num = gh.pr_exists_for(branch, twin) or gh.create_pr(branch, twin)
pr, problems = gh.validate_created(int(num), sha, tg['file'], expected_commits=[sha])
print('PR', num, 'problems', problems)
