#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
uv_bin="${MST_UV_BIN:-/cache/cch/toolchains/uv/bin/uv}"
uv_install_dir="$(dirname -- "$uv_bin")"
python_dir="${MST_UV_PYTHON_DIR:-/cache/cch/toolchains/uv/python}"
env_dir="${MST_HOST_TEST_ENV:-/cache/cch/python-envs/model-tuning-lab-py311}"
cache_dir="${MST_UV_CACHE_DIR:-/cache/cch/toolchains/uv/cache-cpu}"
index_url="${MST_PYPI_INDEX:-https://pypi.tuna.tsinghua.edu.cn/simple}"

mkdir -p "$uv_install_dir" "$python_dir" "$cache_dir" "$(dirname -- "$env_dir")"

if [[ ! -x "$uv_bin" ]]; then
    curl -LsSf https://astral.sh/uv/install.sh |
        env UV_INSTALL_DIR="$uv_install_dir" sh
fi

export UV_PYTHON_INSTALL_DIR="$python_dir"
export UV_CACHE_DIR="$cache_dir"
export UV_DEFAULT_INDEX="$index_url"

"$uv_bin" python install 3.11
if [[ ! -x "$env_dir/bin/python" ]]; then
    "$uv_bin" venv --python 3.11 "$env_dir"
fi

host_deps=("numpy>=1.26,<3" "pytest>=8,<9" "torch==2.4.1")
"$uv_bin" pip install --python "$env_dir/bin/python" "${host_deps[@]}"

env PYTHONPATH="$repo_root/src${PYTHONPATH:+:$PYTHONPATH}" "$env_dir/bin/python" -c 'import numpy, pytest, torch; print(f"python deps ready: torch={torch.__version__} numpy={numpy.__version__} pytest={pytest.__version__}")'

echo "Host-test environment: $env_dir"
echo "Run: PYTHONPATH=$repo_root/src $env_dir/bin/python -m pytest"
