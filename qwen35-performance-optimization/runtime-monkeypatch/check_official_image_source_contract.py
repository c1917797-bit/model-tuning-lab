#!/usr/bin/env python3
"""Validate the monkeypatch's source contract without initializing an NPU."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import textwrap


SOURCES = {
    "registry": Path("/vllm-workspace/vllm/vllm/model_executor/models/registry.py"),
    "qwen_gdn": Path(
        "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/"
        "qwen_gdn_linear_attn.py"
    ),
    "qwen_model": Path(
        "/vllm-workspace/vllm/vllm/model_executor/models/qwen3_5.py"
    ),
    "ascend_gdn": Path(
        "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"
    ),
    "layernorm": Path(
        "/vllm-workspace/vllm-ascend/vllm_ascend/ops/layernorm.py"
    ),
    "weight_prefetch": Path(
        "/vllm-workspace/vllm-ascend/vllm_ascend/ops/weight_prefetch.py"
    ),
    "linear": Path(
        "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear.py"
    ),
    "linear_op": Path(
        "/vllm-workspace/vllm-ascend/vllm_ascend/ops/linear_op.py"
    ),
}

REQUIRED_METHODS = {
    "registry": {"_LazyRegisteredModel": {"inspect_model_cls": {"self"}}},
    "qwen_gdn": {
        "QwenGatedDeltaNetAttention": {"__init__": {"self", "prefix"}}
    },
    "qwen_model": {"Qwen3_5Model": {"load_weights": {"self"}}},
    "ascend_gdn": {
        "AscendGatedDeltaNetAttention": {"forward": {"self", "hidden_states"}}
    },
    "layernorm": {
        "AscendGemmaRMSNorm": {"forward_oot": {"self", "x", "residual"}}
    },
    "weight_prefetch": {
        "WeightPrefetchMethod": {
            "_maybe_prefetch_mlp_gate_up_weight_preprocess": {
                "self",
                "x_dependency",
                "forward_context",
                "curr_layer_prefix",
            }
        }
    },
    "linear": {
        "AscendRowParallelLinear": {
            "__init__": {"self", "input_size", "output_size", "prefix"},
            "forward": {"self", "input_"},
        }
    },
    "linear_op": {
        "MatmulAllreduceRowParallelOp": {
            "__init__": {"self", "layer"},
            "apply_impl": {"self", "input_"},
        }
    },
}

REQUIRED_FUNCTIONS = {
    "linear_op": {"_get_row_parallel_op": {"prefix", "layer"}},
}

EXACT_METHOD_ANCHORS = {
    ("qwen_model", "Qwen3_5Model", "load_weights"): (
        "    params_dict = dict(self.named_parameters())\n"
        "    loaded_params: set[str] = set()\n"
    ),
    ("ascend_gdn", "AscendGatedDeltaNetAttention", "forward"): (
        "    num_tokens = hidden_states.size(0)\n"
        '    if hasattr(self, "in_proj_qkv"):\n'
    ),
    ("linear", "AscendRowParallelLinear", "forward"): (
        "    if self.custom_op is not None:\n"
        "        return self.custom_op.apply(input_)\n"
    ),
    ("linear_op", "MatmulAllreduceRowParallelOp", "apply_impl"): (
        "    if self.reduce_results and self.tp_size > 1:\n"
        "        output = torch_npu.npu_mm_all_reduce_base(\n"
    ),
}

EXACT_FUNCTION_ANCHORS = {
    ("linear_op", "_get_row_parallel_op"): (
        "    if matmul_allreduce_enable():\n"
        "        return MatmulAllreduceRowParallelOp(layer)\n"
    ),
}


def _classes(tree: ast.AST) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }


def _methods(class_node: ast.ClassDef) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in class_node.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _functions(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _node_source(source: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    return textwrap.dedent(
        "".join(
            source.splitlines(keepends=True)[node.lineno - 1 : node.end_lineno]
        )
    )


def _arguments(method: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = method.args
    return {
        item.arg
        for item in (*args.posonlyargs, *args.args, *args.kwonlyargs)
    }


def main() -> int:
    parsed: dict[str, tuple[str, ast.Module]] = {}
    report: dict[str, object] = {"schema": "qwen35-source-contract/v1", "files": {}}

    for logical_name, path in SOURCES.items():
        raw = path.read_bytes()
        source = raw.decode("utf-8")
        parsed[logical_name] = (source, ast.parse(source, filename=str(path)))
        report["files"][logical_name] = {
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }

    for logical_name, required_classes in REQUIRED_METHODS.items():
        source, tree = parsed[logical_name]
        classes = _classes(tree)
        for class_name, required_methods in required_classes.items():
            if class_name not in classes:
                raise AssertionError(f"{logical_name}: missing class {class_name}")
            methods = _methods(classes[class_name])
            for method_name, required_args in required_methods.items():
                if method_name not in methods:
                    raise AssertionError(
                        f"{logical_name}.{class_name}: missing method {method_name}"
                    )
                actual_args = _arguments(methods[method_name])
                missing_args = required_args - actual_args
                if missing_args:
                    raise AssertionError(
                        f"{logical_name}.{class_name}.{method_name}: "
                        f"missing arguments {sorted(missing_args)}"
                    )

                anchor_key = (logical_name, class_name, method_name)
                if anchor_key in EXACT_METHOD_ANCHORS:
                    method = methods[method_name]
                    method_source = _node_source(source, method)
                    anchor = EXACT_METHOD_ANCHORS[anchor_key]
                    count = method_source.count(anchor)
                    if count != 1:
                        raise AssertionError(
                            f"{logical_name}.{class_name}.{method_name}: "
                            f"expected exact v0.23.0 anchor once, found {count}"
                        )

    for logical_name, required_functions in REQUIRED_FUNCTIONS.items():
        source, tree = parsed[logical_name]
        functions = _functions(tree)
        for function_name, required_args in required_functions.items():
            if function_name not in functions:
                raise AssertionError(
                    f"{logical_name}: missing function {function_name}"
                )
            function = functions[function_name]
            missing_args = required_args - _arguments(function)
            if missing_args:
                raise AssertionError(
                    f"{logical_name}.{function_name}: "
                    f"missing arguments {sorted(missing_args)}"
                )
            anchor = EXACT_FUNCTION_ANCHORS.get((logical_name, function_name))
            if anchor is not None:
                count = _node_source(source, function).count(anchor)
                if count != 1:
                    raise AssertionError(
                        f"{logical_name}.{function_name}: "
                        f"expected exact v0.23.0 anchor once, found {count}"
                    )

    if "MergedColumnParallelLinear" not in parsed["qwen_gdn"][0]:
        raise AssertionError("qwen_gdn: MergedColumnParallelLinear is unavailable")

    report["result"] = "pass"
    print(json.dumps(report, indent=2, sort_keys=True))
    print("PASS_OFFICIAL_IMAGE_SOURCE_CONTRACT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
