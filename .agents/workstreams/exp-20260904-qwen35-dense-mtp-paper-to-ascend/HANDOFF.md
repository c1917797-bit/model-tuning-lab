# Qwen3.5 Dense MTP Paper-to-Ascend

- State: `started / not-ready`.
- Base: `origin/main@fbc79c41c37c8900f0623ce8941304e9bfde5cf1`.
- Resource lease: physical NPU0-3 and loopback port 8220 only.
- Exclusion: do not stop, restart, inspect inside, or otherwise perturb the
  existing physical NPU4-7 workload or its port 8210 service.
- Current candidate: exact speculative decoding with the checkpoint's built-in
  Qwen3.5 MTP head; confirm selection against historical Decode profiling and
  installed vLLM/vLLM-Ascend 0.23.0 source before implementation.
- Resume: complete source/profile selection evidence, declare the experiment
  thresholds, then baseline on a fresh NPU0-3 service.
