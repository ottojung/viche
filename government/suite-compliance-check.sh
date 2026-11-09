#!/bin/sh
# Act 21 §5: audit the exact resulting commit/tree using committed suite-status
# history, the pre-push receipt plus post-push publication event, and (Act 26)
# the reviewer's detached pre-landing record. The event is hash-bound to the
# receipt and must have a later high-resolution timestamp; a receipt alone is
# never chronology evidence. A suite-status record committed by the same change
# is not pre-change evidence. Usage: suite-compliance-check.sh [repo]
set -eu
repo=${1:-${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
python3 - "$repo" "$state" <<'PY'
import datetime, hashlib, json, os, re, subprocess, sys, time
repo,state=sys.argv[1:]
start=time.monotonic()
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
    def valid_run(run, number):
        return (isinstance(run,dict) and type(run.get('run')) is int
                and run.get('run')==number and type(run.get('exit')) is int
                and run.get('result') in ('green','red')
                and re.fullmatch(r'[0-9a-f]{64}',str(run.get('output_sha256',''))) is not None)
    if any(not valid_run(run,i+1) for i,run in enumerate(runs)):
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
def canonical_digest(record):
    """Act 26 §2.1(3): hash the record minus its own digest field.

    UTF-8 JSON, lexicographically sorted keys, ','/':' separators, no
    insignificant whitespace and no trailing newline. Escaped code points would
    not be UTF-8, so ensure_ascii is false.
    """
    body={key:value for key,value in record.items() if key!='sha256'}
    canonical=json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
def iso_epoch(value):
    if not isinstance(value,str) or not value.strip():
        return None
    try:
        parsed=datetime.datetime.fromisoformat(value.strip().replace('Z','+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed=parsed.replace(tzinfo=datetime.timezone.utc)
    return parsed.timestamp()
def record_time(record):
    """Act 26 §2.1: created_at must not be later than the board pin's time.

    The pin is the chronology evidence; a created_at after the pin is
    backdated or inconsistent, and a record without a pin is incomplete.
    """
    pin=record.get('board_pin')
    if not isinstance(pin,dict) or not isinstance(pin.get('message_id'),str) or not pin['message_id'].strip():
        return None
    pin_time=iso_epoch(pin.get('server_timestamp'))
    created=iso_epoch(record.get('created_at'))
    if pin_time is None or created is None or created > pin_time:
        return None
    return pin_time
def act26_record(path,data):
    """Return the record's epoch time only if it is a complete Act 26 record."""
    if not isinstance(data,dict) or data.get('schema')!='act26-prelanding-record/v1':
        return None
    for field in ('commit','tree','parent','reviewer','independence_basis',
                  'phase','bill_id','landing_authorisation'):
        value=data.get(field)
        if not isinstance(value,str) or not value.strip():
            return None
    if data.get('verdict')!='pass':
        return None
    if data.get('status') in ('parent_mismatch','fail','failed'):
        return None
    commands=data.get('commands')
    if not isinstance(commands,list) or not commands:
        return None
    for entry in commands:
        if (not isinstance(entry,dict)
                or not isinstance(entry.get('command'),str)
                or not entry['command'].strip()
                or type(entry.get('exit')) is not int):
            return None
    if not isinstance(data.get('main_at_verification'),str) or not data['main_at_verification'].strip():
        return None
    timestamp=record_time(data)
    if timestamp is None:
        return None
    assertions=data.get('content_assertions')
    if not isinstance(assertions,list) or not assertions:
        return None
    for assertion in assertions:
        if not isinstance(assertion,dict):
            return None
        for field in ('expected','actual','basis'):
            value=assertion.get(field)
            if not isinstance(value,str) or not value.strip():
                return None
    digest=data.get('sha256')
    if not isinstance(digest,str) or re.fullmatch(r'[0-9a-f]{64}',digest) is None:
        return None
    if canonical_digest(data)!=digest:
        return None
    # Act 26 §2.1(3) writes the digest to a detached <record>.sha256, repeated
    # in the pin. A missing detached digest is a missing required field, and a
    # present one must agree with the canonical recomputation.
    try:
        with open(path+'.sha256',encoding='utf-8') as sidecar:
            detached=sidecar.read().strip()
    except OSError:
        return None
    if detached!=digest:
        return None
    return timestamp
try:
    main=git('rev-parse','--verify','main')
    commits=git('rev-list','--first-parent','--reverse',main).splitlines()
    positions={c:i for i,c in enumerate(commits)}
    # One batched tree/time lookup replaces a `git rev-parse` subprocess per
    # commit and per candidate record; this is the other dominant cost against
    # the monitor's 60s budget.
    trees={}
    commit_times={}
    for line in git('rev-list','--format=%H %T %ct',main).splitlines():
        parts=line.split()
        if len(parts)==3 and re.fullmatch(r'[0-9a-f]{40,64}',parts[0]):
            trees[parts[0]]=parts[1]
            try:
                commit_times[parts[0]]=int(parts[2])
            except ValueError:
                pass
    # Only a commit whose first-parent diff touches the status file can be a
    # record. Scanning every commit with `git show` was the dominant cost
    # (71s over 1141 changes against a 60s monitor budget); this one `git log`
    # prefilter is behaviour-preserving because the first_parent_paths check
    # below is kept.
    record_candidates=git('log','--first-parent','--reverse',
                          '--diff-merges=first-parent','--format=%H',
                          '--','records/suite-status.json').splitlines()
    records=[]
    for rec_commit in record_candidates:
        try:
            data=json.loads(subprocess.check_output(['git','-C',repo,'show',rec_commit+':records/suite-status.json'],text=True,stderr=subprocess.DEVNULL))
        except (subprocess.CalledProcessError, ValueError):
            continue
        recorded_commit=data.get('commit')
        # A status entry is evidence only if that commit itself introduced or
        # updated the status file; subsequent history snapshots aren't new runs.
        touched=first_parent_paths(rec_commit)
        if 'records/suite-status.json' in touched:
            records.append((rec_commit,data,'git',
                            'records/suite-status.json@'+rec_commit))
    # reviewed-merge.sh stores an immutable receipt before publishing and emits
    # a bound event after a successful push. Both are outside Git; chronology is
    # therefore only as trustworthy as the delivery host, filesystem and writer.
    import glob
    publications={}
    for filename in sorted(glob.glob(os.path.join(state,'delivery','published-*.json'))):
        try:
            with open(filename,'rb') as f: raw=f.read()
            event=json.loads(raw)
            if (event.get('generated_by')=='government/reviewed-merge.sh'
                    and isinstance(event.get('commit'),str)
                    and type(event.get('published_at_ns')) is int
                    and re.fullmatch(r'[0-9a-f]{64}',str(event.get('receipt_sha256','')))):
                publications[event['commit']]=event
        except (OSError,ValueError):
            continue
    for filename in sorted(glob.glob(os.path.join(state,'delivery','verified-*.json'))):
        try:
            with open(filename,'rb') as f: raw=f.read()
            data=json.loads(raw)
            if (data.get('generated_by')=='government/suite-status.sh'
                    and data.get('suite') in ('tests/run-all.sh','tests/records-smoke.sh')
                    and type(data.get('recorded_at')) is int):
                # A pre-push receipt alone cannot establish chronology: it may
                # have been copied into state after main changed. Require the
                # post-push event emitted by reviewed-merge.sh, bound to this
                # exact receipt digest, and strict timestamp ordering.
                event=publications.get(data.get('commit'))
                digest=hashlib.sha256(raw).hexdigest()
                if (event is not None and event.get('receipt_sha256')==digest
                        and event.get('published_at_ns') > data.get('recorded_at') * 1000000000):
                    records.append((None,data,'pre-push-receipt',
                                    os.path.basename(filename)))
        except (OSError,ValueError):
            continue
    # Act 26 §2.1 writes the reviewer's record to the state directory before a
    # fast-forward landing, so it is not in Git and has no suite-status shape.
    # It is evidence only on the same exact commit/tree as the change, and only
    # if its recorded time precedes the landing. A fast-forward creates no
    # commit at the landing, so the next first-parent commit is the first
    # deterministic upper bound on when the change became history. A record
    # for the current tip therefore fails closed until a later commit exists.
    act26_records=[]
    for filename in sorted(glob.glob(os.path.join(state,'delivery','*.json'))):
        try:
            with open(filename,'rb') as f: data=json.loads(f.read())
        except (OSError,ValueError):
            continue
        timestamp=act26_record(filename,data)
        if timestamp is not None:
            act26_records.append((os.path.basename(filename),data,timestamp))

    changes=[]
    for i,commit in enumerate(commits):
        paths=first_parent_paths(commit)
        paths=[p for p in paths if p.startswith(('government/','tests/','records/'))]
        if not paths:
            continue
        expected_suite=('tests/records-smoke.sh'
                        if all(p.startswith('records/') for p in paths)
                        else 'tests/run-all.sh')
        tree=trees.get(commit) or git('rev-parse',commit+'^{tree}')
        # Require the record commit to precede the main change. The record must
        # name that exact commit and its tree; a matching parent is insufficient
        # because it does not verify the resulting merge tree.
        prior=[]
        for rc,r,source,name in records:
            recorded=recorded_result(r,expected_suite)
            if recorded not in ('green','red') or r.get('tree') != tree:
                continue
            candidate=r.get('commit','')
            try:
                cand_tree=trees.get(candidate)
                if cand_tree is None:
                    cand_tree=git('rev-parse','--verify',candidate+'^{tree}')
                if cand_tree != tree:
                    continue
                if candidate != commit:
                    continue
                if source=='git' and positions.get(rc, i) >= i:
                    continue
                if source=='pre-push-receipt' and type(r.get('recorded_at')) is not int:
                    continue
            except (subprocess.CalledProcessError, OSError):
                continue
            prior.append((rc,r,source,name))
        reds=[(rc,r,source,name) for rc,r,source,name in prior
              if recorded_result(r,expected_suite)=='red']
        greens=[(rc,r,source,name) for rc,r,source,name in prior
                if recorded_result(r,expected_suite)=='green']
        # Act 26 chronology: the next first-parent commit bounds the landing.
        upper=commit_times.get(commits[i+1]) if i+1 < len(commits) else None
        act26_greens=[]
        parent=commits[i-1] if i>0 else None
        if upper is not None:
            act26_greens=[(name,r) for name,r,stamp in act26_records
                          if r.get('commit')==commit and r.get('tree')==tree
                          and r.get('parent')==parent
                          and r.get('main_at_verification')==parent
                          and stamp < upper]
        if reds:
            status='violation'; reason='red suite recorded for exact commit/tree'
        elif greens or act26_greens:
            labels=sorted(set(source for _,_,source,_ in greens))
            names=sorted(set(name for _,_,_,name in greens))
            if act26_greens:
                labels.append('act26-prelanding-record')
                names.extend(name for name,_ in act26_greens)
            status='compliant'; reason='preceding green record for exact commit/tree ('+','.join(sorted(set(labels)))+')'
        elif any(recorded_result(r,expected_suite)=='red'
                 and r.get('commit')==commit and r.get('tree')==tree
                 for _,r,_source,_name in records):
            status='red_chronology_unresolved'
            reason='exact red run exists but its pre-merge ordering is not established'
        else:
            status='unreadable'; reason='no preceding exact-commit/tree suite record'
        change={'commit':commit,'tree':tree,'paths':paths,'status':status,'reason':reason}
        if status=='compliant':
            change['source']=names[0] if len(names)==1 else ','.join(names)
            change['source_labels']=sorted(set(labels))
        changes.append(change)

    # Count distinct main changes with a recorded exact red result as episodes;
    # repeated status-file snapshots for the same main commit do not multiply it.
    red_events=len(set((x['commit'],x['tree']) for x in changes if x['status']=='violation'))
    total=len(changes)
    good=sum(x['status']=='compliant' for x in changes)
    print(json.dumps({'status':'measured','wall_seconds':round(time.monotonic()-start,3),'main_red_episodes':red_events,
      'change_count':total,'compliant':good,
      'unreadable':sum(x['status']=='unreadable' for x in changes),
      'violations':sum(x['status']=='violation' for x in changes),
      'red_chronology_unresolved':sum(x['status']=='red_chronology_unresolved' for x in changes),
      'green_suite_compliance_rate':(good/total if total else None),
      'changes_reaching_main_red':[x for x in changes if x['status']=='violation'],
      'red_chronology_unresolved_changes':[x for x in changes if x['status']=='red_chronology_unresolved'],
      'per_change':changes},sort_keys=True))
except (subprocess.CalledProcessError, OSError) as err:
    print(json.dumps({'status':'unreadable','reason':str(err),'wall_seconds':round(time.monotonic()-start,3)}))
PY
