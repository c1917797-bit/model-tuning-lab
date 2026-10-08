# Draft only: cache10 exact-ID split quality protocol

**Not approved or executed.** The user must explicitly choose this revised
method before any `cache10split` service starts. The alternative is a fresh
original single-service 127-sample candidate/control pair in an actual
uncontended physical NPU0–3 window. An empty `npu-smi` snapshot is not an
exclusive window; `cannbench_ds` has intermittently entered NPU0 and NPU3.
Never stop or alter that foreign container, and never use NPU4–7.

## Why a revision is being considered

The original `cache10r2` candidate service was isolation-invalid when a
foreign NPU0 process entered after 56 persisted samples. Its whole-arm result
cannot be paired or called successful. Independent read-only receipt
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hotpath-cache10r2-clean-set-audit.json`
has SHA256
`99f2578adddd041f7a84fe441a1ac02b754b2c1a8217054e80e855b67e7f55bd`.
It verifies the exact pre-intrusion IDs `0–52,54–56`, 168 scored rows,
raw sample hashes, scorer and explicit-boundary joins, and exact owned
release. Its hot-path worker count is aggregate, not per scored request.

The proposed remainder is exactly ID `53,57–126` (71 samples). No candidate
ID in the clean set is rerun. This minimizes repeated NPU work, but changes
service lifecycles and the c8 queue tail compared with the original full
arm. A resulting comparison must be called
`revised-multi-service-exact-id-partition`, never an original single-service
quality verdict or universal losslessness claim.

## Prospective execution only after method approval

All three new services use fresh, nonexisting roots; LongBench-v2 127-item
frozen source/evaluator/prompt/sample identities; physical NPU0–3 TP4;
Qwen3.6-27B BF16; 41,984 context; 0.85 memory utilization; 3,584 MiB /
10 materialized HYPIC segments; concurrency 8; two one-token warm requests
plus three scored repetitions per sample; temperature/seed 0, thinking off,
natural stopping, and a 2,048-token output cap. Keep the image, source,
model, CPU-binding-off flag, cpuset, dataset bytes, payloads, port and
one-switch HYPIC enablement identical across services. The proposed order is:

1. `no-cache` shard 0: 56 IDs matching the preserved clean candidate set.
2. `no-cache` shard 1: the 71 complementary IDs.
3. `hypic-only` shard 1: the same 71 complementary IDs.

Before each run, inspect live physical 0–3 processes, relevant container
claims, port 8223, exact root absence and ownership. Keep the continuous
foreign-PID guard in flight; a foreign process, probe error, failed request,
or incomplete release invalidates that new root. Never restart a partial root
or reinterpret the old 0.9 baseline as this 0.85 control. Stop and record
the failure rather than consuming more NPU time under a broken pair.

The runner refuses `cache10split` unless
`HYPIC_HOTPATH_SPLIT_USER_APPROVED=yes` is set **after** the user's explicit
method choice. The new
`audit_hotpath_cache10split_quality.py` is an independent, fail-closed
post-run check: it re-audits the original bounded clean set, each new
root's rows, hashes, scorer, request IDs, boundary evidence, guard,
four-worker mapping, exact release, full 127 x 3 pairing and the four
service fingerprints. It deliberately reports
`original_single_service_protocol_equivalent=false` and
`per_scored_request_worker_hot_proven=false`. Score-rule output must be
reported separately from that method qualification.

The existing six-phase performance controller still requires the original
full `cache10r2` quality audit and is **not** runnable from this draft.
If the user approves the revised quality method and its independent audit
passes, prospectively decide whether a qualified quality receipt suffices
to enter the separately frozen 0.85/cache10 matched performance ruler.
Do not weaken its gate silently or compare raw latency against the old
0.9 service.
