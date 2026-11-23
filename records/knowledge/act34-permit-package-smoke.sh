#!/bin/sh
# Hermetic check of the Executive Act34 operating-permit package against the
# real shared gate. Skips (exit 0) until the operator gate lands on main.
set -eu
repo=$(CDPATH= cd "$(dirname "$0")/.." && pwd -P)
gate=$repo/government/knowledge-act34-gate.py
if [ ! -s "$gate" ]; then
  echo 'SKIP: government/knowledge-act34-gate.py not on main yet (operator head e8b0e420)'
  exit 0
fi
for f in records/knowledge/act34-proposed-knowledge-budget.conf \
         records/knowledge/act34-proposed-activation.json; do
  [ -s "$repo/$f" ] || { echo "SKIP: missing $f" >&2; exit 0; }
done
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT HUP INT TERM
town=$tmp/town
mkdir -p "$town/government" "$town/records/knowledge/permits" "$town/records/knowledge/pilot-reviews"
cat > "$town/government/LAWS.md" <<'EOF'
## Act 32 — Institutional Knowledge and Communications Act (enacted 2026-11-20)
## Act 34 — Rapid Full Institutional Activation and Continuous Improvement Act (enacted by lawful ballots)
EOF
cp "$gate" "$town/government/knowledge-act34-gate.py"
cp "$repo/government/knowledge-activation-verify.sh" "$town/government/knowledge-activation-verify.sh"
cp "$repo/records/knowledge/act34-proposed-knowledge-budget.conf" "$town/government/knowledge-budget.conf"
cp "$repo/records/knowledge/act34-proposed-activation.json" "$town/records/knowledge/activation.json"
for o in statistics foresight strategy spying; do
  cp "$repo/records/knowledge/permits/$o.json" "$town/records/knowledge/permits/$o.json"
done
printf '{"source":"fixture"}\n' > "$town/records/knowledge/spying-source-scope.json"
git -C "$town" init -q
git -C "$town" config user.email fixture@example.invalid
git -C "$town" config user.name fixture
git -C "$town" add .
git -C "$town" commit -qm fixture

verify() { VICHE_TOWN_ROOT="$town" /bin/sh "$town/government/knowledge-activation-verify.sh" "$1" >/dev/null 2>&1; }
echo '-- disabled-by-default manifest must fail closed for all four --'
for o in statistics foresight strategy spying; do
  if verify "$o"; then echo "FAIL: $o enabled by disabled manifest" >&2; exit 1; fi
done

python3 - "$town" <<'PY'
import hashlib,json,sys
from pathlib import Path
t=Path(sys.argv[1]); a=t/'records/knowledge/activation.json'
d=json.loads(a.read_text())
for o in d['offices']: d['offices'][o]['enabled']=True
a.write_text(json.dumps(d))
c=t/'government/knowledge-budget.conf'; cfg=json.loads(c.read_text())
for o in cfg['offices']: cfg['offices'][o]['enabled']=True
c.write_text(json.dumps(cfg)); h=hashlib.sha256(c.read_bytes()).hexdigest()
for o in ('statistics','foresight','strategy','spying'):
    p=t/'records/knowledge/permits'/(o+'.json'); permit=json.loads(p.read_text())
    permit['budget_sha256']=h; permit['signature_status']='signed'
    p.write_text(json.dumps(permit))
    d['offices'][o]['permit_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
a.write_text(json.dumps(d))
PY
git -C "$town" add .
git -C "$town" commit -qm 'fixture: lawful signature + activation'

echo '-- signed/enabled package must authorize all four in parallel --'
for o in statistics foresight strategy spying; do
  verify "$o" || { echo "FAIL: $o not authorized after lawful activation" >&2; exit 1; }
done
echo 'PASS: disabled manifest fails closed; signed+enabled package authorizes four adaptive offices in parallel'
