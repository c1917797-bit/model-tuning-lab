# Paper-to-Ascend Piercing Troubleshooting

## Frozen ruler refuses to materialize

- Missing NIAH+, LongBench v2 or CEval is a real incomplete-suite condition. Do not replace them with GSM8K copies or silently reduce the suite.
- Resolve every REQUIRED field in runtime-config.template.json, including image digest, checkpoint manifest, concurrency, request rate, warmup policy and parser version.
- A path must be a non-empty regular file. Directory-level datasets should first receive a deterministic file manifest whose hash is frozen.

## Ablation summary is invalid

- Every model and dataset must have G1, G2, G3 and G4.
- Each warm cell must contain run indices 1, 2 and 3 exactly once.
- Cold compile/graph rows must use classification=cold and are excluded.
- frozen_inputs_sha256, invariant_config_sha256 and treatment_matrix_sha256 must be identical across all comparable rows.
- Every warm row needs finite TTFT, TPOT, OTT, throughput and batch delay; a metric omitted from every group is still an invalid experiment.
- Run indices 1, 2 and 3 must each occur exactly once. A duplicate does not become a fourth repetition.
- G1/G2/G3/G4 switch booleans are fixed; do not encode an extra optimization only in a free-form name.

## Quality gate fails

- The noise threshold must come from repeated G1 measurements on this exact frozen suite. A generic 1-2pp value is not proof.
- Use `max_within_cell_range_pp`: calculate max(score)-min(score) for runs 1/2/3 in every G1 model/dataset cell, then take the maximum. The JSON value, CLI value and recomputed value must agree.
- Noise observations are reconciled against the quality JSONL G1 rows by model/dataset/run. A separately transcribed score fails even when it happens to preserve the same final range.
- If source-quality SHA256 drift is reported, do not patch the evidence hash. Confirm the result change is legitimate, then rerun `build_g1_noise_evidence.py` from the final immutable quality JSONL.
- For the production one-shot path, use `run_analysis_pipeline.py --build-noise-evidence` and omit both the external noise path and manually copied threshold. Fixture mode deliberately cannot use this builder.
- Production Step 6 also requires `--profile-evidence`. The verifier rejects missing artifacts, symlinks, hash mismatches, capture-enabled runs, fewer than two models, non-improving target regions, mismatched ruler bindings, or a profiled candidate different from the unique performance winner.
- Condition A requires an actually shared discrete score.
- Condition B checks each model/dataset cell, so an aggregate win cannot hide a local regression.
- Condition C requires one stable canary digest in G1, one stable digest in the treatment, exact equality between them, and exactly 512 output tokens.
- Fixed-first-channel and L1 results are not substitutes for DRRQR quality evidence.

## Decision remains iterate

- A quality failure always blocks adoption.
- Fewer than two models always blocks the generalization claim.
- Missing metrics, differing performance/quality model-dataset scopes, or no unique all-metric winner block the phrase “全面最优”.
- A positive cross-model average cannot hide a negative model/dataset cell. Inspect `worst_case_improvement_percent_vs_G1` and resolve every local below-threshold result.
- A performance/quality service-config mismatch means the restart did not reproduce the same cell configuration. Compare the two phase rows; do not waive the hash check.
- A checkpoint-manifest mismatch means performance and quality used different weights. A quality group-switch mismatch means the recorded G1-G4 label is false. Regenerate the affected phase; never relabel rows after collection.
- Set a meaningful minimum improvement threshold before final rendering; zero is only suitable for fixtures.

## Timing looks orders of magnitude slower

- Check whether both `VLLM_ASCEND_GDN_RRQR_CAPTURE_ENABLE=1` and `VLLM_ASCEND_GDN_RRQR_CAPTURE_DIR` were set. CPU copies and per-layer torch.save calls can dominate runtime even though capture is bounded. Unset all `VLLM_ASCEND_GDN_RRQR_CAPTURE*` variables before timing.
- If one-shot execution aborts, inspect the emitted argv/error and confirm the cell service stopped. The executor attempts `docker stop <cell service>` in `finally`; a stop failure is a separate operational error and must be resolved before resuming. Re-run preflight and rebuild/re-hash the lifecycle plan rather than reusing a report older than five minutes.
- Inspect the lifecycle journal before resume. Only a running/failed journal with an exact completed-cell prefix and the same plan/preflight hashes is resumable; never hand-edit completed_cells to skip a partially collected cell.
- Separate profiler and non-profiler comparisons.
- Profile manifests must reference exported regular summary files with exact hashes; a directory path or unverified screenshot is not machine-checkable evidence. Keep RRQR capture disabled in both G1 and candidate profiles.
- Remove ACL/torch.compile/graph-capture cold samples from steady-state statistics but retain them as cold evidence.
- If vllm bench stalls on tokenizer/download behavior, use the frozen direct streaming client and record its version/hash.

## Resource isolation

- Always reason in host device paths. The protected container may expose host NPU4-7 as container NPU0-3.
- NPU4-7 and CPU0-95 are forbidden for this workstream.
- A prior container name or status file is not a current lease. Recheck npu-smi, Docker host-device mappings, CPU sets and ownership immediately before action.
- The one-shot executor is dry-run by default and never infers ownership. Execute mode requires the exact NPU0-3 authorization, fresh bound preflight evidence and a verified lifecycle plan; do not bypass those guards with ad-hoc start/stop commands.

## Git delivery

- Use per-command safe.directory if needed; do not change global Git configuration.
- Do not invent user.name or user.email.
- Do not push to official origin.
