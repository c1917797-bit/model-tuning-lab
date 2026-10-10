# r16 original-source full max-2048 quality pair — preregistration

Frozen before device launch. r15's eight selected cases were diagnostic (original source 13/24; current source 10/24) and cannot change the terminal r13 230/381→219/381 rejection. The next decision-changing question is whether the known-good HYPIC `3ad0967` source preserves quality on the *new* full max-2048/c8 physical NPU0–3 ruler.

Use Qwen3.6-27B BF16, TP4, physical NPU0–3 and CPU 112–191, the pinned official image SHA256 `660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`, context 41984, GPU-memory fraction 0.85, material cache 3584 MiB/10 segments, native prefix caching off, LongBench-v2 127 frozen sample IDs, frozen prompt/evaluator/dataset hashes, seed and temperature 0, thinking off, natural EOS, max output 2048, client c8, two one-token warmups and three scored responses per sample. Both arms mount the same clean original source checkout `/cache/cch/hypic_vllm_ascend-r15-original` at commit `3ad0967589304cd8fc4e7cff02f48ecc6125c89f`; only `VLLM_ASCEND_HYPIC_ENABLE` changes. Baseline then candidate run serially with separate fresh services, never concurrently.

Roots must not preexist:

- `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r16-full-baseline`;
- `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r16-full-hypic`.

These are **new** roots. r13's no-cache baseline cannot be reused because its mounted source identity was `c12060c`; all r13/r14/r15 roots remain immutable. Before each arm, freshly resolve `chicaihong01/ma`, prove direct routing, load host-development, verify source cleanliness, exact root absence, physical NPU0–3 process/port 8223 availability and no live controller. Retain the controller's continuous ten-second physical-process guard during in-flight requests; any foreign PID/probe error invalidates the arm. Only remove the exact owned container, never external work or NPU4–7 workloads. A slow live controller is not a reason to relaunch.

The r13 full pair took about 86 and 94 minutes. r16's feasibility estimate is therefore about three hours plus audit/cleanup. At freeze time 2026-10-10 00:41 UTC the user deadline 04:42 UTC leaves roughly four hours; do not start another broad phase before this quality pair finishes. If time or isolation ends the campaign, preserve partial raw rows as incomplete rather than scoring them.

The **prospective quality decision** compares all 381 scored responses per arm. A bounded `NO_MATERIAL_REGRESSION_OBSERVED` requires the candidate mean correct count per run to be at least the minimum of the three matching baseline run counts, no difficulty/length category whose candidate mean falls below the corresponding baseline run range, and candidate mean length-limit count per run no greater than the maximum baseline run count. Otherwise classify `REJECT_OR_QUALIFY`; no arbitrary universal percentage-point tolerance or post-hoc cold-request exclusions. Report paired flips, each repetition, length finishes, and the separate aggregate hot evidence. The historical source lacks current request-ID worker telemetry, so do not claim universal per-request four-worker attribution. This gate is not proof of mathematical losslessness, GSM8K safety, C3, or publishable performance; those remain separate.

Selectors:

```sh
HYPIC_R16_ARM=no-cache python3 -B r16_original_source_full_adapter.py --check
HYPIC_R16_ARM=hypic-only python3 -B r16_original_source_full_adapter.py --check
HYPIC_R16_ARM=no-cache python3 -B r16_original_source_full_adapter.py
python3 -B audit_r16_original_source_full.py --baseline-only
HYPIC_R16_ARM=hypic-only python3 -B r16_original_source_full_adapter.py
python3 -B audit_r16_original_source_full.py
```

The commands above are the prospective new-root contract, not instructions to rerun any completed old root. Audit must verify 127 unique samples, 381 scored response hashes and recomputed scores per arm, matched source/fingerprint, continuous isolation and exact owned release. Only an independently valid full pair can support the new ruler's conclusion.
