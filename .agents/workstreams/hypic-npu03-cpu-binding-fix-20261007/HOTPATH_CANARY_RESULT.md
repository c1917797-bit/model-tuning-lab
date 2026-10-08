# 2026-10-08 HYPIC hot-path quality protocol repair: paired canary

## Verdict

The earlier `quality-context-41984-clean2` campaign remains an off-path
quality-safety result. It did not send explicit segment ends and produced zero
worker-hot PIDs, so it could not accept or reject actual HYPIC reuse quality.
Do not alter or pool its frozen 12 units.

The repaired request protocol **passed a paired single-sample canary** on
physical NPU0-3. This proves the public chat request can carry explicit
segment boundaries and that the natural 2048-max-output scored request really
uses the HYPIC hot path. It is not a full-dataset quality acceptance or
complete paper reproduction; C3 and paper-original implementation parity are
still open.

## Matched observation

- Model, image, source, LongBench-v2 sample index 0 and frozen evaluator were
  fingerprint-checked. Sample ID `66ebed525a08c7b9b35e1cb4`, prompt SHA-256
  `1d1f65e33f8c94fcc7d55873d68434871b61df479a10fab43a663395d251a7c0`,
  24,616 input tokens, reference `B`. Both arms used the same explicit ends
  `[16384, 24616]`, two 1-token warm requests, then a natural request capped
  at 2,048 output tokens with temperature/seed 0 and thinking disabled.
- No-cache: 742 output tokens, predicted `A`, incorrect; zero worker-hot PIDs.
- HYPIC: 699 output tokens, predicted `A`, incorrect. The scored request,
  *after* warm-up, emitted `worker_hot_path` on four distinct worker PIDs;
  each verified 16,376 skipped prefix tokens. Warm-up emitted no worker-hot
  event, so the attribution is unambiguous. This sample shows no accuracy
  delta, not evidence of aggregate parity.
- Both services passed foreign-process guards with zero foreign NPU0-3 PIDs
  and zero probe errors. Their own containers were removed and NPU0-3 plus
  port 8223 released. NPU4-7 and unrelated containers were untouched.

External immutable receipts:

- `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-baseline/canary-result.json`
  SHA-256 `6093ae3468e06ba47e125ee28838911d33846c655b49bfdf64bfd9023f748912`.
- `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-canary/canary-result.json`
  SHA-256 `f206085cbfb41f6a5446eb92a8963df3b30dbab6d8a8cbb0c872488bbd11b2e1`.

Next acceptance work is a fresh, predeclared, matched LongBench-v2 quality
ruler under this explicit-boundary protocol, with its own baseline and HYPIC
arms, repeated runs, row/hash pairing, hot-path evidence, and release audit.
The prior short GSM8K prompts cannot trigger the >=4096-token rewrite path;
they remain off-path safety data unless a separately declared long-context
adaptation is tested. Preserve the previous performance C1/C2 pass separately.
