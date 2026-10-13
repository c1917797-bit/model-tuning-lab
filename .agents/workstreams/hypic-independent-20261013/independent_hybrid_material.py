"""Request-level independent material contract. Serving attachment is pending."""
from dataclasses import dataclass
from independent_c1_reference import apply_segment
from independent_c2_reference import relocate_keys
@dataclass(frozen=True)
class MaterialIdentity:
    model: str
    code: str
    layer: str
    rank: int
    tokens_sha256: str
    length: int
    boundary_tokens: int
def validate_material(actual,expected):
    if actual!=expected:raise ValueError("model/code/layer/rank/token/boundary identity mismatch")
    if not actual.model or not actual.code or not actual.layer or len(actual.tokens_sha256)!=64:
        raise ValueError("incomplete material identity")
    if actual.rank<0 or actual.length<=actual.boundary_tokens or actual.boundary_tokens<3:
        raise ValueError("invalid segment or live boundary")
def materialize_linear_body(actual,expected,body_affine,live_state_after_boundary):
    validate_material(actual,expected)
    # Caller must execute the current request's boundary before reusing the body.
    return apply_segment(body_affine,live_state_after_boundary)
def materialize_attention_body(actual,expected,public_keys,public_values,old_positions,new_positions,inv_freq):
    validate_material(actual,expected)
    body_len=actual.length-actual.boundary_tokens
    if public_keys.shape[0]!=body_len or public_values.shape[0]!=body_len:
        raise ValueError("cached body token coverage mismatch")
    private_keys=relocate_keys(public_keys,old_positions,new_positions,inv_freq)
    return private_keys,public_values.clone()
