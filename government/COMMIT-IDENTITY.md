# Viche office/seat commit identity (Founder directive, 2026-11-27)

Every real repository commit is authored and committed as
`Otto Jung <otto.jung@vauplace.com>`, signed with subkey
`08AF2726387BD4A4C87DF1821BEDDF96D7B1BA2B`, and credits the actual
contributor in a final `Co-authored-by:` trailer. Shared repository Git
configuration is never changed for this: use the `government/commit-identity.py`
tool, which supplies identity through `GIT_AUTHOR_*`/`GIT_COMMITTER_*` and
`git -c` and signs with `git commit -S`.

- Contributor identities are explicit `--contributor 'Name <email>'` arguments
  supplied by the accountable office; they are validated strictly and never
  inferred from Git config, board labels, prompts or file content.
- The shared managed-agent `prepare-commit-msg` hook adds
  `Co-authored-by: Antonina Agent <id>@antonina.local` when no explicit
  trailer is present. Do not overwrite or bypass that hook for ordinary commits.
- Use `--no-verify` only as a deliberate, reviewed exception; it skips hooks.
- Synthetic fixtures may set `VICHE_COMMIT_FIXTURE=1` to skip signing; this is
  never valid for a real delivery commit.

The operator's integrator patch (`delivery/commit-attribution-20261127`,
`ab614c90`) preserves co-authors through Viche integration. This worktree does
not edit `government/integrator.py`, to avoid a conflict; it coordinates with
Antonina issue `KFUiNF5QeWVrViVlgIrdUI-piteously`.
