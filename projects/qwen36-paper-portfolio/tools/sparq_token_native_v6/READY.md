# SparQ v6 default OFF; MAIN-owned dispatch only

Actual software tests/default entries/source audit are preparation only.
No Torch/Docker/NPU was started by the preparation agent.

MAIN review integrates canonical.patch exclusively into new:
projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/

One MAIN foreground CLI (replace manifest SHA with this packet's actual value):
 /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/numeric_gate.py --host-execute --source-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_MANIFEST_SHA --output /cache/cch/sparq-token-v6-UNIQUE_NEW_LEAF

Default OFF entries:
 /usr/bin/python3 -B PACKET/numeric_gate.py
 /usr/bin/python3 -B PACKET/preflight.py
 /usr/bin/python3 -B PACKET/consume_numeric.py
 /usr/bin/python3 -B PACKET/model_bridge.py

Actual software source validation:
 /usr/bin/python3 -B PACKET/test_contract.py
 /usr/bin/python3 -B PACKET/test_abi.py
 /usr/bin/python3 -B PACKET/numeric_gate.py --source-audit-only --source-manifest PACKET/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_MANIFEST_SHA

MAIN CLI uses actual effective host/daemon ancestor cgroup CPU and ordinaryRAM,
not os.cpu_count. New CPU-only owned guest has inspected Devices[] and no device
requests/cgroup rules or actual Ascend nodes/FDs. Its actual observer writes
/sparq-results/ABI_OBSERVATIONS.json before assertions, with SHA-bound original
host alias NEW_HOST/cpu-preflight/ABI_OBSERVATIONS.json. Both byte-exact raw and
inline copies must agree. Actual CPU Torch/import/required native keyword ABI
and four independent CPU-FP64 golden cases must pass before exact CPU CID
stop-retain and creation of a distinct physical6->logical0 NPU guest.

The actual CPU child CLI explicitly includes --host-output-root NEW_HOST/cpu-preflight;
consumer binds the complete original child argv and raw stdout marker. No new
extra unowned container is required for collecting a predictable source name.

NPU canary and complete numerical producer recheck actual schemas/signatures
before any set_device. Native keyword is slot_indices; unchanged actual writer
receives wrapper slot_mapping. The source SHA and exact AST mapping are fixed;
checks are not optional and incompatible signatures are never unioned.

Shared sequential resources: guest8GiB/1CPU, host256MiB/1CPU, reserve8GiB/2CPU =
ordinary16.25GiB/effective4CPU; output5GiB + disk8GiB reserve. CPU/NPU phases share
one maximum5400s including90s cleanup, no lease reset, cutoffOct9 11:17:31Z.
Physical0–3 actual PID/start/hash/cgroup stay protected. Device declarations
alone do not block; foreign real4–7 processes/nonidleHBM/physical6 FD conflicts
failclosed. Exact owned CID full inspect precedes only that CID stop15;
all primary/secondary failures retained, both containers stopped-retained,
never rm and never stop foreign/protected workloads.

Full B1..16/eager1+graph3/160/meanOFFON =128 cases20480 independent per-head
numerical steps, full actual NPU Python PID/argv/start/cgroup proof distinct from
canary. Original dense KV retained; selected scratch/logits/mean are added HBM.
Failure stops/retains, no reduced matrix or relaxed threshold retry.

Independent whole-original terminal consumer after MAIN complete raw envelope:
 /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/consume_numeric.py --execute --shard NEW_HOST/gate --terminal ORIGINAL_AWMCP_JSON --terminal-sha256 ACTUAL_TERMINAL_SHA --proof NEW_HOST/proof.json --source-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_MANIFEST_SHA --host-result NEW_HOST/RESULT.json --host-result-sha256 ACTUAL_RESULT_SHA --expected-peer lgw_a6109c51076a4a2c9d2674ca5a8704a0 --output NEW_COMPONENT_AUTHORITY.json

Full raw original operation_get/direct a_exec identity and complete host/child
argv/marker/result/observer/proof/case/step SHA linkage are mandatory. Actual
software/Git envelope examples and failed v4 receipts are not NPU authorities.
Component schema remains v4 for unchanged fields; it binds this v6 manifest.

Current pending: actual v6 no-device ABI/CPU golden, owned NPU canary/full matrix,
independent actual original terminal consumption. After those: real model
startup/dummy/profile/TP4 and actual64layers16FA48GDN/mixed/paused/reuse/longcontext
allocator/native10GiB+candidateaux≤2GiB perrank capacity, matched C16 fixed1024
dense three pairs and final2048 frozen dataset/scorer. No NPU_READY, service
performance, memory saving, task quality or formal paper24h claim exists.

V6 additionally runs PACKET/test_launch_linkage.py. No v5 source-review failure is hardware evidence. Exact source-bound OWNER/CPU argv producer-validator-consumer closure is mandatory; legacy V5 markers/ABI schema remain explicitly supported as one unchanged protocol, not an alternative owner or argv.
