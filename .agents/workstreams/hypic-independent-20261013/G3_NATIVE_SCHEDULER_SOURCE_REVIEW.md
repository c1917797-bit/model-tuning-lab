# Concurrent PIC admission source review

Source read operations: 03c9/03ca; live official image unchanged.
Exact source: /vllm-workspace/vllm/vllm/v1/core/sched/scheduler.py
SHA256: 9ae1491f57a6294e32416b93ef2ea68107fa0d65c3a4d7f745f1261012f735e9

Running requests calculate logical uncomputed tokens, apply the long-prefill
threshold and cap by remaining token budget (lines403-415). Waiting requests
apply the same cap at699, unless native chunking is disabled and the complete
request exceeds budget (lines689-699). This explains observed8191/16381/24570
partial prefixes in G3r1, not external interference or a broken public producer.
The model hook currently prunes AFTER native scheduling, so the scheduler does
not reclaim the16376 avoided PIC body rows in its admission budget.

Next design must distinguish logical KV allocation/position progress from actual
compute-row budget and preserve full request/token/slot/sampling identities.
Do not simply increment num_computed_tokens across PIC without material/state/KV
installation and fourrank execution proof. Do not disable chunking or lower c16
silently to mask the gap. Any prospective source/config change gets a new contract,
matching baseline and immutable root after current03bc terminal/source/release audit.
No existing HYPIC scheduler/runner code was inspected or imported in this review.
This review is not a implemented scheduler, NPU validation or full40 acceptance.
