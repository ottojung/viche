#!/bin/sh
# Act 21 §5: audit the exact resulting commit/tree using committed suite-status
# history and, when available, the immutable pre-push delivery receipts. A
# historical suite-status record for a commit added to main by that same commit
# is not pre-change evidence. Usage: suite-compliance-check.sh [repo]
set -eu
repo=${1:-${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
python3 - "$repo" "$state" <<'PY'
import json, subprocess, sys
repo,state=sys.argv[1:]
def git(*args):
    return subprocess.check_output(['git','-C',repo,*args], text=True).strip()
def first_parent_paths(commit):
    """Paths introduced by this first-parent step (including merge commits)."""
    try:
        parent=git('rev-parse','--verify','--quiet',commit+'^1')
    except subprocess.CalledProcessError:
        return git('diff-tree','--root','--no-commit-id','--name-only','-r',commit).splitlines()
    return git('diff','--name-only','--no-renames',parent,commit).splitlines()
def recorded_result(data, expected_suite):
    """Accept only generated records with a run matching the reported result."""
    if (data.get('generated_by')!='government/suite-status.sh'
            or data.get('suite')!=expected_suite):
        return None
    runs=data.get('runs')
    if not isinstance(runs,list):
        return None
    if any(not isinstance(run,dict) or run.get('run')!=i+1
           or not isinstance(run.get('exit'),int)
           for i,run in enumerate(runs)):
        return None
    if data.get('result')=='green':
        if (len(runs)==1 and runs[0].get('result')=='green'
                and runs[0].get('exit')==0):
            return 'green'
        if (len(runs)==2 and runs[0].get('result')=='red'
                and runs[0].get('exit')!=0 and runs[1].get('result')=='green'
                and runs[1].get('exit')==0):
            return 'green'
    if (data.get('result')=='red' and len(runs)==2
            and all(run.get('result')=='red' and run.get('exit')!=0
                    for run in runs)):
        return 'red'
    return None
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
        touched=first_parent_paths(rec_commit)
        if 'records/suite-status.json' in touched:
            records.append((rec_commit,data,'git'))
    # reviewed-merge.sh stores an immutable receipt before publishing the
    # candidate. The receipt is outside Git, so it can establish pre-push
    # ordering only to the extent the host filesystem and writer are trusted.
    import glob, os
    for filename in sorted(glob.glob(os.path.join(state,'delivery','verified-*.json'))):
        try:
            with open(filename) as f: data=json.load(f)
            if (data.get('generated_by')=='government/suite-status.sh'
                    and data.get('suite') in ('tests/run-all.sh','tests/records-smoke.sh')
                    and isinstance(data.get('recorded_at'),int)):
                records.append((None,data,'pre-push-receipt'))
        except (OSError,ValueError):
            continue

    changes=[]
    for i,commit in enumerate(commits):
        paths=first_parent_paths(commit)
        paths=[p for p in paths if p.startswith(('government/','tests/','records/'))]
        if not paths:
            continue
        expected_suite=('tests/records-smoke.sh'
                        if all(p.startswith('records/') for p in paths)
                        else 'tests/run-all.sh')
        tree=git('rev-parse',commit+'^{tree}')
        # Require the record commit to precede the main change. The record must
        # name that exact commit and its tree; a matching parent is insufficient
        # because it does not verify the resulting merge tree.
        prior=[]
        for rc,r,source in records:
            recorded=recorded_result(r,expected_suite)
            if recorded not in ('green','red') or r.get('tree') != tree:
                continue
            candidate=r.get('commit','')
            try:
                if git('rev-parse','--verify',candidate+'^{tree}') != tree:
                    continue
                if candidate != commit:
                    continue
                if source=='git' and positions.get(rc, i) >= i:
                    continue
                if source=='pre-push-receipt' and r.get('recorded_at',0) <= 0:
                    continue
            except (subprocess.CalledProcessError, OSError):
                continue
            prior.append((rc,r,source))
        reds=[(rc,r,source) for rc,r,source in prior
              if recorded_result(r,expected_suite)=='red']
        greens=[(rc,r,source) for rc,r,source in prior
                if recorded_result(r,expected_suite)=='green']
        if reds:
            status='violation'; reason='red suite recorded for exact commit/tree'
        elif greens:
            status='compliant'; reason='preceding green record for exact commit/tree ('+','.join(sorted(set(source for _,_,source in greens)))+')'
        elif any(recorded_result(r,expected_suite)=='red'
                 and r.get('commit')==commit and r.get('tree')==tree
                 for _,r,_source in records):
            status='red_chronology_unresolved'
            reason='exact red run exists but its pre-merge ordering is not established'
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
      'red_chronology_unresolved':sum(x['status']=='red_chronology_unresolved' for x in changes),
      'green_suite_compliance_rate':(good/total if total else None),
      'changes_reaching_main_red':[x for x in changes if x['status']=='violation'],
      'red_chronology_unresolved_changes':[x for x in changes if x['status']=='red_chronology_unresolved'],
      'per_change':changes},sort_keys=True))
except (subprocess.CalledProcessError, OSError) as err:
    print(json.dumps({'status':'unreadable','reason':str(err)}))
PY
