# HYPIC quality hot-path repair, separate protocol

The frozen `quality-context-41984-clean2` quality campaign is an off-path
safety result. Its evaluator sent ordinary chat requests while automatic text
chunking was disabled and no `vllm_xargs.hypic_segment_ends` were supplied.
Consequently its zero `worker_hot_path` events do not establish quality for
actual HYPIC reuse. Preserve its raw rows and negative strict audit unchanged.

## Candidate-only canary

`hotpath_quality_canary.py` pins LongBench-v2 sample 0 from the clean2 dataset
and evaluator, verifies the frozen baseline row hash, and sends explicit token
ends `[16384, 24616]` through the public chat API. The default invocation uses
one owned HYPIC container on physical NPU0-3, two one-token observations, then
one natural request with `max_tokens=2048`. Four distinct worker PIDs must emit new
`worker_hot_path` events *after* that scored request begins, with at least 4096
verified skipped tokens each. This is a path/transport preflight, not a paired
accuracy or performance verdict. Warm-up events are not attributed to the
scored request. The NPU guard, exact container identity, and release receipts
must pass; NPU4-7 and unrelated containers are out of scope.

Run the same script with `HYPIC_HOTPATH_CANARY_ARM=no-cache` for a separate
single-use baseline root and the same warm/scored request contract. The
baseline must show no worker-hot events. Compare its sample result with the
candidate, but do not treat one sample as formal quality acceptance.

If the canary fails, diagnose transport, token boundaries, materialization,
or event attribution from its evidence; do not relax the four-worker gate or
claim success. Its external root is distinct and single-use.

## Formal follow-on ruler

After a passing canary, run a fresh matched baseline/HYPIC quality campaign
using the **same** long-context prompts, explicit segment-boundary contract,
sampling, 2048 maximum output, scoring, and three repeats. Confirm the request
bytes and token counts match, candidate requests actually traverse all four
worker hot paths, guard finds no foreign NPU0-3 processes, and both services
are released. Declare acceptance thresholds before looking at scores. Do not
pool new protocol rows with clean2. Original short GSM8K prompts cannot meet
the 4096-token rewrite minimum; padding them would be a new task/ruler and
must be labelled as such. C3 and original-paper implementation parity remain
separate gaps from C1/C2 and must not be implied by a quality result.
