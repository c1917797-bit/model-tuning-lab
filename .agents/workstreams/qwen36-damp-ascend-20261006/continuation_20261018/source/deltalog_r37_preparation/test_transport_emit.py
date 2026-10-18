"""Pure transport controls; no model, closed data or actual prepare invocation."""
import sys
sys.dont_write_bytecode = True
import base64
import hashlib
import io
import json
from pathlib import Path
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import transport_emit as T


class Controls(unittest.TestCase):
    def setUp(self):
        self.generator = dict(path='/fixture/prepare.py', bytes=15171,
                              sha256=T.GENERATOR_SHA256)
        self.patch = dict(path='/fixture/patch.json', bytes=12, sha256='2'*64)
        self.model = '/fixture/new-model'
        self.early = '/fixture/new-early'
        self.big = '汉字"\\\n' * 20000
        self.bundle = dict(receipt=dict(prepared_only=True, qualified=False), trees={
            self.model: {'unchanged.py': 'original\n', 'modified.py': 'new\n',
                         'SOURCE_TEMPLATE.json': self.big},
            self.early: {'owner.py': 'owner\n'}})
        old_m = dict(files={
            'unchanged.py': T.ref('/fixture/old-model/unchanged.py', b'original\n'),
            'modified.py': T.ref('/fixture/old-model/modified.py', b'old\n')})
        old_e = dict(files={'owner.py': T.ref('/fixture/old-early/owner.py', b'owner\n')})
        self.preparer = types.SimpleNamespace(
            MODEL_NEW=self.model, EARLY_NEW=self.early,
            M_OLD_REF=T.ref('/fixture/old-model/SOURCE_TEMPLATE.json', json.dumps(old_m).encode()),
            E_OLD_REF=T.ref('/fixture/old-early/SOURCE_TEMPLATE.json', json.dumps(old_e).encode()))
        self.preparer.checked = lambda r: json.dumps(
            old_m if r == self.preparer.M_OLD_REF else old_e).encode()
        self.args = dict(receipt=False, index=False, files=False, fragment=False,
            expected_package_id=None, tree='model', offset=0, limit=32,
            names_json=None, name=None, byte_offset=0, byte_count=T.FRAGMENT_CAP)

    def value(self, **kwargs):
        return T.response(types.SimpleNamespace(**dict(self.args, **kwargs)),
                          self.preparer, self.bundle, self.generator, self.patch)

    def test_index_identifies_original_copy_and_changed_refs(self):
        rows = self.value(index=True)['entries']
        values = {r['relative_name']: r for r in rows}
        self.assertIsNotNone(values['unchanged.py']['unchanged_original_ref'])
        self.assertIsNone(values['modified.py']['unchanged_original_ref'])
        self.assertEqual(values['SOURCE_TEMPLATE.json']['transfer'], 'fragments-then-one-patch')

    def test_pagination_and_complete_inventory_digest(self):
        first = self.value(index=True, limit=1)
        second = self.value(index=True, offset=1, limit=2,
                            expected_package_id=first['package_id'])
        receipt = self.value(receipt=True)
        self.assertEqual(first['next_offset'], 1)
        self.assertIsNone(second['next_offset'])
        self.assertEqual(receipt['file_counts'], dict(model=3, early=1))
        self.assertEqual(receipt['package_id'], second['package_id'])

    def test_unknown_duplicate_or_traversal_names_refused(self):
        for names in (['missing.py'], ['../unchanged.py'], ['modified.py', 'modified.py'], [], [2]):
            with self.subTest(names=names), self.assertRaises(ValueError):
                self.value(files=True, names_json=json.dumps(names))

    def test_small_utf8_file_batch(self):
        value = self.value(files=True, names_json='["modified.py","unchanged.py"]')
        self.assertEqual(value['files']['modified.py']['utf8_content'], 'new\n')
        self.assertLessEqual(len(T.wire(value)), T.OUTPUT_CAP)

    def test_large_batch_refused_before_any_stdout(self):
        value = self.value(files=True, names_json='["SOURCE_TEMPLATE.json"]')
        output = types.SimpleNamespace(buffer=io.BytesIO())
        with patch.object(T.sys, 'stdout', output):
            with self.assertRaises(ValueError):
                T.emit(value)
        self.assertEqual(output.buffer.getvalue(), b'')

    def test_byte_fragments_reconstruct_multibyte_utf8_exactly(self):
        offset = 0
        pieces = []
        package_id = self.value(receipt=True)['package_id']
        while True:
            value = self.value(fragment=True, name='SOURCE_TEMPLATE.json',
                               byte_offset=offset, expected_package_id=package_id)
            self.assertLessEqual(len(T.wire(value)), T.OUTPUT_CAP)
            piece = base64.b64decode(value['base64'], validate=True)
            self.assertEqual(len(piece), value['fragment_bytes'])
            self.assertEqual(hashlib.sha256(piece).hexdigest(), value['fragment_sha256'])
            pieces.append(piece)
            offset = value['next_byte_offset']
            if offset is None:
                break
        actual = b''.join(pieces)
        self.assertEqual(actual, self.big.encode('utf8'))
        self.assertEqual(T.ref(self.model+'/SOURCE_TEMPLATE.json', actual), value['ref'])

    def test_mixed_package_and_source_ref_refused(self):
        package_id = self.value(receipt=True)['package_id']
        self.bundle['trees'][self.early]['owner.py'] += 'changed\n'
        with self.assertRaises(ValueError):
            self.value(index=True, expected_package_id=package_id)
        self.bundle['trees'][self.early]['owner.py'] = 'owner\n'
        self.patch = dict(self.patch, sha256='3'*64)
        with self.assertRaises(ValueError):
            self.value(index=True, expected_package_id=package_id)

    def test_negative_offset_and_overlarge_pages_refused(self):
        for kwargs in (dict(index=True, offset=-1), dict(index=True, offset=99),
                       dict(index=True, limit=65), dict(fragment=True, name='modified.py', byte_offset=4),
                       dict(fragment=True, name='modified.py', byte_count=T.FRAGMENT_CAP+1)):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.value(**kwargs)

    def test_actual_frozen_generator_authenticates_and_remains_unmodified(self):
        path = HERE / 'prepare_r37.py'
        raw = path.read_bytes()
        value = T.ref(str(path), raw)
        module = T.load_generator(value)
        self.assertTrue(callable(module.prepare))
        self.assertEqual(path.read_bytes(), raw)
        with self.assertRaises(ValueError):
            T.checked_generator(dict(value, sha256='0'*64))


if __name__ == '__main__':
    unittest.main()
