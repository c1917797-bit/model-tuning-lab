"""Independent convolution-boundary stitching for same projected segment input.
This does not establish equality of hidden inputs across different contexts.
"""
import torch
from independent_c2_reference import causal_conv_reference
def stitch_conv_boundary(projected_segment,public_conv_output,weights,incoming_tail,*,bias=None,activation=None):
    length=projected_segment.shape[0];width=weights.shape[1]
    if public_conv_output.shape!=projected_segment.shape:
        raise ValueError("cached output shape mismatch")
    if length<width-1:
        raise ValueError("short segment requires complete live computation")
    warmup=width-1
    private=public_conv_output.clone()
    if warmup:
        corrected,_=causal_conv_reference(projected_segment[:warmup],weights,incoming_tail,bias,activation)
        private[:warmup]=corrected
        next_tail=projected_segment[-warmup:].float().clone()
    else:
        next_tail=projected_segment[:0].float().clone()
    return private,next_tail,warmup
