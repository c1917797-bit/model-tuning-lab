# SlimInfer Qwen3.6 Ascend Runtime Metadata Canary

Date: 2026-09-14

## Outcome

The read-only metadata canary passed on Qwen3.6-27B with TP4 on physical
Ascend NPU4-7. All four workers installed the same wrapper and observed the
same profile, prefill, and decode shapes. The service was stopped after the
two requests and all NPUs returned to an empty process state.

This result proves the live metadata topology needed by future SlimInfer or
Tail-Replay work. It does not activate token pruning or state replay and does
not support a performance or accuracy claim.

## Frozen runtime

- Model: /cache/efim/Qwen3.6-27B
- Image: quay.io/ascend/vllm-ascend:v0.23.0
- Image ID:
  sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1
- Plugin source commit: 945cd6c
- Physical-to-container mapping: NPU4-7 -> logical NPU0-3
- Host worker PIDs: 1933866, 1933867, 1933868, 1933869
- Prefix caching: disabled
- Eager mode: enabled
- Maximum model length and batched tokens: 4096

Docker worker PID intersection with host npu-smi proved that this experiment
used only physical NPU4-7. NPU0-3 were not used by this experiment.

## Requests and observed calls

The first request used 196 prompt tokens and generated one token. The second
used five prompt tokens and generated two tokens so the runtime executed both
prefill and one decode step.

Each rank emitted:

| Call | Runtime role | Hidden shape | Position shape | Tokens/padding |
|---|---|---:|---:|---:|
| 0 | profile warmup | 4096 x 5120 | 3 x 4096 | 4096 / 4096 |
| 1 | real prefill | 196 x 5120 | 3 x 196 | 196 / 196 |
| 2 | real prefill | 5 x 5120 | 3 x 5 | 5 / 8 |
| 3 | real decode | 1 x 5120 | 3 x 1 | 1 / 4 |

The response times include first-run runtime and diagnostic overhead and are
not benchmark measurements.

## Live metadata ownership

The model exposed 64 layer entries but only four distinct attention metadata
objects:

1. One AscendMetadata shared by full-attention layers
   3, 7, 11, ..., 63.
2. One GDNAttentionMetadata shared by GDN layers
   0, 4, 8, ..., 60.
3. One GDNAttentionMetadata shared by GDN layers
   1, 5, 9, ..., 61.
4. One GDNAttentionMetadata shared by GDN layers
   2, 6, 10, ..., 62.

For the 196-token prefill, full attention reported
PrefillNoCache, one prefill, zero decodes, a 196-element NPU slot mapping,
a [1, 36] NPU block table, and a two-element query-start tensor. Each GDN
group reported 196 prefill tokens, one state index, one initial-state flag, a
two-element query-start tensor, a [1, 1] causal-convolution cache-index
tensor, and a [4, 2] chunk-index tensor.

For decode, full attention reported DecodeOnly, zero prefills, one decode,
and a one-element slot mapping. Each GDN group reported zero prefill tokens,
one decode token, one decode request, and a one-element state-index tensor.

The top-level ForwardContext slot mapping contained no layer entries. The
active full-attention slot mapping lived inside the shared AscendMetadata.
Any future implementation that mutates the top-level field would therefore
miss the actual runtime owner.

## Consequences

For SlimInfer, layerwise hidden-state compaction cannot be implemented by
editing one layer-local metadata object. One mutation would affect 16 layers,
and GDN convolution/chunk/state fields would need a coherent compact-token
contract.

For Tail-Replay, the observed repeating groups align with the paper's
full-attention-boundary plus following-GDN structure, but runtime metadata is
shared by relative GDN position across all 16 architectural groups. The first
implementation must therefore keep replay state per request and per layer
while treating metadata updates transactionally for each shared runtime object.

## Direction decision

The user approved pausing broad SlimInfer semantic-pruning work after this
checkpoint and prioritizing Tail-Replay. Tail-Replay directly evaluates
Qwen3.6-27B and matches the HYPIC-style shared-prefix use case, but it remains
a cache-hit TTFT technique. Its paper-level LongBench quality retention is not
strict equality, and no Ascend result exists yet.

The next gate is a 5%/10% Tail-Replay NPU numerical canary that compares
reconstructed GDN state and first-token output with a full-prefix control.

## Artifacts

Artifact root:
/cache/cch/sliminfer-qwen36-ascend-tp4-20260914/metadata-canary

- Aborted startup record:
  v1/attempt-summary.json,
  SHA256 4d242c7a816344595320c9aa45d92b6b2f5e3e3e28ab3ad449721a0ca0c3be25.
- Runtime JSONL:
  v2/runtime.jsonl,
  SHA256 c814d78354f41d1a29420067928afdb3a058c662973223f69be137bc9fb4fc92.
- 196-token response:
  v2/response.json,
  SHA256 d7be5bce6a04f392969ed42991c625c3ca87c00f981f8d105bc412c74b2e96bc.
- Prefill/decode response:
  v2/response-prefill-decode.json,
  SHA256 40065d145ee624e44e59b892cb04e969227d5d054eb9c2949dba970146dc31ba.
- Compact summary:
  v2/summary.json,
  SHA256 afb98737d70c0bfb443ba14abf77b7d8c3f3da6b1f2b77f14ae6af67a560afee.
