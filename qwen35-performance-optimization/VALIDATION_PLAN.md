# Qwen3.5 t12 Validation Plan

## Decision

The t12 runtime-only candidate is worth testing because it reconstructs the
previously measured GDN projection-fusion stack without vLLM or vLLM-Ascend
source overlays. It is not yet a final deliverable. The current acceptance
target is:

- TTFT P95 candidate/control ratio at most 0.60 at c1/c5/c8/c16;
- TPOT P95 candidate/control ratio at most 0.80 at c1/c5/c8/c16;
- zero request errors and natural EOS for every measured request;
- semantic quality preserved on all 357 frozen dataset rows;
- no quantization, retraining, MTP, speculative decoding, or base-image
  mutation.

The historical fixed baseline remains useful for continuity, but a fresh
same-environment MTP-off control is the primary denominator after material
environment drift.

## Ordered gates

1. **Offline package gate.** Check syntax, patch SHA256, weight mapping,
   activation-checker fixtures, and an editable install inside the pinned
   official image with no NPU devices and no index access. Run
   `tests/test_official_image_source_contract.sh` to parse the exact embedded
   vLLM and vLLM-Ascend sources, verify every required class, method,
   signature, and exact source-replacement anchor, and exercise the complete
   device-free patch behavior under the image's own Python runtime. A full
   Qwen GDN import is
   not a no-device test in this image because Triton queries the Ascend SoC
   during import; an `rtGetSocVersion` failure without mounted devices is an
   environment boundary, not compatibility evidence.
2. **Resource gate.** Immediately before allocation, prove physical NPU0-3
   have no process and no container declaration, NPU4-7 stay excluded, the
   chosen port is free, at least 48 GiB memory is available, and the
   cooperative lease is held for the complete container lifetime.
3. **Fresh control.** Start the unchanged image with the same model, TP4,
   dtype, generation protocol, and MTP/speculation disabled. Capture image,
   environment, mount, worker, NPU, service-log, and SHA256 evidence. Use the
   same guarded launcher with VARIANT=control so the only treatment difference
   is the disabled versus enabled runtime patch. The activation checker must
   prove both the absence of hook markers for control and four-rank presence
   for candidate.
4. **Candidate activation.** Start t12 from the same image. Require the exact
   patch digest, four-rank hook markers, fused weight mapping, API readiness,
   one worker on each physical NPU0-3, no NPU4-7 mapping, no source overlays,
   and a fixed-input natural-EOS smoke.
5. **Quality canary.** Compare 32 length-stratified temperature-zero prompts.
   A mismatch does not become a performance claim; it triggers paired review
   before expensive measurement.
6. **Fail-fast screen.** Compare c1 and c16 first. A single near-threshold or
   cold-tail result is inconclusive. Reject only a repeatable material miss,
   request failure, activation failure, or quality regression.
7. **Full performance gate.** Run both control and candidate at
   c1/c5/c8/c16 with three repetitions and 32 requests per cell. Decide from
   the median of the three per-run P95 values using
   the root-level `scripts/run_qwen35_benchmark_matrix.py` and
   `qwen35-performance-optimization/scripts/analyze_qwen35_current_targets.py`.
   Each matrix must use a fresh output root and a unique run id. P50 and P99
   are diagnostics; a
   repeatable P99 increase above 10% is a commercial tail-risk flag requiring
   investigation even when the P95 target passes. Use a run-unique cache salt
   for every warmup and measured request so repeated prompts cannot turn later
   cells into prefix-cache hits.
8. **Full quality gate.** Capture all 357 rows from the same-runtime control
   and candidate with temperature 0, seed 1024, identical prompts, and natural
   EOS. Byte-identical output is an automatic pass. If any output differs,
   review every differing pair; any material loss rejects the candidate.
   Use the root-level `scripts/capture_qwen35_quality_outputs.py` with
   `--sample-count 357`, then `scripts/compare_qwen35_quality_outputs.py`
   and the fail-closed
   `qwen35-performance-optimization/scripts/check_qwen35_full_quality.py`.
   All capture, comparison, and review paths must be new and non-reused.
   Because the dataset answer fields are empty, the claim remains bounded to
   paired no-regression evidence on this frozen workload.
9. **Promotion gate.** Copy the exact validated patch bytes into the
   standalone repository only after all performance, quality, activation, and
   provenance gates pass. Pin image digest, patch SHA256, commit, commands,
   artifacts, and rollback instructions. The final PR must contain no
   unvalidated candidate or historical rejected path.

## Stop and rollback

Stop only the exact t12 container. Never stop an external owner, never touch
NPU4-7, never use docker commit, and never modify the base image. Rollback is
container recreation without the patch installation/activation step. Use the
maintained stop script, which requires the expected container name, variant,
and output-root labels to match before issuing docker stop.
