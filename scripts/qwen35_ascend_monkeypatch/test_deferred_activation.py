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


def _load_patch_module(orig_argv=None):
    registry = ModuleType(REGISTRY_NAME)
    registry._LazyRegisteredModel = _LazyRegisteredModel
    sys.modules[REGISTRY_NAME] = registry
    os.environ["QWEN35_ASCEND_MONKEYPATCH"] = "1"
    had_orig_argv = hasattr(sys, "orig_argv")
    saved_orig_argv = getattr(sys, "orig_argv", None)
    if orig_argv is not None:
        sys.orig_argv = orig_argv
    try:
        spec = importlib.util.spec_from_file_location(
            "_qwen35_deferred_activation_probe", PATCH_PATH
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if had_orig_argv:
            sys.orig_argv = saved_orig_argv
        elif hasattr(sys, "orig_argv"):
            del sys.orig_argv


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


def _test_graph_manager(module) -> None:
    created = []

    class BeforePass:
        pass

    class MatmulAllReduceAddRMSNormPass:
        pass

    class AfterPass:
        pass

    class MmarPass:
        _qwen35_mmar_prefill_monkeypatch = True

        def __init__(self, config):
            self.config = config
            created.append(self)

    class GraphFusionPassManager:
        def configure(self, config):
            self.ascend_compilation_config = config
            self.passes = [
                BeforePass(),
                MatmulAllReduceAddRMSNormPass(),
                AfterPass(),
            ]
            if config.get("existing_mmar", False):
                self.passes.insert(1, MmarPass(config))

    original_factory = module._make_mmar_pass
    module._make_mmar_pass = lambda: MmarPass
    try:
        fake = SimpleNamespace(GraphFusionPassManager=GraphFusionPassManager)
        module._patch_graph_manager(fake)
    finally:
        module._make_mmar_pass = original_factory

    enabled_config = {"fuse_allreduce_rms": True}
    manager = GraphFusionPassManager()
    manager.configure(enabled_config)
    assert [type(item).__name__ for item in manager.passes] == [
        "BeforePass",
        "MmarPass",
        "MatmulAllReduceAddRMSNormPass",
        "AfterPass",
    ]
    assert created[-1].config is enabled_config

    manager = GraphFusionPassManager()
    manager.configure({"fuse_allreduce_rms": False})
    assert not any(
        getattr(item, "_qwen35_mmar_prefill_monkeypatch", False)
        for item in manager.passes
    )

    count_before = len(created)
    manager = GraphFusionPassManager()
    manager.configure({"fuse_allreduce_rms": True, "existing_mmar": True})
    assert len(created) == count_before + 1
    assert (
        sum(
            bool(getattr(item, "_qwen35_mmar_prefill_monkeypatch", False))
            for item in manager.passes
        )
        == 1
    )


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
    _test_graph_manager(module)
    child = _load_patch_module(
        [
            "python3",
            "-c",
            "from multiprocessing.spawn import spawn_main; spawn_main()",
            "--multiprocessing-fork",
        ]
    )
    assert child._MULTIPROCESSING_CHILD
    assert child._RUNTIME_ACTIVE
    assert child._RUNTIME_TARGETS <= child._TARGETS
    assert child._is_multiprocessing_child(
        ["python3", "-c", "from multiprocessing.forkserver import main; main()"]
    )
    assert not child._is_multiprocessing_child(["python3", "vllm", "serve"])
    print("PASS: deferred runtime monkeypatch contract")


if __name__ == "__main__":
    main()
