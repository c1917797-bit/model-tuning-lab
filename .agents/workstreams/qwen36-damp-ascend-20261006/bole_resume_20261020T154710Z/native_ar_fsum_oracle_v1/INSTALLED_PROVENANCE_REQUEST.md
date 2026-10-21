# Exact installed operator provenance still required

This is a source-only follow-up request. It is **not** a prerequisite for running the independent CPU arithmetic control, and it grants no NPU or model admission. No stopped-container exec, import, model replay or broad source exemption is requested. MAIN can copy ordinary files read-only from the same stopped AR image, record the CID/image/resolved installed path and complete bytes/SHA, and retain missing paths as explicit missing observations.

Known actual TorchNPU evidence already exists in `g1_review_v2/torch_npu_version_sources_v1`: `version.py` 86B SHA f11e02e3acade31a81657136784872a1d70e2f232cab0ef19d3a605aec47424d reports `2.10.0.post4`, git commit `5dd8ef3f9b375b5ae4a83538d5785754148c3302`; METADATA 21313B SHA f2de008970f546dd403999c04c0a892fd30e6dea3e7e13c1fc5b4dddede8ee49 requires torch 2.10.0. Its embedded older version table is not proof of the actual CANN installation or exact dispatch implementation. The actual dispatcher schema and actual 13 explicit FIA kwargs are already preserved in all captured frames.

Known installed Python source to request: `/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/__init__.py`. It can show binding/export provenance but does not itself prove the implementation in native shared libraries.

The following are **conventional candidate paths to check, not observed existing paths**. Record resolved path and package version only from actual copied bytes; do not manufacture a Ref for a missing file or identify a binary solely from a path prefix:

| Candidate installed path | Purpose |
|---|---|
| `/usr/local/Ascend/ascend-toolkit/latest/version.cfg` | toolkit version/build metadata |
| `/usr/local/Ascend/ascend-toolkit/latest/version.info` | alternative toolkit metadata |
| `/usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/ascend_toolkit_install.info` | architecture/package metadata |
| `/usr/local/Ascend/ascend-toolkit/latest/opp/version.info` | operator package metadata |
| `/usr/local/Ascend/ascend-toolkit/latest/opp/ascend_opp_install.info` | alternative operator metadata |
| `/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/lib/libtorch_npu.so` | installed TorchNPU native binding identity |
| `/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/lib/libop_plugin.so` | installed op-plugin identity if separately present |
| `/usr/local/Ascend/ascend-toolkit/latest/lib64/libopapi.so` | CANN op API identity if present |

If the wheel/toolkit contains a source or build manifest mapping these native binaries to an exact op-plugin commit and exact FIA/IFA kernel build, that manifest is preferable to a release-name assumption. Public source at a nearby branch is advisory until joined to installed binary/build metadata. In any future MAIN-owned admitted singleton replay, record loaded library paths/build IDs from the actual process maps, actual dispatcher schema, exact TorchNPU exported callable and actual device/operator environment. A stopped-image file proves bytes present in the image, not which library a future process loads.

## Official primary documentation reviewed

Official TorchNPU FIA API: https://www.hiascend.com/document/detail/en/Pytorch/2610/apiref/customapi/docs/en/custom_APIs/torch_npu/torch_npu-npu_fused_infer_attention_score.md

Reviewed 2026-10-21. It documents q-length-one dispatch to IncreFlashAttention, a softmax(QK scale)V formula and BF16 support. It states that `inner_precise` 0/1 do not distinguish high precision from high performance for BF16; setting 1 is not an established repair. Its current TND D constraints do not establish support for this actual D256 call. This newer document cannot silently be treated as the exact installed CANN9.1 contract.

CANN9.1-beta3 official URLs attempted:

- https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/910beta3/API/aolapi/context/ops-transformer/aclnnFusedInferAttentionScore.md
- https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/910beta3/API/aolapi/context/ops-transformer/aclnnFusedInferAttentionScoreV5.md
- https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/910beta3/API/aolapi/context/ops-transformer/aclnnIncreFlashAttentionV4.md

The retrieval returned navigation-only pages, inconsistent titles or a timeout. Search snippets are insufficient to close the exact version/shape/dispatch gate. Public Ascend/pytorch commit/submodule source retrieval was also unavailable. Exact installed CANN version and corresponding version-specific primary implementation/contract join remain pending.

## Smallest future same-operator replay design, advisory only

Actual all128 metadata has identical BF16 K/V shape `[4584,128,256]`, stride `[32768,256,1]`, K storage offset 2933760 and V offset 153142272; both share a storage. Q shape/stride is `[1,6,256]`/`[1536,256,1]`, offset0. Original tables are one `[1,36]` int32 row, either pages12..23 then24zeros or pages60..71 then24zeros, 64 frames each. Original valid KV length is132. The saved raw contains all valid132 K/V values, not every unused arena value.

After independent CPU arithmetic control and real installed ABI/source admission, MAIN may prepare a separate defaultOFF singleton operator replay for **all128 frames**, no model load. Preserve all13 explicit kwargs, masks, table values/width, original q/k/v dtype and precision policy. A private same-shape shared storage can reproduce the exact view offsets/strides; place captured valid132 K/V at the recorded table-selected positions and verify bytes before call. Unobserved unused storage is a declared reconstruction, not original captured memory. Report this limitation explicitly.

Preregister two finite unused-storage fillings while preserving every valid operand: zero and a deterministic finite alternating pattern. Compare both replay outputs to the captured output, unchanged FP32/FP64 oracle and each other; retain all results and failures. This tests sensitivity to supposedly ignored cache/tail positions and helps distinguish an ABI/valid-length problem from reproducible kernel arithmetic. It does not by itself prove the internal stage responsible. Do not change `inner_precise`, cast to FP16, change layout, mask, scale or tolerance, substitute a new kernel or call a modified runtime path under the original identity. No code for that NPU replay or owner is included/admitted here.
