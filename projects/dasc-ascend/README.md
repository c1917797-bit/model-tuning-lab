# DASC Ascend Piercing Audit

This project records the terminal audit of **DASC: Decay-Aware State
Compression for Hybrid Linear-Attention Serving** (arXiv:2608.30386) against
the fixed Qwen3.6-27B / Ascend / vLLM-Ascend plugin target.

Decision: **implementation no-go**. The candidate reached the real NPU4-7
cache-hit path and executed its state-lifecycle machinery, but deterministic
replay failed while the dense eager control remained stable. No performance or
GSM8K claim is valid for this candidate.

See `PIERCING_REPORT.md` and `evidence/terminal-audit.json`.
