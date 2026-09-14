# SlimInfer Qwen3.6-27B Ascend identity canary

## Decision

The removable SlimInfer plugin reached the real Qwen3.6-27B TP4 model path on
physical Ascend 910B4 NPU4-7 and was output-transparent in identity mode.

This is an **integration gate pass**, not a SlimInfer algorithm, performance,
or accuracy result. No token pruning was active.

## Frozen identity

- Model: `/cache/efim/Qwen3.6-27B`
- Image: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`
- vLLM-Ascend reference: `5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`
- Tensor parallel degree: 4
- Host devices: physical NPU4, NPU5, NPU6, NPU7
- Container devices: logical NPU0, NPU1, NPU2, NPU3
- Runtime mode: eager, max model length 4096, prefix cache disabled
- Only treatment switch: `MST_SLIMINFER_ENABLE=1` versus `0`

The small eager configuration was selected for correctness and activation
evidence. It is not the formal HYPIC-equivalent performance ruler.

## Accepted evidence

The enabled run owned host worker PIDs 1504637-1504640 on physical NPU4-7.
The disabled run owned host worker PIDs 1599229-1599232 on physical NPU4-7.
Docker PID and host `npu-smi` PID intersections proved ownership.

All four enabled ranks installed the wrapper around
`vllm.model_executor.models.qwen3_5.Qwen3_5Model.forward`. The inherited
implementation resolved to `Qwen3NextModel.forward` at:

`/vllm-workspace/vllm/vllm/model_executor/models/qwen3_next.py`

Source SHA256:

`8d614ce262ab9340585f9a2ad4ab117228f076e3672fcb5f04930ff0a38223ae`

The first one-shot forward events were emitted during engine warmup. They prove
rank-local patch entry, while the later HTTP 200 proves an actual service
request; the evidence does not pretend the one-shot event was request-tagged.

Both serial arms used:

- prompt: `The capital of France is`
- `max_tokens=4`
- `temperature=0`
- `seed=0`

Both returned:

- text: ` Paris.\n\n<think>`
- prompt/completion/total tokens: 5/4/9
- finish reason: `length`
- system fingerprint: `vllm-0.23.0-tp4-39e8812e`

The API returned null token-ID fields. The accepted claim is exact text and
metadata parity, not token-ID parity. The disabled arm produced no SlimInfer
runtime evidence file.

## Preserved failures and corrections

1. `VLLM_PLUGINS=sliminfer_ascend` filtered out the required Ascend platform
   plugin and caused device inference to fail. The corrected list is
   `ascend,sliminfer_ascend`.
2. An early launch was stopped when processes appeared on NPU0-3 before their
   ownership was known. It was not restarted.
3. A single-card negative probe confirmed that host ID 4 is invalid after
   remapping host4 to container logical0.
4. Single-card and full-TP positive probes then proved that container logical
   IDs 0-3 allocate on host physical NPU4-7.
5. A later unrelated process appeared on NPU0 while the accepted SlimInfer
   workers remained on NPU4-7, confirming that PID ownership is the correct
   attribution gate.

No output was overwritten and failed attempts remain in the artifact root.

## Artifact ledger

Root:

`/cache/cch/sliminfer-qwen36-ascend-tp4-20260914`

- `device-mapping-proof.json`:
  `d0b4d0994244769821bb4e5d500ab0a990c1de7b570e0fe425722594ff880e90`
- `identity-canary/attempt-summary.json`:
  `a3cc16aef6a5c0d99e1351a4e980267ac2f83024c9c7b1f48fd74e1b1905f51a`
- `identity-canary/enabled-verified/runtime.jsonl`:
  `753d192e8347ac4096e237ad11f95bd955dcc8b96f7598e3d11bb3582800b4ab`
- `identity-canary/enabled-verified/response.json`:
  `dfb1f85001b2e3297a1d43b774ad1eee92c69a787f3cd55dbd191b91b2dd547d`
- `identity-canary/enabled-verified/gate-summary.json`:
  `638941f590d98ccafc3968582d41a4ff258d603c1ab4112c277ce63952f232f7`
- `identity-canary/disabled-verified-v1/response.json`:
  `b59b587fde8c86f2aecf615f992f0602c1250b17d246821040a1df9e5f9fdaf0`
- `identity-canary/identity-parity.json`:
  `32c73aaeaefa0f261219fcc183363e94e554b2913a298eb685aeab21f0f460d3`

Both accepted service containers are stopped. A post-stop check found no
running process on any NPU.

## Next gate

Implement one bounded semantic pruning canary for a complete prompt only:

1. keep absolute positions for RoPE;
2. maintain compact positions and physical slots for full-attention KV;
3. keep request-local layer metadata and identical TP selection digests;
4. preserve Qwen3.6 GDN recurrent-state semantics;
5. reject partial, resumed, or chunked prompt prefill until implemented;
6. compare dense and pruned NPU tensors/states for finiteness and declared
   tolerances before any endpoint performance screen.

Only a semantic canary that passes these numerical gates may advance to the
HYPIC-equivalent 32768-input, 1024-output performance ruler.
