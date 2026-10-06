"""CPU-only admission and ownership contract; no framework/device imports."""
from dataclasses import dataclass
from math import prod

GDN_LAYERS = tuple(i for i in range(64) if i % 4 != 3)
PACKED_SHAPES = ((12, 128, 16), (12, 128, 112), (12, 4, 112))
PACKED_DTYPES = ("float16", "int8", "float32")
RECIPROCAL_127_FP32 = 0.007874015718698502

class Unsupported(RuntimeError):
    pass

def require(ok, message):
    if not ok:
        raise Unsupported(message)

def admit_text_request(cached, request_id, prompt_tokens):
    """Pinned CachedRequestState payload proof, never a position-shape inference."""
    fields = ("req_id", "prompt_token_ids", "mm_features", "prompt_embeds", "prompt_is_token_ids")
    require(all(hasattr(cached, name) for name in fields), "request payload schema missing")
    require(cached.req_id == request_id, "cached request identity mismatch")
    tokens = cached.prompt_token_ids
    require(type(prompt_tokens) is int and prompt_tokens > 1 and
            isinstance(tokens, list) and len(tokens) == prompt_tokens,
            "token prompt/CPU prompt length mismatch")
    require(isinstance(cached.mm_features, list) and not cached.mm_features,
            "multimodal request unsupported, even with text-like MRoPE")
    require(cached.prompt_embeds is None, "user prompt embeddings unsupported")
    mask = cached.prompt_is_token_ids
    require(mask is None or (isinstance(mask, list) and len(mask) == prompt_tokens and
                            all(type(value) is bool and value for value in mask)),
            "mixed token/embedding prompt unsupported")

def admit_text_forward(input_ids, inputs_embeds, intermediate_tensors, model_kwargs,
                       supports_mm_inputs, requires_raw_input_tokens=False):
    """Permit native text embeddings on MM-capable Qwen, not supplied soft prompts."""
    require(intermediate_tensors is None, "encoder/PP intermediate inputs unsupported")
    require(isinstance(model_kwargs, dict) and not model_kwargs,
            "encoder/multimodal/unknown model kwargs unsupported")
    require(type(supports_mm_inputs) is bool and type(requires_raw_input_tokens) is bool,
            "unknown model input capability")
    if supports_mm_inputs:
        require(inputs_embeds is not None and
                ((input_ids is not None) if requires_raw_input_tokens else input_ids is None),
                "expected native Qwen text-embedding route")
        return "inputs_embeds"
    require(input_ids is not None and inputs_embeds is None, "expected native token-ID route")
    return "input_ids"

def require_copied_native(target_cls, donor_cls):
    require(getattr(target_cls, "_forward_core", None) is donor_cls._forward_core and
            getattr(target_cls, "forward", None) is donor_cls.forward,
            "actual Qwen GDN does not have frozen Ascend native bindings")

def typed_gdn_target(layer, base_cls, target_cls):
    if not isinstance(layer, base_cls):
        return False
    require(type(layer) is target_cls, "unsupported actual GDN instance class")
    return True

def verify_live_layers(dispatch, layers, target_cls, core, native_forward):
    require(isinstance(dispatch, dict) and len(layers) == len(GDN_LAYERS) and
            {int(layer.layer_idx) for layer in layers.values()} == set(GDN_LAYERS),
            "all 48 actual GDN instances must be registered")
    for name, layer in layers.items():
        actual = dispatch.get(name)
        require(actual is layer and type(actual) is target_cls and actual.prefix == name and
                getattr(getattr(actual, "_forward_core", None), "__func__", None) is core and
                getattr(getattr(actual, "forward", None), "__func__", None) is native_forward,
                "actual custom-op dispatch bypasses DAMP: " + name)
    return tuple(sorted(layers))


def typed_shapes(conv_shape):
    require(tuple(conv_shape) in ((3, 2560), (2560, 3)), "unexpected native conv geometry")
    return (tuple(conv_shape), *PACKED_SHAPES)

def byte_counts(conv_shape, padded_page=None):
    payload = prod(conv_shape) * 2 + sum(prod(s) * z for s, z in zip(PACKED_SHAPES, (2, 1, 4)))
    native = prod(conv_shape) * 2 + 12 * 128 * 128 * 4
    require(padded_page is None or padded_page >= payload, "page padding is smaller than typed payload")
    return {"typed_payload_bytes": payload, "native_payload_bytes": native,
            "allocated_page_bytes": padded_page if padded_page is not None else payload}

@dataclass(frozen=True)
class Row:
    request_id: str
    slot: int
    query_tokens: int
    computed_tokens: int
    prompt_tokens: int

@dataclass(frozen=True)
class Turn:
    mode: str
    rows: tuple
    actual_seq_lengths: tuple

def admit(rows, slots, max_decode_batch=1):
    rows = tuple(rows)
    require(rows and len({r.request_id for r in rows}) == len(rows), "empty/duplicate request identities")
    require(len({r.slot for r in rows}) == len(rows), "duplicate state slots")
    for r in rows:
        require(bool(r.request_id) and 0 <= r.slot < slots, "invalid request identity/slot")
        require(r.query_tokens > 0 and r.computed_tokens >= 0 and r.prompt_tokens > 1, "padding/invalid lengths")
    if all(r.computed_tokens == 0 for r in rows):
        require(len(rows) == 1 and rows[0].query_tokens == rows[0].prompt_tokens,
                "only one complete initial prefill is supported")
        return Turn("prefill", rows, (0, rows[0].query_tokens))
    require(all(r.query_tokens == 1 and r.computed_tokens >= r.prompt_tokens for r in rows),
            "mixed/continuation prefill is unsupported")
    require(len(rows) in (1, 16) and len(rows) <= max_decode_batch,
            "operator requires exact B1/B16; use max_num_seqs=1 for first screen")
    return Turn("decode", rows, (0,) + (1,) * len(rows))

class Ownership:
    """Small CPU identities only. A completed prefill replaces a recycled slot."""
    def __init__(self):
        self.rows = {}
    def check(self, turn):
        if turn.mode == "decode":
            for r in turn.rows:
                require(self.rows.get(r.slot) == (r.request_id, r.computed_tokens),
                        "uninitialized/recycled/stale slot or skipped update")
    def publish(self, turn):
        for r in turn.rows:
            self.rows[r.slot] = (r.request_id, r.computed_tokens + r.query_tokens)
