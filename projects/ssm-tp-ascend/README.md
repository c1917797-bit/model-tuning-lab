# SSM Tensor Parallelism on Ascend

This project records the applicability piercing of arXiv:2602.21144,
"Scaling State-Space Models on Multiple GPUs with Tensor Parallelism", against
Qwen3.6-27B on vLLM/vLLM-Ascend v0.23 and Ascend 910B4 TP4.

The current decision is **rejected for this target**. The current stack already
implements channel-local GDN projections, convolution/recurrent-state sharding,
and a RowParallel output boundary. The paper's remaining FP32-to-FP16 AllReduce
quantization does not reduce the payload of the live BF16 service.

See `PIERCING_REPORT.md` and `evidence/applicability-gate.json` for the scoped
evidence. This is not a claim that tensor parallelism is unhelpful for an
unsharded SSM runtime; it is a no-go for adding this paper as a new plugin
optimization to the already-TP4 Qwen3.6 target.
