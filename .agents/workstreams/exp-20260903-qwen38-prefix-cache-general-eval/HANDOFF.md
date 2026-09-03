# Workstream Handoff

- Task: tune Qwen3.8-27B vLLM on chicaihong01 with MMLU, HumanEval, GSM8K baselines.
- Branch: `work/exp-20260903-qwen38-prefix-cache-general-eval`
- Base: `f49c63f8c8f790f8bb79b047cf689f852e1a4682`
- State: started / not-ready
- Original 8100/NPU0-3 service drifted because an independent ablation runner replaced it; it is not used as the experiment baseline.
- Isolated baseline service: `qwen38` at `127.0.0.1:8200`, physical NPU 4-7 mapped to container logical NPU 0-3, TP=4, prefix caching disabled.
- Target proof: host `npu-smi` showed baseline worker PIDs 3153485/3153488/3153490/3153492 on physical NPU 4/5/6/7.
- Data snapshot: MMLU 57 dev + 57 test subjects, GSM8K train/test, HumanEval 164; exact hashes are recorded in the experiment YAML and `/cache/austinov/eval-data/general/manifest.json`.
- First hypothesis: enabling prefix caching improves repeated-prefix general-eval TTFT/throughput without quality regression.
- Candidate isolation: reuse the same physical NPU 4-7 serially after baseline is captured; do not overlap baseline and candidate services.
- Resume: wait for the unrelated NPU0-3 ablation runner to finish, run 3 repeated baseline measurements, checkpoint them, stop baseline, then run prefix-cache candidate on the same NPU4-7 environment.
