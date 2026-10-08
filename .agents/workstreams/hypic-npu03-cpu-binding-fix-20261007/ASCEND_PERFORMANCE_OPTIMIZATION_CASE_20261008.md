# Ascend performance optimization: bounded CPU-binding configuration case

Tested Skill: `ascend-performance-optimization` from main commit
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`. This case is the real
NPU0–3 investigation of a large Decode floor, not a new NPU run. The
diagnosis separated HCCS/AIV link speed from service graph and host
synchronization: standalone TP4 AIV AllReduce and graph replay were fast,
while full-service rank-2 graph task-update waits were long. A cpuset-only
probe reduced rank-2 wait but regressed service TPOT. The next bounded
hypothesis targeted automatic CPU binding using its official vLLM-Ascend
`enable_cpu_binding=false` switch, one primary serving variable.

Replay on chicaihong01:

```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_performance_optimization_case.py
```

It verifies four diagnostic contract/workload hashes, unchanged parsed
stimulus and serving command except the switch, physical 0–3 identity and
4/4 exact 128-token outputs. Profiled diagnostic weighted TPOT went from
499.0045 to 140.9520 ms/token (71.75% lower); this supports the bounded
path-level binding hypothesis, but only ranks 0 and 2 had full exported
profile analysis. The exact internal CPU-pool subcause remains unproven.
The same replay calls the six-run formal no-cache performance verifier:
three 40×1024 c16 baseline TPOT values around 411–418 ms/token versus
three candidate values around 77–78, an 81.12% median reduction with
exact candidate cleanup.

This covers the Skill's evidence-to-one-candidate choice and preference
for a supported configuration, but **not** its full acceptance boundary.
The model-path feature matrix, complete paired 2048-token quality,
memory/stability/tail checks and production rollback gate are not all
established for this configuration. The current HYPIC full-quality arm
uses a different plugin source and a different 0.85 GPU-memory setting;
its evidence cannot be silently substituted for this 0.9 no-cache case.
Keep long-term Skill status `partial-evidence`, not `verified`.
