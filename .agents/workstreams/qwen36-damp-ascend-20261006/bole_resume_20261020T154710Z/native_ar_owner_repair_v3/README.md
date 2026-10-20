# Native AR owner repair v3: exact framework installed/host maps

This new isolated repair keeps v1 and v2 immutable. No host, Docker, Git, NPU or
actual target-image execution was performed here. MAIN's actual v2 source
preparation failed before Docker/NPU because a recursive G1 bundle read opened
installed framework source paths on the host. Its completed model hash and
partial source/control leaves remain prior retained evidence, not an AR result.

Only `ar_owner_common.py` and `prepare_native_owner.py` differ from v2. The
source-only preflight, controller, finite resource/window/cleanup/ownership
guards, no-signal snapshot join, metadata adapter and frozen observer/math are
unchanged. No path-prefix exception is introduced.

Every actual G1 snapshot declares the same exact four framework modules:

| Module | Installed source |
|---|---|
| vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn | /vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py |
| vllm_ascend.ops.gdn | /vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py |
| vllm_ascend.ops.triton.fla.chunk | /vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py |
| vllm_ascend.ops.triton.fla.solve_tril | /vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/solve_tril.py |

All four snapshots must have exactly this module set and identical full
`{path,bytes,sha256}` values. Distinct installed paths are required. The builder
accepts a new required `--framework-host-evidence-json` map keyed by these full
module names. It may contain all four entries, or just the two extras below:

```json
{
  "vllm_ascend.ops.triton.fla.chunk": {
    "path": "<actual absolute host T>/native_ar_framework_sources_v3/chunk.py",
    "bytes": 16312,
    "sha256": "6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5"
  },
  "vllm_ascend.ops.triton.fla.solve_tril": {
    "path": "<actual absolute host T>/native_ar_framework_sources_v3/solve_tril.py",
    "bytes": 14809,
    "sha256": "2d8cd5d3bd365fa5894c7ee0cddc106d1d2b34dd3f3e05f4dbf15e8010d89fc0"
  }
}
```

These paths are interface placeholders, not usable evidence. MAIN already
reported actual docker-cp/byte/SHA verification from its stopped original-image
G1 CID. Supply its actual absolute paths/Ref3 objects. `COPY_RECEIPT.json` remains
separate provenance; the source bytes themselves must reopen successfully.
For qwen_gdn/gdn, omitted host entries can be filled **only** when the exact
installed Ref3 already occurs in the actual ON `runtime_sources`; the builder
then resolves an exact content-equal source-bound host copy in ON `files`.
No new/unknown installed module can be filled this way. A same-path runtime/
snapshot size or digest disagreement fails. Unknown supplied keys fail.

The resulting new INPUTS stores the complete four-entry
`framework_host_evidence` map explicitly. Every host copy must have its own
distinct path and exactly the installed bytes/SHA. This validation occurs
before the existing full model rehash or creation of new source/control leaves,
so a bad map fails early.

Host `readset(installed=False)` skips opening **only** complete Ref3 objects
equal to the declared runtime or framework catalogue. All host copies are
opened and hashed and included in the immutable readset/mounts. Same-prefix,
same-path with different bytes/SHA, Ref2, unknown module and missing evidence
remain ordinary checked refs and fail if absent. Same-image preflight and
Devices[] consumer `readset(installed=True)` reopen every installed framework
Ref and every host copy; no runtime import is added.

## Complete future MAIN recipe

Use this directory's `prepare_native_owner.py` with the original v1/v2 complete
recipe plus the new framework JSON argument. Retain prior failed v2 source/
control/output evidence and choose entirely new AR/control/output names:

```text
/usr/local/python3.12.13/bin/python3 -I -B <new reviewed v3 packet>/prepare_native_owner.py
  --execute
  --G1-source-ref <actual G1-v2 source Ref3 JSON>
  --G1-owner-ref <actual successful G1-v2 RESULT Ref3 JSON>
  --G1-bundle-ref <actual G1-v2 CONSUMER_INPUTS Ref3 JSON>
  --G1-independent-ref <actual G1-v2 ATTRIBUTION Ref3 JSON>
  --G1-inspect-ref <actual raw ON inspect Ref3 JSON>
  --G1-initial-profile-ref <actual historical initial-only profile Ref3 JSON>
  --actual-model-manifest-ref <actual host 5813-byte model manifest Ref3 JSON>
  --frozen-inputs-ref <actual G1 dense/INPUTS.json Ref3 JSON>
  --framework-host-evidence-json <actual full-module-name -> host Ref3 JSON map>
  --native-packet-root <same frozen native_ar_pair source directory>
  --new-AR-root <new absent absolute AR source leaf>
  --new-control-root <new absent absolute control source leaf>
  --output-root /opt/host/vnf/austinov/run-bole-native-ar-<new unique v3 leaf>
```

Use the returned exact INPUTS Ref for the unchanged source audit:

```text
/usr/local/python3.12.13/bin/python3 -I -B <new control>/native_ar_host.py
  --source-audit --inputs-ref <returned INPUTS Ref3 JSON>
```

Only after MAIN separately admits the serial hardware window:

```text
BOLE_NATIVE_AR_MAIN_ENABLE=1 /usr/local/python3.12.13/bin/python3 -I -B <new control>/native_ar_host.py
  --execute --inputs-ref <returned INPUTS Ref3 JSON>
```

These are interfaces, not submitted commands. The unchanged path remains
Devices[] source-only preflight -> stopretain -> TP4 canary/actual native AR
dual131/output2+barrier -> actual no-signal snapshot/identity binding ->
stopretain -> Devices[] frozen pair consumer through metadata-only adapter ->
stopretain. Original3600/180 shared budgets, model hashes, numerical/transaction/
oracle/identity gates and explicit initial-only environment semantics stay in
place. Common plugin effects remain pending and every formal ready flag false.

Six offline tests and eight cold default/help CLIs pass. They cover actual four
snapshot declarations and two reported extra hashes, exact Ref identity,
missing/drift/unknown maps, host-vs-installed reopen behavior, runtime-only
automatic overlap resolution and the five unchanged runtime sources. Temporary
tiny fixture files are unit data only, never actual admission or numerical
evidence. Actual host source audit, same-image execution and native AR model/
pair qualification remain unexecuted by this agent.
