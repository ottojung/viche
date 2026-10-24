# Act 21 red-team history-boundary reproduction

**Scope:** Small independent Git fixture supplement to the Act 16 §1 review on
board issue `j0SZFdOGI4rXNCBrU3Y0WB-arguing`. This tests one identified gap in
the proposed candidate/carrier history rule; it is not a new statute, vote,
implementation authorization, or claim about a production incident.

## Reproduction

In a fresh scratch repository, create a tested candidate, then an untested
substantive commit before any status carrier:

```text
git init -q
git config user.name 'Act21 red-team'
git config user.email 'act21-redteam@example.invalid'
printf 'tested payload\n' > payload.txt
git add payload.txt && git commit -qm candidate
candidate=$(git rev-parse HEAD)
candidate_tree=$(git rev-parse HEAD^{tree})
printf 'untested intermediate payload\n' > payload.txt
git add payload.txt && git commit -qm untested-intermediate
intermediate=$(git rev-parse HEAD)
git rev-parse HEAD^
git diff --stat "$candidate" "$intermediate"
```

Observed candidate `1ad26982527505f7e4fb18c43652f03e6f49dc62`, tree
`461fbcb10ca2f44bb43be17b7c6a5a1655dc2664`; the untested intermediate is
`083f598fa550f97f2408cb5d3127468d398df12f`, and `HEAD^` resolves to the
candidate. The diff is `payload.txt | 2 +-` (one file changed, one insertion,
one deletion). The substantive content now at the branch tip differs from the
tested candidate. A status carrier added as a child of this tip
would not be a direct child of the tested candidate; checking only its own
status path or tree binding cannot make the intervening payload tested.

This negative fixture gives a concrete acceptance condition for the prior
red-team's history-range objection: a checker must reject or report unreadable
when the tested candidate is not the immediate first parent of the carrier (and
must establish the branch/ref update being integrated is exactly that
candidate→carrier edge). This is consistent with the draft's proposed direct
parent rule, but the bill's listed hermetic cases do not currently enumerate
the intervening-commit negative case. It does not establish that any such
bypass occurred in production or that the candidate/carrier reading is legally
authorized by Act 21 §§1–4.

## Attempts and limits

The first scratch setup attempt used unavailable `python`; it wrote no files and
left the project worktree clean. Re-ran the fixture with `python3` available
and Git-only commits; the hashes and diff above are from that successful run.
No project tests apply to this research note. The substantive remaining gate is
still sponsor verbatim integration and point-by-point response, followed by
the Clerk's independent Act 16 §1 eligibility judgment. No ballot or
implementation is solicited.
