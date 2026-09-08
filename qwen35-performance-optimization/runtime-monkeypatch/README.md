# Final Qwen3.5 Runtime Monkeypatch

This directory contains the source-overlay-free Python runtime deliverable
that produced the accepted c1 TTFT result:

- TTFT P95: `966.3259 ms` to `505.1956 ms`;
- TTFT reduction: `47.7%` (`1.9128x` speedup);
- TPOT P95: `39.0459 ms` to `32.3098 ms`;
- workload: frozen c1, three repetitions, 96/96 successful requests;
- hardware: four Ascend 910B4 devices with TP4;
- model: Qwen3.5-27B;
- runtime: vLLM-Ascend 0.23.0, MTP disabled.

The file is copied byte-for-byte from the verified workstream implementation
at commit `ebe9b69aad45a24fa79437705f00ebbeed977e55`. Its expected SHA256 is:

```text
9c8e74ae5ba9adaf74628d74c3361d2e8bcb86792ff1d4c54eca00381e1b92a8  sitecustomize.py
```

## Activation

Mount this directory read-only into the unchanged container and prepend the
mount to the container's existing `PYTHONPATH`:

```bash
docker run --rm \
  -v "$PWD/qwen35-performance-optimization/runtime-monkeypatch:/opt/qwen35-final-monkeypatch:ro" \
  -e QWEN35_ASCEND_MONKEYPATCH=1 \
  -e VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=513 \
  -e VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=16384 \
  -e PYTHONPATH="/opt/qwen35-final-monkeypatch:<preserve-the-image-pythonpath>" \
  quay.io/ascend/vllm-ascend:v0.23.0 \
  <the-existing-vllm-command>
```

`sitecustomize.py` is imported automatically by Python. It defers Ascend/vLLM
imports until the relevant worker modules are available, then installs the
compile-range, bounded-MMAR, GDN prefetch, and RMSNorm/graph-fusion hooks.

Do not replace `<preserve-the-image-pythonpath>` with an empty value: retain
the original image's CANN and vLLM Python paths exactly. The maintained
`scripts/run_qwen35_tp4_dev_service.sh` launcher already applies the proven
mount and environment configuration.

## Boundary

This package is accepted for the revised c1 TTFT >=40% improvement criterion.
It is not validated at c5/c8/c16 and is not the async-finalize C++ candidate.
Re-run a same-environment frozen A/B before carrying its performance claim to
different CANN, model, TP, device, or serving configurations.

The package makes no image-layer change: no package installation, vLLM source
overlay, `docker commit`, quantization, retraining, MTP, or speculative
decoding is used.
