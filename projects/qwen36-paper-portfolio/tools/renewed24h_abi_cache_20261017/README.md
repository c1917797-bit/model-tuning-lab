# Renewed-window ABI and cache-budget repair checkpoint

This is a reproducibility checkpoint, not an accepted performance candidate.

## Observed outcome
- BOLE R15: exact Ref3 is reopened into the real FIA ABI object at the native adapter boundary; local and same-image 94 software cases passed. The four real model workers each produced a complete 775,440,281-byte three-node capture with primary=null.
- The original owner still failed: physical HBM reserve3GiB was violated during the diagnostic. All original failure evidence remains. No independent whole-model consumer, performance or task qualification was granted.
- Actual utilization0.9 allocated about11.2GiB KV. Last physical4–7 HBM use was29762/29774/29813/29823MiB of32768. Free2945–3006MiB is below the unchanged3072MiB reserve.
- BOLE R16 changes only the common cache utilization to0.8, preserves the mathematical/reference gates, and excludes cache-bytes/block-count overrides. Local98 software cases and source review passed; actual device fit and numerical checks remain pending.
- DeltaLog R19 retains explicit6GiB KV, so BOLE's utilization repair must not be blindly copied: actual Ascend worker bypasses utilization-based cache sizing in the explicit-byte branch.
- R19 complete historical closed15 read-only binding and actual-source audit passed. The new owned first-real-decode lifecycle is operation exec-000000000000125d; its result was pending at this checkpoint. Neither a successful bind nor software checks are NPU qualification.

## Repair and test lessons
Use an exact source-bound reference for identity, but pass its independently reopened typed value where the real operator adapter expects a value. Test the actual enabled caller-to-adapter path, not only detached helpers.
A source/argv/receipt join must run the true entry function to its framework boundary: evaluating an isolated expression with invented local variables can hide a missing variable in the real main.
For memory failures, retain the original margin, record actual allocations, and change a common declared allocation policy in a new experiment. Automatic utilization and explicit cache-byte paths are different controls.
A complete worker capture is not an independently validated numerical PASS. Resource failure is not evidence that the paper is invalid.

STAGE.json pins every archived source byte to its original remote source. Archive source paths are not runnable substitutions: original Linux roots, actual source references, resource ownership and fixed active authority remain required. No raw multi-GiB tensor payload was duplicated into Git. HYPIC is not a new result.
