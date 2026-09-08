#!/usr/bin/env python3
"""Editable-install metadata for the runtime-only Qwen3.5 patch."""

from setuptools import setup


setup(
    name="qwen35-vllm-ascend-patch",
    version="0.0.0.dev12",
    description="Runtime-only Qwen3.5 performance patch for vLLM-Ascend 0.23.0",
    py_modules=["sitecustomize"],
    python_requires=">=3.9",
)
