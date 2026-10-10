# R19 explicit-segment cache-pressure diagnosis — read-only

Scope: the already terminal, repaired-source LongBench-v2 max-2048/c32
HYPIC-only arm. This is a post-hoc mechanism diagnostic, not a new experiment,
quality reclassification, or permission to overwrite the immutable root.

## Inputs and method

- Raw root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-full-hypic`.
- `hypic-only/hypic-evidence.jsonl` SHA256:
  `7f5d77692a73e50b7c74cfd42384f77c4138157f6717706ce35044490f3f13e7`.
- Frozen paired quality audit SHA256:
  `40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`.
- Replay event names and sum `ready`, `evicted`, and `failed` across
  `materialization_report` rows. For each of the 127 immutable sample files,
  join each scored API request ID to `worker_hot_request_verified.request_id`
  using the documented exact-ID or API-ID-plus-internal-suffix rule. Count a
  request as proved hot only when exactly one internal ID joins and all four
  worker PIDs occur. This agrees with the independent audit's 134/381 total.

## Observations

| Frozen identity or event | Observed |
| --- | ---: |
| Sample concurrency / warm requests per sample / scored repeats | 32 / 2 / 3 |
| Material cache limit | 3584 MiB / 10 segments |
| Materialization ready / evicted / failed | 126 / 116 / 0 |
| Pending-materialization gate events | 125 |
| Largest number of prefills held by one gate event | 31 |
| Four-worker proved-hot scored requests, repeat 1 | 72/127 |
| Four-worker proved-hot scored requests, repeat 2 | 35/127 |
| Four-worker proved-hot scored requests, repeat 3 | 27/127 |

The 536 `worker_hot_request_verified` worker events uniquely join to those
134 scored API requests. `worker_hot_path` is logged only once per worker, so
its four startup PIDs must **not** be used as a per-request coverage counter.
The separate all-request quality result remains 227/381 no-cache versus
219/381 HYPIC (`REJECT_OR_QUALIFY`).

## Interpretation and next discriminating gate

Thirty-two concurrently submitted distinct sample warm-ups compete for a
ten-segment material cache. The 116 observed evictions and declining proved-hot
coverage across repetitions are consistent with cache churn contributing to
the strict activation shortfall. This is not proof that cache churn caused the
eight-response net quality loss: unproved requests are not necessarily cold,
and the full-request quality result includes every scored request. Do not
retroactively change the frozen hot or quality gates.

After the live GSM8K arm and its independent audit finish, any capacity or
schedule repair must be a **prospective**, one-factor, same-source comparison
with a fresh matched no-cache baseline and immutable roots. Check memory
feasibility and physical NPU0–3/port availability before device use. Do not
reuse the r19 baseline under a changed material-cache identity, and do not
substitute isolated GDN results for end-to-end quality.
