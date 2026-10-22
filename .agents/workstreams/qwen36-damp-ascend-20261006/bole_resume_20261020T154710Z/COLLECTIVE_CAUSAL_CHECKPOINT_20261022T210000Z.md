# BOLE projection-reduction diagnostic checkpoint — 2026-10-22

## Actual NPU finding

The V5 whole-model diagnostic completed both existing G1/G2 requests on physical NPU4–7.
All four workers supplied complete FP32/BF16-independent raw evidence at the observed
projection boundary: each rank's BF16 pre-reduction tensor was identical across G1/G2,
whereas the post-reduction tensors differed at 179,994 of 670,720 elements.
Within each generation, all four ranks agreed. Neither two diagnostic requests nor this
boundary alone qualify the BOLE algorithm.

Independent exact-BF16 addition-order analysis checked 16,384 differing coordinates
per generation: every checked native post value was in the possible BF16 binary-addition
order set. Coverage is partial; per-coordinate possible orders do not establish a
single global reduction tree, native-kernel identity, or a native arithmetic defect.

## Controlled standalone NPU replay

Both variants used the same four immutable actual G1 pre-reduction raw tensors
(shape [131,5120], BF16), same image, worker source and observed library file refs.
Each variant reset the fixed input and executed eight native SUM all-reduces.

| Variant | Unique full output tensors per rank, across 8 calls | Four ranks equal at every call |
| --- | --- | --- |
| HCCL_DETERMINISTIC absent | 8 / 8 / 8 / 8 | yes |
| HCCL_DETERMINISTIC=true | 1 / 1 / 1 / 1 | yes |

All 64 raw output files were independently rehashed after terminal completion.
The explicit flag was observed in all four deterministic workers; torch deterministic
mode remained false in both variants. HCCL_ALGO and ASCEND_LAUNCH_BLOCKING remained absent.
Observed library file refs matched across ranks and variants, but pathname hashing does
not prove mapped library or native transport-kernel identity.

Both host controllers completed with no primary/secondary error, worker child exit0,
and own containers stopped, retained, not deleted, PID0, and not OOM-killed.
Fresh npu-smi after both runs showed no processes on NPU4–7 and baseline HBM
2868/2872/2868/2867 MiB. External NPU0–3 work was not stopped.

## Evidence identities

- Whole-model V5 output: /opt/host/vnf/austinov/run-bole-reduction-ON-v5_20261022T200000Z
- V5 RESULT SHA256: 5c98986d6b7056186c5a5dad5a538b4b7befb5179981fd0fe3c7867146294edd
- Independent analysis: /opt/host/vnf/austinov/run-bole-projection-analysis-20261022T203900Z-v1/ANALYSIS.json
- Analysis SHA256: 229376b2d4fa973c8943a49aa5dc89215c14f0b7e9c1b580bbefbf4b9db0f094
- Default replay: /opt/host/vnf/austinov/run-bole-native-ar-collective-replay-default-20261022T204700Z-v1
- Default RESULT SHA256: 1ef98cf97f1e546cf51374872cfb1773b78914d90042b31b7993e811cf415a00
- Deterministic replay: /opt/host/vnf/austinov/run-bole-native-ar-collective-replay-deterministic_true-20261022T204700Z-v1
- Deterministic RESULT SHA256: adde9b2226a97ccc7142b9eb68e7394dbbe19fc5592bd78be62bcce6c9b59918
- Worker source: reduction_collective_replay_20261022T201500Z/replay_collective.py
- Worker SHA256: fdc00dac78c235f94fd6d4bb4ad05d03e65eaaf498800b03002580e9422a393d
- Host controller SHA256: 7d2009c6a4ebf14e6d515e3f14254eb64426559c08990f23f5e510e870bd7801
- Terminal dispatch operations: exec-0000000000000825 and exec-0000000000000829
- Independent terminal/raw/flags/container/release verification: exec-000000000000082d

Same-image no-NPU checks passed. Their outer report writer originally appended a
literal backslash-n and made the wrapper JSON invalid; original files were preserved.
Only a new canonical report was generated from the actual verified successful payload.
Tests were not rerun to conceal the formatting defect. Format-recovery evidence lives in
/opt/host/vnf/austinov/run-bole-collective-controls-20261022T204700Z-v1/SOFTWARE_FORMAT_RECOVERY.json.

## Supported inference and next action

The standalone result supports a common native reduction-order/configuration explanation
for the production boundary's non-repeatability. It does NOT identify a BOLE algorithm
error, prove whole-model determinism, or qualify numerical/performance/task accuracy.
The standalone WORLD communicator is not the production vLLM tensor-parallel group.

Next: create a new source-bound opt-in production variant, setting the same common
HCCL flag before API/worker initialization for BOTH native_AR and BOLE, retaining
independent boundary/state/lifecycle checks. Verify all-rank flag inheritance AND actual
production TP repeatability; configuration text alone is insufficient. Preserve old
source/results. Do not change numerical thresholds. Changed common configuration
requires matched baseline performance later.

Parallel preparation must close the actual 1024-token native_AR/BOLE performance
source and consumer contracts, including HTTP IDs and all-rank retirement receipts.
Disable only proven diagnostic copies; retain input identity, algorithmic compact KV,
state publication, TP consensus, rollback and slot-ownership checks.

## Unfinished acceptance and time/resource scope

candidate_qualification=false; numerical_qualified=false; formal_performance=false;
task_accuracy=false. No throughput/TTFT/TPOT or task score is claimed by this diagnostic.
The last two tiny NPU replays lasted about 40s each, not continuous card occupancy.
Do not claim the whole preceding interval had no idle time.

Current internal finite batch retains original cutoff 2026-10-22 23:10 UTC.
A new full phase must still fit its unchanged phase+cleanup admission budget.
No historical deadline or user acceptance criterion is reset.
