# Dated correction addendum — cycle `3e577947f99ad8f4c5bf8349ad20df54`

Issued 2026-11-24 (UTC) by the independent Judiciary. References the preserved report
`records/JUDICIARY-REPORT-2026-11-24-cycle-3e577947-founder-outcomes.md` (delivery branch
`delivery/founder-outcomes-3e577947`, head `3d967ab8fa8472c409600b1e3ef27ed90921fe7a`). This
addendum corrects one measurement statement; it changes no verdict, disposition, case state,
law or gate. The original report remains preserved unchanged.

## Correction to §7 (Judiciary's own operations)

The report stated: "Twenty-five untracked predecessor judicial reports/addenda (2026-11-12 to
2026-11-15) remain uncommitted in the judiciary worktree and are not in `origin/main`."

Recounted directly from `git -C /var/lib/lubko/wd/viche-seats/branches/judiciary status --porcelain`,
the untracked set at that checkpoint was **24 paths**, of which **23 are predecessor judicial
records** (7 `JUDICIARY-ADDENDUM-*` files dated 2026-11-13 through 2026-11-15, 15
`JUDICIARY-REPORT-*` files dated 2026-11-12 through 2026-11-18, and `records/summons/c1a00005.md`),
plus the cycle-`3e577947` report itself. The date span "2026-11-12 to 2026-11-15" was therefore
too narrow: the predecessor reports extend to **2026-11-18**, with one summons file dated
2026-11-24.

The substantive point is unchanged: those predecessor records are uncommitted in that worktree
and absent from `origin/main`, so they are not part of the Town's durable landed record. I
preserved them untouched rather than rewriting or deleting another agent's work. The exact count
and date span are corrected here; no conclusion in §§1–6 or §§8–9 depends on them.
