#!/usr/bin/env bash
set -euo pipefail

cp -a /readonly/qwen38-nvfp4-ascend /tmp/qwen38-src
pip install --no-deps --no-build-isolation /tmp/qwen38-src
exec vllm serve /model \
  --host 127.0.0.1 --port "${PORT}" --tensor-parallel-size 4 --seed 1024 \
  --tokenizer /tokenizer \
  --served-model-name Qwen3.8-27B-NVFP4-reference \
  --quantization modelopt_mixed_ascend_bf16_reference \
  --max-num-seqs 16 --max-model-len 32768 --max-num-batched-tokens 32768 \
  --trust-remote-code --gpu-memory-utilization 0.90 --enable-prefix-caching \
  --mamba-cache-mode align --additional-config '{"enable_cpu_binding":true}' \
  --default-chat-template-kwargs '{"enable_thinking":false}' \
  --mamba-cache-dtype bfloat16 --mamba-ssm-cache-dtype bfloat16 --async-scheduling
