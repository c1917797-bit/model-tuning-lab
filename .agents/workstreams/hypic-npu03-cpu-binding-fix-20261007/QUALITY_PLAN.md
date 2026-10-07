# HYPIC binding-off paired 2048-token quality plan

Status: in progress, not a quality verdict. Operation `exec-0000000000000c6d` runs the paired controller; no-cache LongBench-v2 run1 started at 2026-10-07 14:36 UTC with physical worker PID proof on NPU0-3. User authorized continued use of physical NPU0-3 until the complete quality campaign finishes; NPU4-7 and the pre-existing sleep container remain out of scope. This quality campaign is separate from the fixed-output 40960-context performance runs.

## Frozen scientific question

After both arms use the same supported CPU-binding-off repair, does enabling only HYPIC preserve or improve natural-EOS model quality under the 2048-token ruler? The no-cache binding-off arm is the quality denominator; the HYPIC-only binding-off arm is the treatment. The HYPIC environment switch is the sole arm difference. The CPU-binding switch is common to both arms. The old binding-enabled LongBench baselines and partial GSM8K rows are historical, not reusable controls.

Identity: Qwen3.6-27B BF16 at /cache/efim/Qwen3.6-27B; official image sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1; HYPIC source 3ad0967589304cd8fc4e7cff02f48ecc6125c89f; TP4, HCCL AIV, FULL_DECODE_ONLY graph mode, physical NPU0-3, cpuset 112-191, port 8223, max_model_len=max_num_batched_tokens=41984. Both arms disable native prefix caching. The longest frozen LongBench prompt is 39642 tokens; 39642 + 2048 = 41690 < 41984.

Frozen dataset and evaluator: LongBench-v2 127 samples, SHA256 cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a; GSM8K 1319 samples, SHA256 3730d312f6e3440559ace48831e51066acaca737f6eabec99bccb9e4b3c39d14; evaluator SHA256 9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0. Use its frozen prompt/template/scorer/postprocessor. Three complete repetitions per arm and dataset, c32, max_out_len 2048, ignore_eos false, seed 0, temperature 0, thinking disabled, 2400-second request timeout and two retries.

## Progression and acceptance

1. Verify hashes, longest-prompt capacity, model shard metadata, exact source/image and live resource ownership before a service starts. Launch an exact isolated container with the common binding-off flag and only arm-specific HYPIC switch. Prove four worker PIDs on physical NPU0-3 and a real request.
2. Run one complete no-cache quality arm, then stop and prove port/device release. Keep one result per sample with index and response hash. Resume only missing valid indexes after an interruption; never trust an old summary without recomputing row counts and hashes.
3. Run the exact paired HYPIC quality arm with the same generation, evaluator, datasets, image, context, CPU binding, and resource mapping. Require HYPIC activation evidence. Stop and prove release.

The fixed within-arm unit order is LongBench run1, GSM8K run1, LongBench run2, GSM8K run2, LongBench run3, GSM8K run3. The treatment uses the identical order. This surfaces a complete representative unit of each dataset early without changing the frozen dataset/sample order within a unit.
4. Independently audit all 12 units (2 arms x 2 datasets x 3 repetitions): every expected index, zero failures, hashes, summary arithmetic, sample IDs/prompt-token identity, and per-sample wins/losses. Report all run accuracies, baseline variability, mean percentage-point deltas, LongBench difficulty/length categories, and length-limit rates.
5. Quality pass only if both dataset mean accuracy deltas are nonnegative, LongBench category deltas are nonnegative, and length-limit rate does not increase. A negative delta beyond the corresponding baseline three-run range is a regression; a negative delta inside that range is inconclusive. Any missing/invalid row or identity drift is invalid, not a quality score.

## Time feasibility

The old binding-enabled quality attempt took about 3 h 40 min for three LongBench baseline runs and completed only 80/1319 GSM8K rows in about 17 minutes before fail-fast. Those rates do not transfer to binding-off; the new fixed-output service improved throughput about 3.9x, but natural-EOS quality traffic may differ. A rough complete paired estimate is 9-30 hours plus service transitions and audit. The user explicitly allowed continued 0-3-card use through completion after the earlier one-day target elapsed. Record actual per-unit wall time and revise ETA after the first full LongBench and GSM8K units. Use a six-hour per-unit safety timeout, retain any valid partial rows, and diagnose a timeout before resuming; never silently shorten dataset, output cap, concurrency, or repetitions.

Raw artifacts live under /cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984, outside Git. No production/main promotion until paired quality, independent audit, release and integration review pass.
