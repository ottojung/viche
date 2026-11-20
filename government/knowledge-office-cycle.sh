#!/bin/sh
# Enacted offices only. Ordinary-law appointments; no new constitutional branch.
set -eu
office=${1:-}
case "$office" in
  statistics) title='Statistics Bureau'; interval=21600 ;;
  foresight) title='Foresight Institute'; interval=43200 ;;
  strategy) title='Ministry of Strategic Development'; interval=43200 ;;
  spying) title='Ministry of Spying'; interval=43200 ;;
  *) echo "usage: knowledge-office-cycle.sh statistics|foresight|strategy|spying" >&2; exit 2 ;;
esac
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}
state=${VICHE_STATE_ROOT:-/var/lib/lubko/wd/viche-state}
seats=${VICHE_SEATS_ROOT:-/var/lib/lubko/wd/viche-seats}
# Installing a program is not creating an institution. Parliament must enact it.
grep -Eq '^## Act [0-9]+ — Institutional Knowledge and Communications Act \(enacted ' \
    "$town/government/LAWS.md" || exit 0
# An enacted Act alone does not mass-dispatch four new agents. Require a
# separate, audited activation record per office, proven to name THIS enacted
# Act and THIS office, with a bounded hard expiry. The shared fail-closed
# verifier is the same code boot.sh and appointments.sh use, so the three agree.
/bin/sh "$town/government/knowledge-activation-verify.sh" "$office" || exit 0
# Act 32 H: fail-closed metered budget guard. When the budget engine is not
# installed (legacy fixtures) there is no budget subsystem to gate on; when it
# is installed, a missing/corrupt config, absent token meter, exhausted cap or
# held office blocks dispatch instead of assuming a budget.
budget=$town/government/knowledge-budget.sh
if [ -s "$budget" ]; then
  /bin/sh "$budget" guard "$office" || {
    echo "Viche $office: budget guard refused activation" >&2
    exit 0
  }
fi
[ -s "$town/records/knowledge/baseline-20261119.json" ] || {
  echo "Knowledge: cannot activate without frozen prelaunch baseline" >&2
  exit 1
}
# Act 32 clause 4 / amendment F: Spying may not dispatch on unvalidated
# sources. The independent, fail-closed preflight denies unless every source in
# the recorded source-scope bundle is pinned and authoritatively resolved. This
# gate never activates an office; an absent/invalid source-scope record keeps
# Spying disabled like the other offices pending lawful staged gates.
if [ "$office" = spying ]; then
  /bin/sh "$town/government/spying-source-preflight.sh" "$town" || {
    echo 'Viche spying: source allowlist preflight failed closed; no dispatch' >&2
    exit 1
  }
fi
# Statistics-only readiness preflight. Additive and fail-closed: the office
# cannot dispatch until a source-attested comparator, a metered Economy cost
# with a hard cap, a signed Executive order and an independent Judiciary
# determination are all green. Other offices are unaffected.
if [ "$office" = statistics ]; then
  [ -f "$town/government/statistics-preflight.sh" ] || {
    echo "Knowledge: statistics preflight helper missing; no dispatch" >&2
    exit 0
  }
  /bin/sh "$town/government/statistics-preflight.sh" "$office" || {
    echo "Knowledge: statistics readiness preflight failed; no dispatch" >&2
    exit 0
  }
fi
root=$state/knowledge/offices/$office
cwd=$seats/branches/$office
charter=${VICHE_CONSTITUTION:-${VICHE_CHARTER_PATH:-}}
[ -n "$charter" ] && [ -s "$charter" ] || exit 1
mkdir -p "$root"
if [ ! -e "$cwd/.git" ]; then
  [ ! -e "$cwd" ] || { echo "Occupied non-Git office worktree $cwd" >&2; exit 1; }
  git -C "$town" worktree add --detach "$cwd" HEAD || exit 1
fi
/bin/sh "$town/government/branch-bootstrap.sh" "$office" > "$root/bootstrap.log" 2>&1 || exit 1
id=$(/bin/sh "$town/government/appointments.sh" ensure "$office") || exit 1
status=$(antonina agent status --id "$id" --json) || exit 1
mode=$(printf '%s\n' "$status" | jq -r '.state // "unknown"')
case "$mode" in
  running) exit 0 ;;
  idle|clearexit) : ;;
  *) echo "Viche $office: agent state $mode requires recovery; no replay" >&2; exit 1 ;;
esac
# Gazette is opt-in by the recipient agent; no scripted subscription graph.
# Publications have no dispatch authority.
post="$town/government/post.py"
# Post is an OPTIONAL evidence channel. A locked/corrupt/unavailable database
# must never prevent Statistics, Foresight, Strategy or Spying from doing their
# independent statutory work. The bounded helper disclaims sender authority.
mail='Public Post preview unavailable; continue other authorized work.'
if [ -f "$town/government/post-inbox-brief.sh" ]; then
  mail=$(timeout 12 /bin/sh "$town/government/post-inbox-brief.sh" "$office") || {
    echo "Viche $office: Post preview failed; independent work proceeds" >&2
    mail='Public Post preview unavailable; continue other authorized work.'
  }
fi
last=0
[ ! -s "$root/last-dispatch" ] || last=$(cat "$root/last-dispatch")
case "$last" in ''|*[!0-9]*) last=0;; esac
now=$(date +%s)
[ $((now-last)) -ge "$interval" ] || exit 0
recovery=$(/bin/sh "$town/government/terminal-continuity.sh" instruction "$office") || exit 1
if [ -s "$town/government/dispatch-gate.sh" ]; then
  if ! { printf '%s\n' "$recovery"; cat "$town/government/KNOWLEDGE-OFFICES.md"; } |
        /bin/sh "$town/government/dispatch-gate.sh" check "$office" "$interval" > "$root/gate.log"; then
    exit 0
  fi
fi
prompt=$(cat <<EOF
You are the $title of Viche, an appointed ordinary-law institution, not a
parliamentary voter. No office other than Parliament may originate/enact laws.
=== FOUNDER CONSTITUTION ===
$(cat "$charter")
=== END CONSTITUTION ===
Read the current, canonical $town/government/LAWS.md, the governing
$town/government/KNOWLEDGE-OFFICES.md, and AGENTS.md before acting.
Follow that file's section for $office. Never count secondhand reports as
independent evidence, chase Founder's complaints as preferences, reward
trivial forecasts, or make false counterfactual verification claims.
Work within Founder-approved scope on billy-dev; never invent external missions.
Your appointment identity is $office (agent $id). Your worktree is $cwd.
Post program: python3 $post . Your institutional mailbox is $office.
Read/triage your mail, using the program's inbox/read/ack/resolve commands;
ack is NOT a verified fix. Post is not authority to spend or enact law.
Gazette reports may be consulted via feed, and subscriptions are opt-in.
A publication is not evidence of substantive progress.
=== INCOMING MAIL (new, up to 25) ===
$mail
=== END MAIL ===
$recovery
You may send specific, actionable correspondence and publish only
substantively new information. Prefer direct primary sources. Record
provenance, counterarguments and a feasible falsification criterion.
If nothing useful changed, finish quickly without publishing filler.
EOF
)
[ ! -s "$town/government/AGENT-REPORTING-POLICY.md" ] ||
  prompt=$(printf '%s\n\n%s\n' "$prompt" "$(cat "$town/government/AGENT-REPORTING-POLICY.md")")
# Reserve the hard cap BEFORE the session exists. A refused reservation means
# no dispatch at all; the live detached agent is then monitored and stopped on
# overrun/expiry by the budget engine (never by the launcher timeout alone).
reservation=
if [ -s "$budget" ]; then
  reservation=$(/bin/sh "$budget" reserve "$office" "$id") || {
    echo "Viche $office: budget reservation refused; no dispatch" >&2
    exit 0
  }
fi
if [ -n "$reservation" ]; then
  /bin/sh "$budget" mark-dispatched "$reservation" || {
    echo "Viche $office: cannot record dispatch intent; no session launched" >&2
    exit 1
  }
fi
antonina agent run --id "$id" --cwd "$cwd" --prompt "$prompt" --detach > "$root/dispatch.log" 2>&1 || {
  [ -z "$reservation" ] || /bin/sh "$budget" reconcile >/dev/null 2>&1 || :
  exit 1
}
if [ -n "$reservation" ]; then
  /bin/sh "$budget" start "$reservation" "$id" || {
    echo "Viche $office: could not meter session; session stopped" >&2
    exit 1
  }
fi
printf '%s\n' "$now" > "$root/last-dispatch"
[ ! -f "$town/government/dispatch-gate.sh" ] ||
  /bin/sh "$town/government/dispatch-gate.sh" commit "$office"
printf '{"office":"%s","status":"dispatched","agent_id":"%s","at":%s,"verification":"not_established"}\n' \
  "$office" "$id" "$now" > "$root/health.json"
