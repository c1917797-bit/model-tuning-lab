"""Synthetic CPU-only controls; these fixtures are not captured BOLE evidence."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
RUNTIME = HERE if (HERE / 'sourceio.py').is_file() else HERE.parent
WORKSPACE = next((p for p in HERE.parents if (p / 'bole_service_reference').is_dir()), None)
REFERENCE = RUNTIME if (RUNTIME / 'identity_oracle.py').is_file() else (
    WORKSPACE / 'bole_service_reference' / 'qualified')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


R = module('g1_independent_reader_test', HERE / 'consume_service.py')
C = module('g1_test_sourceio', RUNTIME / 'sourceio.py')
O = module('g1_test_original_identity_oracle', REFERENCE / 'identity_oracle.py')
G1 = module('g1_test_contract', RUNTIME / 'g1_contract.py')
PROFILE = dict(endpoint='/v1/completions', prompt_count=1, n=1,
               beam_search=False, streaming_input=False)


class Target:
    """Only the argmax interface used by the pure decision function."""
    def __init__(self, greedy):
        self.greedy = greedy
        self.shape = (len(greedy), 100)
    def argmax(self, dim):
        assert dim == -1
        return SimpleNamespace(tolist=lambda: list(self.greedy))


class FakeTensor:
    def __init__(self, elements, width=2, cpu=True, contiguous=True):
        self.elements, self.width = elements, width
        self.device = SimpleNamespace(type='cpu' if cpu else 'npu')
        self.contiguous = contiguous
    def numel(self):
        return self.elements
    def element_size(self):
        return self.width
    def is_contiguous(self):
        return self.contiguous


class Tests(unittest.TestCase):
    def setUp(self):
        R.C = C
        R.CM = SimpleNamespace(O=O, PROFILE=PROFILE)
        R.G1 = G1

    def test_default_off_and_help_are_standalone(self):
        for args in ([], ['--help']):
            result = subprocess.run([sys.executable, str(HERE / 'consume_service.py'), *args],
                                    capture_output=True, text=True, check=True)
            self.assertNotIn('Traceback', result.stderr)
            if not args:
                self.assertEqual(json.loads(result.stdout), dict(enabled=False, NPU=False))

    def test_v6_numerical_and_vocabulary_functions_unchanged(self):
        new = ast.parse((HERE / 'consume_service.py').read_text())
        current = {n.name: n for n in new.body if isinstance(n, ast.FunctionDef)}
        # Prospectively pinned from the qualified V6 reader before G1 data.
        original = dict(
            tp_logits='dd2fdba3c69ff2ff9bcb49383138c7fee3f466b32ce2086b5f8dbf2f949ce919',
            fa_math='1e072068d888d0dfba737539a64620255ce79fddd69b2095f4532770a4c77ded',
            conv_math='e664a7ddf985dec67ff4855397645d93134c142556d76af4993f59522b50899e',
            decide='e226f3775348b23681337b2cdf15a700632f0aa42bbc745096309c7dd9eb6d55',
            tp_owner_agreement='66eb7ffe6d7d46e2aefb4d16b66c5d03f25f974a8f206c6ec7c94a19bba616f4',
            mtp_join='465e27dbd429d8ea6e4de5025cf4581d47cd72d1af3b6ff6ed4569dcd2c50350',
            rank_vocabulary_joins='cbba405bba8037fbdf56294337bd5e1818db6f857274cf3eb7013d0edf4b9557')
        for name, expected in original.items():
            actual = hashlib.sha256(ast.dump(current[name], include_attributes=False).encode()).hexdigest()
            self.assertEqual(actual, expected, name)

    def test_one_remaining_output_never_accepts_a_child(self):
        for greedy in ([8], [8, 11], [8, 11, 12]):
            step = dict(scheduled_nodes=len(greedy), remaining_output=1, tokens=[7, 8, 9])
            path, emitted, nxt = R.decide(None, step, Target(greedy))
            self.assertEqual(path, (0,))
            self.assertEqual(emitted, (8,))
            self.assertEqual(nxt, tuple(greedy))

    def test_prior_owner_generation_version_and_native_counter_fail_before_math(self):
        raw = dict(rank=0, request=dict(request='second-request', generation=2))
        owner = dict(request='second-request', generation=2, slot=0, length=131, version=0)
        schedule = dict(req_ids=['second-request'], request_id='second-request',
            computed_tokens=131, num_tokens_without_spec=132, scheduled_num_tokens=1,
            scheduled_spec_tokens=[], CPU_input_token_ids=[7], request_output_tokens=[7])
        for mutation in ('generation', 'version', 'length', 'counter', 'request'):
            step = dict(owner=copy.deepcopy(owner), scheduled_nodes=1, tokens=[7,8,9],
                request_output_tokens_before=[7], remaining_output=1,
                native_schedule=copy.deepcopy(schedule))
            if mutation == 'counter':
                step['native_schedule']['computed_tokens'] = 132
            else:
                step['owner'][mutation] = dict(generation=1, version=1, length=132,
                                              request='first-request')[mutation]
            with self.assertRaises(ValueError):
                R.consume_step(None, {}, raw, step, 0, [7], None)

    def test_logical_charge_counts_repeated_tensors_and_rejects_opaque_or_device(self):
        t = SimpleNamespace(Tensor=FakeTensor)
        tensor = FakeTensor(13)
        self.assertEqual(R.primitive_tensor_bytes(t, dict(a=tensor, b=[tensor, 3, None])), 52)
        for bad in (object(), {True: 1}, FakeTensor(1, cpu=False), FakeTensor(1, contiguous=False)):
            with self.assertRaises(ValueError):
                R.primitive_tensor_bytes(t, bad)

    def reuse_fixture(self, reused):
        requests = []
        for generation in (1, 2):
            offset = 0 if reused or generation == 1 else 100
            step = dict(before_GDN=[dict(layer=i, group=i, physical_slot=i + offset)
                                    for i in R.GDN_LAYERS],
                        before_FA=[dict(layer=i, physical_pages=[i + offset, i + offset + 1])
                                   for i in R.FA_LAYERS])
            requests.append(dict(request=dict(request='request-%d' % generation,
                                               generation=generation), steps=[step]))
        gdn = [[[x['layer'], x['group'], x['physical_slot']]
                for x in r['steps'][0]['before_GDN']] for r in requests]
        fa = [[[x['layer'], x['physical_pages']]
               for x in r['steps'][0]['before_FA']] for r in requests]
        return dict(requests=requests, native_slot_reuse=dict(
            schema='bole.two-request-actual-slot-reuse/v1', generations=[1, 2],
            requests=['request-1', 'request-2'], GDN_before=gdn, FA_before=fa,
            GDN_reused=reused, FA_reused=reused))

    def test_allocator_reuse_and_nonreuse_are_both_truthful_observations(self):
        for reused in (True, False):
            report = R.slot_reuse(self.reuse_fixture(reused))
            self.assertIs(report['slot_reuse_observed'], reused)

    def test_claimed_reuse_cannot_replace_actual_mapping(self):
        raw = self.reuse_fixture(False)
        raw['native_slot_reuse']['GDN_reused'] = True
        with self.assertRaises(ValueError):
            R.slot_reuse(raw)

    def test_missing_or_duplicate_layer_slot_cannot_be_omitted_from_reuse(self):
        raw = self.reuse_fixture(True)
        raw['requests'][1]['steps'][0]['before_GDN'][0]['layer'] = R.GDN_LAYERS[1]
        with self.assertRaises(ValueError):
            R.slot_reuse(raw)

    def byte_fixture(self, root):
        def file(name, data=b'{}\n'):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return C.ref(path)
        evidence = []
        for prefix in ('BOLE-PREFILL-CACHE', 'BOLE-FA-PREFILL-MAPPING',
                       'BOLE-NATIVE-LIBRARY-IDENTITY'):
            for generation in (1, 2):
                evidence.append(file('%s-REQUEST-%02d-RANK-0.json' % (prefix, generation)))
        for index in range(25):
            evidence.append(file('CONV-MODEL-CALIBRATION-RANK-0/%02d.pt' % index))
        published_journal = file('IDENTITY-rank0-000001.json')
        evidence.append(published_journal)
        final_journal = file('IDENTITY-rank0-000002.json')
        pair = dict(raw=file('BOLE-TREE-RANK-0.pt'), receipt=file('BOLE-TREE-RANK-0.json'))
        raw = dict(rank=0, tensor=FakeTensor(10))
        exported = dict(schema='bole.model-diagnostic-primitives/v1', model_ready=False,
                        cap_bytes=2**30, logical_tensor_bytes=20)
        account = dict(cap_bytes=2**30, serialization_header_allowance=2**20,
            logical_tensor_bytes=20, raw_bytes=pair['raw']['bytes'],
            evidence_bytes=sum(r['bytes'] for r in evidence), reserved_metadata_bytes=64*2**20,
            remaining_journal_reserve=8*2**20-published_journal['bytes'], receipt_reserve=65536)
        receipt = dict(rank_evidence_refs=evidence, byte_accounting=account)
        bundle = dict(journal=[published_journal, final_journal])
        return (SimpleNamespace(Tensor=FakeTensor), dict(model_receipt_root=str(root)),
                raw, exported, pair, receipt, bundle)

    def test_complete_future_journal_reserve_and_final_bytes_recomputed(self):
        with tempfile.TemporaryDirectory() as directory:
            args = self.byte_fixture(Path(directory))
            report = R.byte_accounting(*args)
            self.assertIs(report['original_aggregate_cap_preserved'], True)
            self.assertEqual(report['logical_tensor_bytes'], 20)

    def test_unaccounted_observer_or_undercharged_bytes_rejected(self):
        for mutation in ('omitted', 'duplicate', 'undercharged', 'journal'):
            with tempfile.TemporaryDirectory() as directory:
                args = self.byte_fixture(Path(directory))
                receipt, bundle = args[5], args[6]
                if mutation == 'omitted':
                    receipt['rank_evidence_refs'].pop(0)
                elif mutation == 'duplicate':
                    receipt['rank_evidence_refs'].append(receipt['rank_evidence_refs'][0])
                elif mutation == 'undercharged':
                    receipt['byte_accounting']['evidence_bytes'] -= 1
                else:
                    bundle['journal'].pop()
                with self.assertRaises(ValueError):
                    R.byte_accounting(*args)

    def test_two_request_logical_cap_cannot_be_inflated_or_underdeclared(self):
        for exact_large in (True, False):
            with tempfile.TemporaryDirectory() as directory:
                args = self.byte_fixture(Path(directory))
                if exact_large:
                    args[2]['tensor'] = FakeTensor(2**29)
                    args[3]['logical_tensor_bytes'] = 2**30
                else:
                    args[3]['logical_tensor_bytes'] -= 1
                with self.assertRaises(ValueError):
                    R.byte_accounting(*args)

    def identity_fixture(self, root, mutation=None):
        def write(name, value):
            return C.write(root / name, value)
        sr = write('source.json', dict(model_receipt_root=str(root)))
        front = dict(pid=900, start_ticks=42, cgroup='owned-cid/frontend')
        rows, journals, snapshots, hosts = [], [], [], []
        ids = ['cmpl-bole-g1-131-tree-1-0-12345678',
               'cmpl-bole-g1-131-tree-2-0-87654321']
        for ordinal, label in enumerate(('tree-1', 'tree-2', 'retirement-barrier'), 1):
            server = 'cmpl-bole-g1-131-' + label
            rr = write('response-%d.json' % ordinal, dict(id=server))
            rows.append(dict(label=label, response=rr, header='bole-g1-131-' + label))
            event = dict(schema='vllm023.actual-assignment/v1', source_sha256=O.ASSIGN_SHA,
                         identity=front, before_request_id=server + '-0',
                         before_external_req_id=None, disable_request_id_randomization=False,
                         after_request_id=ids[ordinal - 1] if ordinal < 3 else server + '-0-00000000',
                         after_external_req_id=server + '-0')
            journals.append(write('IDENTITY-frontend-%06d.json' % ordinal, dict(
                schema='bole.actual-identity-journal/v1', source=sr, role='frontend',
                kind='assignment', event=event)))
        for rank in range(4):
            identity = dict(pid=1000 + rank, start_ticks=42, cgroup='owned-cid/rank%d' % rank)
            stat = '%d (synthetic-worker) S %s42 0 0' % (identity['pid'], '0 ' * 18)
            snapshot = dict(pid=identity['pid'], proc_stat=stat, cgroup=identity['cgroup'],
                            source_ref=sr, allow_hf32=False)
            snapshots.append(snapshot)
            hosts.append(dict(guest=snapshot, host=dict(physical=rank + 4)))
            events = []
            def ev(seq, new=(), cached=(), finished=(), scheduled=None, before=(), after=()):
                scheduled = {} if scheduled is None else scheduled
                return dict(schema='vllm023.actual-worker-update/v1', seq=seq, rank=rank,
                    identity=identity, source_sha256=O.NPU_SHA, new_req_ids=list(new),
                    cached_req_ids=list(cached), finished_req_ids=list(finished),
                    num_scheduled_tokens=scheduled, total_num_scheduled_tokens=sum(scheduled.values()),
                    requests_before=list(before), requests_after=list(after), batch_after=list(after))
            a, b = ids
            events.append(ev(1, new=[a], scheduled={a:131}, after=[a]))
            events.append(ev(2, cached=[a], scheduled={a:1}, before=[a], after=[a]))
            events.append(ev(3, new=[b], finished=[a], scheduled={b:131}, before=[a], after=[b]))
            events.append(ev(4, cached=[b], scheduled={b:1}, before=[b], after=[b]))
            events.append(ev(5, finished=[b], before=[b]))
            if mutation:
                mutation(rank, events, ids)
            for index, event in enumerate(events, 1):
                journals.append(write('IDENTITY-rank%d-%06d.json' % (rank, index), dict(
                    schema='bole.actual-identity-journal/v1', source=sr, role='rank%d' % rank,
                    kind='worker_update', event=event)))
        http = write('http.json', dict(schema=G1.HTTP_SCHEMA, source=sr, rows=rows))
        bundle = dict(http=http, journal=journals, snapshots=snapshots, host_bindings=hosts,
            frontend_binding=dict(guest=front, NSpid=[900], owned_cid='owned-cid',
                                  host=dict(cgroup='owned-cid', start_ticks=42)))
        return sr, bundle, ids

    def test_actual_identity_oracle_accepts_two_sequential_lifecycles(self):
        with tempfile.TemporaryDirectory() as directory:
            sr, bundle, expected = self.identity_fixture(Path(directory))
            assigned, bindings = R.identity_join(sr, bundle)
            self.assertEqual(assigned, expected)
            self.assertEqual(set(bindings), set(range(4)))

    def test_second_request_http_completion_without_worker_retirement_rejected(self):
        def missing(rank, events, ids):
            events[-1]['finished_req_ids'] = []
            events[-1]['requests_after'] = events[-1]['batch_after'] = [ids[1]]
        with tempfile.TemporaryDirectory() as directory:
            sr, bundle, _ = self.identity_fixture(Path(directory), missing)
            with self.assertRaisesRegex(ValueError, 'retirement'):
                R.identity_join(sr, bundle)

    def test_wrong_rank_process_identity_rejected(self):
        def wrong(rank, events, ids):
            if rank == 3:
                events[1]['identity'] = dict(pid=1000, start_ticks=42, cgroup='foreign')
        with tempfile.TemporaryDirectory() as directory:
            sr, bundle, _ = self.identity_fixture(Path(directory), wrong)
            with self.assertRaises(ValueError):
                R.identity_join(sr, bundle)

    def test_second_ingress_before_first_retirement_rejected(self):
        def overlap(rank, events, ids):
            a, b = ids
            events[1].update(new_req_ids=[b], num_scheduled_tokens={a:1,b:131},
                             total_num_scheduled_tokens=132, requests_after=[a,b], batch_after=[a,b])
            events[2]['new_req_ids'] = []
        with tempfile.TemporaryDirectory() as directory:
            sr, bundle, _ = self.identity_fixture(Path(directory), overlap)
            with self.assertRaises(ValueError):
                R.identity_join(sr, bundle)

    def test_missing_journal_ordinal_and_duplicate_ref_rejected(self):
        for duplicate in (False, True):
            with tempfile.TemporaryDirectory() as directory:
                sr, bundle, _ = self.identity_fixture(Path(directory))
                if duplicate:
                    bundle['journal'].append(bundle['journal'][-1])
                else:
                    bundle['journal'] = [r for r in bundle['journal']
                                         if not r['path'].endswith('rank2-000002.json')]
                with self.assertRaises(ValueError):
                    R.identity_join(sr, bundle)


if __name__ == '__main__':
    unittest.main()
