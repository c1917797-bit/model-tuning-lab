"""Device-free regression controls for the exact cleanup-summary boundary."""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cleanup_summary as C


class ReadMutation:
    def __init__(self, stream, mutate):
        self.stream, self.mutate = stream, mutate

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()

    def fileno(self):
        return self.stream.fileno()

    def read(self, limit):
        data = self.stream.read(limit)
        self.mutate()
        return data


class CleanupSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cleanup-summary-v4-')
        self.root = Path(self.temp.name)
        self.path = self.root / 'cleanup.json'
        self.value = {'stopped': True, 'retained': True, 'errors': []}
        self.data = (json.dumps(self.value, sort_keys=True) + '\n').encode()
        self.path.write_bytes(self.data)
        self.summary = self.summary_for(self.path)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def summary_for(path):
        return {'path': str(path),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def test_exact_summary_derives_full_ref_and_parses_verified_bytes(self):
        original = dict(self.summary)
        derived, value = C.read_cleanup_summary(self.summary, self.path)
        self.assertEqual(derived, dict(original, bytes=len(self.data)))
        self.assertEqual(value, self.value)
        self.assertEqual(self.summary, original)
        self.assertEqual(self.path.read_bytes(), self.data)

    def test_accepts_exact_cap_whole_file(self):
        self.path.write_bytes(self.data + b' ' * (C.CAP - len(self.data)))
        derived, value = C.read_cleanup_summary(self.summary_for(self.path), self.path)
        self.assertEqual(derived['bytes'], C.CAP)
        self.assertEqual(value, self.value)

    def test_rejects_oversize_before_open(self):
        with self.path.open('wb') as stream:
            stream.truncate(C.CAP + 1)
        with mock.patch.object(C.os, 'open') as opening:
            with self.assertRaisesRegex(ValueError, 'bounded complete'):
                C.read_cleanup_summary(self.summary, self.path)
        opening.assert_not_called()

    def test_rejects_extra_or_missing_keys(self):
        variants = [dict(self.summary, bytes=len(self.data)),
                    {'path': self.summary['path']},
                    {'sha256': self.summary['sha256']}, {},
                    dict(self.summary, unexpected=None)]
        for variant in variants:
            with self.subTest(variant=variant):
                with self.assertRaisesRegex(ValueError, 'summary shape'):
                    C.read_cleanup_summary(variant, self.path)

    def test_rejects_wrong_container_types(self):
        class DictSubclass(dict):
            pass
        for value in [None, [], (), 'path', DictSubclass(self.summary)]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'summary shape'):
                    C.read_cleanup_summary(value, self.path)

    def test_rejects_wrong_field_types(self):
        for field in ['path', 'sha256']:
            for value in [None, 0, True, [], {}, self.path]:
                with self.subTest(field=field, value=value):
                    variant = dict(self.summary)
                    variant[field] = value
                    with self.assertRaisesRegex(ValueError, 'must be strings'):
                        C.read_cleanup_summary(variant, self.path)

    def test_rejects_invalid_sha_shape(self):
        for digest in ['', '0' * 63, '0' * 65, 'g' * 64, 'A' * 64]:
            with self.subTest(digest=digest):
                with self.assertRaisesRegex(ValueError, 'lowercase SHA256'):
                    C.read_cleanup_summary(dict(self.summary, sha256=digest), self.path)

    def test_rejects_wrong_whole_sha(self):
        with self.assertRaisesRegex(ValueError, 'whole cleanup evidence SHA256'):
            C.read_cleanup_summary(dict(self.summary, sha256='0' * 64), self.path)

    def test_rejects_suffix_not_covered_by_supplied_sha(self):
        with self.path.open('ab') as stream:
            stream.write(b' ')
        with self.assertRaisesRegex(ValueError, 'whole cleanup evidence SHA256'):
            C.read_cleanup_summary(self.summary, self.path)

    def test_rejects_mismatched_expected_path(self):
        with self.assertRaisesRegex(ValueError, 'expected cleanup path'):
            C.read_cleanup_summary(self.summary, self.root / 'other.json')

    def test_rejects_relative_noncanonical_or_parent_traversal_paths(self):
        variants = ['cleanup.json', str(self.root) + '//cleanup.json',
                    str(self.root) + '/./cleanup.json',
                    str(self.root) + '/sub/../cleanup.json',
                    str(self.path) + '\x00']
        for path in variants:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    C.read_cleanup_summary(dict(self.summary, path=path), path)
        with self.assertRaisesRegex(ValueError, 'expected cleanup path'):
            C.read_cleanup_summary(self.summary, Path('cleanup.json'))

    def test_rejects_wrong_expected_path_type(self):
        for value in [None, True, 1, [], {}]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, 'expected cleanup path'):
                    C.read_cleanup_summary(self.summary, value)

    def test_rejects_directory(self):
        with self.assertRaisesRegex(ValueError, 'ordinary regular file'):
            C.read_cleanup_summary(dict(self.summary, path=str(self.root)), self.root)

    def test_rejects_fifo_without_opening(self):
        fifo = self.root / 'pipe'
        os.mkfifo(str(fifo))
        with mock.patch.object(C.os, 'open') as opening:
            with self.assertRaisesRegex(ValueError, 'ordinary regular file'):
                C.read_cleanup_summary(dict(self.summary, path=str(fifo)), fifo)
        opening.assert_not_called()

    def test_rejects_leaf_symlink(self):
        link = self.root / 'cleanup-link.json'
        link.symlink_to(self.path)
        with self.assertRaisesRegex(ValueError, 'ordinary regular file'):
            C.read_cleanup_summary(dict(self.summary, path=str(link)), link)

    def test_rejects_ancestor_symlink(self):
        real = self.root / 'real'
        real.mkdir()
        target = real / 'cleanup.json'
        target.write_bytes(self.data)
        link = self.root / 'linked'
        link.symlink_to(real, target_is_directory=True)
        path = link / 'cleanup.json'
        with self.assertRaisesRegex(ValueError, 'ordinary directories'):
            C.read_cleanup_summary(dict(self.summary, path=str(path)), path)

    def test_rejects_invalid_json_after_valid_sha(self):
        self.path.write_bytes(b'{broken json}\n')
        with self.assertRaises(json.JSONDecodeError):
            C.read_cleanup_summary(self.summary_for(self.path), self.path)

    def mutated_read(self, mutate):
        original = os.fdopen
        def open_wrapped(descriptor, mode):
            return ReadMutation(original(descriptor, mode), mutate)
        return mock.patch.object(C.os, 'fdopen', side_effect=open_wrapped)

    def test_rejects_file_growth_during_read(self):
        def mutate():
            with self.path.open('ab') as stream:
                stream.write(b' ')
        with self.mutated_read(mutate):
            with self.assertRaisesRegex(ValueError, 'changed during read'):
                C.read_cleanup_summary(self.summary, self.path)

    def test_rejects_same_size_file_mutation_during_read(self):
        def mutate():
            previous = self.path.stat()
            self.path.write_bytes(b' ' * len(self.data))
            os.utime(str(self.path), ns=(previous.st_atime_ns, previous.st_mtime_ns + 1_000_000_000))
        with self.mutated_read(mutate):
            with self.assertRaisesRegex(ValueError, 'changed during read'):
                C.read_cleanup_summary(self.summary, self.path)

    def test_rejects_path_replacement_even_with_equal_content(self):
        other = self.root / 'replacement.json'
        other.write_bytes(self.data)
        with self.mutated_read(lambda: os.replace(str(other), str(self.path))):
            with self.assertRaisesRegex(ValueError, 'changed during read'):
                C.read_cleanup_summary(self.summary, self.path)

    def test_rejects_parent_replaced_with_symlink_during_read(self):
        directory = self.root / 'original'
        directory.mkdir()
        self.path = directory / 'cleanup.json'
        self.path.write_bytes(self.data)
        self.summary = self.summary_for(self.path)
        moved = self.root / 'moved'
        def mutate():
            directory.rename(moved)
            directory.symlink_to(moved, target_is_directory=True)
        with self.mutated_read(mutate):
            with self.assertRaisesRegex(ValueError, 'ordinary directories'):
                C.read_cleanup_summary(self.summary, self.path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
