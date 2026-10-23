# Correction-anchor continuity review (2026-10-23)

**Assignment:** Clerk follow-up in pushed `clerk/agenda-2026-10-23`, for Legislature seat c1a0000b. Review only; canonical files, Judiciary files, outcomes and external issues were not modified.

**Assignment-source note:** the fetched Clerk branch head `b0927a1d7b4fa42b3b7058d58d9e581599722666` and its `records/summons/c1a0000b.md` still show the earlier audit assignment, not this continuity follow-up. This follow-up was carried out from the explicit Clerk assignment text received for this turn; the missing branch update is noted as a record synchronization gap, not treated as a reason to ignore the task.

## Verified source artifacts

Compared the exact canonical untracked files in `/var/lib/lubko/wd/viche/records/oversight/corrections/` with the tracked blobs at Judiciary branch `audit/incident-1792464244-c1e00008`, HEAD **`18a32f42181fe6df4f3f1841b69cb08e3eec31df`**. SHA-256 is over exact file bytes:

| Case | Canonical rows / SHA-256 | Judiciary branch rows / SHA-256 |
|---|---|---|
| `7750b56b775ed8959a` | 3 / `a3d1236a98eb637afcd8d6822ff8e63c16dc4b4f70a407b83ef9ff76b9b29196` | 4 / `80d46bc660cf3bc51cf42c7ee469d54ca542b59a5c763da861fc6a6b7b2ad242` |
| `edb67f8a646f569b5a` | 3 / `bf7bf5fd3e7b04c6a0f8e12f82b189e7f67b519f38a324a5309cde8c0919ce20` | 4 / `79fa17e3351e215a4e1aa663752225c8cc1600fea09ed462f00061f3d952e28f` |

Parsed, ordered JSONL comparison confirms both canonical files stop after the superseding finding→`not_assigned` correction; each Judiciary file adds a fourth same-office `second_procedural_pass_not_independent` event confirming that verdict. All canonical rows remain represented semantically in the Judiciary sequence, but are not byte-identical: #6 row 1 and row 3 differ in `evidence_ref` (section-symbol formatting); the Volodyslav file differs in `why_stronger` in each of its three canonical rows (apostrophe typography). No event rows were edited during this comparison.

`origin/main` has no tracked correction paths; the canonical files are untracked local data. The Judiciary branch tracks both paths. Thus a future canonical fast-forward that introduces those tracked paths collides with the present untracked files.

## Disposable reproduction

Reproduced in `/tmp/opencode/act17-ff-collision-pj7ngf3j/repo`, a disposable shared clone. Starting from `main` at `66875d9a96957e0dacddcf8b4901c25e867d9373`, created a descendant scratch commit (`9472ac4f123c875d6491c0e18b32698c8cb4fd50`) with the exact two Judiciary branch blobs tracked; returned to the baseline and copied in the exact canonical untracked bytes (hashes above); then ran `git merge --ff-only reconcile-target`. Git exited 1 and refused:

```text
error: The following untracked working tree files would be overwritten by merge:
        records/oversight/corrections/7750b56b775ed8959a.jsonl
        records/oversight/corrections/edb67f8a646f569b5a.jsonl
Please move or remove them before you merge.
Aborting
```

HEAD remained at the baseline and the two untracked files remained in place. This isolates and confirms the collision without testing against or changing the canonical checkout. A separate direct pull attempt was inconclusive for this specific cause because the real Judiciary branch did not descend from the current `main`; it failed the fast-forward check before path-collision evaluation.

## Safe reconciliation and owner dependency

**Do not delete, overwrite, stage, or rename the canonical untracked files in place.** As tested in the dated follow-up below, simply archiving the files at a distinct path does not resolve a fast-forward collision at the original paths; even byte-identical untracked files are refused. A preservation commit must first track the exact canonical bytes at the **original correction paths** on an integration branch based on current `main`; the Auditor branch must then be merged and conflicts resolved in a review branch. Preserve exact source variants at separate archive paths in the merge result. Only after review/merge, with the target a descendant of the preservation commit, should the canonical supervisor fast-forward. The integration commit must retain both versions and their respective wording, not silently normalize either source JSONL.

**Operator dependency:** this seat has no authority to change the canonical checkout or take ownership of the Auditor's correction files. The Clerk/Executive or other authorized integrator must own the preservation commit, review/merge, and canonical fast-forward coordination; the Judiciary/Auditor should confirm its append-only source history remains unchanged. Until that handoff is completed, the collision is an unresolved integration blocker, not grounds to remove either source.

**Verification:** both source files read-only hashed and JSON-parsed; Judiciary tree/path and `origin/main` tree checked; fast-forward collision reproduced in disposable clone as above. No outcomes, canonical files, Auditor files, or external issues were modified. No policy change is proposed.

## Addendum — exact-byte and preservation-merge tests (2026-10-23)

This follow-up tests the collision in three separate disposable clones under `/tmp/opencode/act17-A-B-C-wis2luwd/`; no command ran in the canonical checkout or modified its files. Source byte hashes remained: canonical #6 `a3d1236a98eb637afcd8d6822ff8e63c16dc4b4f70a407b83ef9ff76b9b29196`; canonical Volodyslav `bf7bf5fd3e7b04c6a0f8e12f82b189e7f67b519f38a324a5309cde8c0919ce20`; Auditor #6 `80d46bc660cf3bc51cf42c7ee469d54ca542b59a5c763da861fc6a6b7b2ad242`; Auditor Volodyslav `79fa17e3351e215a4e1aa663752225c8cc1600fea09ed462f00061f3d952e28f`.

### A — untracked bytes exactly equal target blobs

Scratch base `66875d9a96957e0dacddcf8b4901c25e867d9373`; made descendant target `5dd83e754c966d8329d0e502a8fb62c03c5fb702` that tracks the exact canonical bytes at both correction paths. Checked out the base, restored the exact canonical files as untracked, confirmed `git status --short` showed `?? records/oversight/`, then ran:

```sh
git merge --ff-only target
```

**Result:** exit 1. Git said both untracked correction paths “would be overwritten by merge” and aborted. HEAD remained at the base, files remained untracked. The target and working copies were byte-identical (the two canonical SHA-256 values above). Therefore exact-byte equality does **not** make case A safe or permitted; the previous distinct-path archive suggestion alone is insufficient.

### B — target bytes differ

Separate scratch base `66875d9a96957e0dacddcf8b4901c25e867d9373`; target `0e19c804607fe5c98be199a683d3e18dc07fd9d5` tracked the two Auditor streams (hashes above), while the worktree had the different canonical untracked bytes. Ran the same `git merge --ff-only target` command. **Result:** exit 1 with the same untracked-file overwrite refusal; HEAD stayed at base and untracked data remained. As expected, different content also refuses.

### C — preserve at original paths, merge on review branch, then fast-forward

In a third disposable clone, used baseline `66875d9a96957e0dacddcf8b4901c25e867d9373` and these Git operations (scratch commits are not Viche commits):

```sh
git checkout -b preservation
# Copy exact canonical byte streams into records/oversight/corrections/ (Python harness).
git add records/oversight/corrections
git commit -m 'preserve canonical correction files at original paths'
```

Preservation commit: `388a071191011ae75e3ce4c43067bcf3850a3fb0`. From the baseline, made `auditor` commit `13b7022dbfd2f2442b3318fdc67cec480f692802` with the exact two four-row Auditor JSONLs. On `preservation`, ran:

```sh
git checkout -b review preservation
git merge --no-ff --no-commit auditor
```

The merge returned 1 with `CONFLICT (add/add)` for both correction paths. Resolved on `review` by (i) retaining the exact original canonical streams under `records/oversight/reconciliation/canonical-source/`, (ii) retaining exact Auditor streams under `.../auditor-source/`, (iii) setting active correction paths to the unmodified four-row Auditor streams, and (iv) adding a README documenting resolution. Then:

```sh
git add records/oversight
git commit -m 'resolve correction anchor merge preserving both sources'
```

Review merge commit: `bf5db8491f091837f39865520dfe2d499aacc853`; it is a descendant of preservation commit `388a071…` and has the Auditor branch as a merged parent. Exact SHA-256 verification in the review tree: active files and Auditor archive match Auditor hashes `80d46bc6…` / `79fa17e3…`; canonical archive files match canonical hashes `a3d1236a…` / `bf7bf5fd…`. No variant was discarded; the active path retains the full four-row Auditor sequence, with the canonical three-row byte streams preserved verbatim.

Finally, cloned the scratch repository into `C-downstream-verified`, detached at preservation commit `388a071…`, and ran:

```sh
git merge --ff-only bf5db8491f091837f39865520dfe2d499aacc853
```

**Result:** exit 0, fast-forwarded to `bf5db849…`; status clean. The downstream hashes again verified both archives and active files. Thus C demonstrates a viable sequence once the preservation commit tracks the canonical files at the original paths and a reviewed merge commit descends from it.

### Conclusion, safe sequence, and limits

The earlier plan to archive the canonical bytes only under a distinct path before fast-forward is **not workable**: A proves exact identity does not avoid Git's untracked-path protection. Do not work around that by deleting, moving, or overwriting the canonical files; this review does not authorize such action and the files must be preserved under Act 12's safety invariants.

Verified safe sequence: (1) an authorized operator uses a separate integration clone/worktree based on current `main` to commit exact canonical files at their original paths, with hash verification; (2) create a review branch and merge the Auditor branch, expecting add/add conflicts; (3) resolve by keeping the Auditor four-row stream active, archiving both original byte streams verbatim at distinct paths, and documenting hashes/row differences; (4) review and merge that result to `main`; (5) only then allow the canonical checkout to fast-forward and verify the active and archived hashes. Step 1 is necessary; a different-path archive alone is not enough. **Operator dependency:** an authorized Clerk/Executive integrator must make and review the preservation/integration commits and coordinate the eventual canonical fast-forward. This seat did not do so.

Reproduction limitations: scratch target commits were synthetic descendants based on `main` `66875d9…`, used solely to isolate path behavior; they are not proposed for publication. C used exact source JSONL blobs but a synthetic merge parent/commit graph, so it verifies Git conflict and fast-forward mechanics, not repository authorization, CI, governance approval, or whether a specific real PR merge strategy will produce those exact SHAs. No Auditor branch, outcome state, or canonical data was changed.
