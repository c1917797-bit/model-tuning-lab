"""Experimental eager/compile hook candidate; disabled unless explicitly installed.

Not a validated graph integration. Install before compilation only, never on a
serving model. Verify graph dispatch and numerical equivalence before E2E use.
"""


def install(model_instance, *, enabled=False, ratio=0.1, include_linear=False):
    if not enabled:
        return []
    if not 0 < ratio <= 1:
        raise ValueError("ratio must be in (0, 1]")
    text = getattr(model_instance, "language_model", model_instance)
    backbone = text.model
    plans = []
    for layer in backbone.layers:
        kind = getattr(layer, "layer_type", None)
        if kind == "full_attention":
            projection = layer.self_attn.o_proj
        elif kind == "linear_attention" and include_linear:
            projection = layer.linear_attn.out_proj
        else:
            continue
        weight = layer.mlp.gate_up_proj.weight
        if str(weight.dtype) != "torch.bfloat16":
            raise ValueError("candidate only supports BF16 weights")
        size = min(int(weight.numel() * weight.element_size() * ratio), 18 * 1024 * 1024)
        if size <= 0:
            raise ValueError("empty prefetch range")
        plans.append((projection, weight, size))
    if not plans:
        raise ValueError("no eligible attention output projections")
    import torch_npu
    handles = []
    try:
        for projection, weight, size in plans:
            def hook(module, inputs, output, weight=weight, size=size):
                dependency = output[0] if isinstance(output, tuple) else output
                if dependency.ndim == 2 and 0 < dependency.shape[0] < 500:
                    torch_npu.npu_prefetch(weight, dependency, size, 0)
                # None leaves the projection output untouched.
                return None
            handles.append(projection.register_forward_hook(hook))
    except Exception:
        for handle in handles:
            handle.remove()
        raise
    return handles
