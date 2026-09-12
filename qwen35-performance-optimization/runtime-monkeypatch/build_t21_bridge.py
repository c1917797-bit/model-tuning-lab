#!/usr/bin/env python3
"""Build the optional T21 public-ACL bridge inside the pinned official image."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CppExtension


HERE = Path(__file__).resolve().parent
TORCH_NPU_ROOT = Path(__import__("torch_npu").__file__).resolve().parent
CANN_ROOT = Path(os.environ.get("ASCEND_HOME_PATH", "/usr/local/Ascend/cann-9.1.0"))


def main() -> None:
    setup(
        name="qwen35-t21-public-acl-bridge",
        version="0.0.1",
        ext_modules=[
            CppExtension(
                name="qwen35_t21_bridge",
                sources=[str(HERE / "native" / "qwen35_t21_public_acl_bridge.cpp")],
                include_dirs=[
                    str(TORCH_NPU_ROOT / "include"),
                    str(CANN_ROOT / "include"),
                ],
                library_dirs=[
                    str(TORCH_NPU_ROOT / "lib"),
                    str(CANN_ROOT / "lib64"),
                ],
                libraries=["torch_npu", "opapi", "ascendcl", "dl"],
                # PyTorch 2.11 public headers intentionally leave parameters
                # unused in virtual defaults, so do not promote third-party
                # header warnings to errors. Our source is still built with
                # the normal warning set.
                extra_compile_args=[
                    "-O2",
                    "-Wall",
                    "-Wextra",
                    "-Wno-unused-parameter",
                ],
                extra_link_args=[
                    f"-Wl,-rpath,{TORCH_NPU_ROOT / 'lib'}",
                    f"-Wl,-rpath,{CANN_ROOT / 'lib64'}",
                ],
            )
        ],
        cmdclass={"build_ext": BuildExtension.with_options(use_ninja=False)},
        script_args=sys.argv[1:] or ["build_ext", "--inplace"],
    )


if __name__ == "__main__":
    main()
