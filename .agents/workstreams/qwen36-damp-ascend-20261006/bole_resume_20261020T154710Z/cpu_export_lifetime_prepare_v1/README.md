# Real Torch CPU export-lifetime control — prepared, not executed

Only this script and README are new. No Torch, Docker, NPU, HTTP, authority or controller was executed/created during preparation. Default is OFF; --check is standard-library source/AST/budget checking only. MAIN supplies any future approved same-image process and host proof.

## Exact source reuse

The script pins complete diagnostic_export.py, sourceio.py, original qualification sink/observer, native source inputs, TAP and the reviewed codec renderer/helper. It renders the actual released sink with that renderer. It extracts the actual logical_bytes and actual export → exclusive save/flush/fsync/close → Ref verification → independent weights_only CPU t.load prefix, not a lookalike serializer. Original and released variants differ only by the actual codec's del raw at this prefix. Observational AST hooks record stage metadata, weakrefs and a returned saved value; original save/loader/budget predicates remain.

Real Torch is imported only after --execute. The original exporter accepts CPU tensors: its source detaches, calls cpu() and contiguous(), without requiring NPU. Therefore this is a CPU ABI/storage control, not fake NPU input. CPU export can share storage with its still-owned CPU input, unlike genuine NPU D2H. Storage statistics and this limitation are explicit; no model NPU capture is reported released or zero. Model-owned NPU capture remains unmeasured, unchanged and required in later joint accounting.

## Two separate modes, fresh processes

small: 2 MiB opaque byte tensors, including a true shared-storage tensor/view pair.

conditional-first2k: 236219712 bytes =225.27667236328125 MiB, a conditional shape-object subset only. It starts from253046592B worst encoded subset, keeps24 native pages/conv11, changes private25→17 K/V, bool mask and int32 table for16FA. Unlike the earlier rounded225.324MiB estimate, this also subtracts mask/table differences. It is NOT an observed model first frame and omits other real frame/workspace objects. It uses synthetic opaque real Torch CPU byte tensors, not fabricated model state receipts.

A small result cannot establish the full mode; a full CPU result cannot qualify model/NPU fit, algorithm correctness, short8/160/1024 coverage or performance. Each variant/mode needs its own fresh process and unique absolute output leaf; this script does not spawn or schedule processes.

Future MAIN invocation examples inside its reviewed same image (not run here):

python3 -I -B /absolute/path/cpu_export_lifetime.py --execute --mode small --variant original --output /approved/fresh-original-small

python3 -I -B /absolute/path/cpu_export_lifetime.py --execute --mode small --variant released --output /approved/fresh-released-small

Repeat separately with --mode conditional-first2k only after reviewing small output and actual process/disk budget. Do not reuse output leaves. Full mode remains untested.

## What it measures and what remains pending

At baseline/input/export/save-close/release/before-reopen/after-reopen/full-bitwise stages it records Linux PSS, RSS, HWM and complete real tensor dtype/shape/stride/offset/storage pointer/size. Actual storage/view dedup is counted separately from logical tensor bytes. Weakrefs prove whether exported real Tensor Python wrappers remain at reopen. Original expects live exported wrappers; released expects none. This does not prove Torch allocator release, NPU D2H sharing, aggregate model/worker memory or an exact continuous PSS peak. Kernel RSS HWM and sampled PSS are reported, not relabeled as a model fit proof.

The complete reopened values are checked bitwise, including tensor ABI and all primitives. The actual file is independently reopened through original sourceio.checked. Every created raw file is retained; no deletion/release/ACK occurs.

The original384MiB logical and at-most1GiB caps remain. Pre-allocation retains TWO logical copies +128MiB checkpoint +64MiB metadata reserve, adds actual process baseline for CPU admission, and checks free disk. It does not lower reserves because CPU storage happens to alias. Stage PSS/RSS-HWM exceeding the bounded process cap fails. These conservative CPU controls are not the complete model joint-budget consumer.

For a future rejection control, use a lower explicit --joint-cap-bytes; no payload allocation should occur. --inject-failure-before-reopen deliberately fails only after durable save and retains raw with FAILURE.json. Exceptions retain first error and available raw; no successful result substitutes for failure. Actual Torch serialization, lifetime, bitwise and failure-retention outcomes are all pending. No generated code or model algorithm is evaluated.
