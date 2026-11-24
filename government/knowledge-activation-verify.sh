#!/bin/sh
# Fail-closed shared verifier for Institutional Knowledge Act office activation.
#
# Exits 0 ONLY when both hold:
#   (a) exactly one Institutional Knowledge and Communications Act is enacted in
#       canonical LAWS.md (the Act number is parsed at runtime, never hardcoded);
#   (b) the named office has a live activation whose authorized_by binds BOTH
#       that exact enacted Act number AND this exact office, inside a bounded
#       and currently valid time window.
#
# A bare "act:" prefix, a different Act number, another office's authorization,
# a missing/malformed field, malformed JSON or an absent record all fail closed.
# boot.sh, appointments.sh and knowledge-office-cycle.sh all use this one file
# so their activation decisions cannot drift apart. POSIX sh; no bashisms.
set -eu

office=${1:-}
town=${VICHE_TOWN_ROOT:-/var/lib/lubko/wd/viche}

case "$office" in
  statistics|foresight|strategy|spying) ;;
  *) exit 1 ;;
esac

laws=$town/government/LAWS.md
[ -s "$laws" ] || exit 1
# Act34's explicit new ordinary-law permission supersedes the first-use
# Act32/33 preflight circularity only for adaptive offices; it does NOT let an
# unreviewed JSON enabled flag authorize a session. The gate checks the
# enacted law and Git-committed Executive permit, Economy budget and 48-hour
# Judiciary stop, with exact office/hash/term matching.
if grep -Eq '^## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act \(enacted ' "$laws"; then
    [ -s "$town/government/knowledge-act34-gate.py" ] || exit 1
    activation=$town/records/knowledge/activation.json
    permit_ref=$(jq -er --arg office "$office" '
      .offices[$office].permit_ref | select(type == "string")
    ' "$activation") || exit 1
    permit=$town/$permit_ref
    [ -s "$permit" ] || exit 1
    # The v3 verifier is opt-in per durable Executive permit and is unavailable
    # until the exact Act 35 text is genuinely enacted. Legacy bytes/path stay intact.
    if jq -e '.control_certification != null' "$permit" >/dev/null 2>&1; then
      if grep -Eq '^## Act 35 — Knowledge Offices Ordinary Funding and Operations Parity Act 2026 \(enacted ' "$laws"; then
        [ -s "$town/government/knowledge-act34-certified-gate.py" ] || exit 1
        timeout 30 python3 "$town/government/knowledge-act34-certified-gate.py" "$office" "$town"
        exit $?
      fi
      exit 1
    fi
    timeout 20 python3 "$town/government/knowledge-act34-gate.py" "$office" "$town"
    exit $?
fi

# Require exactly one distinct enacted IKCA Act number. Ambiguity fails closed.
act_nums=$(
  sed -n 's/^## Act \([0-9][0-9]*\) — Institutional Knowledge and Communications Act (enacted .*/\1/p' "$laws" |
    sort -u
)
[ -n "$act_nums" ] || exit 1
[ "$(printf '%s\n' "$act_nums" | wc -l)" -eq 1 ] || exit 1
act_num=$act_nums

activation=$town/records/knowledge/activation.json
[ -s "$activation" ] || exit 1
now=$(date +%s)

# authorized_by must be exactly "act:<ACT_NUMBER>:<OFFICE>". This binds the
# specific enacted Act and the specific office; it cannot be replayed for a
# different office or satisfy a forged/generic Act reference.
jq -e \
  --arg office "$office" \
  --arg expect "act:$act_num:$office" \
  --argjson now "$now" '
    .schema=="viche-knowledge-activation-v1" and
    (.offices[$office].enabled==true) and
    (.offices[$office].authorized_by|type=="string") and
    (.offices[$office].authorized_by==$expect) and
    (.offices[$office].not_before|type=="number") and
    (.offices[$office].expires_at|type=="number") and
    ((.offices[$office].expires_at - .offices[$office].not_before) > 0) and
    ((.offices[$office].expires_at - .offices[$office].not_before) <= 3888000) and
    (.offices[$office].not_before <= $now) and
    (.offices[$office].expires_at > $now)
  ' "$activation" >/dev/null || exit 1

# A fixed telemetry reporter is NOT the independent adaptive Statistics Bureau.
# Founder's 2026-11-23 correction invalidates deterministic-v1 as an OFFICE
# activation mode. A manually invoked diagnostic does not authorize an office.
if [ "$office" = statistics ] &&
   jq -e '.offices.statistics.trial_mode == "deterministic-v1"' "$activation" >/dev/null 2>&1; then
  echo "Statistics: diagnostic-only mode cannot authorize a Bureau" >&2
  exit 1
fi

# Act 33 requires a separately authenticated Judiciary PROCEED before every
# Statistics / successor dispatch. An enabled JSON flag and an act label alone
# have never proved phase approval. The pointer only chooses the phase record;
# the independent verifier checks its Git provenance and officer corroboration.
if grep -Eq '^## Act 33 — Prospective Statistics Trial Clarification \(enacted ' "$laws"; then
  record=$(jq -er --arg office "$office" '
    .offices[$office].phase_gate_record |
    select(type == "string" and
           test("^records/knowledge/phases/[A-Za-z0-9_-]+[.]json$"))
  ' "$activation") || exit 1
  [ -s "$town/$record" ] || exit 1
  jq -e --arg office "$office" --argjson act "$act_num" '
    .schema=="viche-knowledge-phase-gate-v1" and
    .office==$office and .act==$act and .decision=="proceed"
  ' "$town/$record" >/dev/null 2>&1 || exit 1
  [ -s "$town/government/knowledge-phase-gate.sh" ] || exit 1
  # A missing or hung verifier denies only the office. Do not stop Parliament.
  timeout 30 /bin/sh "$town/government/knowledge-phase-gate.sh" verify "$record" >/dev/null 2>&1 || exit 1
fi
exit 0
