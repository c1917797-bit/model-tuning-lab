#!/usr/bin/env python3
"""Device-free contract tests for the runtime-only GDN projection fusion."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace


PATCH_PATH = Path(__file__).with_name("sitecustomize.py")


def load_patch():
    os.environ["QWEN35_ASCEND_MONKEYPATCH"] = "1"
    os.environ["VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS"] = "1"
    spec = importlib.util.spec_from_file_location("_qwen35_gdn_probe", PATCH_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTensor:
    def __init__(self, shape=(1, 1)):
        self.shape = shape

    def size(self, dim=None):
        return self.shape if dim is None else self.shape[dim]

    def split(self, sizes, dim=-1):
        shape = list(self.shape)
        outputs = []
        for size in sizes:
            shape[dim] = size
            outputs.append(FakeTensor(tuple(shape)))
        return tuple(outputs)

    def reshape(self, *shape):
        return FakeTensor(tuple(shape))

    def contiguous(self):
        return self


def test_projection_construction(patch):
    class MergedColumnParallelLinear:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __call__(self, hidden_states):
            width = sum(self.kwargs["output_sizes"]) // 4
            return FakeTensor((hidden_states.size(0), width)), None

    class QwenGatedDeltaNetAttention:
        def __init__(
            self,
            config,
            vllm_config,
            prefix="",
            gqa_interleaved_layout=False,
        ):
            self.gqa_interleaved_layout = gqa_interleaved_layout
            self.quant_config = None
            self.hidden_size = 5120
            self.key_dim = 1024
            self.value_dim = 1024
            self.num_v_heads = 64
            self.tp_size = 4
            self.in_proj_qkvz = object()
            self.in_proj_ba = object()

    fake = SimpleNamespace(
        QwenGatedDeltaNetAttention=QwenGatedDeltaNetAttention,
        MergedColumnParallelLinear=MergedColumnParallelLinear,
    )
    patch._patch_qwen_gdn_linear_attn(fake)
    attention = QwenGatedDeltaNetAttention(None, None, prefix="layers.0.linear_attn")
    assert not hasattr(attention, "in_proj_qkvz")
    assert not hasattr(attention, "in_proj_ba")
    assert attention.fuse_qwen35_gdn_projections
    assert attention.in_proj_qkvzba.kwargs["output_sizes"] == [
        1024,
        1024,
        1024,
        1024,
        64,
        64,
    ]
    qkvz, ba = attention.project_qkvz_ba(FakeTensor((1, 5120)))
    assert qkvz.size(-1) == 1024
    assert ba.size(-1) == 32


def test_weight_mapping(patch):
    class Qwen3_5Model:
        def named_parameters(self):
            return [("model.layers.0.linear_attn.in_proj_qkvzba.weight", object())]

        def load_weights(self, weights):
            stacked_params_mapping = [("old", "old", 0)]
            params_dict = dict(self.named_parameters())
            loaded_params: set[str] = set()
            return stacked_params_mapping, params_dict, loaded_params

    fake = SimpleNamespace(Qwen3_5Model=Qwen3_5Model)
    patch._patch_qwen35_model(fake)
    mapping, _, _ = Qwen3_5Model().load_weights([])
    assert mapping[:4] == [
        ("in_proj_qkvzba", "in_proj_qkv", (0, 1, 2)),
        ("in_proj_qkvzba", "in_proj_z", 3),
        ("in_proj_qkvzba", "in_proj_b", 4),
        ("in_proj_qkvzba", "in_proj_a", 5),
    ]


def test_ascend_forward_selection(patch):
    class AscendGatedDeltaNetAttention:
        def forward(self, hidden_states, output):
            num_tokens = hidden_states.size(0)
            if hasattr(self, "in_proj_qkv"):
                return "unfused-qkv"
            return num_tokens, mixed_qkv, z, b, a

    fake = SimpleNamespace(
        AscendGatedDeltaNetAttention=AscendGatedDeltaNetAttention
    )
    patch._patch_ascend_gdn(fake)
    attention = AscendGatedDeltaNetAttention()
    attention.in_proj_qkvzba = object()
    attention.key_dim = 1024
    attention.value_dim = 1024
    attention.tp_size = 4
    attention.head_v_dim = 128
    attention.project_qkvz_ba = lambda hidden: (
        FakeTensor((hidden.size(0), 1024)),
        FakeTensor((hidden.size(0), 32)),
    )
    attention._split_ba_for_tp = lambda ba: ba.split([16, 16], dim=-1)
    num_tokens, mixed_qkv, z, b, a = attention.forward(
        FakeTensor((1, 5120)), None
    )
    assert num_tokens == 1
    assert mixed_qkv.size(-1) == 768
    assert z.size(-1) == 128
    assert b.size(-1) == 16
    assert a.size(-1) == 16


def test_bounded_mmar_disabled(patch):
    class GraphFusionPassManager:
        def configure(self, config):
            self.config = config

    os.environ["VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD"] = "0"
    fake = SimpleNamespace(GraphFusionPassManager=GraphFusionPassManager)
    patch._patch_graph_manager(fake)
    assert not getattr(
        GraphFusionPassManager, "_qwen35_mmar_pass_monkeypatched", False
    )


def main():
    patch = load_patch()
    test_projection_construction(patch)
    test_weight_mapping(patch)
    test_ascend_forward_selection(patch)
    test_bounded_mmar_disabled(patch)
    print("PASS: runtime-only GDN projection fusion contract")


if __name__ == "__main__":
    main()
