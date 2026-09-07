#!/usr/bin/env python3
"""Device-free contract test for the deferred Ascend monkeypatch activation."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


PATCH_PATH = Path(__file__).with_name("sitecustomize.py")
REGISTRY_NAME = "vllm.model_executor.models.registry"


class _LazyRegisteredModel:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def inspect_model_cls(self):
        if self.fail:
            raise RuntimeError("synthetic inspection failure")
        return "inspected"


def _load_patch_module():
    registry = ModuleType(REGISTRY_NAME)
    registry._LazyRegisteredModel = _LazyRegisteredModel
    sys.modules[REGISTRY_NAME] = registry
    os.environ["QWEN35_ASCEND_MONKEYPATCH"] = "1"
    spec = importlib.util.spec_from_file_location(
        "_qwen35_deferred_activation_probe", PATCH_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _test_compile_ranges(module) -> None:
    class AscendConfig:
        def __init__(self):
            self.vllm_config = SimpleNamespace(compilation_config=object())
            self.original_calls = 0
            self.ranges = [64, 1024]

        def update_compile_ranges_split_points(self):
            self.original_calls += 1

        def _get_compile_ranges(self, _config):
            return self.ranges

        def _set_compile_ranges(self, _config, ranges):
            self.ranges = ranges

    fake = SimpleNamespace(
        AscendConfig=AscendConfig,
        logger=SimpleNamespace(info=lambda *_args, **_kwargs: None),
    )
    os.environ["VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD"] = "512"
    os.environ["VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS"] = "16384"
    module._patch_ascend_config(fake)
    config = AscendConfig()
    config.update_compile_ranges_split_points()
    assert config.original_calls == 1
    assert config.ranges == [64, 512, 1024, 16384]


def _install_fake_vllm_utils() -> None:
    for name in ("vllm", "vllm.model_executor", "vllm.model_executor.models"):
        package = sys.modules.setdefault(name, ModuleType(name))
        package.__path__ = []
    utils = ModuleType("vllm.model_executor.models.utils")
    utils.extract_layer_index = lambda prefix: int(prefix.split(".")[2])
    sys.modules[utils.__name__] = utils


def _test_weight_prefetch(module) -> None:
    calls = []
    fallback_calls = []

    class WeightPrefetchMethod:
        MLP_GATE_UP = "gate_up"

        def __init__(self):
            self.mlp = SimpleNamespace(prefetch_ratio={self.MLP_GATE_UP: 0.1})

        def _maybe_prefetch_mlp_gate_up_weight_preprocess(
            self, x_dependency, forward_context, curr_layer_prefix
        ):
            fallback_calls.append(
                (x_dependency, forward_context, curr_layer_prefix)
            )
            return "fallback"

    class Data:
        @staticmethod
        def element_size():
            return 2

        @staticmethod
        def numel():
            return 1000

    _install_fake_vllm_utils()
    layers = [
        SimpleNamespace(
            mlp=SimpleNamespace(
                gate_up_proj=SimpleNamespace(weight=SimpleNamespace(data=Data()))
            )
        )
        for _ in range(4)
    ]
    extra_ctx = SimpleNamespace(
        model_instance=SimpleNamespace(model=SimpleNamespace(layers=layers)),
        prefetch_mlp_gate_up_proj=False,
    )
    fake = SimpleNamespace(
        WeightPrefetchMethod=WeightPrefetchMethod,
        _EXTRA_CTX=extra_ctx,
        MAX_PREFETCH_WEIGHT_SIZE=150,
        torch=SimpleNamespace(
            ops=SimpleNamespace(
                vllm=SimpleNamespace(
                    prefetch_preprocess=lambda **kwargs: calls.append(kwargs)
                )
            )
        ),
    )
    module._patch_weight_prefetch(fake)
    method = WeightPrefetchMethod()
    result = method._maybe_prefetch_mlp_gate_up_weight_preprocess(
        "dependency", "context", "model.layers.3.mlp.prefetch"
    )
    assert result == "fallback"
    assert len(fallback_calls) == 1
    assert not calls

    result = method._maybe_prefetch_mlp_gate_up_weight_preprocess(
        "dependency", "context", "model.layers.3.linear_attn.prefetch"
    )
    assert result is None
    assert len(calls) == 1
    assert calls[0]["weight"] is layers[3].mlp.gate_up_proj.weight
    assert calls[0]["start_flag"] == "dependency"
    assert calls[0]["max_weight_size"] == 150
    assert extra_ctx.prefetch_mlp_gate_up_proj


def _test_layernorm_postprocess(module) -> None:
    postprocess = []

    class AscendGemmaRMSNorm:
        def forward_oot(self, x, residual=None):
            return (x, residual)

    fake = SimpleNamespace(
        AscendGemmaRMSNorm=AscendGemmaRMSNorm,
        get_weight_prefetch_method=lambda: SimpleNamespace(
            maybe_prefetch_mlp_weight_postprocess=postprocess.append
        ),
    )
    module._patch_layernorm(fake)
    norm = AscendGemmaRMSNorm()
    no_residual = norm.forward_oot("x")
    assert postprocess == [no_residual]
    with_residual = norm.forward_oot("x", "residual")
    assert with_residual == ("x", "residual")
    assert postprocess == [no_residual]


def main() -> None:
    module = _load_patch_module()
    assert module._ENABLED
    assert not module._RUNTIME_ACTIVE
    assert module._TARGETS == {REGISTRY_NAME}

    try:
        _LazyRegisteredModel(fail=True).inspect_model_cls()
    except RuntimeError as exc:
        assert str(exc) == "synthetic inspection failure"
    else:
        raise AssertionError("synthetic inspection failure was swallowed")
    assert not module._RUNTIME_ACTIVE
    assert module._TARGETS == {REGISTRY_NAME}

    assert _LazyRegisteredModel().inspect_model_cls() == "inspected"
    assert module._RUNTIME_ACTIVE
    assert module._RUNTIME_TARGETS <= module._TARGETS

    assert _LazyRegisteredModel().inspect_model_cls() == "inspected"
    assert module._RUNTIME_ACTIVE
    _test_compile_ranges(module)
    _test_weight_prefetch(module)
    _test_layernorm_postprocess(module)
    print("PASS: runtime hooks activate only after successful model inspection")


if __name__ == "__main__":
    main()
