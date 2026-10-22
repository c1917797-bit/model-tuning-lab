# Continuation source frozen; NPU admission pending

Observed stage: 2026-10-22 12:47 UTC. This is a separate batch authorized by the current user instruction to continue. The original report deadline remains 2026-10-22 12:38:41 UTC; its final-goal-not-achieved report was committed and normally pushed as 66b7fca6168f5e103717f279b548a7b6e5f8a72b and independently verified at origin.

## Actual completed work

The 22 reviewed preparation files were deployed under their new paths and all full bytes/SHA identities matched. The preparation descriptor contains 28 inputs; the real host controls add the descriptor itself, yielding 29 exact before/after entries. The actual host ran 11 boundary controls, 8 integration controls, 16 projection controls and the bounded metadata-capacity calculation. All child exit codes were zero, all original resource caps held, and an independent MAIN read reopened every input and raw stage stream. This is PASS_SOURCE_ONLY; the capacity calculation uses fabricated bounds and is not tensor evidence.

MAIN then issued the genuine source-only review. The builder actually created the new template, source, command contract and BUILD_RECORD without modifying its inputs. The independent v4 auditor actually validated the complete original runtime/clock comparisons and exact equality of its proof readset with the host's actual source/command/dependency readset. It retained the original twenty same-image test enumeration, original thresholds and cleanup. Those twenty tests have not been run under the new source by this stage.

## Exact evidence

- Host controls inspection: /opt/host/vnf/austinov/run-bole-continuation-control-review-v1-20261022T123800Z/CHECK.json — 22125 B / 1d188f47371e28c193a90d955cffdd19e3568cf416119f1417afcf5d437956df
- MAIN source review: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/boundary_probe_prepare_v3_continuation_20261022T120055Z/MAIN_REVIEW.json — 8183 B / 141caba52d0aed2b8cfae6d4010a58e21e015bb3097ec38ef9f3403a9a4d3020
- Freeze execution: /opt/host/vnf/austinov/run-bole-continuation-source-freeze-v1-20261022T124000Z/EXECUTION.json — 10179 B / 006f50a6c9e327dd963423fa299b549e17ae26717032980a0cd620554acf127d
- Bound source: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/SOURCE_BOUND.json — 1638841 B / d28e57b46ae913182ff8ebc0f35a1c631f12fce647376af495a4b59c4d8e10df
- Bound commands: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bound-boundary-ON-v3-continuation_20261022T120055Z/COMMANDS.json — 4880 B / 8abb00b1e0ff4a240bb3932725fb342fa1bb576bcf23284c1c77284cd000f66a
- Build record: /opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/boundary_probe_prepare_v3_continuation_20261022T120055Z/BUILD_RECORD.json — 1299299 B / 89e94c8cad8ff1d2769d033d7a3e6c1cff638992c97ab4799d645e5aa25872e4
- Audit execution: /opt/host/vnf/austinov/run-bole-continuation-source-audit-outer-v1-20261022T124100Z/EXECUTION.json — 2458 B / 3c8c0e022dda6df280125a7fa457d52ab0f285c694d685b592a9dd438a37c9a3
- Source audit: /opt/host/vnf/austinov/run-bole-boundary-source-audit-v4-continuation_20261022T120055Z/SOURCE_AUDIT.json — 1424700 B / 08c783e7989397f25a6db83fa9d1f1d86807e9154a8691058f6ee5d510a62cc6
- Audit result: /opt/host/vnf/austinov/run-bole-boundary-source-audit-v4-continuation_20261022T120055Z/RESULT.json — 725 B / 2d1b765da76e01215ef86639b37c0804718a851d307580cd761c1a1f83105647

The new internal finite batch is 2026-10-22 12:00:55–18:00:55 UTC. The original phase=3600 seconds, cleanup=180 seconds, whole prepare admission=3780 seconds and physical devices 4–7 remain unchanged. The finite batch does not extend the old report window.

## Concrete remaining blockers and next step

The independent MAIN dispatch review found an evidence-adapter defect before any dispatch: a current controller whose external-output context is the new directory cannot validate old owners using that current directory. The historical source/output context must be reproduced exactly while keeping original full create/inspect/environment/label/device/resource predicates. The parent launcher must supply the original external-output opt-in before loading the controller, and the six current full inspect receipts must be retained losslessly inside the unchanged evidence cap. Versioned draft fixes and independent review are pending; none is described as admitted.

A fresh actual-resource snapshot and exact six historical ownership/cleanup chains are still required immediately before dispatch. The 12:14 observation is historical, with seven process-scan races retained and a protected external NPU1 workload; it is not a current lease. No new owner, container or NPU model request has been started by this continuation stage.

The new projection observer will hash actual projection input and source-visible output/reduction boundaries. It records weight metadata; it does not hash full effective weight bytes or observe private backend formats. These limitations must remain in causal conclusions.

## Original findings remain unchanged

The complete original ON/OFF state pair is FAIL (36 versus 32 rank-frame keys); comparing only the 32 common keys is not an acceptance gate. The previous ON-only boundary diagnostic found the first observed difference between layer0 norm and out_proj return, with unknown cause. No candidate numerical/multistep/lifecycle acceptance, new whole-model >=10% throughput result, formal paired TTFT/TPOT or final GSM8K/HumanEval/MMLU acceptance is established.

Only after the low-observation candidate itself passes true-NPU numerical, multistep-state and lifecycle gates can it enter same-config fixed-1024 whole-model screening and the three required formal pairs. Final tasks remain thinking off, max_tokens=2048, normal EOS, with raw scores, percentage-point loss and relative loss.
