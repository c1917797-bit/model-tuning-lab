# Workstream Handoff

- Task: tune Qwen3.8-27B vLLM on chicaihong01 with MMLU, HumanEval, GSM8K baselines.
- Branch: `work/exp-20260903-qwen38-prefix-cache-general-eval`
- Base: `f49c63f8c8f790f8bb79b047cf689f852e1a4682`
- State: started / not-ready
- Baseline service: `qwen38` at `127.0.0.1:8100`, NPU 0-3, TP=4.
- First hypothesis: enabling prefix caching improves repeated-prefix general-eval TTFT/throughput without quality regression.
- Candidate isolation: NPU 4-7 on a separate port/container; do not stop or reconfigure baseline.
- Resume: complete environment orientation, create reproducible benchmark client, run repeated baseline, then candidate.
