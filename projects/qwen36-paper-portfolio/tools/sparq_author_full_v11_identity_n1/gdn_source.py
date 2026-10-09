"""Exact MAIN-copied public dependency bindings; no bootstrap at import."""
import importlib
import evidence as c
PINS={
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/MANIFEST.json": "2287ff93333612616c3f552e9137693c4995ea27d206f82dac5a45009bf6c502",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/gdn.py": "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/patch_qwen3_5.py": "21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/qwen_gdn_linear_attn.py": "885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/mamba_utils.py": "1d854c36fe1b32cfacd071393c05fc155f37190fe19afc5e6c02d5d0a2d561f3",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/mamba_abstract.py": "d7cba061c9d8c55b00e18bc7af515cfd28d875eee76c04fea7f6861f2d1c4e08",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/gdn_attn_builder.py": "42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16"
}
RUNTIME_PINS={
 "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py": "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
 "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py": "21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3",
 "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py": "885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0",
 "/vllm-workspace/vllm/vllm/v1/worker/mamba_utils.py": "1d854c36fe1b32cfacd071393c05fc155f37190fe19afc5e6c02d5d0a2d561f3",
 "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/abstract.py": "d7cba061c9d8c55b00e18bc7af515cfd28d875eee76c04fea7f6861f2d1c4e08",
 "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py": "42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16"
}
def sources():
 for path,digest in PINS.items():c.bound(path,digest)
 return dict(PINS)
def runtime():
 sources()
 for path,digest in RUNTIME_PINS.items():c.bound(path,digest)
 # Existing bridge has already initialized vllm_ascend.ops before this point.
 return dict(gdn=importlib.import_module("vllm_ascend.ops.gdn"),
  builder=importlib.import_module("vllm_ascend.ops.gdn_attn_builder"))
