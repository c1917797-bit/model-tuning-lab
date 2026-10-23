# Renewed24h: native precursor and next BOLE admission

Window: 2026-10-23T07:35:53Z to 2026-10-24T07:35:53Z, cleanup included. Human instruction: continue the proposed new24h plan. Old deadlines/results remain immutable.

## Completed real NPU precursor

Exact model: /cache/efim/Qwen3.6-27B; pinned image sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1. Actual native AR input2048/output1, TP4 physical4-7, no BOLE or MTP intervention. Canary, native metadata/HTTP token-ID/worker-exit consumers passed across4 ranks. Each rank observed16 FA and48 GDN layers. Native FA allocation was24 kernel pages; AR conv width3 is NOT evidence of BOLE/MTP conv width11.

Producer operation exec-0000000000000b7b was observed running; its terminal operation registry later returned not_found. Do not invent a terminal AWMCP exit0 or rerun the model. Actual producer RESULT primary=null/secondary=[] and elapsed607.5344634900102; original host PID3143162 absent. Exact CPU/model owned containers stopped-retained, PID0, OOM=false; exit137 resulted from normal explicit stop. Actual model stopped2026-10-23T08:10:50.83939622Z. Independent replay exec-0000000000000ba1 exit0 reran the actual source-bound native metadata consumer after release.

Refs:
- SOURCE_BOUND: bound-native-2k-prefill-observation-v1/SOURCE_BOUND.json, bytes2016137, sha2569ea364778b734bad3d8e6721d79def668721668bf1ab3df7fc2cc7bd2ad79b79
- Producer RESULT: /opt/host/vnf/austinov/run-native-2k-prefill-observation-v1/RESULT.json, bytes2827404, sha25601e6ef27dd31d12102a0ffff0be0cbd7a60af51f9d5727504eb0e09917ada724
- Independent NATIVE_REPORT: /opt/host/vnf/austinov/run-native-2k-prefill-independent-recovery-20261023T090200Z/NATIVE_REPORT.json, bytes5043, sha256839809fc0f2ffc07137be957fc21a7f953c4575b89d3b56214fad3d3d8687d99
- RECOVERY: same directory/RECOVERY.json, bytes1004, sha256cd9b158894db9f30879fe34897377b29bf444aba28d5153fa601dc867755b0dc

This is not BOLE numerical qualification, formal throughput or task accuracy. An actual BOLE worker must bind its own strong NativeGeometry and actual same-process prefill witness.

## Corrected budget interpretation, prospective only

Original g3_long_output_v2 README defines1GiB as per-rank captured-evidence reservation, not total process RSS. Original g2_channel uses ONE logical+wire+checkpoint+metadata. Old CPU oracle was separate8GiB. Later FAST executes CPU reload/reference synchronously in each real model worker; its actual container is32GiB, not that historical8GiB consumer. Later J additionally mixed2CPU copies and an unmeasured8+8MiB temporary assumption into the evidence cap, then permanently refused. That is an adaptation/accounting defect, not a paper no-go.

Successor will keep1GiB evidence,384MiB logical,448MiB wire,128MiB checkpoint,64MiB metadata caps. It must separately bind current same-worker/cgroup CPU usage and summed4-rank reservations within unchanged32GiB model/host reserve, and NPU capture/HBM. Preserve actual bounded Writer, sticky failure/raw retention, independent numerical/reference and ACK rules. No historical result is reclassified. No caller PASS or external JSON substitutes live objects.

The proposed tiny D2H shard is NOT dispatched: it cannot prove full-frame fit and is no longer the next discriminating acceptance edge. Existing same-image CPU Torch alias/lifetime tests remain only CPU diagnostics; identical HWM does not prove savings.

## CURRENT/NEXT and efficiency

CURRENT: source-owned joint evidence/CPU budget v2 in a new edit scope; no numerical tolerances changed.
NEXT: connect actual strong prefill/geometry and resource admission into PREFIX/codec/Observer/sink, complete source reconstruction and same-image actual-entry controls, then new output-root BOLE input2048/output8 NPU validation.
After real numerical success: longer160-step validation and matched whole-model1024 screening, then3 pairs and GSM8K/HumanEval/MMLU smoke/full.

The native terminal was not processed promptly (actual stop08:10Z, inspected~08:54Z). Continuous utilization is not demonstrated; no full-window no-idle claim. Preparation is presently the limiting edge. Do not launch artificial loads or repeat completed native work.

Protected0-3 untouched. No new hugepage release or historical raw deletion. Git push remains blocked by unchanged unavailable HTTPS authentication; no repeated speculative retries.
