import enum
from functools import wraps
import hashlib
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import independent_c2_native_forward as guard

OWNER_SOURCE = """class Qwen3NextModel:
    def forward(self, input_ids, positions, intermediate_tensors=None, inputs_embeds=None):
        return input_ids
"""
MODEL_SOURCE = """class Qwen3_5Model(Qwen3NextModel):
    pass
"""


class NativeForwardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.owner_path = root / "qwen3_next.py"
        self.model_path = root / "qwen3_5.py"
        self.owner_path.write_text(OWNER_SOURCE)
        self.model_path.write_text(MODEL_SOURCE)
        self.owner = types.ModuleType(guard._OWNER_MODULE)
        self.owner.__file__ = str(self.owner_path)
        exec(compile(OWNER_SOURCE, str(self.owner_path), "exec"), vars(self.owner))
        self.model = types.ModuleType(guard._MODEL_MODULE)
        self.model.__file__ = str(self.model_path)
        self.model.Qwen3NextModel = self.owner.Qwen3NextModel
        exec(compile(MODEL_SOURCE, str(self.model_path), "exec"), vars(self.model))
        self.compilation = types.ModuleType("vllm.config.compilation")
        class CompilationMode(enum.IntEnum):
            NONE = 0
            STOCK_TORCH_COMPILE = 1
        self.compilation.CompilationMode = CompilationMode
        self.addCleanup(patch.stopall)
        patch.dict(sys.modules, {guard._OWNER_MODULE: self.owner,
            guard._MODEL_MODULE: self.model,
            "vllm.config.compilation": self.compilation}).start()
        patch.object(guard, "_OWNER_SOURCE_SHA256",
                     hashlib.sha256(OWNER_SOURCE.encode()).hexdigest()).start()
        patch.object(guard, "_MODEL_SOURCE_SHA256",
                     hashlib.sha256(MODEL_SOURCE.encode()).hexdigest()).start()
        self.cls = self.model.Qwen3_5Model
        self.forward = self.cls.forward

    def verify(self):
        return guard.verify_c2_native_forward(self.cls, self.cls.forward)

    def installed(self):
        receipt = self.verify()
        @wraps(self.forward)
        def wrapper(*args, **kwargs):
            return self.forward(*args, **kwargs)
        wrapper._independent_compact_model_owned = True
        self.cls.forward = wrapper
        instance = self.cls()
        instance.do_not_compile = True
        instance.compilation_config = types.SimpleNamespace(
            mode=self.compilation.CompilationMode.NONE)
        instance.vllm_config = types.SimpleNamespace(
            compilation_config=instance.compilation_config)
        return instance, wrapper, receipt

    def test_exact_inherited_entry_and_owned_eager_instance(self):
        instance, wrapper, receipt = self.installed()
        self.assertIs(receipt.forward, self.forward)
        self.assertIs(receipt.globals_dict, vars(self.owner))
        self.assertIs(receipt.code, self.forward.__code__)
        guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_verification_compiles_but_does_not_execute_source(self):
        source = OWNER_SOURCE + "\nraise AssertionError('must not execute official source')\n"
        self.owner_path.write_text(source)
        with patch.object(guard, "_OWNER_SOURCE_SHA256",
                          hashlib.sha256(source.encode()).hexdigest()):
            self.verify()

    def test_unknown_wrapped_forward_is_not_unwrapped(self):
        @wraps(self.forward)
        def unknown(*args, **kwargs):
            return self.forward(*args, **kwargs)
        self.owner.Qwen3NextModel.forward = unknown
        with patch.object(guard.inspect, "unwrap", side_effect=AssertionError("unwrap")):
            with self.assertRaises(ValueError):
                self.verify()

    def test_own_model_override_even_same_function_is_rejected(self):
        self.cls.forward = self.forward
        with self.assertRaises(ValueError):
            self.verify()

    def test_foreign_globals_with_same_code_are_rejected(self):
        foreign = types.FunctionType(self.forward.__code__, dict(vars(self.owner)),
                                     "forward", self.forward.__defaults__)
        self.owner.Qwen3NextModel.forward = foreign
        with self.assertRaises(ValueError):
            self.verify()

    def test_wrong_code_in_verified_file_and_globals_is_rejected(self):
        source = "def other(self, input_ids, positions, intermediate_tensors=None, inputs_embeds=None):\n    return positions\n"
        exec(compile(source, str(self.owner_path), "exec"), vars(self.owner))
        self.owner.Qwen3NextModel.forward = self.owner.other
        with self.assertRaises(ValueError):
            self.verify()

    def test_wrong_class_or_source_bytes_rejected(self):
        with self.assertRaises(ValueError):
            guard.verify_c2_native_forward(self.owner.Qwen3NextModel, self.forward)
        self.model_path.write_text(MODEL_SOURCE + "# drift\n")
        with self.assertRaises(ValueError):
            self.verify()

    def test_install_rejects_changed_native_defaults(self):
        self.forward.__defaults__ = (None, 1)
        with self.assertRaises(ValueError):
            self.verify()

    def test_replacement_class_entry_is_rejected(self):
        instance, wrapper, receipt = self.installed()
        @wraps(wrapper)
        def another(*args, **kwargs):
            return wrapper(*args, **kwargs)
        self.cls.forward = another
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_instance_forward_override_is_rejected(self):
        instance, wrapper, receipt = self.installed()
        instance.forward = types.MethodType(wrapper, instance)
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_native_code_swap_after_install_is_rejected(self):
        instance, wrapper, receipt = self.installed()
        self.forward.__code__ = (lambda self, a, b, c=None, d=None: b).__code__
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_native_defaults_or_kwdefaults_change_is_rejected(self):
        instance, wrapper, receipt = self.installed()
        self.forward.__defaults__ = (None, 1)
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)
        self.forward.__defaults__ = receipt.defaults
        self.forward.__kwdefaults__ = {"other": None}
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_native_owner_rebinding_or_wrapping_is_rejected(self):
        instance, wrapper, receipt = self.installed()
        self.owner.Qwen3NextModel.forward = lambda *args: None
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_new_wrapped_attribute_on_native_is_rejected(self):
        instance, wrapper, receipt = self.installed()
        self.forward.__wrapped__ = self.forward
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_boolean_compile_flag_is_not_sufficient_for_stock_compile(self):
        instance, wrapper, receipt = self.installed()
        instance.compilation_config.mode = self.compilation.CompilationMode.STOCK_TORCH_COMPILE
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_missing_false_or_truthy_eager_flag_is_rejected(self):
        instance, wrapper, receipt = self.installed()
        for flag in (False, None, 1):
            instance.do_not_compile = flag
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)

    def test_compilation_config_alias_or_plain_integer_mode_rejected(self):
        instance, wrapper, receipt = self.installed()
        instance.vllm_config.compilation_config = types.SimpleNamespace(
            mode=self.compilation.CompilationMode.NONE)
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)
        instance.vllm_config.compilation_config = instance.compilation_config
        instance.compilation_config.mode = 0
        with self.assertRaises(ValueError):
            guard.assert_c2_owned_forward(instance, self.cls, wrapper, receipt)


if __name__ == "__main__":
    unittest.main()
