"""Independent C1 boundary + affine-body reuse, with explicit approximate outputs."""
from dataclasses import dataclass
import torch
from independent_c1_reference import apply_segment
from independent_hybrid_material import validate_material
@dataclass(frozen=True)
class LinearPublicBody:
    identity: object
    affine: object
    core_outputs: torch.Tensor
    conv_tail: torch.Tensor

def reuse_linear_segment(material,expected,initial_state,boundary_runner):
    """Run live boundary then compose cached body. No native slots are mutated.
    boundary_runner consumes this request's live projected boundary and incoming
    conv/SSM state via its closure; returns [boundary,Hv,Dv] outputs and key-major
    [Hv,Dk,Dv] state. Cached core body is an intentional PIC approximation, not
    an exact-output assertion. Quality must be evaluated separately.
    """
    validate_material(material.identity,expected)
    body_tokens=expected.length-expected.boundary_tokens
    if material.core_outputs.ndim!=3 or material.core_outputs.shape[0]!=body_tokens:
        raise ValueError("public core output coverage mismatch")
    if initial_state.shape!=material.affine.zero_state.shape:
        raise ValueError("incoming state orientation/shape mismatch")
    if material.conv_tail.ndim!=2 or material.conv_tail.shape[0]!=3:
        raise ValueError("this selected model requires width4 convolution")
    # Do not mutate native cache or public storage before live boundary succeeds.
    boundary_outputs,state_after_boundary=boundary_runner(initial_state.clone())
    if boundary_outputs.shape!=(expected.boundary_tokens,*material.core_outputs.shape[1:]):
        raise ValueError("live core boundary output coverage mismatch")
    if state_after_boundary.shape!=initial_state.shape:
        raise ValueError("live boundary state shape mismatch")
    if boundary_outputs.device!=material.core_outputs.device:
        raise ValueError("live/public output device mismatch")
    final_state=apply_segment(material.affine,state_after_boundary)
    output=torch.cat((boundary_outputs,material.core_outputs.clone()),dim=0)
    return output,final_state,material.conv_tail.clone()
