# Qwen3.5 t12 Runtime Monkeypatch Candidate

This directory contains a source-overlay-free Python candidate for the
unchanged vLLM-Ascend 0.23.0 image. It is not the final commercial performance
deliverable: offline installation and contract tests pass, and live activation
plus smoke passed on physical NPU0-3, but the c1/32 fail-fast performance gate
missed the current TTFT >=40% and TPOT >=20% targets.

The candidate installs five coordinated runtime changes:

- fused Qwen3.5 GDN qkvz/ba projection construction;
- six-way checkpoint weight mapping into the fused projection;
- Ascend GDN forward consumption of the fused outputs;
- linear-attention gate/up weight prefetch;
- Gemma RMSNorm prefetch postprocessing.

The rejected bounded-MMAR fallback from historical t11 is not present in t12.
The base runtime's ordinary MMAR remains enabled. The expected
sitecustomize.py SHA256 is:

    aaa4f27c244d68b6f628325b521d703abde0f05973459b1f4517d1fad1cabe1b

## Editable installation

Run this before starting vLLM workers:

    cd /path/to/runtime-monkeypatch
    ./install_editable.sh
    source ./load_patch.sh
    ./run_with_patch.sh vllm serve /path/to/model <existing arguments>

install_editable.sh uses the familiar editable-install model, but adds
--no-index and --no-build-isolation. This matters with pip 26 in the pinned
image: plain pip install --no-deps -e . tried to download an isolated
setuptools build dependency, while the maintained installer passed with no
network and no NPU devices.

The installation changes only the disposable container writable layer and the
editable Python path. It does not modify the image and must never be followed
by docker commit. Installing after vLLM workers have already started does not
retroactively patch those processes; recreate or restart the service after
installation.

## Current evidence boundary

Passed:

- Python and shell syntax;
- static projection-fusion contract tests;
- exact official-image source-contract validation without network or devices;
- device-free behavior checks for fused/fallback projection construction,
  weight mapping, Ascend forward selection, linear-attention gate/up prefetch,
  and Gemma RMSNorm prefetch postprocessing;
- activation-checker positive and negative fixtures;
- offline editable installation in the exact v0.23.0 image with network=none
  and no NPU device mapping.

Live evidence now recorded:

- activation passed in a disposable official-image container on physical NPU0-3;
- no physical NPU4-7 devices were mounted into the candidate container;
- the patch was mounted read-only and injected through Python path mechanics;
- fixed-input smoke completed 1/1 with natural EOS and the same response hash
  as control;
- c1/32 fail-fast completed 32/32 with natural EOS, but only reduced TTFT P95
  from 6502.636 ms to 5697.694 ms (12.38%) and TPOT P95 from 31.754 ms to
  31.641 ms (0.36%);
- only 16/32 response hashes matched the paired control run, so this candidate
  must not be promoted as precision-lossless without deeper paired review.

Still pending for a final money patch:

- four-rank live activation on physical NPU0-3;
- fresh same-environment MTP-off control;
- c1/c5/c8/c16, three repeats, TTFT P95 reduction at least 40%;
- c1/c5/c8/c16, three repeats, TPOT P95 reduction at least 20%;
- paired quality validation over all 357 frozen rows.

Historical t11 reached a 47.7% c1 TTFT P95 reduction but only a 17.3% TPOT P95
reduction. Those measurements are provenance, not a t12 performance claim.
The latest standalone t12 run reached only 12.38% TTFT P95 reduction and 0.36%
TPOT P95 reduction at c1/32, so t12 is a validated loader/activation baseline,
not the final optimization.

Run `../tests/test_official_image_source_contract.sh` on the host to detect
class, method, signature, or exact source-anchor drift in the pinned image.
This intentionally does not import the Qwen GDN stack: that import initializes
the Triton Ascend target and therefore belongs to the live NPU activation gate.

See ../VALIDATION_PLAN.md for the ordered gates and rollback boundary.
