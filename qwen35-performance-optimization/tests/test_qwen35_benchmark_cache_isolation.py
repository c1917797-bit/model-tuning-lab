#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "qwen35_query_rewrite_bench.py"
)


def main() -> None:
    spec = importlib.util.spec_from_file_location("qwen35_benchmark", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    salts = {
        module.request_cache_salt("run-a", concurrency, repetition, index)
        for concurrency in (1, 5, 8, 16)
        for repetition in (1, 2, 3)
        for index in range(32)
    }
    assert len(salts) == 4 * 3 * 32
    assert None not in salts
    assert module.request_cache_salt("", 1, 1, 0) is None
    assert (
        module.request_cache_salt("run-a", 1, 1, 0)
        != module.request_cache_salt("run-b", 1, 1, 0)
    )
    print("PASS: benchmark prefix-cache isolation contract")


if __name__ == "__main__":
    main()
