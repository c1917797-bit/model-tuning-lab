# SparQ011 fixed selector diagnosis — actual evidence, Oct8

## Decision scope

Original native011 remains FAILED_NOT_PROMOTED. This stage localizes its support
difference; it does not pass full numerical/graph/model/E2E/task gates or reject
the paper. No sampling, precision setter, algorithm or threshold was changed.
Qwen3.6-27B plugin/default-OFF target, physical4–7 only, original runtimes/images
unchanged. HYPIC remains historical exemplar, not a new portfolio acceptance.

## Same-image CPU producer

MAIN12d2 actually passed8 stdlib tests;12d5 passed source/CLI prerequisites.
MAIN12d7 completed0 in23.323s with Devices[]/no device nodes, image660ce23...
and Torch2.10.0+cpu. It recovered all128 original selected tokens uniquely from
the complete BF16 K AND V pair across2110 live positions.
- Root: /cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq011-cpu-diagnostic-20261008-001
- RESULT SHA277d34a8c867c212e013e144e948e43d8701643188b03c9c246f9368f933c9b8.
- DIAGNOSTIC at run-sparq011-checkpoint-cpu-001-main-20261008-01/DIAGNOSTIC.json,
  SHA3a672637c5d86ee141b102899f8c8296042cbefd10ed14a244cea0ca68b2b18f.
- Failed original raw: failure-b1-eager-mean1-t0-061.pt,
  SHAb9e546d69e8e5a948d628698215dac8d94306731c0de9c9e386601d36d8e6875.
- CPU32 cutoff425/801 scores both0.0028536412864923477, exact FP32 tie.
  Stable CPU32 picked425; recovered original NPU picked801 and matched FP64.
- CPU64 scores425=0.002853641112585417,801=0.0028536415249622313.
  Original native channels, scores and precision settings are not in that raw.
  They cannot be recovered by assuming this later process's settings.

CPU outputs are diagnostics, not NPU/E2E benefits. CPU launch/terminal/software
original envelopes are retained under that root with ORIGINAL_MAIN_12D* names.

## Actual physical6 fixed-input native observation

MAIN12dd passed6 actual stdlib source-prefix/default-OFF prerequisites.
MAIN12de completed0 in66.487s, not a full011 retry.
- Root: /cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq011-fixed-observation-20261008-001
- RESULT SHA61cf9c1a9c1b4e3ca67ac4c3de6e2c4db70a2d9f9d8b949212b6cd9f07f5aa79.
- OBSERVATION SHAbb126c0712b44a77bd5335760ca5a5e482f73e38a690a6c78772e3016ad055c4.
- Actual source prefix is GraphTokenWorkspace.run through selected assignment,
  core SHAc5ef88f12828597469f7f3ce32a78ca4b4bb31d66c38beba102420d11bb21393.
  Only diagnostic return was appended; PA/cache writer/full graph was not run.
- Eight eager observations have identical selected tokens and raw file hash
  084af33dfb2b6c647365d57bafddf25b841f213c7213b980673f0fa0cc366748.
  Channels match CPU32; support matches FP64 and recovered original support,
  not CPU32. Native score425=.0028536412864923477,
  score801=.002853641752153635, separation4.656612873077393e-10 (2 FP32 ULP).
- This new process reports allow_hf32=false and Torch matmul precision highest.
  cube_math_type attribute is unavailable. No precision control was set.
  Neither this fresh allocation nor eager prefix establishes original graph
  pointer lifetime, original runtime flags or causal attribution.
- Host PID1322096; actual native stage host PID1322533/start37684539,
  namespace7; physical6->guest0. Distinct native-stage process ownership is
  captured, not borrowed from a canary.
- Exact owned CIDbf17a4bab3b153987764b2e5f38dcb916ef3298938d7cba353081c5845aec944,
  stopped/retained/not deleted, cleanup errors[]. Cleanup SHA
  7073a48ca42ea9e77e23c84a03e8cdcc482830d0c96a0caec6282f62e92ec945.
- MAIN12e0 independently revalidated identical stopped state, Pid0/noExec/noOOM,
  immutable own mapping/config and physical4–7 idle. No protected-card mutation.
  External0–3 workers580648–51 continued. MemAvailable93872260KiB.

All full_matrix/model/performance/accuracy_evaluated flags remain false.
Original12DD/12DE/12E0 tool envelopes are saved under this root, separate from
Git. Private source package:
 /cache/cch/qwen36-paper-preparation-20261007/sparse/main-sparq011-fixed-observation-v1-001
observe.py SHAa54ce310cefc951355b7a4bac2aa7735a15959d90935737f25b4e0f006066ad0;
host_dispatch.py SHA4bf1c5a4d605e8f9e668c4e96af58d2bbad085c5e18ca2ee98f87db8b1e8dd24.
Its SOURCE and actualCLI are bound in PLAN/launch receipts; no output overwrite.

## Algorithm-specific next seam and clock

Audit the author's actual dtype/GQA reduction/tie semantics before independently
registering any successor oracle. A CPU32 exact support check is not justified
by CPU32 naming alone; do not auto loosen it after observing a tie.
Reject unexplained non-tie differences and retain full output/feedback/state/
slot/graph gates. Existing011 is not retrospectively passed.

Explicit formal SparQ start/deadline fields are missing in the current queue.
Known documented attempt observation is2026-10-07T19:12:54.328698Z, not proof
of the earliest paper start. This observation conservatively capped itself at
Oct8 19:00Z, and did not reset a clock. Portfolio Oct9 11:17:31Z unchanged;
expired KIVI/DAMP work is not relaunched.
SparsePrefix actual TP4/lifecycle readiness is the next admission priority,
subject to full source review, CPU prerequisite and fresh summed budget.
Three preparers remain API/source-only while MAIN alone owns execution.

## Deployed HTTP producer source, not HTTP acceptance

MAIN12e0 copied exact public api_server.py without starting/executing the guest:
 /cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-660-20261008-0937-001/api_server.py
25625B SHA6d8df133280618a1afffa9d03e4655af011f2f94ced0f90c15f7fc8b0afc538f;
source /vllm-workspace/vllm/vllm/entrypoints/openai/api_server.py, owned stopped
image660 guest. Completion/SSE protocol closure and real task dataset/prompt/
scorer identities remain pending; no synthetic task score substitutes them.

## Alignment and publication

This stage advances failed native selector diagnosis, not generic kernel tuning.
No new accepted non-HYPIC matched1024 throughput>=10% or final2048 task result.
The global goal remains active. Ordinary RAM/CPU/IO are shared-host admission
and timing-comparability factors; external0–3 PID churn alone is not interference.
No further hugepage release (32GiB already SPENT), foreign stop, main/force push,
original runtime/image mutation or credential bypass.
Stage checkpoints are local while the known HTTPS authentication blocker remains.
