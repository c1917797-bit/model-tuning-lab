"""Local pure-data controls only; never host/Docker/NPU admission."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), 'exec'), value.__dict__)
    return value


R = module('_restore_local_control', HERE / 'restore_snapshot_mounts_v1.py')
P = module('_producer_local_control', HERE.parent / 'final_snapshot_draft/final_snapshot_v4.py')
M = module('_main_local_control', HERE / 'main_admission_v4.py')


def fixture():
    a = dict(Type='bind', Source='/exact/source/α', Destination='/a', RW=False)
    b = dict(Type='bind', Source='/exact/source/b', Destination='/b', RW=True)
    changed = dict(b, Source='/exact/changed/b')
    arrays = [[a, b, a], [a, b, a][::-1], [changed, a, changed, b]]
    arrays[1] = [b, a, a]  # Same values/multiplicity, different full order.
    value = dict(schema='bole.final-readonly-host-snapshot/v4', complete=True, errors=[])
    for key in ('NPU', 'resources_admitted', 'candidate_qualification', 'numerical_qualified',
                'paired_gate_pass', 'performance_admitted', 'formal_performance'):
        value[key] = False
    for section, mounts in zip(('inspect_before', 'inspect_old_after', 'newly_running_inspect'), arrays):
        value[section] = dict(containers=[dict(Id='a'*64, mounts=copy.deepcopy(mounts))])
    original = copy.deepcopy(value)
    value['complete_mount_tables'] = P.share_complete_mount_members(types.SimpleNamespace(bounded=lambda: None), value)
    return json.loads(json.dumps(value)), original


class Controls(unittest.TestCase):
    def test_order_duplicates_change_and_whole_bytes(self):
        value, original = fixture()
        proof = R.restore(value)
        self.assertEqual(proof['array_count'], 3)
        self.assertEqual(proof['member_count'], 3)
        for section in ('inspect_before', 'inspect_old_after', 'newly_running_inspect'):
            self.assertEqual(R.canonical(value[section]), R.canonical(original[section]))
        self.assertFalse(proof['resources_admitted'])

    def reject_atomic(self, mutate):
        value, _ = fixture()
        mutate(value)
        before = copy.deepcopy(value)
        with self.assertRaises((ValueError, KeyError, IndexError)):
            R.restore(value)
        self.assertEqual(value, before)

    def test_corrupt_order_rejected_atomically(self):
        self.reject_atomic(lambda v: v['complete_mount_tables']['arrays'][2]['ordered_member_indices'].reverse())

    def test_boolean_index_rejected_atomically(self):
        self.reject_atomic(lambda v: v['complete_mount_tables']['arrays'][2]['ordered_member_indices'].__setitem__(0, True))

    def test_missing_binding_rejected_atomically(self):
        self.reject_atomic(lambda v: v['complete_mount_tables']['bindings'].pop())

    def test_member_hash_corruption_rejected_atomically(self):
        self.reject_atomic(lambda v: v['complete_mount_tables']['members'][0].__setitem__('Source', '/changed'))

    def test_failed_snapshot_rejected_atomically(self):
        self.reject_atomic(lambda v: v.__setitem__('complete', False))

    def test_producer_ref2_and_ref3_exact_complete_hash(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory)/'input.json'
            body = b'{"only":"read"}\n'
            path.write_bytes(body)
            ref2 = dict(path=str(path), sha256=hashlib.sha256(body).hexdigest())
            rs = M.Readset()
            self.assertEqual(rs.read(ref2), body)
            self.assertEqual(rs.read(dict(ref2, bytes=len(body))), body)
            self.assertEqual(rs.refs[str(path)]['bytes'], len(body))
            with self.assertRaises(ValueError):
                rs.read(dict(ref2, bytes=len(body)+1))
            with self.assertRaises(ValueError):
                rs.read(dict(ref2, sha256='0'*64))
            self.assertEqual(path.read_bytes(), body)

    def test_exact_create_argv_restores_only_saved_mount_order(self):
        owned = dict(mounts={'/a': ['/source/a', False], '/z': ['/source/z', True]})
        def create(value):
            argv = ['/docker', 'create', '--label', 'exact=label', '--device', '/dev/4:/dev/0:rwm']
            for destination, (source, rw) in value['mounts'].items():
                argv += ['--mount', 'type=bind,source=' + source + ',destination=' + destination + ('' if rw else ',readonly')]
            return argv + ['exact-image', '-c', 'exact-init']
        S = types.SimpleNamespace(create_argv=create)
        actual = create(dict(mounts={'/z': owned['mounts']['/z'], '/a': owned['mounts']['/a']}))
        self.assertNotEqual(actual, create(owned))
        self.assertTrue(M.exact_created_argv(actual, owned, S))
        for bad in (actual[:10] + actual[6:8] + actual[10:], actual[:6] + actual[8:],
                    [part.replace('exact=label', 'wrong=label') for part in actual],
                    [part.replace('source=/source/z', 'source=/changed') for part in actual]):
            with self.assertRaises(ValueError):
                M.exact_created_argv(bad, owned, S)

    def test_exec_limit_inheritance_exact_or_fail_closed(self):
        inf = M.resource.RLIM_INFINITY
        actual = {M.resource.RLIMIT_CPU: (inf, inf), M.resource.RLIMIT_FSIZE: (inf, inf),
                  M.resource.RLIMIT_AS: (512 * 2**20, inf)}
        with mock.patch.object(M.resource, 'getrlimit', side_effect=lambda key: actual[key]), \
             mock.patch.object(M.os, 'sched_getaffinity', return_value={166}):
            M.require_exec_limits()
            for key, wrong in ((M.resource.RLIMIT_CPU, (150, inf)),
                               (M.resource.RLIMIT_CPU, (150, 150)),
                               (M.resource.RLIMIT_FSIZE, (16 * 2**20, inf)),
                               (M.resource.RLIMIT_FSIZE, (16 * 2**20, 16 * 2**20)),
                               (M.resource.RLIMIT_AS, (512 * 2**20, 512 * 2**20))):
                original = actual[key]
                actual[key] = wrong
                with self.assertRaises(ValueError):
                    M.require_exec_limits()
                actual[key] = original

    def test_default_off_without_host_reads(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(HERE/'main_admission_v4.py')],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        value = json.loads(result.stdout)
        self.assertEqual(value, dict(enabled=False, frozen=False, NPU=False, resources_admitted=False))

    def test_unfrozen_check_rejected_before_inputs_or_host_reads(self):
        result = subprocess.run([sys.executable, '-I', '-B', str(HERE/'main_admission_v4.py'), '--check-only'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        value = json.loads(result.stdout)
        self.assertIn('draft is not frozen/reviewed', value['error'])
        self.assertFalse(value['resources_admitted'])
        self.assertFalse(value['dispatch_performed'])


if __name__ == '__main__':
    unittest.main()
