# BOLE native-prefill repeatability boundary probe — source draft

## Scope and current conclusion

This child-source proposal observes **only the ON short arm, two identical requests in one actual TP4 process**. It is a diagnostic for the repeatability failure already demonstrated in retained evidence. It is not a change to the numerical algorithm and cannot qualify the candidate, the low-observation performance path, throughput, TTFT, TPOT, or task accuracy.

The independently retained within-arm projection reports that both original ON and OFF processes have identical request payloads and explicit seed 0 across their two requests, but each process already has 47/48 different incoming GDN state and leading-convolution digests at its first TREE observation; layer 0 alone agrees. Consequently the old ON/OFF toggle is not established as a cause. The old pair remains failed; an observation that finds a narrower boundary will not repair that result.

This preparation is local and source-only. No remote command, NPU launch, original result edit, old source overwrite, or runtime authorization is performed by these files. A new frozen child, unique output, actual device/process/container/resource checks, original owner admission, and the fixed **2026-10-22 12:38:41 UTC** deadline remain MAIN responsibilities. The original whole phase and cleanup limits remain 3600 and 180 seconds.

## Frozen candidate files

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `boundary_probe_v1.py` | 30245 | `24f12bae4c583d076d264e435578138de37ffddbf98e8175314b684ae420657b` |
| `boundary_delta.py` | 9525 | `17b95c2ed565f3aead8a4a6ac783f5ce9a6c66c99e168449c0d1e293fe9abf3c` |
| `test_boundary_probe_v1.py` | 8959 | `4f345ee0968f845875726d847fc6d94cd95c88525493fad6db85c8780e470e7c` |

These are review candidates, not installed files. Any later supported correction needs a new hash/freeze before deployment. Local `rendered_v1` and `rendered_v2` are superseded source previews; `rendered_v3` reflects the seven-file observer delta including terminal budget accounting. None is an NPU result.

## Exact insertion boundaries

Line numbers below identify the parent source copies, not a new mathematical implementation.

| Parent source boundary | Added observation | What the name does and does not imply |
| --- | --- | --- |
| `service_runner.py:303`, immediately before the first `T.install_capture` | Create the double-opt-in observer, assign `calibration.boundary_probe`, and register its own restorer | All preceding original native method, vocabulary, source, and configuration checks remain before new module-hook installation. The original calibration constructor signature, call, and order are preserved. |
| `prefill_tail.py:54`, before the original `_old(...)` call | For layer 0, hash all actual 131 rows of `mixed_qkv`, `b`, and `a`; for layer 1, retain the bounded projection witnesses | These are real projected operands passed to the unchanged native core, not a reconstructed input or a shape-based substitute. Layer-0 final state equality alone does not establish equality of Q. |
| `prefill_tail.py:59–63`, after the original return and the existing leading3/extra-byte checks | Each of 48 actual GDN layers records full selected state, full selected convolution slot, and separate leading3 digest | This is a source-level **native core-return witness before registration**. Existing tail checks execute before the new witness. Blocking copies create observation synchronization; this is not an instantaneous device timestamp. |
| `service_runner.py:332–334`, after the original `R.register` | Join all earlier native witnesses to real registered bindings, then capture `post_native_prefill_registered` | Earlier `cache_observation.capture`, FA observation, and `restore_tail()` have already occurred. The label deliberately does not claim “immediately on native model return.” |
| `model_process_calibration.py:59–60` | `calibration_before` | Original source, callable, ABI, and registration identity checks have already run. This is immediately before the create/reuse branch, not before all of `ProcessCalibration.acquire`. |
| `model_process_calibration.py:97–98` | `calibration_after` | All original calibration/receipt/library validation and original proof construction have completed. Original twelve-case numerical logic is unchanged. |
| `service_runner.py:549`, immediately around `old_mtp` for the first draft of each request only | `initial_mtp_before` and `initial_mtp_after` | The original one-first-pass MTP call, result, original validation, and `finally` restoration to eight drafts are preserved. No later MTP call is substituted or suppressed. |
| Original `emit_retirement` inside `retire_performance_request` | Record after the existing digest retirement and metadata retirement; remove new hooks on the second generation | `LiveOwner.retire` remains the native retirement authority. Its original request/batch removal and output-budget checks happen first. The observer does not manufacture a release or a scheduler ACK. |
| `performance_host.py:117–118`, after actual final worker snapshots and before original consumer | `BP.terminal_accounting(C,m)` into `summary['boundary_terminal_budget']` | Read-only host accounting includes final snapshots and PERF-COMPLETE that arrive after the last observer file. The original streaming consumer and controller cleanup still execute. |

The exact single-occurrence replacement function refuses missing or repeated parent fragments. `runtime(old, short_out)` returns complete source text for the expanded runtime set, allowing the independent child validator to compare entire files, not merely approve a list of filenames.

## Numerical and lifecycle observations

Each generation has 48 native-return records and five whole-target GDN captures. Each whole-target capture reads all 48 selected recurrent states and all 48 full convolution slots. Every full convolution digest is accompanied by a separate digest of the first three logical convolution positions.

The recurrent state and leading3 convolution region must be finite. Extra convolution storage is hashed as storage/lifecycle evidence; it is not required to be numerically finite or equal between requests. Unused or speculative entries are never mixed into a claimed numerical pass.

Registration must join the actual layer object, metadata object, request object, registered `conv_arena`, recurrent state object, and physical slot to the earlier native invocation. Per capture, the arena object, backing storage pointer and size, data pointer, offset, shape, stride, dtype, and device must still match the native witness. Existing `cache_registry.py:34–35` already requires real ordered `layer.layer_idx`; this is not a newly guessed property.

The observer retains strong worker, runner, model, and bounded request references. It accepts two distinct genuine native request objects in monotonic generations, requires complete native layer order, and rejects a repeated stage, unexpected phase, missing registration join, or unsupported geometry. Such a refusal invalidates this diagnostic scope; it does not redefine the original mathematical gate.

### Raw numerical range

The following full logical outputs are hashed, but only **actual token positions 123 through 130** are saved as raw BF16 values. There is no unused token padding in either the logical hashes or the slices.

| Stage | Full logical shape per rank | Raw bytes per generation |
| --- | --- | ---: |
| Layer 0 native core output | 131 × 12 × 128 | 24576 |
| Layer 0 gated norm output | 1572 × 128; 12 rows per token | 24576 |
| Layer 0 out projection | 131 × 5120 | 81920 |
| Layer 0 post-attention norm hidden | 131 × 5120 | 81920 |
| Layer 0 post-attention norm residual | 131 × 5120 | 81920 |
| Layer 0 MLP output | 131 × 5120 | 81920 |
| Layer 1 mixed QKV projection | 131 × 2560 | 40960 |
| Layer 1 b | 131 × 12 | 192 |
| Layer 1 a | 131 × 12 | 192 |
| **Total** | **Nine slices** | **418176** |

Layer 0 mixed QKV, b, and a also receive full logical hash-only witnesses before the native core; their raw values are not saved.

The full 131-token hashes are producer witnesses. A reader can independently reopen every retained byte and compute numerical errors on the last-eight-token slices, but it cannot recompute a full 131-token hash from those slices. Slice equality or low slice error is not a full-tensor numerical acceptance result.

All four module hooks return `None`. They read the actual returned objects and check object/storage/shape signatures before and after capture. Hooks are attached to layer-0 norm, out projection, post-attention layer norm, and MLP submodules; decoder `forward` is not replaced. They remain inert outside the actual native-prefill scope and are removed by their exact handles. A foreign replacement fails ownership checking and is not silently deleted. Constructor failure and the existing guarded runtime failure path remove this observer's installed hooks while preserving the original primary exception.

### MTP storage limitation

The MTP records identify the actual runner-owned drafter and draft model, inspect the actual cache-bearing modules, and preserve real tensor backing/offset/stride/shape descriptions. They explicitly report:

- `draft_actual_write_footprint_known = false`;
- `alias_exclusion_proven = false`;
- sharing a backing allocation alone is not evidence of overlapping active writes.

The current draft does not reconstruct the native draft attention slot mapping or its actual write extents. It cannot prove draft/target disjointness. The original native cache-management contract is not extended with a new disjointness assumption. This limitation can block numerical qualification while still permitting a useful bounded diagnostic observation.

## Resource bounds and original budget accounting

The first broad raw-capture proposal was rejected during source preparation because it would have added evidence outside the original allocation. The implemented profile uses the original `OTHER = 3 MiB/rank` category for **all new raw and JSON files**. Original metadata and total caps remain 64 MiB and 1 GiB per rank. New binaries are conservatively charged within that existing metadata allocation; they do not receive a new raw budget.

| Bound | Value per rank | Enforcement/evidence |
| --- | ---: | --- |
| Exact raw bytes for two requests | 836352 | Nine fixed eight-token BF16 slices per generation; completion requires exact total |
| Metadata hard cap | 524288 | Writer checks before every file |
| Conservative metadata encoding bound | 501961 | `metadata_envelope.py` with 64-bit addresses/IDs, maximum admitted encoded paths/names, conv width 16, and eight draft cache tensors |
| Largest metadata record bound | 51151 | Complete reference index; per-file cap remains 131072 |
| Additional readback hard cap | 536870912 | Counter charged before every complete logical D2H read |
| Maximum admitted readback arithmetic | 515220032 | Two × six × 48 full state/conv captures, all nine full logical stage reads, and both generations' layer-0 input witnesses |
| Required additional `OTHER` headroom while writing | 65536 | Checked against actual current original accounting |
| Original `OTHER` cap | 3145728 | Unchanged; both per-write and host-terminal checks |

At the old observed maximum `OTHER` value 1668008, the conservative new bytes plus the reserved headroom total 3071857 bytes, leaving 73871 bytes below 3 MiB. This arithmetic is a source-preparation check, not a promise about a new run's future files. Every new write calls real `g3_budget.actual` before and after writing; the host repeats accounting after final worker snapshots.

The amended original accounting explicitly discovers every file in `BOUNDARY-R{rank}`, including a partially written file. It also includes retained original `STATE-…-R{rank}.json` and `.STATE-…-R{rank}.json.pending-*` files in total metadata accounting, and MTP-load stages/snapshot pending files in their original observer allocation. It does not treat files omitted by historical globs as free storage.

New observer files use a single `O_EXCL` ordinary file and fsync. There is no retained second staging copy. An interrupted file is retained and incomplete; it cannot be retried under the same name or treated as successful. The reader requires the complete final index and the exact directory closure. Original publishers and their stage accounting are unchanged.

The observer adds blocking D2H copies and CPU hash/finite work, so it changes execution scheduling. Native tensor arithmetic, native stream/event APIs, and persistent target cache writes are not replaced. Existing owner wall-clock, container memory, disk, and cleanup admission remain authoritative; a CPU payload-size calculation is not a new RSS entitlement or a latency guarantee.

## Exact evidence closure

Each rank expects 148 files: 130 JSON records and 18 binary slices. The G2 complete index lists exactly the preceding 147 files and does not contain itself. It is not sufficient to find some successful records in a directory.

The expected set is one G0 INSTALL record; for each of G1/G2, one layer-0 input record, 48 native records, nine raw metadata records plus nine raw binaries, five boundary records, and one retirement record; finally one G2 COMPLETE record. Records carry the same source SHA and PID, actual rank, generation, and event identity. Full source Refs are retained in INSTALL and COMPLETE.

The independent reader must reopen strict path/bytes/SHA Refs, reject symlinks/partial or extra files, require exact event sets/order and source/owner joins, and preserve the before/after input readset. It compares the three hash classes separately and computes slice errors only on saved raw values. It must also consume the original HTTP, native identity, retirement, and controller cleanup evidence; observer completeness alone is not complete run acceptance.

## Source lineage and preserved gates

The intended child lineage is the exact retained `bound-short-ON-v2/SOURCE_BOUND.json`, while retaining the historical short-profile transformation proof. The existing validator's `D.runtime` whole-file recomputation must remain active. A separately reviewed child validator reconstructs the amended short delta and validator from pinned parent bytes and fixes the helper/delta hashes; it cannot merely trust a new function named `runtime` or skip the old comparison.

Runtime edits are confined to seven complete files: service runner, host service, command contract, performance host, prefill tail, process calibration wrapper, and G3 accounting. The extra runtime keys are exactly `prefill_tail.py`, `model_process_calibration.py`, and `g3_budget.py`; the other four already belong to the old runtime transform.

The following mechanisms remain original bytes: model-entry numerical routines, native GDN and attention code, core112, paged/FIA math, service bridge, transaction/eligibility, selected-path commit, native `LiveOwner`, retirement helper, and old state-digest producer. Existing runtime/installed-source refs, component receipts, numerical thresholds, cleanup predicates, clock authority, dependency closure, client closure, and all original twenty controls are retained. The eleven new CPU controls are an additional diagnostic-source scope; they are not relabeled old controls or NPU results.

The new flag is `BOLE_NATIVE_BOUNDARY_PROBE_ENABLE=1`, and the manifest key is `boundary_probe_profile`. Host command closure and the actual performance-spawn environment both carry the flag. The declaration must equal the helper's exact typed constant. Without both declaration and flag, an enabled run is refused. With neither, the factory returns `None` before reading runtime owners, installing hooks, or writing files.

## Negative outcomes and interpretation

Source/closure mismatch, incomplete events, budget failure, unknown runtime geometry, identity drift, nonfinite logical state, or incomplete native retirement produce an invalid diagnostic. No gate is relaxed in response. A phase-to-phase digest difference is recorded rather than silently normalized or erased.

If layer-0 QKV/b/a inputs agree but the core output differs, the observation narrows the first changed region to the original core execution and its native context. If the core output agrees and a later stage first differs, it narrows the propagation interval. Side inputs not recorded by this observer, including gated norm z, still limit attribution. A first differing boundary does not by itself prove one kernel, allocation, or stream operation is the root cause.

If adding the observer makes the two requests agree, that does not establish that the old failure was fixed: blocking copies can change timing. If the difference is reproducible, the raw slices quantify it only over their saved logical range. Any repair still needs evidence for its cause, a new version/output identity, and the original real-NPU numerical, multistep, lifecycle, full-model performance, and final task-accuracy gates.

