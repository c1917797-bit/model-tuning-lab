# Qwen3.8 General-Eval Prefix Cache Continuation

- Natural-prompt correctness anchor: three valid runs from `80bd4b1f279e3704324a6bdfa68f7bb2cac71058`; MMLU median 0.708772, GSM8K median 0.90625, HumanEval pass@1 median 0.609756.
- Current performance protocol, per latest user instruction: exact 2048 prompt tokens, exact 40 completion tokens, concurrency 8, three repetitions.
- Fixed performance snapshot: `/cache/austinov/eval-data/general/perf_2k40.v2.jsonl`, SHA256 `a40b8df38c08d3dc2580b5aa53ff7c5d23702224f82774ed6bff718c35e298f7`, 513 requests derived from MMLU/GSM8K/HumanEval prompts.
- Padding does not manufacture a shared prefix: original prompt remains first; each short prompt gets unique deterministic right-padding token IDs.
- Candidate variable only: Prefix Cache OFF -> ON.
- Hardware claim: physical NPU4-7; do not use NPU0-3.
- Dedicated A/B endpoint: 127.0.0.1:8210 to prevent unrelated local clients from using the experiment service.
- Run three clean 2k40 baseline repetitions (Prefix Cache OFF), checkpoint+push, then three clean candidate repetitions (Prefix Cache ON), followed by natural-prompt correctness verification and decision.
