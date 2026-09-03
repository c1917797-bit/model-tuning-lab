# Qwen3.8 General-Eval Prefix Cache Continuation

- Start point: `80bd4b1f279e3704324a6bdfa68f7bb2cac71058` (three valid baseline runs recorded and pushed).
- Frozen protocol: MMLU 57x5 = 285, GSM8K 64, HumanEval 164, concurrency 8, three repetitions.
- Baseline medians: wall 441.473954s; output 108.853534 tok/s; MMLU 0.708772; GSM8K 0.90625; HumanEval pass@1 0.609756.
- Candidate variable only: Prefix Cache OFF -> ON.
- Hardware claim: physical NPU4-7; do not use NPU0-3.
- Dedicated candidate endpoint: 127.0.0.1:8210 to prevent unrelated local clients from using the experiment service.
- Resume by validating the worktree/upstream, launching a clean Prefix Cache ON candidate on 8210, then running three clean general-eval repetitions.
