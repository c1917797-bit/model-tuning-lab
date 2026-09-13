#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import torch

os.environ["QWEN35_ASCEND_GDN_CONV_PREPACK"] = "1"

path = (
    Path(__file__).resolve().parents[1]
    / "runtime-monkeypatch"
    / "sitecustomize.py"
)
spec = importlib.util.spec_from_file_location("qwen35_conv_prepack_patch", path)
assert spec is not None and spec.loader is not None
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)


class Attention(torch.nn.Module):
    def __init__(self):
        super().__init__()
        source = torch.arange(24, dtype=torch.float32).reshape(6, 1, 4)
        self.conv1d = torch.nn.Module()
        self.conv1d.weight = torch.nn.Parameter(source, requires_grad=False)
        self.register_parameter(
            patch._PACKED_GDN_CONV_WEIGHT_NAME,
            torch.nn.Parameter(
                torch.empty(4, 6, dtype=torch.bfloat16), requires_grad=False
            ),
        )


attention = Attention()
replace_calls = []


def replace_parameter(module, name, value, prefer_copy=False):
    replace_calls.append((module, name, prefer_copy))
    setattr(module, name, torch.nn.Parameter(value, requires_grad=False))


patch._pack_qwen35_gdn_conv_weight(attention, replace_parameter)
packed = attention.get_parameter(patch._PACKED_GDN_CONV_WEIGHT_NAME)
expected = (
    attention.conv1d.weight.view(6, 4)
    .transpose(0, 1)
    .to(torch.bfloat16)
    .contiguous()
)
torch.testing.assert_close(packed, expected)
assert packed.shape == (4, 6)
assert packed.dtype == torch.bfloat16
assert packed.is_contiguous()
assert replace_calls == [
    (attention, patch._PACKED_GDN_CONV_WEIGHT_NAME, True)
]

source = path.read_text(encoding="utf-8")
assert "QWEN35_ASCEND_GDN_CONV_PREPACK" in source
assert "process_weights_after_loading" in source
assert "self._qwen35_ascend_conv1d_weight.transpose(0, 1)" in source
assert "from vllm.model_executor.utils import replace_parameter" in source
assert "upstream-derived Qwen GDN conv" in source

print("PASS: upstream-derived GDN conv-prepack monkeypatch")
