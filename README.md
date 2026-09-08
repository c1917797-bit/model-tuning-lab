# Qwen3.5 vLLM-Ascend Runtime Patch

Independent, source-overlay-free runtime patch for Qwen3.5-27B on Ascend
910B4 with vLLM-Ascend 0.23.0.

This repository is deliberately separate from vLLM, vLLM-Ascend,
`ops-transformer-lab`, `model-tuning-lab`, and
`drror_vllm_ascend`. It does not modify any of those repositories or rebuild
the base image.

## Validated result

Frozen c1 protocol, TP4 on physical NPU0-3, three repetitions and 96/96
successful requests:

| Metric | Baseline | Patched | Change |
| --- | ---: | ---: | ---: |
| TTFT P95 | 966.3259 ms | 505.1956 ms | 47.7% lower / 1.9128x |
| TPOT P95 | 39.0459 ms | 32.3098 ms | 17.3% lower / 1.2085x |

The patch is accepted for the revised c1 TTFT reduction threshold of at least
40%. It is not validated at c5/c8/c16 and does not claim a 40% TPOT reduction.

## Quality evidence boundary

The t11 run completed a fixed-input 1/1 smoke and 96/96 benchmark requests
with zero errors and natural EOS. That proves service/request correctness, not
full semantic accuracy. A historical paired gate for the retained GDN fusion
plus gate/up-prefetch stack found 16/16 sampled outputs semantically equivalent
with zero material regressions (11/16 byte-identical and 12/16 identical after
whitespace normalization), but it is not a candidate-specific quality gate for
t11. All 357 dataset `answer` fields are empty, so no reference-answer accuracy
score is available. Before a production quality claim, run the registered
same-runtime 32-sample paired semantic gate and require 32/32 equivalence with
zero material regressions.

## Install and load order

The base container is started first, then this repository is installed as an
editable, dependency-free Python package. The activation variables must be set
before the `vllm serve` Python process starts. A monkeypatch cannot be injected
safely into an already-running worker process.

### 1. Pull the validated base image

```bash
docker pull quay.io/ascend/vllm-ascend:v0.23.0
```

If a registry mirror is required, verify that its image ID and repository
digest match the validated image before using it.

### 2. Create the base container

Only physical NPU0-3 are exposed. NPU4-7 are intentionally absent:

```bash
docker run -itd \
  --name qwen35_vllm_ascend_patch \
  --network host \
  --shm-size=64g \
  --device /dev/davinci0 --device /dev/davinci1 \
  --device /dev/davinci2 --device /dev/davinci3 \
  --device /dev/davinci_manager \
  --device /dev/devmm_svm \
  --device /dev/hisi_hdc \
  -v /usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64:ro \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info:ro \
  -v /etc/ascend_install.info:/etc/ascend_install.info:ro \
  -v /usr/local/dcmi:/usr/local/dcmi:ro \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi:ro \
  -v /cache:/cache \
  quay.io/ascend/vllm-ascend:v0.23.0 \
  bash
```

This does not modify the image. Do not run `docker commit`.

### 3. Install the standalone patch package

Enter the running base container, update this independent repository, and
install it without dependency resolution:

```bash
docker exec -it qwen35_vllm_ascend_patch bash
cd /cache/cch/qwen35-vllm-ascend-patch
git pull --ff-only origin main
python3 -m pip install --no-deps -e .
```

The editable installation exposes the verified top-level `sitecustomize`
module to subsequently started Python processes without copying vLLM or
vLLM-Ascend source. The package uses an offline-friendly setuptools editable
installer and does not download runtime dependencies.

### 4. Activate and start vLLM

Still inside the same container shell:

```bash
export QWEN35_ASCEND_MONKEYPATCH=1
export VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=513
export VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=16384

python3 -m qwen35_vllm_ascend_patch
vllm serve <model-path> --tensor-parallel-size 4 <other-validated-arguments>
```

The self-check must report this repository's `sitecustomize.py`, the expected
SHA256, and `"activation_requested": true`.

For a no-install development fallback, source `load_patch.sh` or run a command
through `run_with_patch.sh`. Those helpers prepend this repository to the
existing `PYTHONPATH` rather than replacing it.

The exact bounded-MMAR gate is:

```text
QWEN35_ASCEND_MONKEYPATCH=1
VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=513
VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=16384
```

Python imports `sitecustomize.py` automatically at interpreter startup. The
patch defers Ascend/vLLM imports until the worker modules become available,
then installs the compile-range, bounded-MMAR, GDN prefetch, RMSNorm, and graph
fusion hooks in every TP worker.

## Integrity

Expected `sitecustomize.py` SHA256:

```text
9c8e74ae5ba9adaf74628d74c3361d2e8bcb86792ff1d4c54eca00381e1b92a8
```

Run the device-free contract test:

```bash
python3 tests/test_contract.py
```

The validated deployment used the unchanged
`quay.io/ascend/vllm-ascend:v0.23.0` image. Installing the editable package
changes only the disposable container writable layer; never use `docker
commit`. Keep the repository on a host mount, preferably read-only for the
serving phase. Re-run the frozen A/B before carrying the performance claim to
different model, CANN, device, TP, or serving configurations.
