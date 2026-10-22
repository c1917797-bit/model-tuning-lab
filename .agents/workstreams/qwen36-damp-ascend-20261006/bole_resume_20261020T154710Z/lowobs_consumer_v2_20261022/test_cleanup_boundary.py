"""Source-only controls using retained ON-v2 cleanup bytes, not NPU results."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'fixtures' / 'original_ON_v2'
EXPECTED = {
    'cpu-preflight': (1245, 'f933c4c006a3eaa29745bd1de5b2939d4c407a456ead0e9d149dc20286bf69cd'),
    'dense': (1213, '54bcb155380f1d0b5762a3b22433a8592c8cf0352d355b7f53825351475d562d'),
}


def load_reader(filename, root=ROOT):
    path = root / filename
    spec = importlib.util.spec_from_file_location('_local_control_' + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


READERS = (
    load_reader('read_short_results_v2.py'),
    load_reader('consume_pair_v2.py'),
)


def fixture(role):
    path = FIXTURES / role / 'cleanup.json'
    data = path.read_bytes()
    size, sha = EXPECTED[role]
    if (len(data), hashlib.sha256(data).hexdigest()) != (size, sha):
        raise ValueError('retained real producer fixture bytes changed')
    # This local fixture Ref rebases only the path. Its JSON bytes and original
    # producer SHA are unchanged; it is never represented as a new experiment.
    return path, {'path': str(path), 'sha256': sha}, data


class CleanupBoundaryTests(unittest.TestCase):
    def test_retained_real_producer_bytes_are_read_without_rewriting(self):
        for role in EXPECTED:
            path, summary, data = fixture(role)
            original_summary = dict(summary)
            for reader in READERS:
                with self.subTest(role=role, reader=reader.__name__):
                    value = reader.cleanup_obj(summary, path)
                    self.assertEqual(value, json.loads(data))
                    self.assertIs(value['stopped'], True)
                    self.assertIs(value['retained'], True)
                    self.assertEqual(value['errors'], [])
                    self.assertEqual(summary, original_summary)
                    self.assertEqual(path.read_bytes(), data)

    def test_generic_ref3_parser_still_rejects_the_producer_ref2(self):
        _, summary, _ = fixture('dense')
        for reader in READERS:
            with self.subTest(reader=reader.__name__):
                with self.assertRaisesRegex(ValueError, 'exact Ref'):
                    reader.obj(summary)

    def test_bad_whole_sha_is_rejected(self):
        path, summary, _ = fixture('dense')
        for reader in READERS:
            with self.subTest(reader=reader.__name__):
                with self.assertRaisesRegex(ValueError, 'whole cleanup evidence SHA256'):
                    reader.cleanup_obj(dict(summary, sha256='0' * 64), path)

    def test_cross_role_expected_path_is_rejected(self):
        _, summary, _ = fixture('cpu-preflight')
        expected, _, _ = fixture('dense')
        for reader in READERS:
            with self.subTest(reader=reader.__name__):
                with self.assertRaisesRegex(ValueError, 'expected cleanup path'):
                    reader.cleanup_obj(summary, expected)

    def test_cleanup_adapter_does_not_accept_a_ref3_alias(self):
        path, summary, data = fixture('dense')
        for reader in READERS:
            with self.subTest(reader=reader.__name__):
                with self.assertRaisesRegex(ValueError, 'exact cleanup summary shape'):
                    reader.cleanup_obj(dict(summary, bytes=len(data)), path)

    def test_cached_module_alias_cannot_replace_pinned_helper(self):
        path, summary, data = fixture('dense')
        poison = types.ModuleType('cleanup_summary')
        poison.read_cleanup_summary = mock.Mock(side_effect=AssertionError('wrong helper alias'))
        aliases = {'cleanup_summary': poison, '_bole_lowobs_cleanup_summary_v2': poison}
        with mock.patch.dict(sys.modules, aliases):
            for reader in READERS:
                with self.subTest(reader=reader.__name__):
                    self.assertEqual(reader.cleanup_obj(summary, path), json.loads(data))
        poison.read_cleanup_summary.assert_not_called()

    def test_changed_helper_bytes_are_rejected_before_execution(self):
        scratch = ROOT / 'validation_tmp'
        scratch.mkdir(exist_ok=True)
        path, summary, _ = fixture('dense')
        for filename in ('read_short_results_v2.py', 'consume_pair_v2.py'):
            with self.subTest(reader=filename):
                with tempfile.TemporaryDirectory(prefix='helper-pin-', dir=scratch) as temp:
                    root = Path(temp)
                    (root / filename).write_bytes((ROOT / filename).read_bytes())
                    (root / 'cleanup_summary.py').write_bytes(
                        (ROOT / 'cleanup_summary.py').read_bytes() + b'\n')
                    reader = load_reader(filename, root)
                    with self.assertRaisesRegex(ValueError, 'exact copied cleanup summary helper'):
                        reader.cleanup_obj(summary, path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
