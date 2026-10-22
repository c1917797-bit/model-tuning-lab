"""CPU-only opt-in, exclusive-output, accounting and hook-lifecycle controls.

These tests contain no NPU numerical/state qualification and do not replace
or rename the original twenty short-profile controls.
"""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

_spec = importlib.util.spec_from_file_location('boundary_probe_test_subject',
                                              Path(__file__).with_name('boundary_probe_v1.py'))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)


class Bomb:
    def __getattribute__(self, key):
        raise AssertionError('disabled path accessed owner/runtime: ' + key)


class FakeModule:
    def __init__(self):
        self._forward_hooks = {0: 'pre-existing-foreign-hook'}
        self.serial = 1

    def register_forward_hook(self, callback):
        index = self.serial
        self.serial += 1
        self._forward_hooks[index] = callback
        return SimpleNamespace(id=index, remove=lambda: self._forward_hooks.pop(index))


class BoundaryControls(unittest.TestCase):
    def test_exact_logical_scope_and_bounded_raw_reservation(self):
        self.assertIs(B.DECLARATION['hash_native0_inputs'], True)
        self.assertEqual((len(B.RAW_SHAPES), len(B.GDN_LAYERS), len(B.PHASES)), (9, 48, 5))
        logical = 0
        for shape in B.RAW_SHAPES.values():
            elements = 1
            for axis in shape:
                elements *= axis
            self.assertEqual(elements % 131, 0)
            logical += elements * 2
        self.assertEqual(logical * 8 // 131 * 2, B.RAW_CAP)
        total = 2 * 6 * 48 * (786432 + 16 * 2560 * 2) + logical * 2 + 677008 * 2
        self.assertEqual(total, 515220032)
        self.assertLessEqual(total, B.DEVICE_READ_CAP)

    def test_wrong_boundary_order_is_sticky_before_tensor_read(self):
        probe = B.Probe.__new__(B.Probe)
        probe._identity = lambda: None
        probe.failed, probe.scope, probe.phase = False, False, -1
        probe.bindings = []
        probe.t = Bomb()
        with self.assertRaises(ValueError):
            probe.capture('initial_mtp_after')
        self.assertIs(probe.failed, True)
        self.assertEqual(probe.phase, -1)

    def test_disabled_never_accesses_runtime_or_owner(self):
        for value in (None, '', '0'):
            environ = {} if value is None else {B.FLAG: value}
            self.assertIsNone(B.create(Bomb(), Bomb(), Bomb(), {}, environ,
                                      Bomb(), Bomb(), Bomb()))

    def test_both_optins_and_exact_typed_declaration_required(self):
        for environ, declaration in (({}, B.DECLARATION), ({B.FLAG: '0'}, B.DECLARATION),
                                     ({B.FLAG: '1'}, None), ({B.FLAG: 'yes'}, B.DECLARATION)):
            with self.assertRaises(ValueError):
                B.select(environ, declaration)
        changed = copy.deepcopy(B.DECLARATION)
        changed['generations'] = True
        with self.assertRaises(ValueError):
            B.select({B.FLAG: '1'}, changed)
        changed = copy.deepcopy(B.DECLARATION)
        changed['extra_qualification'] = True
        with self.assertRaises(ValueError):
            B.select({B.FLAG: '1'}, changed)
        self.assertEqual(B.select({B.FLAG: '1'}, copy.deepcopy(B.DECLARATION)), B.DECLARATION)

    def test_exclusive_write_and_sticky_no_retry(self):
        with tempfile.TemporaryDirectory() as d:
            seen = []
            writer = B.Writer(Path(d) / 'rank', seen.append)
            first = writer.put('first.bin', b'original', raw=True)
            self.assertEqual(seen, [8, 0])
            self.assertEqual(Path(first['path']).read_bytes(), b'original')
            with self.assertRaises(FileExistsError):
                writer.put('first.bin', b'replace!', raw=True)
            self.assertEqual(Path(first['path']).read_bytes(), b'original')
            with self.assertRaises(ValueError):
                writer.put('new.bin', b'x', raw=True)
            self.assertFalse((writer.root / 'new.bin').exists())

    def test_admission_recounts_real_files_including_foreign_partial(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'rank'
            def admission(prospective):
                actual = sum(p.stat().st_size for p in root.iterdir())
                B.need(actual + prospective <= 8, 'real aggregate cap')
            writer = B.Writer(root, admission)
            writer.put('first.bin', b'abcd', raw=True)
            (root / 'interrupted.bin').write_bytes(b'12345')
            with self.assertRaises(ValueError):
                writer.put('second.bin', b'z', raw=True)
            self.assertFalse((root / 'second.bin').exists())

    def test_per_file_and_total_raw_caps_before_write(self):
        with tempfile.TemporaryDirectory() as d:
            writer = B.Writer(Path(d) / 'one', lambda n: None)
            with self.assertRaises(ValueError):
                writer.put('oversize.bin', b'x' * (96 * 1024 + 1), raw=True)
            self.assertEqual(list(writer.root.iterdir()), [])
            writer = B.Writer(Path(d) / 'two', lambda n: None)
            remaining = B.RAW_CAP
            index = 0
            while remaining:
                size = min(96 * 1024, remaining)
                writer.put('%d.bin' % index, b'x' * size, raw=True)
                remaining -= size
                index += 1
            with self.assertRaises(ValueError):
                writer.put('overflow.bin', b'x', raw=True)
            self.assertEqual(writer.raw, B.RAW_CAP)
            self.assertFalse((writer.root / 'overflow.bin').exists())

    def test_plain_exclusive_directory_and_filenames(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            (base / 'real').mkdir()
            (base / 'link').symlink_to(base / 'real', target_is_directory=True)
            with self.assertRaises(ValueError):
                B.Writer(base / 'link' / 'rank', lambda n: None)
            for index, name in enumerate(('../escape.bin', 'child/file.bin', '.hidden.bin')):
                writer = B.Writer(base / ('rank%d' % index), lambda n: None)
                with self.assertRaises(ValueError):
                    writer.put(name, b'no', raw=True)
                self.assertEqual(list(writer.root.iterdir()), [])

    def test_inactive_hooks_return_none_and_remove_only_own_handles(self):
        modules = [FakeModule() for _ in range(4)]
        probe = B.Probe.__new__(B.Probe)
        probe.model = SimpleNamespace(layers=[SimpleNamespace(
            linear_attn=SimpleNamespace(norm=modules[0], out_proj=modules[1]),
            post_attention_layernorm=modules[2], mlp=modules[3])])
        probe.scope = False
        probe.handles, probe.hook_owners = [], []
        probe._identity = lambda: self.fail('inactive hook accessed live request')
        probe._raw = lambda *args: self.fail('inactive hook read a tensor')
        probe._install_hooks()
        self.assertEqual(len(probe.handles), 4)
        original = object()
        for module, handle, hook in probe.hook_owners:
            self.assertIsNone(hook(module, (), original))
            self.assertIs(module._forward_hooks[handle.id], hook)
        probe.uninstall()
        self.assertTrue(all(m._forward_hooks == {0: 'pre-existing-foreign-hook'} for m in modules))
        probe.uninstall()  # Safe lifecycle restorer after the explicit final removal.

    def test_foreign_hook_replacement_is_not_removed(self):
        probe = B.Probe.__new__(B.Probe)
        module = FakeModule()
        original = lambda *args: None
        handle = module.register_forward_hook(original)
        replacement = lambda *args: None
        module._forward_hooks[handle.id] = replacement
        probe.handles = [handle]
        probe.hook_owners = [(module, handle, original)]
        with self.assertRaises(ValueError):
            probe.uninstall()
        self.assertIs(module._forward_hooks[handle.id], replacement)

    def test_original_other_and_global_caps_are_enforced(self):
        probe = B.Probe.__new__(B.Probe)
        charges = dict(other=3 * 2**20 - B.OTHER_HEADROOM)
        value = dict(charges=charges, bytes=20 * 2**20)
        probe.B = SimpleNamespace(OTHER=3 * 2**20, actual=lambda *a: value)
        probe.G = SimpleNamespace(METADATA_CAP=64 * 2**20, RAW_CAP=2**30,
                                  FRAME_LOGICAL_CAP=384 * 2**20,
                                  FRAME_WIRE_CAP=448 * 2**20, CHECKPOINT_CAP=128 * 2**20)
        probe.C, probe.manifest, probe.rank = None, {}, 0
        probe._budget(0)
        with self.assertRaises(ValueError):
            probe._budget(1)
        charges['other'] = 0
        value['bytes'] = 56 * 2**20 + 1
        with self.assertRaises(ValueError):
            probe._budget(0)


if __name__ == '__main__':
    unittest.main(verbosity=2)

