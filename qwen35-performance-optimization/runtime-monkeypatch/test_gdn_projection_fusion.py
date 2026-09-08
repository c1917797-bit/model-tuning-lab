#!/usr/bin/env python3
"""Device-free contract tests for the runtime-only GDN projection fusion."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType
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
            quant_config=None,
        ):
            self.gqa_interleaved_layout = gqa_interleaved_layout
            self.quant_config = quant_config
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

    fallback = QwenGatedDeltaNetAttention(
        None,
        None,
        prefix="layers.1.linear_attn",
        quant_config=object(),
    )
    assert not fallback.fuse_qwen35_gdn_projections
    assert hasattr(fallback, "in_proj_qkvz")
    assert hasattr(fallback, "in_proj_ba")


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


def test_linear_attention_gate_up_prefetch(patch):
    calls = []

    class FakeWeight:
        @property
        def data(self):
            return self

        def element_size(self):
            return 2

        def numel(self):
            return 1000

    weight = FakeWeight()
    layer = SimpleNamespace(
        mlp=SimpleNamespace(gate_up_proj=SimpleNamespace(weight=weight))
    )

    class WeightPrefetchMethod:
        MLP_GATE_UP = "gate_up"

        def __init__(self):
            self.mlp = SimpleNamespace(prefetch_ratio={self.MLP_GATE_UP: 0.1})

        def _maybe_prefetch_mlp_gate_up_weight_preprocess(
            self, x_dependency, forward_context, curr_layer_prefix
        ):
            return ("original", curr_layer_prefix)

    fake = SimpleNamespace(
        WeightPrefetchMethod=WeightPrefetchMethod,
        _EXTRA_CTX=SimpleNamespace(
            model_instance=SimpleNamespace(
                model=SimpleNamespace(layers=[layer])
            ),
            prefetch_mlp_gate_up_proj=False,
        ),
        MAX_PREFETCH_WEIGHT_SIZE=128,
        torch=SimpleNamespace(
            ops=SimpleNamespace(
                vllm=SimpleNamespace(
                    prefetch_preprocess=lambda **kwargs: calls.append(kwargs)
                )
            )
        ),
    )

    module_names = (
        "vllm",
        "vllm.model_executor",
        "vllm.model_executor.models",
        "vllm.model_executor.models.utils",
    )
    saved_modules = {name: sys.modules.get(name) for name in module_names}
    try:
        for name in module_names[:-1]:
            module = ModuleType(name)
            module.__path__ = []
            sys.modules[name] = module
        utils = ModuleType(module_names[-1])
        utils.extract_layer_index = lambda prefix: int(prefix.split(".")[2])
        sys.modules[module_names[-1]] = utils

        patch._patch_weight_prefetch(fake)
        method = WeightPrefetchMethod()
        dependency = object()
        method._maybe_prefetch_mlp_gate_up_weight_preprocess(
            dependency,
            object(),
            "model.layers.0.linear_attn.o_proj",
        )
        assert calls == [
            {
                "weight": weight,
                "start_flag": dependency,
                "max_weight_size": 128,
            }
        ]
        assert fake._EXTRA_CTX.prefetch_mlp_gate_up_proj
        assert (
            method._maybe_prefetch_mlp_gate_up_weight_preprocess(
                dependency,
                object(),
                "model.layers.0.self_attn.o_proj",
            )
            == ("original", "model.layers.0.self_attn.o_proj")
        )
        assert len(calls) == 1
    finally:
        for name, saved in saved_modules.items():
            if saved is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = saved


def test_gemma_rmsnorm_prefetch_postprocess(patch):
    calls = []

    class AscendGemmaRMSNorm:
        def forward_oot(self, x, residual=None):
            if residual is not None:
                return x, residual
            return x

    prefetch = SimpleNamespace(
        maybe_prefetch_mlp_weight_postprocess=lambda result: calls.append(result)
    )
    fake = SimpleNamespace(
        AscendGemmaRMSNorm=AscendGemmaRMSNorm,
        get_weight_prefetch_method=lambda: prefetch,
    )
    patch._patch_layernorm(fake)
    norm = AscendGemmaRMSNorm()
    output = object()
    assert norm.forward_oot(output) is output
    assert calls == [output]
    residual = object()
    assert norm.forward_oot(output, residual) == (output, residual)
    assert calls == [output]


def main():
    patch = load_patch()
    test_projection_construction(patch)
    test_weight_mapping(patch)
    test_ascend_forward_selection(patch)
    test_bounded_mmar_disabled(patch)
    test_linear_attention_gate_up_prefetch(patch)
    test_gemma_rmsnorm_prefetch_postprocess(patch)
    print("PASS: runtime-only GDN projection fusion contract")


if __name__ == "__main__":
    main()
