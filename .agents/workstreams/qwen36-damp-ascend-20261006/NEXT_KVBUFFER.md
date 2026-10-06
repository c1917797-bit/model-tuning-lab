# Next-paper preparation packet: KVBuffer FP32 parallel fold

Prepared only; no NPU run, formal start or24h clock. Not a rerun of capacity16 v5.

Source baseline: work/kvbuffer-qwen36-ascend-piercing-20260920,
d5c59876eaee1dc6a0cf425a7668830380d6371d. This branch already contains
targeted AscendC development and genuine negative E2E evidence; portfolio
opportunity-only labels are stale. Existing cap16 serial FP32 screen was
104.110913 versus108.996204 tok/s (-4.482%); v5 vector fast path106.005430
has only same-day noncontemporaneous dense reference(-2.744%), not final acceptance.
Neither rules out the unimplemented parallel buffered contractions/batch fold.

New hypothesis, sole change: retain cap16 and FP32 base/U-log, but batch
Klog*q, Klog*k, weighted U reductions and flush outer products over the log
dimension. Avoid per-entry GetValue/ExpScalar and serial log loops. Keep
non-boundary base unwritten. Include boundary/reset/slot correctness and real IO.

Reuse old plugin, ABI, metadata, graph probe, hash checks, allocator and fixed
output harness. Native recurrence remains per-step oracle. ops-transformer
ChunkGatedDeltaRule uses BF16 state. Pinned FwdH can take FP32 initial state but
K/W/U are BF16/FP16 and chunk.py casts U to BF16; it cannot silently replace
FP32 U-log fold. A BF16/FP16 path would be a separate approximation hypothesis.

Before formal start: isolate work branch/checkpoint; create independently named
library; review full existing probe's metric definitions; audit Cannbot route.
NPU matrix: eager B1/16×160steps,3 independent graph captures, changing slots,
flush boundaries, PAD/reset/reuse, all state/log metadata, input immutability,
guards/pointers; then mixed decode/newprefill with48 layers×4ranks.
Current old limits: output normalized max0.00303 and state relativeL2 2e-6;
do not reinterpret them as final1% task tolerance.

After numerical pass: profiler-off paired dense/candidate screen, TP4 on4-7,
40requests C16, input32768 prefix16384, forced1024output, total40960 outputs.
Both arms same image/model/general optimizations/max lengths/KV memory budget.
One hopeful screen ->3 matched balanced pairs -> final GSM8K/LongBench-v2
non-thinking normal EOS2048. Report pp and relative loss plus original no-loss goal.

Read existing branch files, not guessed paths, before selecting commands:
projects/kvbuffer-ascend/operator/op_kernel/qwen36_gdn_kvbuffer_decode.h;
tools/kvbuffer_candidate_npu_probe.py and tools/fixed_output_screen.py.
New .so and probe hashes are still unimplemented. Not launch-ready.
Preserve unchanged v4/v5 and all negatives; never rerun them without new evidence.
