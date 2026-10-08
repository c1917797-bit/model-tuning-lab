# Ascend inference tuning loop: bounded real-task case

Tested main Skill: `ascend-inference-tuning-loop` at main commit
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`. Real task:
`exp-20261007-hypic-npu03-cpu-binding-fix` on chicaihong01 physical
NPU0–3. The supported upstream configuration switch
`enable_cpu_binding=false` was the sole declared serving change for
the no-cache performance comparison. The experiment YAML froze model,
image, source, benchmark bytes, cpuset, lane, thresholds and cleanup.

Replay on the target host:

```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_inference_tuning_loop_case.py
```

The replay checks all six original performance-file SHA256 values, exactly
equal parsed baseline/candidate workload configurations, three candidate contracts,
40/40 exact-output validity per run, exact owned-container cleanup, and the
predeclared TPOT screen. Baseline weighted TPOT values were 417.5428,
410.8568 and 410.8960 ms/token; candidate values were 77.5641, 77.8308
and 77.0052 ms/token. The median fell 81.12%. This supports a bounded
physical NPU0–3 CPU-binding-off performance result, not a HYPIC paper
effect or 2048-token quality pass.

The main Skill's `planned → baselined → attempted → verified → measured →
decided` sequence is represented by the experiment record and retained raw
runs, with a `partial_component` decision and a next gate. Its stronger
workflow is not fully accepted: full paired 2048-token quality, later
HYPIC activation/performance, and integration to main remain open. The
current host also lacks noninteractive GitHub push authentication, so local
stage commits are not equal to remote; the Skill's immediate-push rule is
currently unmet. Keep this case `partial-evidence` until those gates and
a fresh-main replay are demonstrated.
