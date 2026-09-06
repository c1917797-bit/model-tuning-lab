# Resource Request — WS-20260904-qwen38-dense-paper-to-ascend

## Purpose

Collect the exact missing inputs needed to freeze and execute the reusable G1-G4 piercing ruler. Do not replace a requested dataset with a similarly named benchmark or harness. Preserve the employee-success versions when available.

## Priority 0: employee-success benchmark bundle

Provide the complete directory tree, archive, or immutable repository revision containing:

- `benchmark-3.1-20260119-master`
- `ais_bench/datasets/LongBench-v2`
- dataset registrations for `longbenchv2_gen`, NIAH+, GSM8K and CEval
- `vllm_api_general_chat` model configuration
- `benchmark_prefix_coexistence.py`, `aisbench_test.py` and their `config.py`
- `extract_non_reasoning_content` implementation
- metric parser/report scripts used for TTFT, TPOT, OTT, BD and quality

For every supplied tree/archive, record source owner, version/commit, byte size and SHA256. The old absolute paths are provenance only and do not need to be recreated.

## Priority 1: exact frozen datasets

### NIAH+

Required: data or generator inputs, generator/version, context-length and needle-depth grid, seed, sample IDs/order, prompt template, expected answers and scorer.

### LongBench v2

Required: the exact `LongBench-v2` directory used by `longbenchv2_gen`, subset list, sample IDs/order, prompt template, answer parser and scorer.

### CEval

Preferred: the exact employee-success copy and split/few-shot configuration. Current-host acquisition lead only: EvalScope declares `modelscope/ceval-exam` and `https://modelscope.oss-cn-beijing.aliyuncs.com/open_data/c-eval/ceval-exam.zip`; neither is frozen evidence until materialized and hashed.

### GSM8K

Already present at `/cache/austinov/eval-data/general/prepared/gsm8k_test.jsonl`. Still request the employee-success split, prompt and answer-extraction config so scoring semantics can be matched.

## Priority 2: missing exact evaluation/runtime values

- Complete model/dataset config preceding the truncated `batch_size=32` excerpt
- performance request rate and warmup count/policy
- exact concurrency matrix beyond the recorded 32768-in/1024-out, 40 requests, concurrency 16 case
- cold-sample exclusion rule
- LongBench v2 subset and batch size
- CEval/GSM8K few-shot and split selection
- NIAH+ construction matrix
- tool and parser versions

Already adopted from the successful record: quality uses seed 0, temperature 0, thinking disabled, `ignore_eos=false`, and `extract_non_reasoning_content`; performance and quality run in separate service lifecycles; each measured configuration repeats three times.

## Priority 3: true DRRQR resources

Provide one of:

- official paper implementation/repository and immutable revision;
- the internal DRRQR selection/conversion implementation previously used; or
- complete true-DRRQR checkpoints for both `/cache/austinov/Qwen3.8-27B` and `/cache/Qwen3.5-4B`.

Required provenance: calibration dataset, selection evidence, source config hash, target Dk, changed layers/tensors, converter version, checkpoint config/index/shard hashes. Fixed-first-channel and data-free L1 artifacts are explicitly not acceptable as DRRQR.

## Runtime authority (not a file-search item)

Before replacing the currently running NPU0-3 baseline, the operator must supply exactly:

    I_OWN_NPU0_3_AND_AUTHORIZE_BASELINE_REPLACEMENT

NPU4-7 and CPU0-95 are outside this workstream and must never be touched.

## Delivery acceptance

Place resources in a new non-destructive directory or provide an archive/repository path. Do not overwrite source checkpoints or live benchmark directories. On receipt, run inventory and SHA256 first, then update `test-contract.json`, create `runtime-config.json`, run `freeze_test_contract.py`, and finally run `preflight_piercing.py`. No NPU workload starts unless preflight is ready and authority is explicit.

Copy `resource-intake.template.json` to a new manifest, fill every received path/hash and provenance field, then verify it read-only:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/verify_resource_intake.py --manifest /ABSOLUTE/resource-intake.json --output /ABSOLUTE/resource-intake-verification.json

For directories, the verifier hashes a canonical sorted inventory containing every relative path, byte size and file SHA256. Symbolic links, empty paths, missing assets, wrong dataset names and incomplete DRRQR alternatives fail closed.
