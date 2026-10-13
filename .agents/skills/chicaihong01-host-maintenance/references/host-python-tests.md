## Host-side Python test environment

The host system Python is 3.9 and does not satisfy this repository's
`requires-python >=3.10`. For CPU-only unit tests, use:

- uv: `/cache/cch/toolchains/uv/bin/uv`;
- managed Python: `/cache/cch/toolchains/uv/python`;
- virtual environment: `/cache/cch/python-envs/model-tuning-lab-py311`;
- CPU dependency cache: `/cache/cch/toolchains/uv/cache-cpu`.

From any fresh clone or worktree, run
`./scripts/bootstrap-host-test-env.sh`, then use the printed command. The
script is idempotent, keeps large dependencies on `/cache`, and passes the
current clone's `src` through `PYTHONPATH` instead of binding the shared
environment to one worktree.

This environment is only for host-side unit tests. Device execution remains
inside the pinned Ascend container with its matching CANN, `torch_npu`, vLLM,
and vLLM-Ascend stack. Do not install device packages into the host-test
environment. If dependency resolution selects CUDA/NVIDIA packages or an
unpinned newer Torch, stop and inspect the plan rather than completing the
download.
