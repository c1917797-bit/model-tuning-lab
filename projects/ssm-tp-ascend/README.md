# SSM TP Ascend

Opt-in plugin workstream for arXiv:2602.21144 on Qwen3.6-27B and
vLLM-Ascend.  Version 0.1 contains only a fail-closed production-path probe.
It does not change tensor values, collective selection, or scheduling.

Enable it with:

```text
VLLM_PLUGINS=ascend,ssm_tp_ascend
VLLM_ASCEND_SSM_TP_PROBE_ENABLE=1
VLLM_ASCEND_SSM_TP_EVIDENCE_FILE=/results/evidence.jsonl
```

The probe records the actual GDN row-parallel implementation selected during
model construction and bounded runtime samples containing input, output and
weight dtype/shape/device information.  Formal performance runs must disable
the probe.
