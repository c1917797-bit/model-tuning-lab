# Qwen3.5 vLLM-Ascend Runtime Patch

Independent, source-overlay-free runtime patch for Qwen3.5-27B on Ascend
910B4 with vLLM-Ascend 0.23.0.

This repository is deliberately separate from vLLM, vLLM-Ascend,
`ops-transformer-lab`, `model-tuning-lab`, and
`drror_vllm_ascend`. It does not modify any of those repositories or rebuild
the base image.

## Validated result

This branch now packages the current t12/GDN runtime patch bytes from
`model-tuning-lab`. It is not a final promoted candidate yet: live standalone
activation, c1/c5/c8/c16 x3 performance, and all-357 paired quality validation
are still pending.

Fresh operator evidence confirms the core TTFT-side primitive still works in
the current environment:

| Scope | Result |
| --- | ---: |
| GDN qkvz+ba projection fusion geomean | 2.9509x |
| Correctness | all checked rows passed |
| Artifact | `/cache/austinov/qwen35-gdn-projection-fusion-fresh-20260909T104335Z` |

This is a single-NPU operator microbenchmark, not an end-to-end serving claim.

## Quality evidence boundary

The current package has device-free source/behavioral contracts and operator
correctness evidence. It does not yet have standalone live activation or a full
same-runtime semantic gate. Before a production quality claim, run the
registered 32-sample canary and then the all-357 paired quality gate with zero
material regressions. All 357 dataset `answer` fields are empty, so the claim is
bounded to paired no-regression on this workload rather than external answer
accuracy.

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
git pull --ff-only origin feature/qwen35-validated-runtime-patch
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
export VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1

python3 -m qwen35_vllm_ascend_patch
vllm serve <model-path> --tensor-parallel-size 4 <other-validated-arguments>
```

The self-check must report this repository's `sitecustomize.py`, the expected
SHA256, and `"activation_requested": true`.

For a no-install development fallback, source `load_patch.sh` or run a command
through `run_with_patch.sh`. Those helpers prepend this repository to the
existing `PYTHONPATH` rather than replacing it.

The exact GDN-fusion activation gate is:

```text
QWEN35_ASCEND_MONKEYPATCH=1
VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS=1
```

Python imports `sitecustomize.py` automatically at interpreter startup. The
patch defers Ascend/vLLM imports until the worker modules become available,
then installs GDN projection-fusion, fused weight mapping, Ascend-forward,
prefetch, and RMSNorm postprocess hooks in every TP worker.

## Integrity

Expected `sitecustomize.py` SHA256:

```text
aaa4f27c244d68b6f628325b521d703abde0f05973459b1f4517d1fad1cabe1b
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
