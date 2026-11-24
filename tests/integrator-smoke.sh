#!/bin/sh
# Act 31 integration queue, hermetic: a local bare origin, real
# propose-delivery.sh and suite-status.sh, and a fake antonina for reviewers.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
town=$tmp/town
remote=$tmp/origin.git
state=$tmp/state
mkdir -p "$town" "$state" "$tmp/bin"
git init --bare -q -b main "$remote"
git -C "$town" init -q -b main
git -C "$town" config user.name Fixture
git -C "$town" config user.email fixture@example.invalid
git -C "$town" config commit.gpgsign false
git -C "$town" remote add origin "$remote"
mkdir -p "$town/government" "$town/tests" "$town/records" "$town/constitution"
for f in suite-env.sh suite-status.sh integrator.py propose-delivery.sh review-delivery.sh dispatch-gate.sh; do
  cp "$repo/government/$f" "$town/government/$f"
done
# Fixture-only switch for a verifier setup outage before it emits a record.
python3 - "$town/government/suite-status.sh" <<'PYTEST'
from pathlib import Path
import sys
p=Path(sys.argv[1]);s=p.read_text()
assert "set -eu\n" in s
p.write_text(s.replace("set -eu\n",'set -eu\n[ "${VICHE_TEST_VERIFY_UNAVAILABLE:-no}" != yes ] || exit 2\n',1))
PYTEST
# Suites: red when records/BREAK and records/ARM are both present (green on
# each side alone, red once merged); every run is counted.
cat > "$town/tests/records-smoke.sh" <<'EOF'
#!/bin/sh
echo run >> "${SUITE_COUNTER:-/dev/null}"
if [ -e records/BREAK ] && [ -e records/ARM ]; then echo 'records/BREAK with records/ARM'; exit 1; fi
EOF
cp "$town/tests/records-smoke.sh" "$town/tests/run-all.sh"
printf 'canonical policy\n' > "$town/AGENTS.md"
printf 'old line\n' > "$town/records/shared.md"
printf 'row1\n' > "$town/records/ledger.tsv"
printf '# Laws\n' > "$town/government/LAWS.md"
printf 'charter\n' > "$town/constitution/CONSTITUTION.md"
printf '#!/bin/sh\necho v1\n' > "$town/government/tool.sh"
mkdir -p "$town/records/ballots" "$town/records/bills"
printf 'c1a00001\tClerk\tfixture\nc1a00002\tA\tfixture\nc1a00003\tB\tfixture\nc1a00004\tC\tfixture\nc1a00005\tD\tfixture\n' > "$town/government/seats.tsv"
printf 'Parallel vote fixture\n' > "$town/records/bills/parallel.md"
printf 'New ballot fixture\n' > "$town/records/bills/parallel-new.md"
digest=$(sha256sum "$town/records/bills/parallel.md" | cut -d ' ' -f1)
printf 'c1a00001\tyes\t%s\n' "$digest" > "$town/records/ballots/parallel.tsv"
git -C "$town" add -A
git -C "$town" commit -qm baseline
git -C "$town" push -q -u origin main

# Fake Antonina: records calls, hands out reviewer ids, reports them running.
cat > "$tmp/bin/antonina" <<EOF
#!/bin/sh
echo "\$*" >> "$tmp/antonina.log"
case "\$1 \$2" in
  'agent new') n=\$(grep -c '^agent new' "$tmp/antonina.log"); echo "rev\$n-fixture" ;;
  'agent run') exit 0 ;;
  'agent status') echo '{"state":"running"}' ;;
esac
EOF
chmod +x "$tmp/bin/antonina"
export PATH="$tmp/bin:$PATH" VICHE_TOWN_ROOT="$town" VICHE_STATE_ROOT="$state" SUITE_COUNTER="$tmp/suite-runs"

seat() { # seat NAME: a registered worktree on a fresh branch from main
  git -C "$town" worktree add -q -b "work-$1" "$tmp/$1" main >/dev/null 2>&1
  git -C "$tmp/$1" config user.name Fixture
}
propose() { # propose WORKTREE OFFICE SLUG
  (cd "$tmp/$1" && /bin/sh "$town/government/propose-delivery.sh" --office "$2" "$3") >/dev/null
}
integrate() { python3 "$town/government/integrator.py" run 2>>"$tmp/integrator.log"; }
st() { jq -r --arg b "delivery/$1" '[.entries[] | select(.branch == $b)] | last | .status' "$state/delivery/queue.json"; }
on_main() { git -C "$remote" cat-file -e "main:$1" 2>/dev/null; }

# 1. Additive records (a new file) land without review, as candidate + carrier.
seat a
printf 'plenary outcome\n' > "$tmp/a/records/outcome.md"
git -C "$tmp/a" add -A; git -C "$tmp/a" commit -qm 'c1a00002: plenary outcome'
base=$(git -C "$remote" rev-parse main)
propose a c1a00002 outcome
integrate
test "$(st outcome)" = landed
on_main records/outcome.md
carrier=$(git -C "$remote" rev-parse main)
candidate=$(git -C "$remote" rev-parse main^)
test "$(git -C "$remote" rev-parse main^^)" = "$base"                      # single candidate on main
test "$(git -C "$remote" diff --name-only "$candidate" "$carrier")" = records/suite-status.json
git -C "$remote" show -s --format=%B "$candidate" | grep -q '^Reviewed-By: none (additive records'
git -C "$remote" show -s --format=%B "$candidate" | grep -q '^Proposed-By: c1a00002$'
git -C "$remote" show "main:records/suite-status.json" | jq -e --arg c "$candidate" \
  '.commit == $c and .result == "green" and .verifier == "integrator"' >/dev/null
jq -e '[.assertions[] | select(.expected != .actual)] | length == 0' "$state/delivery/integration-$candidate.json" >/dev/null
test -s "$state/delivery/published-$candidate.json"
test "$(git -C "$town" rev-parse HEAD)" = "$carrier"                     # canonical fast-forwarded
python3 "$town/government/integrator.py" office c1a00002 | grep -q 'landed on main'
test ! -s "$tmp/antonina.log"                                             # no reviewer needed

# 2. A pure append to an existing record is additive too.
seat b
printf 'row2\n' >> "$tmp/b/records/ledger.tsv"
git -C "$tmp/b" add -A; git -C "$tmp/b" commit -qm 'append a ledger row'
propose b judiciary ledger
integrate
test "$(st ledger)" = landed
test "$(git -C "$remote" show main:records/ledger.tsv | wc -l)" -eq 2

# 3. Code needs an independent review; the integrator commissions it, ignores
#    the proposer's own approval and lands after another office approves.
seat c
printf '#!/bin/sh\necho v2\n' > "$tmp/c/government/tool.sh"
git -C "$tmp/c" add -A; git -C "$tmp/c" commit -qm 'tool v2'
before=$(wc -l < "$tmp/suite-runs")
propose c executive tool
test "$(wc -l < "$tmp/suite-runs")" -eq "$before"
test "$(tail -1 "$state/delivery/proposals.tsv" | cut -f6)" = deferred:tests/run-all.sh
head=$(git -C "$tmp/c" rev-parse HEAD)
integrate
test "$(st tool)" = reviewing
grep -q '^agent new --title Viche reviewer: delivery/tool' "$tmp/antonina.log"
grep -q '^agent run --id rev1-fixture ' "$tmp/antonina.log"
grep -q "review-delivery.sh delivery/tool $head approve --office reviewer-rev1-fixture" "$tmp/antonina.log"
python3 "$town/government/integrator.py" office executive | grep -q 'under independent review'
/bin/sh "$town/government/review-delivery.sh" delivery/tool "$head" approve --office executive --reason 'mine' >/dev/null
integrate
test "$(st tool)" = reviewing                                              # self-approval ignored
test "$(grep -c '^agent new' "$tmp/antonina.log")" -eq 1                   # no second reviewer yet
/bin/sh "$town/government/review-delivery.sh" delivery/tool "$head" approve --office reviewer-rev1-fixture --reason 'correct' >/dev/null
integrate
test "$(st tool)" = landed
git -C "$remote" show main:government/tool.sh | grep -q v2
git -C "$remote" show -s --format=%B main^ | grep -q '^Reviewed-By: reviewer-rev1-fixture$'
git -C "$remote" show main:records/suite-status.json | jq -e '.suite == "tests/run-all.sh"' >/dev/null

# 4. A rejection stops the delivery and tells the proposer why.
seat d
printf '#!/bin/sh\necho v3\n' > "$tmp/d/government/tool.sh"
git -C "$tmp/d" add -A; git -C "$tmp/d" commit -qm 'tool v3'
propose d executive tool-v3
integrate
/bin/sh "$town/government/review-delivery.sh" delivery/tool-v3 "$(git -C "$tmp/d" rev-parse HEAD)" reject \
  --office c1a00005 --reason 'breaks the v2 contract' >/dev/null
integrate
test "$(st tool-v3)" = rejected
python3 "$town/government/integrator.py" office executive | grep -q 'REJECTED by c1a00005: breaks the v2 contract'
git -C "$remote" show main:government/tool.sh | grep -q v2

# 5. A red candidate is not landed, keeps its log, and is not re-run every cycle.
seat e
printf 'x\n' > "$tmp/e/records/BREAK"
git -C "$tmp/e" add -A; git -C "$tmp/e" commit -qm 'green alone, red once merged'
SUITE_COUNTER=/dev/null propose e c1a00004 breaker
seat arm
printf 'x\n' > "$tmp/arm/records/ARM"
git -C "$tmp/arm" add -A; git -C "$tmp/arm" commit -qm 'main moves on'
git -C "$tmp/arm" push -q origin HEAD:main
: > "$tmp/suite-runs"
integrate
test "$(st breaker)" = red
if on_main records/BREAK; then echo 'a red candidate reached main' >&2; exit 1; fi
runs=$(wc -l < "$tmp/suite-runs")
test "$runs" -eq 2                                                         # flaky-red rule: two runs
integrate
test "$(wc -l < "$tmp/suite-runs")" -eq "$runs"
log=$(jq -r '[.entries[] | select(.branch == "delivery/breaker")] | last | .log' "$state/delivery/queue.json")
grep -q 'records/BREAK with records/ARM' "$log"
python3 "$town/government/integrator.py" office c1a00004 | grep -q 'RED: tests/records-smoke.sh failed twice'

# 5b. Infrastructure outage before an exact receipt is not a terminal red.
# The old main record is green but belongs to another SHA/tree.
seat verifier_outage
printf 'retriable\n' > "$tmp/verifier_outage/records/verifier-outage.md"
git -C "$tmp/verifier_outage" add -A
git -C "$tmp/verifier_outage" commit -qm 'verification outage recovery fixture'
propose verifier_outage judiciary verifier-outage
VICHE_TEST_VERIFY_UNAVAILABLE=yes integrate
test "$(st verifier-outage)" = approved
if on_main records/verifier-outage.md; then echo 'unverified candidate landed' >&2; exit 1; fi
jq -e '[.entries[] | select(.branch == "delivery/verifier-outage")] | last | .reason | contains("no fresh exact-candidate record")' "$state/delivery/queue.json" >/dev/null
integrate
test "$(st verifier-outage)" = landed
on_main records/verifier-outage.md

# 5c. Git may publish the carrier and lose its acknowledgement. Recover from
# authoritative remote ancestry, without running or recording a second suite.
seat lost_ack
printf 'published once\n' > "$tmp/lost_ack/records/lost-ack.md"
git -C "$tmp/lost_ack" add -A
git -C "$tmp/lost_ack" commit -qm 'lost acknowledgement fixture'
propose lost_ack judiciary lost-ack
REAL_GIT=$(command -v git)
export REAL_GIT
cat > "$tmp/bin/git" <<'GIT'
#!/bin/sh
set -eu
if [ "${VICHE_TEST_ACK_LOST:-no}" = yes ]; then
  case "$*" in
    *' push -q origin '*':refs/heads/main')
      "$REAL_GIT" "$@"
      exit 124
      ;;
  esac
fi
exec "$REAL_GIT" "$@"
GIT
chmod +x "$tmp/bin/git"
VICHE_TEST_ACK_LOST=yes integrate
test "$(st lost-ack)" = approved
on_main records/lost-ack.md
test "$(find "$state/delivery/pending-publication" -name '*.json' | wc -l)" -eq 1
remote_candidate=$(git -C "$remote" rev-parse main^)
test ! -f "$state/delivery/published-$remote_candidate.json"
runs=$(wc -l < "$tmp/suite-runs")
integrate
test "$(st lost-ack)" = landed
test "$(wc -l < "$tmp/suite-runs")" -eq "$runs"
jq -e '.observation=="remote ancestry recovered"' "$state/delivery/published-$remote_candidate.json" >/dev/null
test "$(jq -s --arg sha "$remote_candidate" 'map(select(.candidate==$sha))|length' "$state/delivery/landed.jsonl")" -eq 1
test "$(find "$state/delivery/pending-publication" -name '*.json' | wc -l)" -eq 0
rm "$tmp/bin/git"

# A network helper that starts a child and blocks cannot own the queue lock
# indefinitely. Only the spawned fixture process group is signalled.
python3 - "$town/government/integrator.py" "$tmp" <<'PYTEST'
import importlib.util,os,pathlib,sys,time
spec=importlib.util.spec_from_file_location("integrator_fixture",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=pathlib.Path(sys.argv[2]);fake=d/"bin"/"git"; child=d/"git-child"
fake.write_text('#!/bin/sh\nsleep 30 &\necho $! > "$GIT_TEST_CHILD"\nwait\n')
fake.chmod(0o755)
m.GIT_REMOTE_TIMEOUT=1
started=time.monotonic()
try:
    result=m.git("fetch","origin",check=False,env=dict(os.environ,GIT_TEST_CHILD=str(child)))
    assert result.returncode==124 and time.monotonic()-started<8
    pid=int(child.read_text())
    stat=pathlib.Path("/proc")/str(pid)/"stat"
    if stat.exists(): assert stat.read_text().rsplit(")",1)[1].split()[0] in ("Z","X")
finally:
    fake.unlink()
PYTEST

# 6. A conflict with main is reported, not landed.
seat f
printf 'their line\n' > "$tmp/f/records/shared.md"
git -C "$tmp/f" add -A; git -C "$tmp/f" commit -qm 'edit shared'
seat g
printf 'main line\n' > "$tmp/g/records/shared.md"
git -C "$tmp/g" add -A; git -C "$tmp/g" commit -qm 'edit shared on main'
git -C "$tmp/g" push -q origin HEAD:main
propose f c1a00006 shared
integrate
/bin/sh "$town/government/review-delivery.sh" delivery/shared "$(git -C "$tmp/f" rev-parse HEAD)" approve \
  --office c1a00007 --reason ok >/dev/null
integrate
test "$(st shared)" = conflict
python3 "$town/government/integrator.py" office c1a00006 | grep -q 'CONFLICT: conflicts with main in records/shared.md'

# 7. The Constitution is refused; law without an enactment trailer is refused.
seat h
printf 'amended\n' > "$tmp/h/constitution/CONSTITUTION.md"
git -C "$tmp/h" add -A; git -C "$tmp/h" commit -qm 'amend charter'
propose h c1a00008 charter
seat i
printf '## Act 99\n' >> "$tmp/i/government/LAWS.md"
git -C "$tmp/i" add -A; git -C "$tmp/i" commit -qm 'new act'
propose i c1a00009 law
integrate
/bin/sh "$town/government/review-delivery.sh" delivery/law "$(git -C "$tmp/i" rev-parse HEAD)" approve \
  --office c1a0000a --reason ok >/dev/null
integrate
test "$(st charter)" = refused
test "$(st law)" = refused
jq -r '.entries[] | select(.branch == "delivery/law") | .reason' "$state/delivery/queue.json" | grep -q 'Enacts: BILL'

# 8. Canonical evidence is never overwritten: an untracked canonical file at
#    the same path waits; the stale generated suite record is backed up.
seat j
printf 'new report\n' > "$tmp/j/records/report.md"
git -C "$tmp/j" add -A; git -C "$tmp/j" commit -qm 'report'
printf 'unreviewed local evidence\n' > "$town/records/report.md"
printf '{"stale":true}\n' > "$town/records/suite-status.json"
propose j judiciary report
integrate
test "$(st report)" = approved
jq -r '.entries[] | select(.branch == "delivery/report") | .reason' "$state/delivery/queue.json" | grep -q 'untracked canonical file'
grep -q 'unreviewed local evidence' "$town/records/report.md"
mv "$town/records/report.md" "$tmp/kept-report.md"
integrate
test "$(st report)" = landed
ls "$state/delivery/"suite-canonical-*.json >/dev/null

# 9. An office's dispatch gate wakes when its delivery changes state.
cp "$repo/government/dispatch-gate.sh" "$town/government/dispatch-gate.sh"
echo same | /bin/sh "$town/government/dispatch-gate.sh" check c1a00004 >/dev/null
/bin/sh "$town/government/dispatch-gate.sh" commit c1a00004
if echo same | /bin/sh "$town/government/dispatch-gate.sh" check c1a00004 >/dev/null; then
  echo 'gate did not skip unchanged inputs' >&2; exit 1
fi
printf '[{"status":"landed"}]\n' > "$state/delivery/office/c1a00004.json"
echo same | /bin/sh "$town/government/dispatch-gate.sh" check c1a00004 | grep -q inputs_changed

# 10. Deferring the proposer suite cannot let red code land.
seat redcode
printf '#!/bin/sh\nexit 1\n' > "$tmp/redcode/tests/run-all.sh"
git -C "$tmp/redcode" add -A; git -C "$tmp/redcode" commit -qm 'deliberately red code'
if (cd "$tmp/redcode" && /bin/sh "$town/government/propose-delivery.sh" --office executive --verify red-source) >/dev/null 2>&1; then
  echo 'Explicit source preflight accepted red' >&2; exit 1
fi
if git -C "$remote" show-ref --verify --quiet refs/heads/delivery/red-source; then
  echo 'Failed source preflight pushed a ref' >&2; exit 1
fi
propose redcode executive red-code
test "$(tail -1 "$state/delivery/proposals.tsv" | cut -f6)" = deferred:tests/run-all.sh
integrate
test "$(st red-code)" = reviewing
/bin/sh "$town/government/review-delivery.sh" delivery/red-code "$(git -C "$tmp/redcode" rev-parse HEAD)" approve \
  --office c1a00005 --reason 'fixture review' >/dev/null
base_red=$(git -C "$remote" rev-parse main)
integrate
test "$(st red-code)" = red
test "$(git -C "$remote" rev-parse main)" = "$base_red"

# 11. Distinct concurrent votes append without rewriting existing evidence.
seat vote_a
seat vote_b
printf 'c1a00002\tyes\t%s\n' "$digest" >> "$tmp/vote_a/records/ballots/parallel.tsv"
printf 'c1a00003\tno\t%s\n' "$digest" >> "$tmp/vote_b/records/ballots/parallel.tsv"
for v in vote_a vote_b; do git -C "$tmp/$v" add -A; git -C "$tmp/$v" commit -qm "$v"; done
propose vote_a c1a00002 vote-a
propose vote_b c1a00003 vote-b
integrate
test "$(st vote-a)" = landed
test "$(st vote-b)" = landed
git -C "$remote" show main:records/ballots/parallel.tsv > "$tmp/merged-ballots"
printf 'c1a00001\tyes\t%s\nc1a00002\tyes\t%s\nc1a00003\tno\t%s\n' "$digest" "$digest" "$digest" > "$tmp/expected-ballots"
cmp "$tmp/expected-ballots" "$tmp/merged-ballots"

# An add/add conflict for the first two rows is also append-only.
nd=$(sha256sum "$town/records/bills/parallel-new.md" | cut -d ' ' -f1)
seat new_a
seat new_b
printf 'c1a00002\tyes\t%s\n' "$nd" > "$tmp/new_a/records/ballots/parallel-new.tsv"
printf 'c1a00003\tno\t%s\n' "$nd" > "$tmp/new_b/records/ballots/parallel-new.tsv"
for v in new_a new_b; do git -C "$tmp/$v" add -A; git -C "$tmp/$v" commit -qm "$v"; done
propose new_a c1a00002 new-a
propose new_b c1a00003 new-b
integrate
test "$(st new-a)" = landed
test "$(st new-b)" = landed
test "$(git -C "$remote" show main:records/ballots/parallel-new.tsv | wc -l)" -eq 2

# Different votes by one seat cannot be reconciled automatically.
seat conflict_a
seat conflict_b
printf 'c1a00004\tyes\t%s\n' "$digest" >> "$tmp/conflict_a/records/ballots/parallel.tsv"
printf 'c1a00004\tno\t%s\n' "$digest" >> "$tmp/conflict_b/records/ballots/parallel.tsv"
for v in conflict_a conflict_b; do git -C "$tmp/$v" add -A; git -C "$tmp/$v" commit -qm "$v"; done
propose conflict_a c1a00004 conflict-a
propose conflict_b c1a00004 conflict-b
integrate
test "$(st conflict-a)" = landed
test "$(st conflict-b)" = conflict
test "$(git -C "$remote" show main:records/ballots/parallel.tsv | grep -c '^c1a00004')" -eq 1

# A branch attributed to another office cannot auto-resolve a new seat vote.
seat wrong_a
seat wrong_b
printf 'c1a00004\tyes\t%s\n' "$nd" >> "$tmp/wrong_a/records/ballots/parallel-new.tsv"
printf 'c1a00005\tyes\t%s\n' "$nd" >> "$tmp/wrong_b/records/ballots/parallel-new.tsv"
for v in wrong_a wrong_b; do git -C "$tmp/$v" add -A; git -C "$tmp/$v" commit -qm "$v"; done
propose wrong_a c1a00004 wrong-a
propose wrong_b c1a00002 wrong-b
integrate
test "$(st wrong-a)" = landed
test "$(st wrong-b)" = conflict

# 12. Ready short records land before expensive code, and no more than one
# full-suite candidate is attempted per pass. An aged candidate still follows
# the bounded record batch; this is a guaranteed slot, not age inversion.
seat long_a
seat long_b
seat short_a
printf 'a\n' > "$tmp/long_a/government/a-tool"
printf 'b\n' > "$tmp/long_b/government/b-tool"
printf 'record\n' > "$tmp/short_a/records/short-a.md"
for v in long_a long_b short_a; do git -C "$tmp/$v" add -A; git -C "$tmp/$v" commit -qm "$v"; done
propose long_a executive long-a
propose long_b executive long-b
integrate
for v in long-a long-b; do
  src=$(printf '%s' "$v" | tr - _)
  /bin/sh "$town/government/review-delivery.sh" "delivery/$v" "$(git -C "$tmp/$src" rev-parse HEAD)" approve --office c1a00005 --reason 'fixture review' >/dev/null
done
propose short_a judiciary short-a
integrate
test "$(st short-a)" = landed
test "$(st long-a)" = landed
test "$(st long-b)" = approved
test "$(tail -2 "$state/delivery/landed.jsonl" | jq -r .branch | tr '\n' ' ')" = 'delivery/short-a delivery/long-a '
seat short_b
printf 'record b\n' > "$tmp/short_b/records/short-b.md"
git -C "$tmp/short_b" add -A; git -C "$tmp/short_b" commit -qm short-b
propose short_b judiciary short-b
VICHE_INTEGRATOR_NOW=$(( $(date +%s) + 3601 )) integrate
test "$(st long-b)" = landed
test "$(st short-b)" = landed
test "$(tail -2 "$state/delivery/landed.jsonl" | jq -r .branch | tr '\n' ' ')" = 'delivery/short-b delivery/long-b '

# A record flood cannot starve the oldest ready full-suite candidate, and
# code age cannot suppress the entire ready record lane.
python3 - "$town/government/integrator.py" <<'PYTEST'
import importlib.util,sys
spec=importlib.util.spec_from_file_location("integrator_fixture",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def item(name,at,suite):
    return ({"branch":name,"at":at},{},None,suite)
ready=[item("record-%03d"%i,100+i,"tests/records-smoke.sh") for i in range(100)]
ready += [item("new-code",2000,"tests/run-all.sh"),item("old-code",0,"tests/run-all.sh")]
batch=m.landing_batch(list(reversed(ready)))
assert len(batch)==m.RECORD_BATCH_LIMIT+1
assert [i[0]["branch"] for i in batch[:-1]] == ["record-%03d"%i for i in range(m.RECORD_BATCH_LIMIT)]
assert batch[-1][0]["branch"]=="old-code"
assert len(m.landing_batch(ready[:100]))==m.RECORD_BATCH_LIMIT
PYTEST

# 13. Proposals from before Act 31 (no office column) are never picked up.
printf '2026-11-10T00:00:00Z\twork-x\trefs/heads/delivery/legacy\t%s\ttree\ttests/run-all.sh\n' "$head" \
  >> "$state/delivery/proposals.tsv"
integrate
test "$(jq '[.entries[] | select(.branch == "delivery/legacy")] | length' "$state/delivery/queue.json")" -eq 0

VICHE_INTEGRATOR=off python3 "$town/government/integrator.py" run
echo 'integrator smoke passed'
