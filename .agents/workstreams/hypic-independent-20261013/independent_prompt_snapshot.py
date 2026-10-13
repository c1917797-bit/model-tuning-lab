"""Immutable prompt token snapshot; embeddings/multimodal are unsupported PIC."""
from types import MappingProxyType
def freeze_prompt_tokens(request_ids,states):
    result={}
    for rid in request_ids:
        state=states[rid]
        if state.prompt_token_ids is None or state.mm_features:
            result[rid]=None
            continue
        tokens=tuple(int(x) for x in state.prompt_token_ids)
        if not tokens or any(x<0 for x in tokens):
            raise ValueError("invalid runtime prompt tokens")
        result[rid]=tokens
    return MappingProxyType(result)
