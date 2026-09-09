"""Candidate-only target resolution; does not enable or execute prefetch."""
import re


def resolve_gateup_weight(model_instance, prefix):
    match = re.fullmatch(
        r"(?:language_model\.)?model\.layers\.(\d+)\.(self_attn\.o_proj|linear_attn\.out_proj)",
        prefix,
    )
    if match is None:
        raise ValueError("not a supported attention output projection")
    text_model = getattr(model_instance, "language_model", model_instance)
    backbone = getattr(text_model, "model", None)
    if backbone is None or not hasattr(backbone, "layers"):
        raise ValueError("missing text backbone layers")
    index = int(match.group(1))
    start = getattr(backbone, "start_layer", 0)
    end = getattr(backbone, "end_layer", len(backbone.layers))
    if not start <= index < end:
        raise ValueError("layer outside local pipeline partition")
    layer = backbone.layers[index]
    expected = "linear_attention" if match.group(2).startswith("linear_attn") else "full_attention"
    if getattr(layer, "layer_type", None) != expected:
        raise ValueError("projection prefix disagrees with layer type")
    return layer.mlp.gate_up_proj.weight
