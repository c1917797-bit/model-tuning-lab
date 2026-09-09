#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  echo "source this file before starting vLLM: source $0" >&2
  exit 64
fi

patch_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
expected_sha="9c8e74ae5ba9adaf74628d74c3361d2e8bcb86792ff1d4c54eca00381e1b92a8"
actual_sha="$(sha256sum "$patch_root/sitecustomize.py")"
actual_sha="${actual_sha%% *}"

if [[ "$actual_sha" != "$expected_sha" ]]; then
  echo "Qwen3.5 patch SHA256 mismatch: $actual_sha" >&2
  return 65
fi

case ":${PYTHONPATH:-}:" in
  *":$patch_root:"*) ;;
  *) export PYTHONPATH="$patch_root${PYTHONPATH:+:$PYTHONPATH}" ;;
esac

export QWEN35_ASCEND_MONKEYPATCH=1
export VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD=513
export VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS=16384

echo "Qwen3.5 vLLM-Ascend runtime patch loaded: $expected_sha" >&2
