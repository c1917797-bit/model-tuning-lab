# DUET Ascend Applicability Audit

This project evaluates **DUET: Disaggregated Hybrid Mamba-Transformer LLMs with
Prefill and Decode-Specific Packages** (arXiv:2603.15530) against the fixed
Qwen3.6-27B / Ascend / vLLM-Ascend plugin-delivery target.

Decision: **delivery-boundary no-go**. DUET's claimed gains depend on two new
custom chiplet packages and their memory/interconnect design. The official
repository is an architecture simulator, not deployable Ascend operator or
serving code. No NPU benchmark was launched because it could not activate the
paper mechanism.

See `PIERCING_REPORT.md` and `evidence/applicability-gate.json`.
