"""Exact alias/real-instance metadata tests; no model/NPU execution."""
import unittest
from damp_capture.bindings import (BINDING_SOURCES, bind_aliased_core, live_bindings,
                                    verify_native_alias)
from damp_capture.contract import LAYERS


def classes():
    class Donor:
        def forward(self, *args, **kwargs):
            return self._forward_core(*args, **kwargs)
        def _forward_core(self, payload):
            return payload
    class Receiver:
        pass
    Receiver.forward = Donor.forward
    Receiver._forward_core = Donor._forward_core
    return Donor, Receiver


def instances(receiver):
    result = {}
    for layer in LAYERS:
        prefix = f"language_model.model.layers.{layer}.linear_attn"
        value = receiver(); value.prefix = prefix
        result[prefix] = value
    return result


class BindingTests(unittest.TestCase):
    def test_donor_only_patch_leaves_copied_receiver_alias_unchanged(self):
        donor, target = classes()
        native = target._forward_core
        def wrapper(self, payload): return native(self, payload)
        donor._forward_core = wrapper
        self.assertIs(target._forward_core, native)
        self.assertIsNot(target._forward_core, donor._forward_core)
        with self.assertRaises(ValueError): verify_native_alias(donor, target)

    def test_dual_binding_preserves_original_return_object_and_native_args(self):
        donor, target = classes(); native = donor._forward_core
        calls = []
        def wrapper(self, payload):
            calls.append((self, payload))
            return native(self, payload)
        self.assertIs(bind_aliased_core(donor, target, wrapper), native)
        self.assertIs(target._forward_core, donor._forward_core)
        request, payload = target(), object()
        self.assertIs(request.forward(payload), payload)
        self.assertEqual(calls, [(request, payload)])
        with self.assertRaises(ValueError): bind_aliased_core(donor, target, wrapper)

    def test_all_48_real_receivers_verified_before_forward(self):
        donor, target = classes(); native = donor._forward_core
        def wrapper(self, payload): return native(self, payload)
        bind_aliased_core(donor, target, wrapper)
        table = instances(target); table["unrelated.self_attn"] = object()
        proof = live_bindings(table, donor, target, wrapper)
        self.assertEqual([row["layer"] for row in proof], list(LAYERS))
        self.assertTrue(all(row["core_owner"]["qualname"].endswith("wrapper") for row in proof))
        self.assertTrue(all(row["original_core_owner"]["qualname"].endswith("_forward_core") for row in proof))

    def test_missing_layer_receiver_override_and_subclass_fail_closed(self):
        for fault in ("missing", "override", "subclass", "wrong_prefix"):
            donor, target = classes(); native = donor._forward_core
            def wrapper(self, payload): return native(self, payload)
            bind_aliased_core(donor, target, wrapper)
            table = instances(target); key = next(iter(table))
            if fault == "missing": del table[key]
            elif fault == "override": table[key]._forward_core = native.__get__(table[key], target)
            elif fault == "wrong_prefix": table[key].prefix = "other.layers.0.linear_attn"
            else:
                class UnverifiedSubclass(target): pass
                value = UnverifiedSubclass(); value.prefix = key; table[key] = value
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                live_bindings(table, donor, target, wrapper)

    def test_outer_forward_alias_change_is_rejected(self):
        donor, target = classes()
        target.forward = lambda self, payload: payload
        with self.assertRaises(ValueError): verify_native_alias(donor, target)

    def test_frozen_binding_sources_are_full_sha256(self):
        self.assertEqual(len(BINDING_SOURCES), 3)
        for path, sha in BINDING_SOURCES.items():
            self.assertTrue(path.startswith("/vllm-workspace/"))
            self.assertEqual(len(sha), 64); int(sha, 16)


if __name__ == "__main__":
    unittest.main()
