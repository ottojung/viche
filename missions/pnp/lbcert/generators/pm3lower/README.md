# Perfect matching 3x3: reusable general lower bound

Source: merged public PEqualNP proof L-meta-27460,
`lean/PEqualNP/Outside/L_meta_27460.lean`, upstream revision
`6013fb4cf15e2ef3bdf96c97bc224b036b579ee6`, Apache-2.0 (license included).
The source's internal pm3_lower lemma proves at least 13 gates for any
fan-in-two circuit computing the six-term perfect matching function, not
just the original prefix. The adapter renames its helper namespace, converts
helper declarations to lemmas and closes each exact negative normal-form
prefix proposition at a bound less than 13 by that lemma and omega.
No import of another outside module; no weakening of the exact statement.
The source is hash pinned. A different function, positive statement, bound
13 or greater, or changed conjunct structure is refused.

The previous proof was already merged; this adapter is not a new discovery
of the lower bound. Candidate emission still needs the normal independent
kernel check and legitimate desk lease. In the 17:26 UTC cached catalog,
317 negative statements matched, none were currently offerable. This is
future readiness, not a claim of competitive credit.
