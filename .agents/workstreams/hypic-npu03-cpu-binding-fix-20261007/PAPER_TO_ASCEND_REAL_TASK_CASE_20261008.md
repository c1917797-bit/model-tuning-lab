# Paper-to-Ascend main Skill: HYPIC real-task acceptance case

Tested the exact locally tracked main commit
ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2, Skill blob
ad455c2d22d64eaff61384c23c39bd4693d15636, Qwen3.6 lesson-reference
blob 744b6daa280b14a90930b7be0c7a1055e9170935, and registry blob
2611864bbcf719d57920aae03ff9eb85521526b4. The branch Skill and
reference bytes match main; the branch registry differs, so all status
counts in this case are evaluated against main, not the branch registry.

Real task: port/reproduce HYPIC for text inference on the Qwen3.6-named
27B checkpoint, whose config reports Qwen3_5ForConditionalGeneration with
48 linear-attention and 16 full-attention text layers. Use the official
vLLM-Ascend image, a derivative opt-in plugin, TP4, and physical NPU0–3.
This is a retrospective assessment of an ongoing task, not a claim that
the main Skill's applicability checklist ran before code was written.

| Main applicability gate | Evidence and limit |
| --- | --- |
| Architecture and inference-time fit | The pinned checkpoint and service have a bounded C1/C2 single-instance text path without retraining. Vision, MTP, and other architectures are not tested. |
| Complete method chain and constraint feasibility | The local plugin is a derivative, not the authors' SGLang implementation. C1/C2 are bounded; distributed multi-replica C3 is omitted in a single TP4 instance. The upstream source snapshot is hashed, but its exact Git commit was not established. The architecture review was retrospective. |
| Bottleneck and production seam | Historical same-lane six-unit 32768-input/1024-fixed-output c16 performance audit passed with the supported CPU-binding repair common to both arms and an opt-in HYPIC path. This is a service result for that frozen workload, not a general Decode or full-paper gain. |
| Algorithm identity and decision scope | The workstream labels C1/C2 versus C3 and keeps plugin-derived, historical performance, natural quality, and current explicit-boundary tests separate. |
| Resource isolation | The valid historical performance and clean2 quality attempts include owned-lane audits; later foreign-process conflicts invalidate their own roots. No inference about present occupancy follows. |

The historical performance audit file SHA256 is
de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1.
It reports six valid units, a 22.3562% lower median weighted TPOT,
37.5656 seconds lower TTFT P95, and 1.4223x output throughput for its
frozen c16/1024 workload. Its quality_decision is not-measured. The
separate clean2 2048-token natural-EOS quality protocol finished matched
rows, but scored requests had zero four-worker hot-path activation:
without explicit segment boundaries, those scores cannot validate quality
of the actual reused-token path. Do not pool that protocol with a later one.

The current explicit-boundary r12 stress ran clean source c12060c on
physical NPU0–3 at c8 with max 2048 output. It completed 19/19 prompts,
57/57 scored responses, and 279 clean guard probes, then failed the
predeclared all-hot gate at 52/57 request-level four-worker proofs.
The five misses were one ready-cache/short-prefill-chunk request and four
scored rematerialization producers; exact eviction transitions remain
unproven. No matching 0.85 no-cache control, full 127-prompt quality pair,
GSM8K in-path pair, or same-identity three-round performance matrix exists
for this source. The source-fix causal effect is not isolated.

Decision: partial-evidence for the main Paper-to-Ascend Skill. A bounded
applicability and service-performance route is evidenced, and the Skill's
scope labels prevent claiming C3 or paper-exact reproduction. Its
prospective paper-ingestion/method-parity gate, full in-path quality,
matched current performance, independent final audit, and main integration
have not passed. This case does not promote the derivative, declare a
paper-level success, or increase the historical campaign V count.

Replay with
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_paper_to_ascend_case.py.
It checks exact main blobs, the historical performance artifact hash and
bounded fields, r12's independent negative audit, and the five-miss raw
replay. Once the prospective deployed-effect versus all-hot rule is
chosen, the next experiment must use a fresh same-identity control and
candidate on actually idle physical NPU0–3, preserve full 2048-token
quality and repeated performance units, then update this case from raw
evidence. NPU4–7 and foreign containers remain out of scope.
