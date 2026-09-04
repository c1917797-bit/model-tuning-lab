# Qwen3.8 General-Eval Prefix Cache Continuation

- Natural-prompt correctness anchor: three valid runs from `80bd4b1f279e3704324a6bdfa68f7bb2cac71058`; MMLU median 0.708772, GSM8K median 0.90625, HumanEval pass@1 median 0.609756.
- Current performance protocol, per latest user instruction: exact 2048 prompt tokens, exact 40 completion tokens, concurrency 8, three repetitions.
- Fixed performance snapshot: `/cache/austinov/eval-data/general/perf_2k40.v2.jsonl`, SHA256 `a40b8df38c08d3dc2580b5aa53ff7c5d23702224f82774ed6bff718c35e298f7`, 513 requests derived from MMLU/GSM8K/HumanEval prompts.
- Padding does not manufacture a shared prefix: original prompt remains first; each short prompt gets unique deterministic right-padding token IDs.
- Candidate variable only: Prefix Cache OFF -> ON.
- Hardware claim: physical NPU4-7; do not use NPU0-3 for this experiment.
- Isolation guard: physical NPU4-7 must contain exactly the four VLLM workers belonging to the measured server container. Recurring unrelated NPU0 probes are recorded in resource evidence but do not invalidate a run by themselves; server/client CPU cpusets remain fixed.
- Dedicated A/B endpoint: 127.0.0.1:8210 to prevent unrelated local clients from using the experiment service.
- Prefix Cache OFF 2k40 baseline is complete with three valid runs and zero errors. Median: wall 239.733832s, 2.139873 req/s, 85.594928 output tok/s, 4468.055219 total tok/s, TTFT p50 2363.812ms, E2E p50 3718.403ms. Run-to-run throughput CV is ~1.11%.
- Next: checkpoint+push this baseline evidence, then run three clean Prefix Cache ON candidate repetitions on the same NPU4-7 / CPU0-95 / 8210 setup, followed by natural-prompt correctness verification and decision.
