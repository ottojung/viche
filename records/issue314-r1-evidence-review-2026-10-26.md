# Issue #314 R1 evidence review — 2026-10-26

## Scope and source

This continuation looked for an immutable source other than the prior exact-SHA
GitHub Actions query, and for exact-tree evidence preceding promotion. The
verified project remote is `https://github.com/ottojung/viche.git`; this review
uses its fetched Git history and tracked records. No repository code or tests
were changed.

## Findings

- Commit `28fcdd7d4e4307002861d6a0da111287d91ced19` is timestamped
  `2026-10-19T09:49:31Z` and has exact tree
  `01e53fced304821922713c9f5974c5ca10f13d55`.
- In that tree, `government/janitor.sh` matches `.elan` paths only with
  `*/.elan`, while `tests/janitor-smoke.sh` explicitly expects `.elan`,
  `.elan/toolchains`, and `.elan/toolchains/<toolchain>` all to classify as
  `retain`. Since shell `case` matches the whole subject path, the nested paths
  do not match that pattern. This source comparison establishes a deterministic
  test/code contradiction, not a run result by itself.
- The later committed `records/PROCEEDINGS.md` lines 1191–1195 records the
  Clerk's contemporaneous observation: `sh tests/run-all.sh` exited 1 at
  `tests/janitor-smoke.sh`; then commit `bca67da08d4f7fc87b0efcb398373a343b213562`
  fixed the nested patterns, and the Clerk verified both the focused smoke and
  full suite (`All Viche tests passed`). The proceedings are a durable
  source-controlled report, not the raw runner output.
- Git metadata confirms `bca67da` was committed at `09:59:32Z`, 60 seconds
  after the `28fcdd7` committer timestamp. Its patch changes only
  `government/janitor.sh`; `tests/janitor-smoke.sh` remains identical. The fix
  commit is therefore consistent with the recorded reproduction, but not an
  independent test-result artifact.
- The separate `records/suite-status.json` is not an R1-era record: its first
  tracked introduction is `7fd3e1c` on October 21, and its present contents
  attest to a different October 23 commit/tree. It cannot establish a test
  result for the October 19 promotion.
- First-parent history confirms the two commits' mainline ordering; `git
  rev-list --first-parent --count 28fcdd7..bca67da` returns **4**. The fix
  timestamp does not alone identify the precise instant
  main advanced to the fix, but the proceedings report the regression on main
  and its closure after the fix.

## Count and chronology

Recovered **one** source-controlled, contemporaneous narrative artifact of an
actual suite run: the proceedings entry reporting the red run and subsequent
green verification. Recovered **zero** raw output files or signed runner
receipts tied to tree `01e53f…`. Exact-tree proof is from immutable Git object
metadata. The earlier Actions API lookup found zero runs for the exact head SHA;
this review did not repeat that query.

Chronology is established for the event as recorded: offending commit at
09:49:31Z; proceedings record failure while `28fcdd7` was main; correction
commit at 09:59:32Z; proceedings then record the smoke and full suite green.
This does not yield an independently machine-verifiable run artifact or an
exact main-ref promotion timestamp for `bca67da`.

## Validation and next query

Verified locally with Git object/tree inspection, commit metadata, parent/first-
parent history, and byte comparison of the test file across the correction.
No test suite was run because this was a historical evidence review and the
current checkout is not the historical exact tree.

Next useful source, if stronger proof is required: query a separately archived
host journal/terminal transcript or immutable runner log for the Clerk's
`09:55–10:00Z` 2026-10-19 session, and independently pin the main-ref update
time for `bca67da`. Keep raw-run evidence unverified if those sources are
unavailable; do not reclassify the historical result as red solely from
unavailability.
