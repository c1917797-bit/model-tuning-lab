"""Spawn child import must not create an engine or read model/data paths."""
import runpy
import sys
from pathlib import Path

assert "vllm" not in sys.modules
namespace = runpy.run_path(str(Path(__file__).with_name("sparse_real_workload.py")),
                          run_name="__mp_main__")
assert callable(namespace["main"])
assert "vllm" not in sys.modules
print("PASS spawn import has no engine/model/data side effects")
