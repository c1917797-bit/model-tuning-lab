"""Actual copied-function bind seam, source-only; caller owns full service install."""
import hashlib
import inspect
from pathlib import Path
from .core import require
COPIER="/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py"
COPIER_SHA="21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3"
TARGET="/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py"
TARGET_SHA="885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0"
GDN="/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"
GDN_SHA="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
def bind_receivers(donor,receiver,core,authority,enabled=False):
    require(enabled is True,"continuous receiver binding default OFF")
    authority.require_complete_before_install() # source-bound final plans/pack/unpack/cache lifecycle, not flags
    for path,digest in ((COPIER,COPIER_SHA),(TARGET,TARGET_SHA),(GDN,GDN_SHA)):
        require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,"actual image source drift")
    original=donor._forward_core
    require(receiver._forward_core is original and
            str(Path(inspect.getfile(original)).resolve())==GDN,
            "actual Qwen copied-function alias/native owner drift")
    def wrapped(layer,mixed_qkv,b,a,core_attn_out):
        return core(layer,mixed_qkv,b,a,core_attn_out)
    donor._forward_core=wrapped;receiver._forward_core=wrapped
    # Runner MUST enumerate actual no_compile_layers 48 instances BEFORE call,
    # verify cls/outerforward/native prefix/this function and metadata cardinality.
    # Full original runner/cache allocator install is a separate authority seam;
    # this function cannot claim all48 when it has not observed live instances.
    return wrapped
