# BOLE131 repair1: exact installed model patch identity

Source preparation only; no new model, numerical, scheduler or performance PASS.
Original131 source and actual worker-load failure remain unchanged.

First failure was worker_entry.discover full-attention forward, not the
Qwen3_5Model compilation decorator. Actual installed worker patch imports
patch_qwen3_5 (non310p), which assigns:

- Qwen3NextAttention.forward = AscendQwen3NextAttention.forward
- Qwen3_5DecoderLayer.forward = AscendQwen3_5DecoderLayer.forward
- Qwen3_5MultiTokenPredictor.forward = qwen3_5_mtp_forward

This revision requires exact installed patch Ref3, exact module globals,
qualname, function object and actual assignment target identity for these
three roles. It does not unwrap functions or accept unknown replacements.
The unchanged model forward, GDN core, logits, proposer and worker source
checks remain in force. Generic callable source failures now preserve both
expected/actual Ref3 plus module and qualname in the first-fault exception.

Evidence copies include exact worker patch initializer, qwen3_5 patch and
qwen3_next_mtp patch. The last one patches cache binding, not model forward.
Actual Ascend FA fuses split/norm/RoPE before calling self.attn; the hook is
still at native self.attn after that actual fused operation. No math changes.

CPU controls execute the complete actual FA forward with explicit CPU fixture
operands and the actual three assignment AST bodies. They reject an unknown
wrapper, same-source wrong function, overwritten target and altered source pin.
These controls do not execute Ascend kernels or prove model correctness.

New unique source root ends v1-131-repair1; both CPU and model output roots
contain model131repair1. Existing owner, phase3600, cleanup180, RAM, disk,
profile131/C1/3nodes and all independent tensor contracts stay unchanged.
Scheduler publication remains false; the model remains a diagnostic gate.

MAIN sequence: actual component Ref3 bind, immutable source audit, actual
same-image CPU, then fresh independent TP4 admission and model request.
See COMMANDS.json for exact ordered argv. No preceding failed owner is reused.
