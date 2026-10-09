# HYPIC r13 strict-mode source-path triage

Read-only check of the immutable r13 quality pair; no NPU service was started
and no frozen root changed. This narrows one implementation hypothesis rather
than explaining or reclassifying the quality regression.

- The frozen source container snapshot, reconstructed by the r13 controller,
  has `VLLM_ASCEND_HYPIC_TRUE_POSITION_INDEPENDENT=1` in both arms. The
  candidate has `VLLM_ASCEND_HYPIC_ENABLE=1`, control has `=0`; the independent
  quality auditor confirms only enablement and evidence-file path differed.
- The attested `c12060cd47e7575ead059983d7a8bb4704165c98` source rejects
  nonzero-start materialization when strict mode is enabled. Its separate
  `combined_prefill_approximation` path is the non-strict compatibility mode.
- The candidate's hashed `hypic-evidence.jsonl` has 140
  `position_independent_materialization_candidate` events, every one marked
  `producer_kind=zero_start`; none is marked with the non-strict approximation.
  SHA256: `0fff15b2c17a8b9a013dc670cfef87cad824546f6a470bca5659b8c0a60b44ad`.

Thus the non-strict combined-Prefill approximation is **not an observed cause**
of r13's 230/381→219/381 quality loss. This does **not** show that the strict
zero-start material, GDN transition composition, KV relocation, Decode path,
or concurrent scheduler is numerically equivalent to the disabled control.
The original `REJECT_OR_QUALIFY` and strict 368/381 hot `FAIL` stand.

Replay with `python3 -B
.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_r13_strict_mode_path.py`.
The verifier checks the immutable audit and runtime evidence hashes, current
source attestation, inherited service environment, source strict gate, producer
event kinds, and bounded negative verdict. Next work should compare exact
same-source worker tensors/logits on a newly frozen one-variable canary before
another full quality pair; it must not rerun or rejudge r13.
