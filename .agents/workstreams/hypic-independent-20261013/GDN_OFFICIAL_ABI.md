# Official GDN bridge evidence

Fixed official image660ce23a; chunk.py SHA256
6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5

Read-only no-network/no-device image inspection confirms:
- chunk_gated_delta_rule inputs are BF16 B,T,H,D; g is log-space.
- initial/final state is N,H,K,V. Native service SSM slots require transpose.
- wrapper optionally normalizes keys/queries; bridge enables it consistently.
- forward requires get_forward_context() and initialized PCP group even at PCP1.
- chunk size64, natural exp (use_exp2=False); AscendC state layout is key-major.
- returned final_state comes from official chunk_gated_delta_rule_fwd_h;
  output projection uses chunk_fwd_o, also official unchanged primitives.
- public bridge calls the primitive twice: zero initial with actual V for S,
  identity initial with zero V for T. Grouped keys are explicitly expanded.

These are source facts and CPU-adapter evidence, not a device pass. Next device
test must establish actual forward context/PCP1 and compare same BF16 inputs
against independent recurrence, then test composition on nonzero incoming state.
No old HYPIC module, algorithm implementation or scheduling hook is imported.
