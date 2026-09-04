# Qwen3.8 GDN native state-layout operator optimization

- User explicitly requested operator/algorithm changes, not parameter tuning.
- Performance dataset is `/home/mtuser/cch/query_rewrite.jsonl`, source SHA256 `a7a1c93b...b056e`.
- Fixed exact-2048/40 snapshot is `/cache/austinov/eval-data/query_rewrite_2k40.v2.jsonl`, SHA256 `c7568546...4282ca`, 357 requests. Token IDs are byte-for-byte identical to v1; v2 only adds benchmark metadata.
- Implement the state-layout goal through upstream fused GDN prefill algorithm `77d13e2c0`: it replaces chunk_scaled_dot_kkt + solve_tril + recompute_w_u + chunk fwd kernels with `torch_npu.npu_chunk_gated_delta_rule` and consumes/returns the persistent [N,Nv,Dv,Dk] state layout directly.
- Current torch-npu is 2.10.0.post4 and exposes `npu_chunk_gated_delta_rule`. Patch applies cleanly to the v0.23 image.
- Correctness: operator numerical A/B plus end-to-end output equivalence; query_rewrite answers are empty, so it is not a labeled accuracy dataset.
