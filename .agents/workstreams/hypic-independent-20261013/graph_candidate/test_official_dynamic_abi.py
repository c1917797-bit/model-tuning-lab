"""Execute only the pinned official dynamic-input helper on CPU.

Set HYPIC_GRAPH_DECORATORS_SOURCE to the immutable official decorators.py.
No official module is executed/imported, and no NPU is used.
"""
from enum import Enum
import hashlib
import inspect
import os
from pathlib import Path
import sys
import types
import unittest
import torch

from graph_candidate.entry_router import SelectiveEntryRouter
from graph_candidate.source_contract import PINS, _codes

_SOURCE = os.environ.get("HYPIC_GRAPH_DECORATORS_SOURCE")


class DynamicShapes(Enum):
    BACKED = 0
    UNBACKED = 1


@unittest.skipUnless(_SOURCE, "explicit immutable official decorator source required")
class OfficialDynamicInputABITests(unittest.TestCase):
    def official_helper(self):
        path = Path(_SOURCE).resolve()
        source = path.read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),
                         PINS["vllm.compilation.decorators"][1])
        # Compile without executing the module or any imports. Construct only
        # the exact official helper code with its two documented closure cells.
        codes = [code for code in _codes(compile(source, str(path), "exec",
                     dont_inherit=True, optimize=sys.flags.optimize))
                 if code.co_name == "_mark_dynamic_inputs" and code.co_firstlineno == 414]
        self.assertEqual(len(codes), 1)
        code = codes[0]
        self.assertEqual(code.co_freevars, ("dynamic_arg_dims", "mark_unbacked_dims"))
        def cell(value):
            return (lambda: value).__closure__[0]
        class IntermediateTensors:
            pass
        return types.FunctionType(code, {
            "__builtins__": __builtins__, "torch": torch, "inspect": inspect,
            "IntermediateTensors": IntermediateTensors,
            "DynamicShapesType": DynamicShapes,
            "is_torch_equal_or_newer": lambda version: False,
        }, "_mark_dynamic_inputs", closure=(
            cell({"input_ids": 0, "positions": -1, "intermediate_tensors": 0,
                  "inputs_embeds": 0}), cell({})))

    def tensors(self):
        return torch.arange(4), torch.arange(8).reshape(2, 4), torch.ones(4, 3)

    def test_real_official_helper_marks_installed_named_forward(self):
        class Model:
            def forward(self, input_ids, positions,
                        intermediate_tensors=None, inputs_embeds=None):
                return input_ids
            def __call__(self, *args, **kwargs):
                return self.forward(*args, **kwargs)
        native = Model.forward
        router = SelectiveEntryRouter(model_class=Model, native_call=Model.__call__,
            native_forward=native, compilation_mode=None, graph_mode=None,
            forward_context_class=None, batch_descriptor_class=None,
            get_context=lambda: None, is_compiling=torch.compiler.is_compiling,
            assert_ownership=lambda: None, prefill_forward=native)
        stop = router.install(enabled=True)
        try:
            self.assertEqual(Model.forward.__code__.co_varnames[:5],
                ("self", "input_ids", "positions", "intermediate_tensors", "inputs_embeds"))
            self.assertEqual(inspect.signature(Model.forward), inspect.signature(native))
            input_ids, positions, embeddings = self.tensors()
            self.official_helper()(Model(), DynamicShapes.BACKED,
                input_ids, positions, None, embeddings)
            self.assertEqual(input_ids._dynamo_dynamic_indices, {0})
            self.assertEqual(positions._dynamo_dynamic_indices, {1})
            self.assertEqual(embeddings._dynamo_dynamic_indices, {0})
        finally:
            stop()
        self.assertIs(Model.forward, native)

    def test_real_official_helper_exposes_old_varargs_silent_miss(self):
        class BadModel:
            def forward(self, *args, **kwargs):
                return args[0]
        input_ids, positions, embeddings = self.tensors()
        self.official_helper()(BadModel(), DynamicShapes.BACKED,
            input_ids, positions, None, embeddings)
        self.assertFalse(hasattr(input_ids, "_dynamo_dynamic_indices"))
        self.assertFalse(hasattr(positions, "_dynamo_dynamic_indices"))
        self.assertFalse(hasattr(embeddings, "_dynamo_dynamic_indices"))


if __name__ == "__main__":
    unittest.main()
