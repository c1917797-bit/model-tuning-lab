"""Offline-friendly editable installer for the standalone runtime patch."""

from setuptools import setup


setup(
    name="qwen35-vllm-ascend-patch",
    version="0.1.0",
    description="Runtime-only Qwen3.5 performance patch for vLLM-Ascend 0.23.0",
    python_requires=">=3.9,<3.13",
    packages=["qwen35_vllm_ascend_patch"],
    py_modules=["sitecustomize"],
    install_requires=[],
)
