# SparQ v6 — actual native ABI preparation, not NPU/model ready

Frozen v4 failed MAIN MA0ef8 in its CPU-only ABI guest before any NPU guest.
Its required native signature incorrectly used wrapper argument slot_mapping.
The actual source SHA de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47
has BaseDeviceAdaptor.reshape_and_cache(cls,key,value,key_cache,value_cache,slot_mapping)
calling torch_npu._npu_reshape_and_cache with slot_indices=slot_mapping.

This independent successor preserves all v4 bytes and prior original failure
receipts. It fixes preparation/API verification, not SparQ arithmetic. The internal
sparq_token_v4 core and scalar oracle are byte-exact unchanged; proof source is
explicitly corrected in this successor.
Numerical/complete-component/model seam schemas remain v4 for unchanged contracts;
preparation manifest is v6; ABI/observation schema and V5 marker protocol stay
v5 by explicit unchanged protocol, bound to the new v6 source manifest and owner.
No v4/v5 software or failed ABI result is borrowed as numerical PASS.

Observer collector never asserts on required argument names. It retains both
exports' callable identity, raw inspect signature OR original exception, full doc
and text_signature, every matching namespace/schema/overload with parameter
name/type/kwarg_only/default and return metadata, before/after source import.
It retains actual DeviceOperator binding, full actual deployed module source and
SHA plus actual wrapper method source/signature, mapped native libraries and
stack, initialization/node/Ascend-FD observations. ABI_OBSERVATIONS.json is
written and SHA-bound before API assertions or CPU golden execution. Failure
ABI.json keeps original primary error plus observation Ref/inline raw evidence
and any secondary persistence error; no failed receipt becomes an authority.

Strict checks distinguish wrapper slot_mapping from native slot_indices via
fixed-source SHA and AST exact keyword mapping. One complete callable binding
signature/one npu dispatcher overload must support every native keyword; unions
of partial overloads, foreign _C_ascend schemas, prose-only argument mentions,
positional-only parameters and generic kwargs cannot pass. Raw exception process
addresses remain visible; cross-process ABI identity compares their error type,
not unstable memory addresses. Exact observed signature/doc/schema and successful
source bytes are still compared before any set_device.

Actual CPU Torch imports/golden/schemas for v5 remain pending. Preparation uses
stdlib only; fixture signature tests are not deployment or numerical evidence.
Original failed v4 ABI and child have actual SHA-bound copies in this packet.

Algorithm 2312.04985v6, official revision 554ea6db219405becbdc0a126984a19f181bdc69:
GQA six local heads share rank32 channel-selected support of 128 full tokens,
local1 forced; original native KV remains completely allocated. Mean correction
off/on is explicit. Independent BF16-input CPU-FP64/scalar oracle, own candidate
q and separate reference rq feedback, per-request/head RMS .005/cosine .99998,
full cache/input/topology/scratch/mean guards and request-generation ABA/paused/
reset/reuse remain unchanged. Rank32/budget128 is approximate implementation
validation, not dense attention/task equivalence or saved HBM.

Full numerical gate: B1..16, eager1 + graph3, mean off/on, 160 steps each =
128 cases / 20480 steps. No partial trial/shard can pass.
Actual four CPU-only B1/B2 mean off/on golden smoke cases must pass first.
Model/service remain separate: real TP4/64layer/16FA+48GDN eager diagnostic,
actual mixed prefill/decode + slots/allocator/HBM/longcontext, fair paired fixed
1024 and final2048 frozen tasks are pending. Kernel graph is not model graph.
TP4 service003 is frozen and still depends on unavailable actual v4 component;
it cannot inherit this software correction or v4 failed ABI as PASS.

Source closure: 21 own +1 original native +3 frozen host +2 model snapshots =27.
Host execution remains MAIN-only; preparation starts no Docker/Torch/NPU, shared
Git mutation or new paper24h clock. Portfolio cutoff Oct9 11:17:31Z unchanged.

Successor002 also preserves original import/collection primary errors if partial
observation persistence fails; the latter is secondary, never overwrites primary.
The complete first001 software receipt is retained, not relabelled.

MAIN source review withdrew v5 dispatch: frozen host owner was sparq-token-v5
while frozen proof expected v4; proof's ABI argv omitted actual --host-output-root.
Those were preparation conflicts, not numerical/algorithm results. V5-002 is
retained unchanged. V6 has one hashed receipt.OWNER=sparq-token-v6 shared by
host/proof, one exact complete abi_image_argv shared by host/proof/consumer.
Host validates actual CPU report+observer+Docker/prlimit argv before CPU cleanup
and before any NPU CID creation. Proof derives CPU root only from actual owned
RW mount, binds host alias ABI/observer/proof root, and independently rechecks
the complete command; consumer rechecks exact authority output root as well.
New stdlib cross-module tests read frozen host/proof actual source, invoke the
actual host make_device_proof producer and actual proof validator; only native
ABI validation is stubbed and explicitly not device/numerical authority.
Positive/negative owner, missing/reordered/duplicate root flags, wrong aliases,
observer argv, exact CID and wrapped argv are covered. Old frozen bytes are
SHA-checked and their two rejection paths reproduced as software-only fixtures.
