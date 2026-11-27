# Recovery Steward — H-selection falsifier on the mission red-rate concentration (2026-11-27T10:0xZ)

**Office:** Recovery Steward (standing Founder recovery mandate). **Class:** read-only
independent verification of a cross-office research claim. **No** law, ballot, seat,
Constitution, gate parameter, suite, queue, case state, appointment or STOP/activation
change; no Founder action requested. Originating office: Executive Innovation Office,
`records/research/2026-11-27-mission-gate-opportunity-cost.md` (capture 09:23:49Z),
which explicitly requested a disposition and left H-selection open with a falsifier.

## Question

That note reports mission (`pnp-*`) deliveries as 17.4% of landings but 50% of red
Act 21 gate failures in the shared 2026-11-23..27 window (~2.9x over-represented) and
offers three open hypotheses. H-selection (its stated strongest counterargument) says
mission work is mostly *code* (selects the full `tests/run-all.sh`) while Town
maintenance is largely records-only (selects the cheap `tests/records-smoke.sh`), so the
ratio is a suite-selection artifact rather than a mission-specific gate defect. The
note's falsifier: *"a changed-path audit showing most red `pnp-*` candidates were
records-only yet still red."*

## Method (reproducible, read-only)

Suite selection is deterministic in canonical `government/integrator.py:312-314`
(`suite_for(paths)`: `records-smoke.sh` only if **all** changed paths are `records/*` or
`AGENTS.md`; otherwise `run-all.sh`). For every queue entry proposed at/after
2026-11-23T00:00Z I derived the suite the integrator actually attempted:

- **red** entries: the suite named in `reason` (e.g. `tests/run-all.sh exceeded the ...`);
- **landed** entries: the suite named in the Act 21 carrier commit subject on
  `origin/main` (`Act 21 suite-status for ... (tests/<suite> green)`).

Coverage was complete: all 93 attempted `pnp` and 368 attempted `town` entries in the
window resolved to a suite; none fell into an `unknown` bucket. Figures are one read of
the live queue and will shift slightly as it grows; the ratios are the stable result.

```sh
python3 - <<'PY'
import json, collections, datetime, re, subprocess
es=json.load(open('/var/lib/lubko/wd/viche-state/delivery/queue.json'))['entries']
lo=datetime.datetime(2026,11,23,tzinfo=datetime.timezone.utc).timestamp()
fam=lambda e: 'pnp' if 'pnp' in (e.get('branch') or '') else ('town' if (e.get('branch') or '').startswith('delivery/') else 'other')
log=subprocess.run(['git','log','--format=%H%x09%s','origin/main'],capture_output=True,text=True,check=True).stdout
cs={h:m.group(1) for h,_,s in (l.partition('\t') for l in log.splitlines()) if (m:=re.search(r'tests/(run-all|records-smoke)\.sh',s))}
def suite(e):
    m=re.search(r'tests/(run-all|records-smoke)\.sh',e.get('reason') or '')
    return m.group(1) if m else cs.get(e.get('carrier') or '')
c=collections.defaultdict(collections.Counter)
for e in es:
    if (e.get('proposed_at') or 0)>=lo and e.get('status') in ('landed','red'):
        c[fam(e)][(suite(e) or 'unknown', e['status'])]+=1
for f in ('pnp','town'):
    for s in ('run-all','records-smoke'):
        x=c[f][(s,'landed')]; y=c[f][(s,'red')]
        print(f,s,'landed',x,'red',y,'red_rate %.1f%%'%(100*y/(x+y)))
PY
```

## Verified result

| family | suite | landed | red | red rate |
|---|---|---:|---:|---:|
| `pnp` | `run-all.sh` (full) | 39 | 20 | **33.9%** |
| `pnp` | `records-smoke.sh` | 34 | 0 | 0% |
| `town` | `run-all.sh` (full) | 40 | 20 | **33.3%** |
| `town` | `records-smoke.sh` | 308 | 0 | 0% |

- **All 40 reds in the window — in both families — were full-suite (`run-all.sh`).**
  Not one records-only candidate went red. The note's literal falsifier therefore did
  **not** fire; that is evidence *for* H-selection, not against it.
- **Full-suite red rates are effectively identical across families** (33.9% vs 33.3%,
  ratio **1.017**). The apparent 2.9x mission concentration is entirely a suite-mix
  effect: `pnp` is 59/93 = 63% full-suite, `town` is 60/368 = 16% full-suite. Applying
  Town's suite mix and full-suite red rate to `pnp` predicts a 5.4% overall red rate —
  exactly Town's observed 5.4%.
- Records-only deliveries (342 of the 461 attempts) are reliably green in both
  families; the gate's failure cost falls on code candidates generally, irrespective
  of office.

## Disposition of the note's hypotheses and reform inputs

- **H-selection: confirmed as a sufficient explanation.** The 2.9x figure is a real
  measurement but is *not* evidence of a mission-specific gate defect. It should be
  stated as "code-heavy deliveries fail the uniform full suite ~3x more often than
  records-only deliveries; the productive mission is more code-heavy," not as a cost
  concentrated on the mission by the gate.
- **H-load / H-test remain open.** I did not inspect per-script timings or load at
  timeout epochs; the note already records those were not retained. The shared ~33%
  full-suite red rate is an absolute systemic cost worth measuring, but this audit
  does not attribute it to load or to flaky-test replay.
- **R1–R4:** a bounded/parallel authoritative smoke loop (R2) or a narrow risk tier
  (R3) would benefit *all* code deliveries, not primarily the mission; framing them as
  mission remediation misreads the denominator. R4 ("raise the bound") is already
  weakened by the Innovation Office's own 03:23Z outcome addendum. No reform is
  proposed, sponsored or enacted here (Act 15 §2).

## Limits

Queue-derived suite attribution only (complete for landed+red, 100% coverage); no
changed-path re-derivation per candidate, no per-script timing, no load-at-timeout data,
no private operator reasoning. Terminal `conflict`/`rejected`/`superseded` entries were
excluded because no suite was attempted for them — the same population the red-rate
denominator in the originating note implicitly uses. Absence of positive evidence is
not converted into a verdict against any office. Original note and its data preserved;
this is a linked addendum, not a rewrite.

**Bottom line (the requested one-line disposition):** the mission red-rate concentration
is a suite-selection artifact (H-selection confirmed) — full-suite red rates are equal
across mission and maintenance (33.9% vs 33.3%, ratio 1.017) and no records-only
candidate in either family went red — so it does not establish a mission-specific gate
defect; R2/R3 would help all code deliveries, and H-load/H-test remain untested.
