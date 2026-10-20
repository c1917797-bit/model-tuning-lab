# Native AR owner repair v4: explicit observer dependency closure

Prepared locally only. No host, Docker, Git, NPU or target-image execution was
performed here. All earlier packets and actual v3 evidence remain unchanged.
MAIN reported that actual v3 completed target loading/snapshots on all four
ranks, then the first worker fault was `refs['device_op']` at frozen
`native_ar_observer.py:251`, before HTTP inference. MAIN separately retained the
original host idle-baseline failure after startup exited. This repair neither
changes nor bypasses that resource gate and does not certify its next outcome.

Only three runtime control files differ from v3:

| File | Change |
|---|---|
| ar_owner_common.py | Exact common/observer runtime partition, pinned observer host copy, fail-closed source key audit, readset closure |
| prepare_native_owner.py | New required observer host evidence argument; initial source assembly with merged map and explicit partitions |
| consume_pair_entry.py | Existing metadata-only replacement checks common map equality and reopens the observer-only dependency separately |

The finite controller, source-only Devices[] preflight, private host namespace,
snapshot/no-signal binding and all frozen pair/observer/helper/math bytes are
unchanged. The preparer copies original pair files verbatim. It derives the
initial source JSON directly instead of editing the JSON produced by the old
preparer. Its `frozen_pair_preparer` Ref binds that source derivation boundary.
No existing source file is rewritten.

## Exact source split

The actual G1-v2 `runtime_sources` has **32 keys**. Its complete map is preserved
unchanged as `common_runtime_sources`, without hardcoding its count in admission
logic. The one additional `observer_runtime_sources` entry is:

```json
{
  "device_op": {
    "path": "/vllm-workspace/vllm-ascend/vllm_ascend/device/device_op.py",
    "bytes": 78606,
    "sha256": "de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47"
  }
}
```

MAIN actually copied these bytes from its stopped original-image G1 container
to `T/native_ar_runtime_extra_v4/device_op.py` and checked bytes/SHA; the local
qualified primary copy has the same bytes/SHA. Supply MAIN's actual absolute
host Ref, not this installed path. The input `runtime_host_evidence` contains
all 33 keys; `observer_runtime_host_evidence` explicitly names the one extra
host Ref and must equal its precise subset. Unknown/missing keys, overlap with
an ON common key, same-path host substitution and content drift fail.

The source runtime map must equal the exact union of the unchanged common map
and the one pinned observer entry. Host readset skips only exact declared
installed Ref3 identities. Every host copy is reopened and mounted read-only;
same-image preflight and independent consumer reopen installed and host bytes.
The additional source proves native DeviceOperator class/method identity; it
does not replace any operator or change an original PA/FIA route.

The metadata adapter reports `common_installed_runtime_sources_equal=true`,
with separate observer-only refs. Whole-map `installed_runtime_sources_equal`
is false because AR has the explicit extra dependency. Actual initial-only
environment interpretation and `matched_common_plugin_effects_gate_pending`
remain unchanged. Frozen `consume_pair.image_and_common` stays replaced only
inside the same private reader instance, with exact function restoration; its
original full-map lookup is not called. Frozen run/math/identity consumption
is preserved.

## Pre-load key closure

Builder audits the frozen packet, six donor helpers and all seven owner control
sources **before full model hashing or creating new source/control leaves**.
Host `--source-audit`, Devices[] preflight and independent consumer recompute
the actual copied packet/control audit through `readset`. Direct runtime
subscripts and lexical aliases are checked; finite loop/comprehension keys are
resolved from actual source declarations. Unknown dynamic expressions fail.

The two frozen observer dynamic sets are:

* `sampling_params`, `sampling_metadata`, `gpu_input_batch`, `npu_input_batch`;
* `runner`, `base_runner`, `qwen35`, `qwen_next`.

Its constant keys include `device_op` and the nested forward/FA `block_table`
lookup. `RUNTIME_KEY_AUDIT.json` records the local source locations, full key
sets and every recognized access. The original ON-only map fails at the exact
251 lookup; the explicit union closes. This is a source/AST check for these
reviewed files, not proof of runtime class, inference closure or numerical
behavior. Original real-load instance/method/inference-mode/FA/identity guards
remain mandatory. No tensor/native module is imported in Devices[] preflight.

## Complete future MAIN recipe

Use new, absent v4 AR/control/output leaves and the same frozen native_ar_pair
directory. Retain all prior failed leaves. Run this packet's builder with the
previous v3 arguments plus the new required argument:

```text
/usr/local/python3.12.13/bin/python3 -I -B <reviewed v4>/prepare_native_owner.py
  --execute
  --G1-source-ref <actual successful G1-v2 SOURCE_BOUND Ref3 JSON>
  --G1-owner-ref <actual successful G1-v2 RESULT Ref3 JSON>
  --G1-bundle-ref <actual successful G1-v2 CONSUMER_INPUTS Ref3 JSON>
  --G1-independent-ref <actual successful G1-v2 ATTRIBUTION Ref3 JSON>
  --G1-inspect-ref <actual raw stopped ON Docker inspection Ref3 JSON>
  --G1-initial-profile-ref <actual historical initial-only profile Ref3 JSON>
  --actual-model-manifest-ref <actual 5813-byte full host model manifest Ref3 JSON>
  --frozen-inputs-ref <actual G1 dense/INPUTS.json Ref3 JSON>
  --framework-host-evidence-json <same actual four-module framework host map JSON>
  --observer-runtime-host-evidence-json <JSON object: device_op -> actual absolute host Ref3>
  --native-packet-root <same frozen native_ar_pair directory>
  --new-AR-root <new absent absolute v4 AR source leaf>
  --new-control-root <new absent absolute v4 control source leaf>
  --output-root <new absent absolute v4 owner output leaf>
```

First use its returned INPUTS Ref with:

```text
/usr/local/python3.12.13/bin/python3 -I -B <new control>/native_ar_host.py
  --source-audit --inputs-ref <returned actual INPUTS Ref3 JSON>
```

Only MAIN subsequently admits the serial physical4..7 window and submits:

```text
BOLE_NATIVE_AR_MAIN_ENABLE=1 /usr/local/python3.12.13/bin/python3 -I -B <new control>/native_ar_host.py
  --execute --inputs-ref <returned actual INPUTS Ref3 JSON>
```

These are interfaces, not submitted commands. The unchanged execution remains
Devices[] source-only preflight/stopretain, TP4 canary/load/two native requests,
no-signal actual snapshot joins, stopretain, Devices[] complete independent pair
consumer/stopretain. Original resource, window3600/cleanup180, idle-baseline,
full checkpoint, HF32OFF, worker/source/identity and all mathematical bounds
remain intact. No CPU/NPU/model/HTTP or reference-smoke pass is assumed here.

Eleven offline tests and eight cold default/help CLIs pass. Tiny unit fixtures
are labeled synthetic and never admission evidence. Both actual same-image
execution and the next native AR independent numerical verdict are pending;
all model/task/performance/formal ready flags remain false.
