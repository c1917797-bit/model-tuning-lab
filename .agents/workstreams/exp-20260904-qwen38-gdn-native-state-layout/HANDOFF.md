# Qwen3.8 GDN native state-layout operator optimization

- User explicitly requested operator/algorithm changes, not parameter tuning.
- Performance dataset is `/home/mtuser/cch/query_rewrite.jsonl`, source SHA256 `a7a1c93b...b056e`.
- Fixed exact-2048/40 snapshot is `/cache/austinov/eval-data/query_rewrite_2k40.v1.jsonl`, SHA256 `fd2670e7...d8d71`, 357 requests.
- Target: eliminate GDN prefill `ssm_state[...] .transpose(-1,-2).contiguous()` and reverse writeback by extending `chunk_gated_delta_rule_fwd_h` to consume/produce the persistent cache native [N,H,V,K] layout.
- Current code already supports discontinuous row stride from upstream commit eef9eba3d, but `transpose_state_layout` is reserved false and final-state store is contiguous [K,V].
- Correctness: operator numerical A/B plus end-to-end output equivalence; query_rewrite answers are empty, so it is not a labeled accuracy dataset.
