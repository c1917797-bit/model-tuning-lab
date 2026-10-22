# BOLE short ON/OFF v2: reader repaired, original paired gate failed

Recorded 2026-10-22 07:36:49 UTC. Hard deadline remains **2026-10-22 12:38:41 UTC**; this checkpoint does not extend authority.

## Decision

**SHORT_PAIR_FAIL_NOT_ADMITTED.** The old cleanup-summary reading failure is repaired in a new read-only v4 consumer. The actual original paired gate now fails. No original ON/OFF result or source was modified, no old NPU arm was rerun, and no performance or task-accuracy experiment was launched in this stage.

The 21 targeted cleanup-reader controls pass on the remote host. The actual paired child exits 1 at the unchanged original predicate `all four ranks/two generations/two frames`, before the original per-frame equality loop. Both complete individual-arm validators and host cleanup checks had already returned. This is not evidence of paired equality.

## Preserved evidence

- v4 execution: `/opt/host/vnf/austinov/run-bole-short-pair-reader-v4-20261022T070247Z/EXECUTION.json`, SHA256 `41202d391c8165138555b22e6b07c12d98e88cee456be8a757e35027bac163d1`; operation `undefined`.
- Retained-only diagnostic: `/opt/host/vnf/austinov/run-bole-short-pair-diagnostic-v1-20261022T072523Z/DIAGNOSTIC.json`, 4432793 bytes, SHA256 `3d615eeeb0d9ae010ba7ec2602f82567b7b772bce46d1a8bbde520f736dec30f`; operation `exec-0000000000000673`.
- Resumed host/device-release observations and operation records: `/opt/host/vnf/austinov/run-bole-retained-review-20261022T072523Z`. Snapshot refs are in the companion JSON. These are timestamped observations, not an ongoing idle-device claim.
- Original v3 failure and both original short v2 output roots remain intact. v4 rehashed all **124 original inputs** before/after; the diagnostic rehashed a **136-Ref** readset, including the immutable reader sources and execution records. Both sets are unchanged.

## What the real evidence says

| Item | ON | OFF |
|---|---:|---:|
| Total rank frames | 36 | 32 |
| G1 frames per rank | 5 | 4 |
| G2 frames per rank | 4 | 4 |

The four ON-only keys are each rank's G1/O4. G1's final eight HTTP tokens match, but its proposal/acceptance path already differs. G2's third and eighth output tokens differ: ON `37498`, OFF `12052`, with the same request hash. This is not a task-accuracy estimate.

At G1/O0 on all four ranks, the prompt, committed output prefix, root, full proposed token tuple and recorded semantic fields agree. Nevertheless 47 of 48 GDN layers have different full logical state/conv-before hashes, beginning at layer 1. Layer 0 before/after agrees. All 16 FA layers have different selected K/V after hashes. G2/O0 also starts with 47/48 differing GDN state/conv rows.

The numerical witness hashes logical tensor bytes after a CPU contiguous copy. It excludes addresses, other slots and storage gaps. Conv is the actual three-token leading tail, excluding speculative extra entries. FA after covers selected K/V writes, not the whole prefix or attention output. Thus unused arena padding does not explain these recorded state/conv differences.

**The precise temporal boundary is before first TREE publication, not a separately observed native-prefill return.** The isolated TREE saves arena anchors, checks they remain unchanged, and staging clones the destination as `before`. Native prefill, process calibration and initial MTP precede that retained witness. Existing hashes cannot separate those earlier steps, recover error magnitude, or establish a named operator/root cause. Later unequal histories and selected path shapes also make same-ordinal frames unsuitable for a general same-input numerical claim.

## Reader repair scope

The new helper parses only the producer's exact `{path,sha256}` cleanup summary, requires the expected owned path, bounded ordinary files and directories with no symlinks, checks stable identity and the whole-file hash, and parses those verified bytes. It derives bytes for a local complete Ref. The general strict three-field Ref parser and all original cleanup predicates remain unchanged. No old result is rewritten to manufacture a missing field.

The subsequent diagnostic explicitly retains `paired_gate_pass=false`, `performance_admitted=false` and `cause_determined=false`. Shared-frame comparisons diagnose the failure; they do not replace the complete-key gate.

## Validation and next step

`./scripts/validate-mst.sh` passed, exit 0: “Maintainer Skill Tree structure is valid (20 skills)”. Its raw stdout/stderr and execution Ref are in the companion JSON. This validation is repository structure validation, not NPU numerical or performance qualification.

Continue the narrow source/evidence review of the native-prefill/calibration/initial-MTP interval. Do not guess a cache-zeroing repair, relax exact state equality, or rerun a frozen failed source. Any justified new diagnostic needs a new source/output identity and fresh physical NPU4–7, owner, resource and deadline admission. The low-observation preparation still requires its own real-device numerical, multistep and lifecycle gates; then full-model matched dense/candidate screening, formal fixed-1024 pairs and final task validation remain required.

There is **no new >=10% full-model throughput result, formal TTFT/TPOT result, or GSM8K/HumanEval/MMLU acceptance result** in this checkpoint.
