"""Independent public C1 body producer from canonical public native tensors."""
from independent_hybrid_material import validate_material
from independent_c1_official_bridge import official_segment_affine
from independent_linear_reuse import LinearPublicBody

def build_linear_public_body(identity,keys,values,log_decay,beta,core_outputs,
                             projected_segment,*,state_runner):
    """Inputs must originate from one canonical public segment, not a relocated
    private request. Source/request identity is enforced by serving caller.
    This builds only the body after the live boundary; no old HYPIC code.
    """
    validate_material(identity,identity)
    length=identity.length;cut=identity.boundary_tokens
    if keys.ndim!=4 or values.ndim!=4 or keys.shape[:2]!=(1,length) or values.shape[:2]!=(1,length):
        raise ValueError("canonical public key/value coverage mismatch")
    if log_decay.shape[:2]!=(1,length) or beta.shape!=log_decay.shape:
        raise ValueError("canonical public gate coverage mismatch")
    if core_outputs.shape!=(1,length,values.shape[2],values.shape[3]):
        raise ValueError("canonical public core output coverage mismatch")
    if projected_segment.ndim!=2 or projected_segment.shape[0]!=length:
        raise ValueError("canonical public convolution input coverage mismatch")
    affine=official_segment_affine(state_runner,keys[:,cut:].contiguous(),
                                   values[:,cut:].contiguous(),
                                   log_decay[:,cut:].contiguous(),
                                   beta[:,cut:].contiguous())
    return LinearPublicBody(identity,affine,core_outputs[0,cut:].detach().clone(),
                            projected_segment[-3:].detach().float().clone())

def build_native_linear_public_body(identity,keys,values,log_decay,beta,
                                   core_outputs,projected_segment):
    from independent_c1_state_only import official_state_only
    return build_linear_public_body(identity,keys,values,log_decay,beta,
                                    core_outputs,projected_segment,
                                    state_runner=official_state_only)
