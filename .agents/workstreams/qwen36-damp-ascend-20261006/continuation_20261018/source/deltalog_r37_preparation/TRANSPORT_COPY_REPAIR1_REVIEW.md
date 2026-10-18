# R37 preparation repair1 and exact byte-copy transport

This package only prepares new R37 source trees. It does not create a bound model source, run model code, read closed raw, allocate a payload lease, modify a ledger or extend the authority window. The frozen v1 preparer, its emitted receipt and all R36 source/evidence remain intact.

## Proven active-fixture defect in v1

`test_early_scan.py::Tests.test_stable_equal_and_exact_frozen_owner_source` checks two explicit equations:

1. SHA256 of `software_dependencies/early_scan_template.json` equals the model template's `early_software_policy.prepared_owner_source.sha256`.
2. SHA256 of `software_dependencies/early_scan_owner.py` equals that early template's `files.owner.py.sha256`.

The v1 preparer updated the active owner mirror and model early policy but retained the old mirrored template. Both equations require the active mirrored template to be updated. Repair1 first verifies that the original mirror bytes exactly match the original frozen early template and owner, then assigns the newly generated exact early template and owner bytes. `software_dependencies/early_scan_owner_R31.py.txt` is retained unchanged as the historical negative control.

`test_firstdecode_owner.py` has two old payload path literals used together as a metadata-only mount-policy fixture. `firstdecode_output_policy.install` receives this path as an argument and does not look up the active `model_snapshot_budget.LEAF`, so the old pair was internally compatible. Repair1 replaces exactly those two literals with the new R37 leaf to keep the fixture current. The complete reverse byte transformation is asserted; the AST differs only in those two string constants. No assertion, condition, threshold, test method or test count changes.

## Frozen files

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `prepare_r37_repair1.py` | 16231 | `e8b9d86268e4f59bd5818dcfa6603461f6e486e960551db67b3b01a4d8708837` |
| `transport_emit_repair1.py` | 9812 | `e568fb78bbb81ae73a7a081ef1a17a623f34bda76112967e5e42877331a9e524` |
| `bulk_copy_unchanged.py` | 13684 | `2a8be7b726f3d5d25f144708b9682e643bc13f1dfa97b4e4a6cebd3a23bdbd30` |
| `test_transport_copy_repair1.py` | 10315 | `66c7a84037ca5149ae51437440936ae9b95d2a695e152d64f33fa0afe22cce2f` |

The remote source Ref paths must be measured after deployment. The new transport is pinned to the new preparer bytes and SHA256. The copier is pinned to the new transport bytes and SHA256. The complete package ID includes the actual generator Ref, actual patch-manifest Ref and all destination file Refs. The v1 package ID cannot identify repair1.

## Deployment order

1. Deploy the three frozen program files using the structured patch writer, then verify their exact bytes and SHA256.
2. Obtain a fresh repair1 `--receipt` using `transport_emit_repair1.py` with the actual generator Ref and existing exact patch-manifest Ref.
3. Pass the returned complete package ID to all subsequent transport calls and the copier. The copier supports `--plan` and `--copy`; no mode is default OFF.
4. For the copier, supply `--transport-ref`, `--generator-ref`, `--patch-manifest-ref` and `--expected-package-id`. Both exact destination roots must be wholly absent.
5. After successful byte copying, apply every file in `pending_structured_patch_files` using the structured patch writer. Use bounded `--files` calls for small text or `--fragment` for larger text; reconstruct and verify each complete Ref before the single final patch.
6. Audit the resulting full source closure and template/ticket equations before the actual cheap-prebind, new early bind and same-image early suite, full binder, bound-source audit and owner admission.

## Copy guarantees and limits

The copier derives its plan from the authenticated frozen algorithm's complete in-memory two-tree inventory. It selects only entries with an exact `unchanged_original_ref` whose size and hash equal the target entry. It excludes all leaves named `SOURCE_TEMPLATE.json`, `SOURCE_MANIFEST.json`, `SOURCE_BOUND.json`, and all command-packet leaves beginning `COMMANDS`, even if their original bytes happen to be unchanged. Their contents remain structured-patch inputs.

Before creating any destination, it authenticates every selected original file and checks that both destination roots are absent. It opens every directory component without following symlinks, atomically creates the two new roots, and opens target files with `O_EXCL`. `shutil.copyfileobj` copies raw bytes; no text codec or newline transformation is applied. Original files are fully hashed before and after copying, each destination is hashed immediately, and the final complete copied inventory and all destination Refs are checked again. Existing destination leaves are never opened for truncation.

Any failed copy leaves the partial roots as evidence and refuses an in-place retry because the roots now exist. The program does not delete, replace, resume, allocate a successor root or write an operational receipt to disk. Its bounded stdout receipt contains the exact plan digest, counts, byte totals and pending patch filenames. Final copied-source closure verification remains necessary after the structured patch step.

## Local controls

`python -I -B test_transport_copy_repair1.py` completed 12 tests in 0.127 seconds with no failures or skips. Controls cover exact non-UTF8 byte copying; an existing target root or target file; tampered and symlinked sources; excluded template, bound and command leaves; incorrect source paths, duplicate names and mismatched digests; unexpected final files; default OFF and frozen transport pinning; and the precise active-fixture repair and its reverse AST identity.

These are transport and preparation controls. They do not qualify R37 software, storage, numerical correctness, all-four-rank capture or performance. The actual model software count remains 255, the actual prepared early suite remains 253 plus the unchanged 26 payload controls, and the two original deferred bound-only tests remain required. The original cutoff and full 3600-second owner admission remain unchanged.
