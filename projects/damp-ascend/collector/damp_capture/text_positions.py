"""Source-bound pure-text position/sequence metadata proof; no model imports."""
from .contract import require

TEXT_METADATA_SOURCES = {
    "/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py": "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
    "/vllm-workspace/vllm/vllm/v1/worker/gpu_input_batch.py": "caeeb20f5010d74663c45f9419237191e3c0a149f4c7aa25bc1b73b1112d67ae",
    "/vllm-workspace/vllm/vllm/model_executor/models/qwen3_5.py": "04f3de5372973770d71c5c05f2e8a5e221ec52b62cca7a1e302d9201b61b8adc",
    "/vllm-workspace/vllm/vllm/model_executor/models/qwen3_vl.py": "2935e09be47a893f09176cddb1beb6ed2e73666459de2bfbb08aca50b3e08969",
    "/vllm-workspace/vllm/vllm/model_executor/layers/rotary_embedding/mrope.py": "d5fc5ca640bf47fdfc27447bcc6b67b2294c9ac840bbc736fe75cc6098e2a51c",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py": "42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16",
}


def _ints(values, name):
    require(isinstance(values, (list, tuple)) and
            all(type(v) is int and v >= 0 for v in values), name + " must be nonnegative integer metadata")
    return tuple(values)


def ordered_text_positions(starts, computed, actual_tokens):
    starts, computed = _ints(starts, "query starts"), _ints(computed, "computed tokens")
    require(computed and len(starts) == len(computed) + 1 and starts[0] == 0 and
            type(actual_tokens) is int and actual_tokens > 0 and starts[-1] == actual_tokens,
            "CPU scheduling metadata cardinality/token count mismatch")
    require(all(b > a for a, b in zip(starts, starts[1:])), "empty/nonmonotone scheduled request")
    return tuple(p for a, b, c in zip(starts, starts[1:], computed) for p in range(c, c + b - a))


def text_axis(values, expected, uses_mrope):
    """Select row0 only AFTER exact three-row equality and CPU timeline proof."""
    expected = _ints(expected, "expected text axis")
    require(expected and type(uses_mrope) is bool, "unproven position mode")
    if uses_mrope:
        require(isinstance(values, (list, tuple)) and len(values) == 3,
                "only the source-proven 3-row MRoPE branch is supported")
        rows = tuple(_ints(row, "MRoPE row") for row in values)
        require(rows[0] == rows[1] == rows[2] == expected,
                "MRoPE rows differ or do not match ordered pure-text time axis")
        return rows[0]
    row = _ints(values, "1D text positions")
    require(row == expected, "1D positions do not match ordered text time axis")
    return row


def text_request(prompt_len, mm_features, prompt_embeds, token_mask,
                 uses_mrope, delta, prompt_positions=None):
    require(type(prompt_len) is int and prompt_len > 0, "empty/non-token prompt unsupported")
    require(isinstance(mm_features, list) and not mm_features and prompt_embeds is None,
            "multimodal or prompt-embedding request unsupported, even if positions broadcast")
    require(token_mask is None or (isinstance(token_mask, list) and len(token_mask) == prompt_len and
                                  all(type(v) is bool and v for v in token_mask)),
            "mixed prompt-token/embedding mask unsupported")
    if uses_mrope:
        require(type(delta) is int and delta == 0, "pure-text MRoPE requires zero position delta")
        if prompt_positions is not None:
            text_axis(prompt_positions, tuple(range(prompt_len)), True)


def decode_lengths(actual, starts, slots, num_decodes):
    """Pinned builder ABI is [start0, diff(start0:startN)], NOT cumulative ends."""
    actual, starts, slots = _ints(actual, "actual_seq_lengths"), _ints(starts, "CPU query starts"), _ints(slots, "decode slots")
    require(type(num_decodes) is int and num_decodes > 0 and len(slots) == num_decodes and
            len(set(slots)) == num_decodes and len(starts) >= num_decodes + 1 and starts[0] == 0,
            "decode request/slot/CPU query cardinality mismatch")
    differences = tuple(b - a for a, b in zip(starts[:num_decodes], starts[1:num_decodes + 1]))
    require(differences == (1,) * num_decodes and actual == (starts[0],) + differences,
            "native one-token decode actual_seq_lengths ABI mismatch")
    return actual
