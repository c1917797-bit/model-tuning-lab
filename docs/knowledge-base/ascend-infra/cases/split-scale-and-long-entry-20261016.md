# Split-scale compilation and long-model entry failure: 2026-10-16

This checkpoint is not a new accepted technology. Historical HYPIC is excluded.

## Actual evidence

- DeltaLog051 production and debug libraries compiled in the pinned660 image with Devices=[]; operation094b exited0 in306.451s. The actual host result is `/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-split-scale051-build-new48h-MAIN-20261015-001/RESULT.json` (2806B, SHA a85dcb9f905601ed232ebc8bd56f3650ac759074113001de2f2bc5cd2ec34c66). This proves compilation only, not compiled Meta, NPU numerics or performance.
- The actual dual-build result is8847B SHA3010d9b0a73d2f7b62b6294c8c01fa68176f1e911bee4b43ca7b1ac72bf00a68 at its `cpu-preflight/producer/build/RESULT.json`. Production library SHA6490d16d57d4e43c4d7b75e23d6ac872172461e8868b6843c781da99b0f32041; debug SHA3e2713c5fbee5d3cec1c3dc589d431396c8abf76acb5fd070ae6b9c6a4ad2009. Both remain external, not in Git.
- MXR050 actual predecessor bind094f and source audit0951 passed. Model operation0956 failed before any Docker/NPU/model arithmetic: the explicit RAW parent `/opt/host/vnf/austinov/qwen36-paper-results-new48h` did not exist. MAIN's earlier check covered absent result leaves but omitted the required existing parent. Its empty control output and original failure terminal are preserved. This is an execution-preparation defect, not evidence against MXR.
- MAIN verified every ancestor and created only that precise parent. A new050-repair1 preflight checks parent existence, ancestry, same filesystem and the unchanged227.5GiB combined reservation BEFORE inherited output mkdir;22 local tests passed. It has no actual long-model pass. Its attempted deployment returned unknown timeout; actual read095c found all65 target files absent. No unchanged NPU retry followed.
- 052 numerical and053 model adapters are prepared, not qualified. They require actual new-library Meta and16/160-step gates before model admission; source and software tests do not satisfy those edges.

## Reusable decisions

Validate the entire cold entry before scarce-resource admission, including existing output parents, not only new leaf names. Put a read-only refusal before creating a result root. After a partial entry failure, retain the old root and use a new source/run identity rather than deleting or reusing it.

Compare saved terminal records to their actual executable/argv/source/output and transport representation. An old absolute `/usr/bin/env` invocation with cwd=null is not a different host merely because a newer controller uses a canonical cwd. Qualify that exact observed predecessor, not arbitrary null-cwd commands.

For a bounded phase, inspect every transitive time gate. 052's local CPU lease was720s but its shared source admission still required2880s remaining, so it was not executable in the last29min of the old window. Do not change the old gate to manufacture a late PASS. A new user-authorized window needs distinct current source/authority; completed historical compilation/ABI evidence retains its original source/window identity.

## Acceptance and continuation

No new same-configuration fixed1024 dense/candidate E2E result, three performance pairs, or GSM8K/HumanEval/MMLU result is established by this checkpoint. Old48h acceptance is unmet; implementation failures do not reject either paper. Whole-window utilization is unmeasured; the06:49UTC snapshot had no compute PID on4-7 and no running owned job.

The user explicitly granted another24h. Current authority is `NEW24H_AUTHORITY_20261016.json`:2026-10-16T07:02:13Z through2026-10-17T07:02:13Z. It does not rewrite the old deadline. Next actual edges are new-window DeltaLog compiled Meta→16→160→model→paired performance→task accuracy, and MXR genuine-long-model→typed production qualification→paired performance→tasks. Final gates, device boundaries and default-OFF delivery are unchanged.

Source snapshots under `projects/qwen36-paper-portfolio/tools/new48h_split_scale_and_long_entry_20261016/` are experimental absolute-path snapshots, not a relocatable accepted release. Pending archival completeness is checked separately; missing files must not be called a complete takeover package.

## New-window actual parser refusal

MXR057 deployed51 runtime files and passed source audit0984 (822 read references,32 registered inverse deltas). Operation0986 exited1 after80.239s: same-image Devices=[] software passed12 controls, but native-parser rejected `native[-2:] == ['--worker-cls', expected]`. The actual registered cap48 argv adapter appends lazy-loading flags after the worker flag. This is a positional-validation adaptation defect, not MXR arithmetic failure. The original RESULT and stderr remain under `/opt/host/vnf/austinov/run-mxr-block-long-model057-main-NEW24H_MXR057_001`; the sole CPU container was release-verified. New062 repair must prove the complete generated argv and unique correct worker argument, retain negative controls, and use new result/source identities. No actual NPU/model/performance pass is granted.

The user separately authorized only `/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061`, at most80GiB total and at least100GiB free, with no deletion or service changes. Fresh read-only checks found kubelet not-found/inactive/MainPID0 and only lost+found on that filesystem. This is scoped storage authority, not permission to alter kubelet or the old evidence. DeltaLog16 and160 each need a fresh33GiB phase check; use one retained-data/reservation ledger instead of double-counting the same free space.
