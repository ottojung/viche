#!/bin/sh
# Act 21 §5: audit suite-status evidence against first-parent main history.
# A verification record must precede the change and name the exact resulting
# commit/tree. The history cannot prove how that information was available
# before an unmerged commit; fail closed as unreadable where no such evidence
# exists. Usage: suite-compliance-check.sh [repo]
set -eu
repo=${1:-${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}}
python3 - "$repo" <<'PY'
import json, subprocess, sys
repo=sys.argv[1]
def git(*args):
    return subprocess.check_output(['git','-C',repo,*args], text=True).strip()
try:
    main=git('rev-parse','--verify','main')
    commits=git('rev-list','--first-parent','--reverse',main).splitlines()
    positions={c:i for i,c in enumerate(commits)}
    records=[]
    for rec_commit in commits:
        try:
            data=json.loads(subprocess.check_output(['git','-C',repo,'show',rec_commit+':records/suite-status.json'],text=True,stderr=subprocess.DEVNULL))
        except (subprocess.CalledProcessError, ValueError):
            continue
        recorded_commit=data.get('commit')
        # A status entry is evidence only if that commit itself introduced or
        # updated the status file; subsequent history snapshots aren't new runs.
        touched=git('diff-tree','--root','--no-commit-id','--name-only','-r',rec_commit).splitlines()
        if 'records/suite-status.json' in touched:
            records.append((rec_commit,data))

    changes=[]
    for i,commit in enumerate(commits):
        paths=git('diff-tree','--root','--no-commit-id','--name-only','-r',commit).splitlines()
        paths=[p for p in paths if p.startswith(('government/','tests/','records/'))]
        if not paths:
            continue
        tree=git('rev-parse',commit+'^{tree}')
        # Require the record commit to precede the main change. The record must
        # name that exact commit and its tree; a matching parent is insufficient
        # because it does not verify the resulting merge tree.
        prior=[]
        for rc,r in records:
            if r.get('result') not in ('green','red') or r.get('tree') != tree:
                continue
            candidate=r.get('commit','')
            try:
                if git('rev-parse','--verify',candidate+'^{tree}') != tree:
                    continue
                if candidate != commit or positions.get(rc, i) >= i:
                    continue
            except (subprocess.CalledProcessError, OSError):
                continue
            prior.append((rc,r))
        reds=[(rc,r) for rc,r in prior if r.get('result')=='red']
        greens=[(rc,r) for rc,r in prior if r.get('result')=='green']
        if reds:
            status='violation'; reason='red suite recorded for exact commit/tree'
        elif greens:
            status='compliant'; reason='preceding green record for exact commit/tree'
        elif any(r.get('result')=='red' and r.get('commit')==commit
                 and r.get('tree')==tree for _,r in records):
            status='violation'; reason='red suite recorded for exact commit/tree (after change)'
        else:
            status='unreadable'; reason='no preceding exact-commit/tree suite record'
        changes.append({'commit':commit,'tree':tree,'paths':paths,'status':status,'reason':reason})

    # Count distinct main changes with a recorded exact red result as episodes;
    # repeated status-file snapshots for the same main commit do not multiply it.
    red_events=len(set((x['commit'],x['tree']) for x in changes if x['status']=='violation'))
    total=len(changes)
    good=sum(x['status']=='compliant' for x in changes)
    print(json.dumps({'status':'measured','main_red_episodes':red_events,
      'change_count':total,'compliant':good,
      'unreadable':sum(x['status']=='unreadable' for x in changes),
      'violations':sum(x['status']=='violation' for x in changes),
      'green_suite_compliance_rate':(good/total if total else None),
      'changes_reaching_main_red':[x for x in changes if x['status']=='violation'],
      'per_change':changes},sort_keys=True))
except (subprocess.CalledProcessError, OSError) as err:
    print(json.dumps({'status':'unreadable','reason':str(err)}))
PY
