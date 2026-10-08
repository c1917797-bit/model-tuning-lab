# r12 cold-request attribution from raw logs (bounded)

This is an offline replay of the terminal r12 source and data, not a new
device run or a paired HYPIC verdict. Replay with
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/analyze_cache10r12_fallbacks.py.
It pins hypic-evidence.jsonl SHA256
4a07d50497f730dcd8d3dadd9840ae3f9b47a5e48dbdf4cb96c02a2908adff60,
joins all 57 scored request IDs to their explicit-boundary and worker events,
and confirms 52 four-worker hot requests and exactly five cold ones.

| Scored request | Direct observation | Bounded interpretation |
| --- | --- | --- |
| 77:1 | The candidate segment was marked ready, but the first scheduled prefill chunk was 9,466 tokens, shorter than the 11,456-token reusable segment. The next chunk began at computed token 9,466; the scheduler recorded no hot rewrite. | A ready cache entry alone did not make this partially scheduled request hot. This is a chunk/admission boundary miss, not proof the stored material was corrupt. |
| 77:3 | A scored request reserved and scheduled a new 11,456-token segment producer, then recorded computed_prefix_not_reusable_boundary on the 2,055-token remainder. | Producer/rematerialization path, not a four-worker hot reuse. |
| 81:3 | A scored request produced the 16,384-token first segment, then processed its 2,511-token remainder cold. | Same producer path. |
| 85:2 | A scored request produced the 16,384-token first segment, then processed its 17,971-token remainder cold. | Same producer path. |
| 88:2 | A scored request produced the 9,456-token first segment, then processed its 2,050-token remainder cold. | Same producer path. |

The raw service recorded max_segments=10. It made 23 materialization-plan
attempts for 19 distinct segment hashes; exactly four hashes were produced
twice, and their second producers are the four scored requests above.
The log proves repeated production after a prior ready report; it does not
prove the exact eviction or invalidation transition for each hash. Cache
churn under c8 and a ten-segment limit is plausible, not established as
the sole root cause. Do not turn this into a claim that the c12060c source
regressed or that larger cache would necessarily fix all five misses.

The next full pair must retain the frozen c8/2048/127 payload and matched
0.85 control. If the prospective primary claim is deployed effect, count
all requests and report hot/cold strata without relabeling the five cold
requests. If the primary claim requires 100% hot activation, this r12
configuration fails the gate; any capacity or admission change is a new
treatment fingerprint requiring its own canary and control. Neither choice
permits reusing r12 as a full quality or performance arm. No NPU4–7 use or
foreign-container change occurred in this analysis.
