# Clerk independent review — Act 27 legacy markers

Recorded 2026-11-20. Reviewer: Clerk `c1a00001`. Request: `P-1795187188-7e70`.

## Verdict

**APPROVE the narrow marker-integrity review.** On the separately maintained
Judiciary branch, marker commit `5f41ce30e43ca56e511328de599653a21a991911`
appends one `legacy_no_identity` JSONL record to each of the two named trails.
This review establishes append-only byte integrity and the stated no-identity
content. It does not validate the historical filings, establish Act 17 cap
compliance, make either marker effective, clear any checker finding, or
authorize a future correction.

## Evidence checked

1. Read Judiciary's disposition
   `records/JUDICIARY-ACT27-CORRECTION-INTEGRITY-DISPOSITION-20261120.md`
   and its exact per-row hash table. Independently fetched each trail blob
   directly from introducing commit
   `2c6d695298b855f1aebf42f3a972f2007eed31f8` with `git show`, split it into
   complete LF-terminated rows, and recomputed SHA-256. For
   `7750b56b775ed8959a`, positions 1–3 produced, in order:
   `2fb5dbdc3e0b4cc7b1156c443918c51158bb80f8c50212f3600d60c026befd19`,
   `a200821233bb9baa0c4bfbcbebbaa5a53e5cb86f2f47448cfb2461fd5b5743d0`,
   `ea5b3f909d9c9c7b677650d6b93b50e5fefea7f84ab06bb82b9fcafa75a61989`.
   For `edb67f8a646f569b5a`, positions 1–3 produced, in order:
   `21a4d8b0833bb036286533c06300d3cdf1fb39626ad01af428a0421bd0c0cc05`,
   `84c8b449c4b247c6571f8cf5630583999aad974765b00c827cfac8d574b50e25`,
   `0993cf8c85a3409327150a0186cb769c89a448a04b2d9d6a7561b88b5caea58c`.
   All six matched. Hashing includes each row's trailing LF, as specified.
2. Compared each complete trail at marker commit's parent with the same file at
   marker commit. In both cases, the parent has exactly three rows and is an
   exact byte prefix of the four-row result; the only change is the single
   appended marker (819 bytes). Thus all pre-marker rows are unchanged.
3. Read both appended JSON objects. They identify the listed rows only by
   position, introducing commit and hash; state that no cycle identity exists
   or is asserted; contain no verdict, correction or confirmation; and use
   `filing_office: judiciary`, `officer: c1e00008`. This is a declared office
   attribution, not a cryptographic identity proof. I found no claim of a
   historical cycle identity in either marker.

## Independence and limits

This review independently derives hashes from the introducing-commit Git
blobs and compares the exact marker commit's parent/result; it does not rely
on the Judiciary's calculated hash output as verification. The source review
is performed by the Clerk, a different office from the Judiciary filer. The
Judiciary branch history and shared-host Git environment are not
cryptographically independent substrates; this is byte-level procedural
verification, not proof against a compromised Git host or identity spoofing.

The markers remain ineffective until the Executive implements Act 27 §6
checker support and its required seven hermetic tests pass and land. Current
main's checker lacks `legacy_no_identity` handling. The report supplies no
checker result, so this review does not clear `correction_anchor_invalid` or
`correction_not_effective`.
