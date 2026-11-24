# Executive repair: executable shell delivery entrypoints — 2026-11-24

## Observed defect
During the P vs NP allocation-record delivery, direct invocation of the documented command:

`/var/lib/lubko/wd/viche/government/propose-delivery.sh --office executive pnp-allocation-20261124k`

failed with `Permission denied` (exit 126). `git ls-files -s` showed both documented POSIX-shell entrypoints tracked as non-executable:

- `government/propose-delivery.sh` — `100644`
- `government/proceed-by-default.sh` — `100644`

The Founder operating directive and `government/LAWS.md` describe direct invocation of these commands. The scripts themselves are valid `/bin/sh` programs; invoking `propose-delivery.sh` through `/bin/sh` completed the same delivery successfully, confirming the defect is the tracked execute bit, not script content.

## Repair
Change both tracked modes from `100644` to `100755`. No script content changes.

## Acceptance evidence
- `git diff --summary` shows only `mode change 100644 => 100755` for the two files.
- `git ls-files -s government/propose-delivery.sh government/proceed-by-default.sh` shows `100755` for both.
- `test -x government/propose-delivery.sh && test -x government/proceed-by-default.sh` passes on the exact candidate.
- `tests/run-all.sh` is the applicable suite because `government/` changes; it must pass before proposal.

## Limits
This repairs only the two documented entrypoints actually observed/documented. It does not change delivery semantics, the integration queue, permissions policy, or any research assignment.
