# Sparse Prefix Caching Ascend piercing report

## Decision

- Paper: arXiv:2605.05219, Sparse Prefix Caching for Hybrid and Recurrent LLM Serving.
- Target: Qwen3.6-27B, vLLM/vLLM-Ascend 0.23.0, CANN 9.1, TP4, physical NPU4-7.
- Scope: plugin/monkeypatch integration without modifying upstream runtime.
- Decision: **rejected for the v0.23 thin-adapter implementation path**.
- Paper-level decision: **re-entered with a deeper plugin-owned atomic
  coexistence adapter; NPU correctness remains pending**.
- Performance and accuracy: not measured because the correctness/runtime gate
  failed before a complete generation.

## Mechanism contract

The official implementation keeps full-attention KV available normally and
stores recurrent/GDN states only at distribution-aware sparse checkpoints. On a
hit it restores the deepest recurrent checkpoint no later than the matched
prefix and recomputes the remaining gap.

The plugin implements the placement DP and an immutable fail-closed plan. It
does not claim that changing HYPIC's segment candidate list alone implements the
paper's storage lifecycle.

## NPU evidence

The native hybrid prefix-cache runtime changed the full-attention block size to
1536 tokens. A plan computed at block size 128 was therefore retired before
traffic. Recomputing the same overlap histogram at the live block size produced:

- overlap depths: 2048 x2, 4096 x6, 8192 x18;
- checkpoint budget: 2;
- maximum length: 9216;
- selected positions: 3072 and 7680;
- plan SHA256: `88c272a92f36f21c8b7fad0e31981ff0c170660390ff2bb874fe3e9614533e60`.

On physical NPU4-7, evidence then recorded
`sparse_prefix_candidates_selected` with runtime block size 1536 and selected
positions `[7680, 3072]`. This proves that the live scheduler invoked the
plugin policy; plugin import or plan-load evidence alone was not accepted.

The next scheduler step terminated with:

> HYPIC exact-prefix replay is incompatible with vLLM native prefix caching ...

Source inspection showed that the guard is unconditional on
`kv_cache_manager.enable_caching`; despite the error text mentioning async
mode, disabling async scheduling cannot change the predicate. That deterministic
rerun was therefore cancelled before model startup completed.

## Why this is a no-go

1. True position-independent HYPIC bypasses the cumulative-prefix checkpoint
   selection hook, so it cannot host the paper's checkpoint policy.
2. Cumulative HYPIC requires native position-dependent prefix caching for the
   paper's dense attention-KV contract.
3. In v0.23, cumulative HYPIC rejects native prefix caching before
   materialization because blocks can be published before recurrent state is
   repaired.
4. HYPIC's material store validates both full-attention KV and GDN state for
   each segment. Reusing it directly duplicates a lifecycle the paper keeps
   separate.

Crossing this boundary requires a runtime-level atomic protocol, not another
placement-policy patch. Continuing inside the one-day paper budget would no
longer be a thin plugin adaptation and would displace higher-ranked queued
papers.

## Preserved artifacts

Artifacts remain outside Git under:
`/cache/cch/sparse-prefix-qwen36-npu4-7-20260920`.

Important files:

- `distribution-plan-align1536.json`
- `candidate-cumulative-align1536.hypic-evidence.jsonl`
- `candidate-cumulative-align1536-async-incompatible-docker-json.log`
- `candidate-cumulative-nonstrict-block128-mismatch-docker-json.log`
- `candidate-cumulative-strict-startup-docker-json.log`

No credentials, model data, or large runtime logs are committed.

## Future re-entry gate

Reopen only if a target runtime exposes or safely permits all of:

1. full-attention KV publication independent of recurrent-state readiness;
2. GDN checkpoint commit after every required layer/state is complete;
3. lookup of the deepest checkpoint not exceeding the matched prefix;
4. rollback or recomputation when GDN materialization fails;
5. explicit cache identity covering model, adapter, dtype, TP layout, CANN and
   operator implementation.

After that, rerun NPU multi-step correctness before any throughput comparison.

## Re-entry implementation

The v0.2 plugin now supplies the missing bounded protocol without modifying
upstream source:

1. native vLLM remains the sole owner of full-attention KV;
2. HYPIC remains the sole owner of transactional GDN/conv material;
3. a waiting request is predicted as a hit only after HYPIC reports the
   recurrent checkpoint ready;
4. the plugin bounds the native block-hash lookup to that exact checkpoint;
5. a native KV hit at any different depth fails closed;
6. the existing HYPIC scheduler verifies the computed-token boundary and
   attaches its normal recurrent restore plan.

The adapter is pinned to the reviewed HYPIC v0.8.5 scheduler SHA256. Ten
software tests pass. Real NPU correctness, performance and accuracy evidence
have not yet been produced.
