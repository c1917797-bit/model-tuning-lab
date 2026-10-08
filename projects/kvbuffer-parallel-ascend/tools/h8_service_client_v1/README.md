# H8 service client — preparation, default OFF

This is the new H8 client seam, not a launched model or an accepted optimization.
It reuses the older P1 client's token-ID/usage/SSE approach, but does not reuse
its P1 native gate, library, budget, prefix-OFF launcher, or result schema.

The protocol is 40 requests, C16, 32768 input tokens (16384 shared prefix),
1024 fixed outputs, temperature0/seed0, two one-token warmups. This is a raw
token-ID performance fixture, not a no-thinking task-accuracy evaluation.
Task accuracy remains a separate normal-EOS/no-thinking/max2048 gate.

TTFT starts at actual HTTP submission in a worker. Client queue delay is
reported separately and also in an explicitly labelled inclusive TTFT.
The actual frozen completion sources are93c720549f2a9ef217d7c2a60710225c862032517520dd9ba693d4820f55365c
andc67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7.
Use echo=True with return_token_ids=True: the actual echo branch emits first
prompt IDs even when an initial chunked-prefill output is empty; actual token_ids
still contain only output.delta IDs. An empty prefill event is not the first
output token. Source inspection proves this serialization seam, not a live API.
Throughput spans first enqueue to last response DONE. SSE coalescing is
recorded; text chunks cannot stand in for token IDs. Failed streams remain raw
diagnostic evidence and cannot be silently omitted from a40-request report.

The receiver requires a NEW source-bound `kvbp.h8-model-service-arm/v1` ARM.json
from the MAIN-owned future model controller: prefix ON/align, TP4/PP1/DP1,
BF16, C16, non-speculative/non-async, profiling OFF, same total cache budget,
actual full/mixed prerequisites. An eager pair is only `same-eager-screen`;
`formal-graph-pair` requires its separate model-graph proof and matched dense.
The client does not itself verify the supplied authority or execute Docker,
Torch, or NPU operations. A whole-terminal/worker/budget/paired-arm consumer is
still required. No matched-E2E or task-accuracy PASS is emitted by this client.

Current pending: actual model controller/ARM producer, common fair cache
allocation, source-admission in the exact image, actual TP4 lifecycle/output
verification, model graph, repeated paired performance, and final task accuracy.
No source fixture or helper test satisfies these stages.
