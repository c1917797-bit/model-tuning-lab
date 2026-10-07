# HYPIC NPU0-3 CPU-binding repair

Branch `work/hypic-npu03-cpu-binding-fix-20261007` starts from diagnostic commit `87647ac`. The diagnosis in `../hypic-npu03-comm-root-20261007/REPORT.md` identified enabled automatic CPU binding as the major Decode floor cause, but did not isolate the binding sub-operation. This successor tests the exact supported `enable_cpu_binding=false` configuration as an opt-in repair, without editing the official image.

Only physical NPU0-3 may be used. NPU4-7 are reserved; do not touch the existing `agentgpu-910b4-qwen35-4b-v0` sleep container. The canonical checkout is dirty with unrelated DAMP work, so this independent clone is the repair checkout. The frozen no-cache 40 x 1024 baseline is at `/cache/cch/hypic-qwen36-e2e-2048-20261006/no-cache`; hashes and thresholds are in `../../experiments/exp-20261007-hypic-npu03-cpu-binding-fix.yaml`.

Current stage: planned only. No new device result, production configuration change, or formal quality verdict exists. The existing 4 x 128 profiled binding-off result is mechanism evidence, not formal performance. Start with live ownership checks, then validate the launcher off-device, then one short non-profiled canary. Release only the exact owned container on any exit path.
