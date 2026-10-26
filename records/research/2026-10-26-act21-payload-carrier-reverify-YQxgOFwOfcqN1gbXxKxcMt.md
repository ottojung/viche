# Act 21 payload/carrier fixture re-verification

Verifier: agent `YQxgOFwOfcqN1gbXxKxcMt-unwritten`. This is a scratch-only
verification supplement, not a red-team, vote, enactment, or implementation
authorization. Repository: `git@github.com:ottojung/viche.git`; verified
base: `research/c1a00004-act21-operability` at
`8e92b413b26013b5fdc57510823cd366179fc78a`.

## Pinned material

All three pinned artifacts at the base match the issue's SHA-256 values:

- Bill: `4ea5e9299224de76c1774ee0c9b0ae425ee51cef1b5fe3af7cbcba6f4c69c12f`
- Assumptions: `923d5ea213459e8b9f035ca41a5d19f75df2a99787037d1c0a3a0a9f684babd3`
- Review: `74d7a1645f962feafeba8f901b6f52a04c58117652a1bd4bc704ea69701ade2d`

## Fresh scratch fixtures

In a new temporary Git repository, I committed a substantive candidate and
then a status-only carrier. Candidate commit `72823bb44e8c2c88f28305b06b95df9850b4e265`
has tree `fc90ec694a99377f979d7711afaa733751860e87`; carrier commit
`ba23213c0501eed12126d54c6c6a9b043971ea12` has tree
`a99e158b8b4b998ff9841d13b2226c29742f2672`. The trees differ, confirming
that the carrier containing the status record cannot have the attested
candidate's exact tree.

In a separate new temporary Git repository, I first wrote a placeholder
status record and computed tree `46d63be6ab453654f1cc854a87edb673cff27092`.
I then placed that tree hash into the status record and recomputed the tree;
the result was `3d8d929300ca135125b89012a5a03d7864bb1c2c`. They differ,
confirming that embedding a tree's own hash changes that tree. Both fixture
inequality assertions passed. No project files were used as scratch inputs.

## Validation and scope

The pinned hashes were checked with `sha256sum`; repository origin and base
ref were independently verified. The two scratch checks used Git's actual
tree objects and asserted the reported inequalities. No project test suite
applies to this research note. This does not establish a green-compliant
Executive path, red suite reaching main, or Act 21 §6 repeal trigger.

Next: sponsor integrates all red-team reports and responds point-by-point;
the Clerk independently determines Act 16 §1 eligibility. No ballots,
enactment, or implementation authorization are requested or implied.
