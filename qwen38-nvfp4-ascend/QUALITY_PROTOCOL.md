# Frozen quality protocol

This protocol compares `/cache/austinov/Qwen3.8-27B` (BF16 control) with
`/cache/cch/Qwen3.8-27B-NVFP4` (candidate).  Both arms must use the same fixed
vLLM-Ascend 0.23.0 image, physical devices, tensor-parallel degree, tokenizer,
chat template, request order and decoding settings.  A run is invalid if any
of those identities differs.

## Dataset identities

| Suite | Local source | Frozen population |
| --- | --- | ---: |
| MMLU | `/cache/austinov/eval-data/general/prepared/mmlu` | 57 subjects, 14,042 test questions, 5 subject-local development examples |
| GSM8K | `/cache/austinov/eval-data/general/unpack/gsm8k/grade_school_math/data/test.jsonl` | 1,319 test questions |
| HumanEval | `/cache/austinov/eval-data/general/unpack/humaneval/data/HumanEval.jsonl.gz` | 164 tasks |

`freeze_eval_manifest.py` records file-level SHA256 identities and emits a
stable JSONL request manifest.  Raw datasets and generated model responses stay
under the ignored `artifacts/` directory.

## Prompt and decoding contract

- MMLU: canonical subject-local 5-shot multiple-choice prompt.  The model must
  return one of `A`, `B`, `C`, or `D`; score is exact choice accuracy.
- GSM8K: zero-shot deterministic reasoning prompt ending in `#### <answer>`.
  Score is exact match of the final normalized number after the last `####`.
- HumanEval: the dataset's Python function prompt is sent as a completion, not
  chat.  One deterministic sample is generated per task; score is pass@1.
- Temperature is `0`, top-p is `1`, seed is fixed, and sampling count is `1`.
- Maximum generated tokens are 8 for MMLU, 768 for GSM8K, and 1,024 for
  HumanEval.  Stop sequences are recorded in every raw response artifact.
- The exact tokenizer revision and rendered prompt SHA256 values must be
  captured after chat-template rendering.  BF16 and candidate rendered prompt
  hashes must be identical before scoring is allowed.

## Execution and scoring

Run BF16 first in a fresh disposable container, save all responses, shut down
only that owned container, then run the candidate in a second fresh disposable
container.  Never run the arms concurrently.  The candidate reference adapter
is labelled `BF16-compute weight-fidelity reference`; it does not establish
native NVFP4 performance because activation quantization is not emulated.

HumanEval execution must occur after generation in a restricted, disposable,
network-disabled CPU container with a per-test timeout.  Never execute generated
code on the host or in an NPU-serving container.

`score_text_quality.py` performs strict MMLU/GSM8K parsing, population checks,
rendered-prompt identity checks and paired disagreement reporting. HumanEval is
kept separate because its official functional-correctness evaluator executes
untrusted generated code.

The quality gate is fail closed:

1. zero request failures and complete populations in both arms;
2. identical request IDs and rendered-prompt hashes;
3. no material accuracy regression on any suite;
4. a paired disagreement report for every answer changed by the candidate.

Until a domain owner specifies a different tolerance, `no material regression`
means candidate aggregate accuracy is not below BF16 for each suite.  Exact
per-item equality is additionally reported but is not required because two
numerically faithful precisions may choose different yet correct answers.

## Performance separation

Quality requests do not double as performance evidence.  TTFT, TPOT and
throughput use a separately frozen workload, warm-up, concurrency matrix and
three measured repetitions.  Performance may only be claimed for a runtime
whose numerical semantics match the checkpoint format being named.
