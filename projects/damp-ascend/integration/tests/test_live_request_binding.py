"""No-framework contracts for the real copied-Qwen binding and text admission."""
import unittest
from types import SimpleNamespace
from damp_integration.contract import (
    GDN_LAYERS, Unsupported, admit_text_forward, admit_text_request,
    require_copied_native, typed_gdn_target, verify_live_layers,
)
from damp_integration.patch import SOURCES


def fixture():
    class Base:
        pass
    def native(self, *args, **kwargs):
        return "native"
    def outer(self, *args, **kwargs):
        return "outer"
    class Donor(Base):
        _forward_core = native
        forward = outer
    class Qwen(Base):
        _forward_core = Donor._forward_core
        forward = Donor.forward
    def hook(self, *args, **kwargs):
        return native(self, *args, **kwargs)
    return Base, Donor, Qwen, native, outer, hook


def layers_for(target):
    layers = {}
    for index in GDN_LAYERS:
        obj = target()
        obj.layer_idx = index
        obj.prefix = "model.layers." + str(index) + ".linear_attn"
        layers[obj.prefix] = obj
    return layers


def request(**changes):
    fields = dict(req_id="r", prompt_token_ids=[3, 7], mm_features=[],
                  prompt_embeds=None, prompt_is_token_ids=None)
    fields.update(changes)
    return SimpleNamespace(**fields)


class BindingTests(unittest.TestCase):
    def test_real_source_pins(self):
        self.assertEqual(SOURCES["/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py"],
                         "21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3")
        self.assertEqual(SOURCES["/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py"],
                         "885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0")

    def test_donor_only_patch_does_not_patch_receiver(self):
        base, donor, target, native, outer, hook = fixture()
        require_copied_native(target, donor)
        donor._forward_core = hook
        self.assertIs(target._forward_core, native)
        self.assertFalse(isinstance(target(), donor))
        with self.assertRaises(Unsupported):
            require_copied_native(target, donor)
        with self.assertRaises(Unsupported):
            verify_live_layers(layers_for(target), layers_for(target), target, hook, outer)

    def test_dual_binding_all_48_actual_instances(self):
        base, donor, target, native, outer, hook = fixture()
        require_copied_native(target, donor)
        donor._forward_core = target._forward_core = hook
        layers = layers_for(target)
        dispatch = dict(layers, unrelated_full_attention=object())
        self.assertEqual(len(verify_live_layers(dispatch, layers, target, hook, outer)), 48)
        self.assertEqual(next(iter(layers.values()))._forward_core(), "native")

    def test_typed_spec_checks_actual_qwen_not_donor_isinstance(self):
        base, donor, target, native, outer, hook = fixture()
        self.assertTrue(typed_gdn_target(target(), base, target))
        self.assertFalse(typed_gdn_target(object(), base, target))
        for obj in (base(), donor()):
            with self.assertRaises(Unsupported):
                typed_gdn_target(obj, base, target)

    def test_missing_or_duplicate_layer_rejected(self):
        base, donor, target, native, outer, hook = fixture()
        donor._forward_core = target._forward_core = hook
        layers = layers_for(target)
        name = next(iter(layers))
        for dispatch in (None, {}, {k: v for k, v in layers.items() if k != name}):
            with self.assertRaises(Unsupported):
                verify_live_layers(dispatch, layers, target, hook, outer)
        del layers[name]
        with self.assertRaises(Unsupported):
            verify_live_layers(layers, layers, target, hook, outer)
        layers = layers_for(target)
        next(iter(layers.values())).layer_idx = 1
        with self.assertRaises(Unsupported):
            verify_live_layers(layers, layers, target, hook, outer)

    def test_wrong_actual_object_prefix_or_class_rejected(self):
        base, donor, target, native, outer, hook = fixture()
        donor._forward_core = target._forward_core = hook
        layers = layers_for(target)
        name = next(iter(layers))
        other = target()
        other.prefix, other.layer_idx = name, 0
        with self.assertRaises(Unsupported):
            verify_live_layers(dict(layers, **{name: other}), layers, target, hook, outer)
        layers[name].prefix = "wrong"
        with self.assertRaises(Unsupported):
            verify_live_layers(layers, layers, target, hook, outer)

    def test_core_or_outer_shadowing_rejected(self):
        base, donor, target, native, outer, hook = fixture()
        donor._forward_core = target._forward_core = hook
        layers = layers_for(target)
        target._forward_core = native
        with self.assertRaises(Unsupported):
            verify_live_layers(layers, layers, target, hook, outer)
        target._forward_core = hook
        target.forward = lambda self: None
        with self.assertRaises(Unsupported):
            verify_live_layers(layers, layers, target, hook, outer)

    def test_native_binding_changed_before_install_rejected(self):
        base, donor, target, native, outer, hook = fixture()
        target._forward_core = hook
        with self.assertRaises(Unsupported):
            require_copied_native(target, donor)
        target._forward_core = native
        target.forward = lambda self: None
        with self.assertRaises(Unsupported):
            require_copied_native(target, donor)


class TextPayloadTests(unittest.TestCase):
    def test_plain_token_request(self):
        admit_text_request(request(), "r", 2)
        admit_text_request(request(prompt_is_token_ids=[True, True]), "r", 2)

    def test_media_rejected_even_with_text_like_positions(self):
        for features in ([object()], None, {}):
            cached = request(mm_features=features)
            cached.mrope_positions = [[0, 1]] * 3
            with self.subTest(features=features), self.assertRaises(Unsupported):
                admit_text_request(cached, "r", 2)

    def test_user_embedding_and_mixed_mask_rejected(self):
        for changes in (
            dict(prompt_embeds=object()), dict(prompt_embeds=[]),
            dict(prompt_token_ids=None), dict(prompt_is_token_ids=[True, False]),
            dict(prompt_is_token_ids=[1, 1]), dict(prompt_is_token_ids=[True]),
        ):
            with self.subTest(changes=changes), self.assertRaises(Unsupported):
                admit_text_request(request(**changes), "r", 2)

    def test_request_schema_and_identity_fail_closed(self):
        with self.assertRaises(Unsupported):
            admit_text_request(request(), "other", 2)
        for field in ("req_id", "prompt_token_ids", "mm_features", "prompt_embeds", "prompt_is_token_ids"):
            cached = request()
            delattr(cached, field)
            with self.subTest(field=field), self.assertRaises(Unsupported):
                admit_text_request(cached, "r", 2)
        with self.assertRaises(Unsupported):
            admit_text_request(request(), "r", 3)

    def test_native_text_embeddings_are_not_user_soft_prompts(self):
        native = object()
        self.assertEqual(admit_text_forward(None, native, None, {}, True), "inputs_embeds")
        self.assertEqual(admit_text_forward(native, native, None, {}, True, True), "inputs_embeds")
        self.assertEqual(admit_text_forward(native, None, None, {}, False), "input_ids")
        for ids, embeds, supports in ((None, None, True), (native, native, True),
                                     (native, None, True), (None, native, False)):
            with self.subTest(supports=supports), self.assertRaises(Unsupported):
                admit_text_forward(ids, embeds, None, {}, supports)

    def test_encoder_media_and_unknown_kwargs_rejected(self):
        native = object()
        for key in ("encoder_inputs", "encoder_outputs", "pixel_values", "image_grid_thw",
                    "multi_modal_data", "future_unknown"):
            with self.subTest(key=key), self.assertRaises(Unsupported):
                admit_text_forward(None, native, None, {key: None}, True)
        with self.assertRaises(Unsupported):
            admit_text_forward(None, native, object(), {}, True)
        with self.assertRaises(Unsupported):
            admit_text_forward(None, native, None, {}, 1)
        with self.assertRaises(Unsupported):
            admit_text_forward(None, native, None, {}, True, True)
        with self.assertRaises(Unsupported):
            admit_text_forward(None, native, None, {}, True, 1)


if __name__ == "__main__":
    unittest.main()
