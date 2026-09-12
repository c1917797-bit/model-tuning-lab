# T22 accuracy no-regression gate

## Non-negotiable rule

A latency improvement never compensates for an accuracy regression. Performance
and quality are independent mandatory gates; failure of either rejects the
candidate and restores the official runtime path.

## Evidence boundary

The frozen `/cache/cch/query_rewrite.jsonl` workload has 357 questions but all
357 `answer` fields are empty. It is valid for latency and paired-output
stability, but its reference-similarity aggregate is not accuracy evidence.
No report may use those empty answers to claim that model accuracy is
preserved.

For this workload:

- all 357 requests must complete without error and with natural EOS;
- byte-identical candidate/control outputs pass directly;
- every non-identical pair must otherwise have a row-level, hash-bound review
  record; summary-only manual approval is invalid;
- any material semantic regression rejects the candidate.

## Reference-backed accuracy gate

Only a candidate that first passes the performance fail-fast may consume the
full accuracy budget. Run fresh official-control and candidate evaluations
against the locally frozen AISBench GSM8K test set:

- dataset:
  `/cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl`;
- expected rows: 1,319;
- expected dataset SHA-256:
  `3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14`;
- scorer: the supplied AISBench GSM8K numeric postprocessor;
- decoding: temperature 0, seed 0, thinking disabled, natural EOS,
  `max_out_len=1024`;
- three complete repetitions per side, with zero failed requests.

Promotion requires each candidate repetition and the candidate median accuracy
to be no lower than the identity-matched official control. Preserve per-row
correctness and response hashes so any control-correct/candidate-wrong
transition is inspectable. If a run is incomplete, identity-mismatched, or
cannot be scored from reference answers, quality remains unproven and
promotion is forbidden.

This gate proves no measured regression on the frozen paired and GSM8K
workloads. It does not claim universal accuracy for every possible prompt.
