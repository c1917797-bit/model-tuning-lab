# FlashInfer actual no-device ABI prerequisite — 2026-10-07

## Scoped result

MAIN fully reviewed and integrated default-OFF FlashInfer native-state gate v3.
Actual source/CLI software checks MA0e00 passed47 tests and all12 source bindings;
they did not run Torch, Docker, NPU, models or benchmarks.

Before spending a device matrix, MAIN created one bounded no-device prerequisite.
Original MA0e01 ended exit1/35.177s; independent raw consumer MA0e03 ended exit0.
The failure is a prepared interface mismatch, NOT an Ascend numerical failure,
paper-wide no-go, memory/OOM failure, external NPU occupation or speed result.

Actual installed versions: torch2.10.0+cpu, torch_npu2.10.0.post4,
vllm-ascend0.23.0, CANN9.1.0 from real install metadata.
All four requested dispatcher exports exist. The actual old-FIA out overload ends
`Tensor? workspace=None, Tensor[] out) -> (Tensor, Tensor)`.
It has no `attention_out` or `softmax_lse` named arguments.
Frozen v3's validator and callsite require those nonexistent names, so v3 is
NOT admissible for the20480-step NPU matrix in this stack. Preserve v3 unchanged;
a separate successor must use the real output-list ABI and consume actual
no-device schema evidence before set_device. Actual workspace/LSE shape,
native arithmetic, empty domains, NPUGraph and complete matrix remain pending.

This packet only adapts exact normalized partial attention-state composition.
Current Ascend already has native merge; source/schema correctness alone cannot
establish new load-balancing/tiling or serving benefit. Real algorithm-specific
model integration, same-dense paired1024 and final2048 task tests remain mandatory.

## Exact evidence and ownership

New raw root:
`/cache/cch/flashinfer-native-abi-v1-20261007-1716-001`.
The1716 label is only a unique leaf label; actual execution was around17:05Z.

- report.json SHA1d691e38880779c30804848be1416ec74dfe222384b859a1b2fef5c174250cd7
- RESULT.json SHAc77364426aee22007a330ab2017b79f935e669483dadaf9cfb7998611a724cb7
- OWNED.json SHA264ca9b2d3c6173b264e032c89feac03dfc8665264c44819283fa4d3bbf00d2b
- stopped inspect SHA45698d590d5449696e21ae3b07cf6b6745d0060affbb0c150272166e91cddc72
- source manifest SHAcac64aad92d738c6319c3c0d8eaea6af1926d925fbf4ec3f7a427936d1803caa
- producer SHA9c3e0650f68f14d48e080b65f9b06cacbba4c1bf62a6e3ffc9a0ca3ce665a424
- host SHA6c68847f8ef819315fa3369aa78a41ab6c506b65a6a32a4fd59b7b5cf9356c36

Actual direct target chicaihong01/ma,a6109,peer_direct. Original terminal is
preserved in FLASHINFER_ABI_AWMCP_RECEIPT_20261007.json, not invented from child
output or a later consumer.

Owned CIDbe9891a5b182d312051cf0dae289e78a9764b86d90010e66f80f3300db38741e
was stopped and retained: Pid0, noExec, noOOM, Devices[]; no rm, model mount,
privilege, host network or external service change. Guest8GiB/1CPU;
host256MiB/1CPU plus unchanged8GiB/2CPU reserve. Actual ancestor quota/cpuset,
CPU allocation and live guest cgroup were checked. Original producer peak RSS
881212KiB. The imported package attempted an internal npu-smi query in its
no-device namespace; it failed there and is retained in stderr. No NPU/control
device was exposed and explicit npu.is_initialized() was false before schemas.
The prepared-call mismatch remains the actual primary failure.

Ordinary MemAvailable in MA0df8 was117182296KiB (~111.75GiB), physical0–7 had
no compute processes. Outside original0–3 workers exited independently; no
action stopped them. Current clocks unchanged: KVBuffer Oct8 08:29:54Z,
portfolio Oct9 11:17:31Z. NPU lane is idle due to MAIN/source readiness, not
claimed external occupancy. Completed32GiB hugepage authority remains spent.

## Actual immutable model-seam snapshots

The same no-device producer saved byte-exact installed source files before
the schema assertion. These are valid source artifacts despite failure; they
do not constitute a model integration or numerical result.

- source_snapshots/attention_v1.py:
  SHA80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390
- source_snapshots/model_runner_v1.py:
  SHA94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968

Runtime paths were under /vllm-workspace/vllm-ascend/vllm_ascend; snapshot Ref
uses /abi-results inside the image and this raw root on host. The independent
consumer readback verified stopped ownership and original raw report bytes.
Sparse preparer was given the exact host snapshot paths/SHA for SparQ's real
attention/runner bridge, plus actual schema evidence for independent v4 repair.
No rejected AdaKV payload was relayed or resubmitted.

A transient MAIN source-review assertion that inherited workspace was4GiB was
withdrawn before dispatch: exact H8 SHA4ddd75... defines WORKSPACE=5GiB.
The frozen H8 module remained unmodified and no result inherited that false
budget claim. Read the directly invoked source, not another helper layer.

## Next stage

Recurrent preparer closes H8 all batches/lifecycle/model bridge; sparse preparer
uses actual ABI for FlashInfer v4 and installed model sources for SparQ; lowbit
preparer closes actual host/daemon CPU admission and W4 packing. MAIN alone
admits reviewed native jobs. No new E2E throughput, TTFT/TPOT, GSM8K or
LongBench-v2 measurement has been produced by this prerequisite.
