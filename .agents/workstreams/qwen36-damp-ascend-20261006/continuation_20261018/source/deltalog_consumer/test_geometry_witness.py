"""Pure CPU controls. Synthetic metadata is never NPU/model qualification."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import geometry_witness as G


def ref(path, raw):
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def source(name):
    return ref(Path('/synthetic-no-model-execution') / name, name.encode())


class Alias:
    """Only a fixture path alias, no actual model execution or permission."""
    def __init__(self, root):
        self.root = root

    def actual_ref(self, value):
        p = Path(value['path'])
        return dict(value, path=str(self.root / p.relative_to(G.GUEST_ROOT)))


def fixture(rank=0, pid=311):
    report = dict(source=source('payload.json'), model_source=source('model.json'),
        domain=dict(cid='fixture-cid-only', host_pid=7000 + rank, start_ticks=991,
                    physical=rank + 4, rank=rank), namespace_pid=pid,
        active_metadata=dict(pools=[], selections=[]), raw_bytes=100,
        storage_budget=dict(prefill_control=source('PREFILL-COMPLETE.json'),
                            snapshot_bytes=200, controls_before_final_bytes=0))
    rows, ptr = [], 2**40
    for layer in range(64):
        kind = 'GDN' if layer < 48 else 'FA'
        roles = ('conv', 'base', 'K', 'U', 'lambda_log', 'decay', 'length') \
            if kind == 'GDN' else ('K', 'V')
        for role in roles:
            if kind == 'FA':
                dtype, shape = 'torch.bfloat16', [17, 128, 2, 128]
            else:
                dtype, shape = {
                    'conv': ('torch.float32', [2, 768, 4]),
                    'base': ('torch.float32', [2, 12, 128, 128]),
                    'K': ('torch.bfloat16', [2, 4, 7, 128]),
                    'U': ('torch.float32', [2, 12, 7, 128]),
                    'lambda_log': ('torch.float32', [2, 12, 16]),
                    'decay': ('torch.float32', [2, 12, 16]),
                    'length': ('torch.int32', [2, 12, 16])}[role]
            stride, count = [], 1
            for n in reversed(shape):
                stride.insert(0, count)
                count *= n
            dt, element = G.DTYPES[dtype]
            pool = dict(index=len(rows), pointer=ptr, nbytes=count * element)
            report['active_metadata']['pools'].append(pool)
            geometry = dict(pointer=ptr, storage_offset=0, element_bytes=element,
                            dtype=dt, shape=shape, strides=stride, format_code=2)
            selection = dict(prefix='layer.%d' % layer, group=int(kind == 'FA'),
                role=role, kind=kind, pool=pool['index'], geometry=geometry,
                cpu_rows=[0] if kind == 'GDN' else list(range(17)),
                gpu_rows=[0] if kind == 'GDN' else list(range(17)),
                physical_rows=[] if kind == 'GDN' else list(range(17)),
                physical_block_tokens=128, kernel_block_tokens=128,
                writes=[] if kind == 'GDN' else [[16, 0, 512]])
            report['active_metadata']['selections'].append(selection)
            rows.append(dict(schema=G.ROW_SCHEMA, source=report['source'],
                model_source=report['model_source'], domain=report['domain'], pid=pid,
                prefix=selection['prefix'], group=selection['group'], role=role,
                tensor_identity=100000 + len(rows), shape=shape, stride=stride,
                storage_offset=0, element_bytes=element, dtype=dtype,
                device='npu:%d' % rank, numel=count, contiguous=True,
                pointer=ptr, storage_pointer=ptr, storage_bytes=pool['nbytes'],
                storage_identity=200000 + len(rows), qualification=False,
                numerical_executed=False, format_code=2, format_error=None,
                predicate=dict(contiguous=True, positive=True, ND2=True)))
            ptr += pool['nbytes'] + 4096
    return report, rows


def observer_bytes(rows):
    # Exact production observer serialization; never report/reserialized length.
    return b''.join((json.dumps(row, sort_keys=True, allow_nan=False) + '\n').encode()
                    for row in rows)


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='geometry-control-', dir=HERE)
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.report, self.rows = fixture()
        self.path = self.root / 'FIRST-DECODE-GEOMETRY-p311.jsonl'
        self.aio = Alias(self.root)

    def write(self, rows=None, raw=None):
        raw = observer_bytes(self.rows if rows is None else rows) if raw is None else raw
        self.path.write_bytes(raw)
        self.report['storage_budget']['controls_before_final_bytes'] = \
            self.report['storage_budget']['prefill_control']['bytes'] + len(raw)
        return ref(self.path, raw)

    def validate(self, rr=None):
        return G.validate_geometry_witness(self.report, rr or self.write(), self.aio)

    def refuses(self, operation):
        with self.assertRaises((ValueError, OSError, KeyError, TypeError)):
            operation()

    def test_production_nonzero_observer_ledger_old_fails_new_passes(self):
        rr = self.write()
        b = self.report['storage_budget']
        self.assertEqual(368, len(self.rows))
        self.assertGreater(rr['bytes'], 0)
        self.assertLessEqual(rr['bytes'], G.MAX_BYTES)
        self.assertNotEqual(b['controls_before_final_bytes'], b['prefill_control']['bytes'])
        witness = self.validate(rr)
        value = G.validate_control_accounting(self.report, witness, 1000)
        self.assertEqual(value['geometry_bytes'], rr['bytes'])
        self.assertFalse(witness.evidence()['qualification'])

    def test_rank_three_valid(self):
        self.report, self.rows = fixture(3, 314)
        self.path = self.root / 'FIRST-DECODE-GEOMETRY-p314.jsonl'
        self.assertEqual(self.validate().rank, 3)

    def test_bytes_are_original_serialization_not_reserialized(self):
        raw = observer_bytes(self.rows).replace(b'"schema": ', b'"schema":  ')
        witness = self.validate(self.write(raw=raw))
        self.assertEqual(witness.bytes, len(raw))

    def test_undercounted_geometry_rejected(self):
        rr = self.write()
        self.report['storage_budget']['controls_before_final_bytes'] -= 1
        self.refuses(lambda: G.validate_control_accounting(self.report, self.validate(rr), 1000))

    def test_zero_geometry_accounting_rejected(self):
        rr = self.write()
        b = self.report['storage_budget']
        b['controls_before_final_bytes'] = b['prefill_control']['bytes']
        self.refuses(lambda: G.validate_control_accounting(self.report, self.validate(rr), 1000))

    def test_overcount_rejected(self):
        rr = self.write()
        self.report['storage_budget']['controls_before_final_bytes'] += 1
        self.refuses(lambda: G.validate_control_accounting(self.report, self.validate(rr), 1000))

    def test_same_report_witness_required(self):
        witness = self.validate()
        self.report['raw_bytes'] += 1
        self.refuses(lambda: G.validate_control_accounting(self.report, witness, 1000))

    def test_control_cap_unchanged(self):
        self.refuses(lambda: G.validate_control_accounting(self.report, self.validate(), G.CONTROL_CAP))

    def test_worker_cap_unchanged(self):
        self.report['storage_budget']['snapshot_bytes'] = G.ALLOCATED_CAP
        self.refuses(lambda: G.validate_control_accounting(self.report, self.validate(), 1000))

    def test_wrong_payload_source(self):
        self.rows[0]['source'] = source('wrong-payload.json')
        self.refuses(self.validate)

    def test_wrong_model_source(self):
        self.rows[0]['model_source'] = source('wrong-model.json')
        self.refuses(self.validate)

    def test_wrong_rank(self):
        for rank in (1, False, 0.0):
            with self.subTest(rank=repr(rank)):
                self.rows[0]['domain'] = dict(self.rows[0]['domain'], rank=rank)
                self.refuses(self.validate)

    def test_wrong_cid(self):
        self.rows[0]['domain'] = dict(self.rows[0]['domain'], cid='stale')
        self.refuses(self.validate)

    def test_wrong_host_pid(self):
        self.rows[0]['domain'] = dict(self.rows[0]['domain'], host_pid=8)
        self.refuses(self.validate)

    def test_wrong_start_ticks(self):
        self.rows[0]['domain'] = dict(self.rows[0]['domain'], start_ticks=8)
        self.refuses(self.validate)

    def test_wrong_namespace_pid(self):
        self.rows[0]['pid'] += 1
        self.refuses(self.validate)

    def test_wrong_worker_filename(self):
        self.path = self.root / 'FIRST-DECODE-GEOMETRY-p312.jsonl'
        self.refuses(self.validate)

    def test_wrong_alias_root(self):
        rr = self.write()
        self.aio = Alias(self.root / 'unrelated')
        self.refuses(lambda: self.validate(rr))

    def test_full_file_tampering(self):
        rr = self.write()
        raw = self.path.read_bytes().replace(b'layer.0', b'layer.9', 1)
        self.path.write_bytes(raw)
        self.refuses(lambda: self.validate(rr))

    def test_truncated_with_original_ref(self):
        rr = self.write()
        self.path.write_bytes(self.path.read_bytes()[:-1])
        self.refuses(lambda: self.validate(rr))

    def test_truncated_with_recomputed_ref(self):
        self.refuses(lambda: self.validate(self.write(raw=observer_bytes(self.rows)[:-1])))

    def test_missing_complete_row_with_recomputed_ref(self):
        self.rows.pop()
        self.refuses(self.validate)

    def test_duplicate_role_row(self):
        self.rows[-1] = copy.deepcopy(self.rows[-2])
        self.refuses(self.validate)

    def test_duplicate_report_role(self):
        selections = self.report['active_metadata']['selections']
        selections[-1] = copy.deepcopy(selections[-2])
        self.refuses(self.validate)

    def test_duplicate_pool_index(self):
        self.report['active_metadata']['pools'].append(
            copy.deepcopy(self.report['active_metadata']['pools'][0]))
        self.refuses(self.validate)

    def test_duplicate_pool_extent(self):
        pools = self.report['active_metadata']['pools']
        pools[-1]['pointer'] = pools[0]['pointer']
        pools[-1]['nbytes'] = pools[0]['nbytes']
        self.refuses(self.validate)

    def test_wrong_storage_extent(self):
        self.rows[0]['storage_bytes'] += 1
        self.refuses(self.validate)

    def test_wrong_view_stride(self):
        self.rows[0]['stride'] = [s * 2 for s in self.rows[0]['stride']]
        self.refuses(self.validate)

    def test_dtype_mismatch(self):
        self.rows[0]['dtype'] = 'torch.bfloat16'
        self.refuses(self.validate)

    def test_failed_original_nd2_predicate(self):
        self.rows[0]['format_code'] = 29
        self.refuses(self.validate)

    def test_numerical_claim_rejected(self):
        self.rows[0]['numerical_executed'] = True
        self.refuses(self.validate)

    def test_cpu_device_rejected(self):
        self.rows[0]['device'] = 'cpu'
        self.refuses(self.validate)

    def test_unknown_schema_field_rejected(self):
        self.rows[0]['override'] = True
        self.refuses(self.validate)

    def test_duplicate_json_keys(self):
        raw = observer_bytes(self.rows).replace(b'"group": 0', b'"group": 0, "group": 0', 1)
        self.refuses(lambda: self.validate(self.write(raw=raw)))

    def test_nonfinite_json(self):
        raw = observer_bytes(self.rows).replace(b'"group": 0', b'"group": NaN', 1)
        self.refuses(lambda: self.validate(self.write(raw=raw)))

    def test_empty_observation_ref_rejected(self):
        self.refuses(lambda: self.validate(self.write(raw=b'')))

    def test_extra_blank_row(self):
        self.refuses(lambda: self.validate(self.write(raw=observer_bytes(self.rows) + b'\n')))

    def test_symlink_file(self):
        rr = self.write()
        real = self.root / 'ordinary.jsonl'
        self.path.rename(real)
        self.path.symlink_to(real)
        self.refuses(lambda: self.validate(rr))

    def test_symlink_parent(self):
        rr = self.write()
        alias = self.root / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        rr = dict(rr, path=str(alias / self.path.name))
        self.aio = Alias(alias)
        self.refuses(lambda: self.validate(rr))

    def test_file_change_during_full_read(self):
        rr = self.write()
        original = G.os.read
        changed = False
        def read(fd, n):
            nonlocal changed
            raw = original(fd, n)
            if not changed:
                changed = True
                with self.path.open('ab') as stream:
                    stream.write(b'x')
            return raw
        with mock.patch.object(G.os, 'read', read):
            self.refuses(lambda: self.validate(rr))

    def sidecar(self):
        entries = []
        for rank in range(4):
            pid = 311 + rank
            entries.append(dict(rank=rank, namespace_pid=pid,
                report_ref=ref(self.root / ('FIRST-DECODE-%d' % pid) / 'FIRST-DECODE-REPORT.json', b'report'),
                geometry_ref=ref(self.root / ('FIRST-DECODE-GEOMETRY-p%d.jsonl' % pid), b'geometry')))
        value = dict(schema=G.SIDECAR_SCHEMA, consumer_source=source('consumer.json'),
            model_source=source('model.json'), payload_source=source('payload.json'),
            reports_ref=source('reports.json'), geometry=entries)
        refs = [x['report_ref'] for x in entries]
        return value, refs

    def check_sidecar(self, value, refs):
        return G.validate_geometry_sidecar(value, source('consumer.json'), source('model.json'),
            source('payload.json'), source('reports.json'), refs, str(self.root))

    def test_complete_sidecar(self):
        self.assertEqual(set(self.check_sidecar(*self.sidecar())), {0, 1, 2, 3})

    def test_sidecar_stale_consumer(self):
        value, refs = self.sidecar()
        value['consumer_source'] = source('stale.json')
        self.refuses(lambda: self.check_sidecar(value, refs))

    def test_sidecar_missing_fourth_rank(self):
        value, refs = self.sidecar()
        value['geometry'].pop()
        self.refuses(lambda: self.check_sidecar(value, refs))

    def test_sidecar_duplicate_rank(self):
        value, refs = self.sidecar()
        value['geometry'][3]['rank'] = 2
        self.refuses(lambda: self.check_sidecar(value, refs))

    def test_sidecar_duplicate_pid(self):
        value, refs = self.sidecar()
        value['geometry'][3]['namespace_pid'] = 313
        self.refuses(lambda: self.check_sidecar(value, refs))

    def test_sidecar_wrong_report_ref(self):
        value, refs = self.sidecar()
        value['geometry'][0]['report_ref'] = dict(refs[0], sha256='0'*64)
        self.refuses(lambda: self.check_sidecar(value, refs))

    def test_sidecar_geometry_wrong_directory(self):
        value, refs = self.sidecar()
        value['geometry'][0]['geometry_ref']['path'] = str(self.root / 'nested' / 'FIRST-DECODE-GEOMETRY-p311.jsonl')
        self.refuses(lambda: self.check_sidecar(value, refs))

    def test_sidecar_traversal(self):
        value, refs = self.sidecar()
        value['geometry'][0]['geometry_ref']['path'] = str(self.root) + '/nested/../FIRST-DECODE-GEOMETRY-p311.jsonl'
        self.refuses(lambda: self.check_sidecar(value, refs))


if __name__ == '__main__':
    unittest.main()
