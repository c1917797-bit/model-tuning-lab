# EPD-Serve Ascend Piercing

This project records the applicability piercing of arXiv:2601.11590,
"EPD-Serve: A Flexible Multimodal EPD Disaggregation Inference Serving System
On Ascend", against the fixed Qwen3.6-27B text-generation acceptance workload.

The current decision is **rejected for the fixed acceptance target and
four-card resource envelope**. The paper's main benefit requires mixed
multimodal traffic and multiple independently scheduled E/P/D instances. The
formal LongBench-v2, GSM8K, and fixed-output performance workloads are text
only, so they bypass Encode by design, while one Qwen3.6 TP4 instance already
uses all four allowed cards.

See `PIERCING_REPORT.md` and `evidence/applicability-gate.json`.
