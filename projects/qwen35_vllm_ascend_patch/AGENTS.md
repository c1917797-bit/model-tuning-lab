# Qwen3.5 runtime patch project instructions

Read `../../AGENTS.md`, `../../.agents/HANDOFF.md`, and
`../../.agents/skills.registry.yaml` before working in this project. Root
maintainer skills and Git policy are canonical; do not copy a second Maintainer
Skill Tree into this directory.

Project-specific boundaries:

- Target Qwen3.5-27B, Ascend 910B4, vLLM-Ascend 0.23.0, and tensor parallel
  size 4 unless a new experiment explicitly freezes another denominator.
- Use only physical NPU0-3 for this project and always protect physical NPU4-7.
  Re-prove processes, container declarations, ports, memory, and the cooperative
  lease before every live run.
- Keep the official vLLM-Ascend image and host installation unchanged. Load the
  patch only into a new disposable container through a read-only repository
  mount plus `PYTHONPATH` or an editable no-dependency install in that
  container's writable layer. Never use `docker commit`, `docker cp`, source
  overlays, or site-packages replacement.
- Final acceptance requires, for each of c1/c5/c8/c16 over three repetitions,
  TTFT P95 at least 40 percent lower and TPOT P95 at least 20 percent lower
  than the frozen fresh control, plus zero material regressions in all 357
  paired quality rows.
- Quantization, retraining, MTP, speculative decoding, and model-layer skipping
  are outside this objective. The deliverable remains an opt-in runtime Python
  monkeypatch.
- Preserve raw artifacts, protocol identity, image identity, and SHA256 outside
  Git. A passing unit test, operator microbenchmark, activation check, or
  repository import is not an end-to-end performance or quality pass.
