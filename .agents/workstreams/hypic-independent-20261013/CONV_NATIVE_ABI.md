# Official convolution ABI source facts

Inspected fixed official image660ce23a gdn.py, ordinary PCP1 prefill path.
Operator: torch.ops._C_ascend.npu_causal_conv1d_custom.
Inputs/output are token-major; conv weights transpose from channels,width to
width,channels. Conv state slot is sequence,state_length,channels (width−1).
Metadata supplies query_start_loc, cache_indices, initial_state_mode;
num_accepted_tokens=None, run_mode=0, activation_mode=1 for SiLU.
Decode run_mode=1 is a distinct path and must not be substituted in Prefill.

Selected27B TP4 projected Q/K/V channels:2560, width4, state_length3.
Next inspect metadata initial-state enum and index dtypes before device call;
do not guess zero/warm initialization. Canonical reference state is3,channels.
Source inspection is not a device ABI or numerical pass.
