"""Synthetic metadata and full actual sink-AST execution; not Torch/NPU evidence."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
WS = HERE.parent
sys.path.insert(0, str(HERE))
import runtime_joint_ledger as J
import render_joint_ledger as R


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class Tensor:
    def __init__(self, size):
        self.size = size

    def numel(self):
        return self.size

    def element_size(self):
        return 1


class C:
    need = staticmethod(J.need)

    @staticmethod
    def ref(path):
        p = Path(path)
        data = p.read_bytes()
        return dict(path=str(p), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

    @staticmethod
    def checked(ref):
        J.need(C.ref(ref['path']) == ref, 'actual fixture file exact Ref')
        return Path(ref['path'])

    @staticmethod
    def obj(ref):
        return json.loads(C.checked(ref).read_bytes())

    @staticmethod
    def write(path, value):
        with Path(path).open('x') as stream:
            json.dump(value, stream, sort_keys=True, allow_nan=False)
            stream.write('\n')
        return C.ref(path)


def setup(root, *, logical=1024, used=0, overflow=False):
    source = dict(path='/synthetic/not-an-authority', bytes=1, sha256='0'*64)
    frame = dict(source=source, rank=0, generation=1, ordinal=0, owner=dict(generation=1),
                 before_GDN=[], after_GDN=[], before_FA=[], after_FA=[], tensor=Tensor(logical),
                 publication={})
    calls = dict(export=0, save=0, load=0, numeric=0)
    L = module(WS/'fastpath_long_gate_prepare_v1/long_gate_primitives.py', 'actual_long')
    G = types.SimpleNamespace(__file__=str(WS/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/g2_contract.py'),
        RAW_CAP=J.RAW_CAP, FRAME_LOGICAL_CAP=J.LOGICAL_CAP, FRAME_WIRE_CAP=J.FRAME_WIRE_CAP,
        CHECKPOINT_CAP=J.CHECKPOINT_RESERVE, METADATA_CAP=J.METADATA_RESERVE)

    def export(t, f, *, cap_bytes):
        calls['export'] += 1
        J.need(logical <= cap_bytes, 'actual original exporter cap')
        return dict(schema='bole.model-diagnostic-primitives/v1', logical_tensor_bytes=logical,
                    payload={k:v for k,v in f.items() if k!='tensor'})

    def save(raw, stream):
        calls['save'] += 1
        if overflow:
            stream.write(b'a'*3000)
            stream.write(b'b'*3000)
        else:
            stream.write(json.dumps(raw, sort_keys=True).encode())

    def load(path, **kwargs):
        calls['load'] += 1
        # Actually reopen the exact real fixture file, not the export object.
        return json.loads(Path(path).read_bytes())

    def consume(t, C, m, source, frame, *, previous):
        calls['numeric'] += 1
        return dict(schema='bole.actual-fastpath-numeric-frame-ack/v1', source=source, rank=0,
                    generation=frame['generation'], ordinal=frame['ordinal'],
                    frame_checks_passed=True, numerical_qualified=False, formal_performance=False)
    X = types.SimpleNamespace(__file__=str(WS/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole/diagnostic_export.py'), export=export)
    N = types.SimpleNamespace(__file__=str(WS/'fastpath_numeric_bridge_prepare_v1/fastpath_numeric_consumer.py'), consume_frame=consume)
    original_path=WS/'fastpath_numeric_bridge_prepare_v1/fastpath_numeric_sink.py'
    original=original_path.read_text()
    files, inverse=R.adapt({'fastpath_numeric_sink.py':original})
    J.need(R.inverse(files,inverse)=={'fastpath_numeric_sink.py':original}, 'actual complete sink inverse')
    m=dict(runtime_joint_capture_ledger=dict(J.CONTRACT), files={
        'runtime_joint_ledger.py':C.ref(J.__file__), 'long_gate_primitives.py':C.ref(L.__file__),
        'g2_contract.py':C.ref(G.__file__), 'fastpath_numeric_sink.py':C.ref(original_path),
        'diagnostic_export.py':C.ref(X.__file__), 'fastpath_numeric_consumer.py':C.ref(N.__file__)})
    c=dict(t=types.SimpleNamespace(Tensor=Tensor,save=save,load=load), C=C, m=m, source=source,
           rank=0, root=root, used=used, metadata_bytes=0, previous=None)
    ns=dict(__file__=str(original_path), __name__='actual_full_sink_AST_software_fixture')
    exec(compile(files['fastpath_numeric_sink.py'],'actual-full-rendered-sink-AST','exec'),ns)
    ns['_CONTEXT']=c
    return ns, frame, c, calls, dict(long_gate_primitives=L, g2_contract=G,
                                   diagnostic_export=X, fastpath_numeric_consumer=N,
                                   runtime_joint_ledger=J)


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print(json.dumps(dict(mocked_runtime_predecessor=True, source_ready=False,
            runtime_budget_pass=False, Torch=False, NPU=False,
            scope='metadata/full-actual-sink-AST stage wiring only'),sort_keys=True))

    def test_writer_predebits_short_syscall_and_blocks_serializer_finalizer(self):
        ledger=types.SimpleNamespace(failed=False,quota=16,written=0)
        writes=[]
        stream=types.SimpleNamespace(write=lambda b:(writes.append(bytes(b)) or len(b)-1))
        writer=J.Writer(ledger,stream)
        with self.assertRaises(ValueError):writer.write(b'abcd')
        self.assertEqual(ledger.written,4)
        self.assertTrue(ledger.failed)
        with self.assertRaises(J.BudgetReject):writer.write(b'footer')
        self.assertEqual(writes,[b'abcd'])

    def test_actual_full_sink_rejects_before_all_allocation_calls(self):
        logical=2**20
        retained=J.RAW_CAP-2*logical-J.CHECKPOINT_RESERVE-J.METADATA_RESERVE-J.SERIALIZATION_TEMP-J.FAILURE_TEMP
        with tempfile.TemporaryDirectory(prefix='bole-joint-software-') as tmp:
            ns,f,c,calls,modules=setup(Path(tmp),logical=logical,used=retained)
            with mock.patch.dict(sys.modules,modules), self.assertRaisesRegex(J.BudgetReject,'before X.export'):
                ns['sink'](f)
            self.assertEqual(calls,dict(export=0,save=0,load=0,numeric=0))
            self.assertEqual(list(Path(tmp).iterdir()),[])

            self.assertTrue(c['runtime_joint_ledger'].failed)
            self.assertEqual(c['runtime_joint_ledger'].phase,'failed')
            # Even a later change in available quota cannot retry this frame.
            c['used']=0
            with mock.patch.dict(sys.modules,modules), mock.patch.object(J,'require_temporary_evidence'), self.assertRaisesRegex(ValueError,'no unACKed or failed'):
                ns['sink'](f)
            self.assertEqual(calls,dict(export=0,save=0,load=0,numeric=0))

    def test_actual_full_sink_real_wire_reload_ack_and_retained_first(self):
        with tempfile.TemporaryDirectory(prefix='bole-joint-software-') as tmp:
            root=Path(tmp)
            ns,f,c,calls,modules=setup(root)
            # Explicit SYNTHETIC predecessor seam for downstream stage controls;
            # no actual runtime admission or tensor-memory evidence is implied.
            with mock.patch.dict(sys.modules,modules), mock.patch.object(J,'require_temporary_evidence'):
                ack=ns['sink'](f)
            self.assertEqual(calls,dict(export=1,save=1,load=1,numeric=1))
            ref=ack['actual_frame']
            self.assertEqual(ref,C.ref(root/'G1-O0.pt'))
            self.assertEqual(c['used'],ref['bytes'])
            self.assertEqual(c['runtime_joint_ledger'].phase,'idle')
            self.assertEqual(c['runtime_joint_ledger'].logical,1024)
            release=C.obj(C.ref(root/'G1-O0-RELEASE.json'))
            self.assertTrue(release['retained'])
            self.assertFalse(release['numerical_qualified'])

    def test_actual_full_sink_overflow_partial_fsync_ref_no_reload_or_ack(self):
        logical=1024
        first=J.RAW_CAP-2*logical-J.CHECKPOINT_RESERVE-J.METADATA_RESERVE-J.SERIALIZATION_TEMP-J.FAILURE_TEMP-4096
        with tempfile.TemporaryDirectory(prefix='bole-joint-software-') as tmp:
            root=Path(tmp)
            ns,f,c,calls,modules=setup(root,logical=logical,used=first,overflow=True)
            with mock.patch.dict(sys.modules,modules), mock.patch.object(J,'require_temporary_evidence'), mock.patch.object(os,'fsync',wraps=os.fsync) as sync:
                with self.assertRaisesRegex(J.BudgetReject,'partial serialization preserved') as error:
                    ns['sink'](f)
                self.assertGreaterEqual(sync.call_count,2)
            self.assertEqual(calls,dict(export=1,save=1,load=0,numeric=0))
            ref=C.ref(root/'G1-O0.pt')
            self.assertEqual(ref['bytes'],3000)
            self.assertEqual(c['used'],first+3000)
            self.assertEqual(c['runtime_joint_ledger'].ref,ref)
            self.assertTrue(c['runtime_joint_ledger'].failed)
            self.assertIn(ref['sha256'],str(error.exception))
            self.assertFalse((root/'G1-O0-RELEASE.json').exists())
            with mock.patch.dict(sys.modules,modules), self.assertRaises(ValueError):
                ns['sink'](f)

    def test_dynamic_quota_and_no_caller_PASS_or_one_copy_mode(self):
        with tempfile.TemporaryDirectory(prefix='bole-joint-software-') as tmp:
            ns,f,c,calls,modules=setup(Path(tmp),logical=225*2**20)
            with mock.patch.dict(sys.modules,modules), mock.patch.object(J,'require_temporary_evidence'):
                joint=J.Joint(c)
                admission=joint.pre_export(f,225*2**20)
            self.assertGreater(admission['quota'],225*2**20)
            self.assertLess(admission['quota'],J.FRAME_WIRE_CAP)
            self.assertIsNone(admission['wire_lower_bound'])
            self.assertEqual(admission['cpu_copies'],2)
            c['m']['runtime_joint_capture_ledger']['caller_PASS']=True
            with mock.patch.dict(sys.modules,modules), self.assertRaises(ValueError):
                J.Joint(c)

    def test_unmeasured_temporary_default_refuses_before_export(self):
        with tempfile.TemporaryDirectory(prefix='bole-joint-software-') as tmp:
            ns,f,c,calls,modules=setup(Path(tmp))
            with mock.patch.dict(sys.modules,modules), self.assertRaisesRegex(ValueError,'temporary high-water unmeasured'):
                ns['sink'](f)
            self.assertEqual(calls,dict(export=0,save=0,load=0,numeric=0))
            self.assertEqual(list(Path(tmp).iterdir()),[])
            c['m']['runtime_joint_capture_ledger']=dict(J.CONTRACT,cpu_copies=1)
            with mock.patch.dict(sys.modules,modules), self.assertRaises(ValueError):
                J.Joint(c)

    def test_composes_with_actual_codec_delraw_and_never_changes_numeric_hardrefusal(self):
        codec=module(WS/'state_capture_codec_prepare_v1/render_state_codec.py','actual_codec_renderer')
        root=WS/'formal_pair_ready_prepare_v1/strict-source-proposal-v3/prepared-source-bole'
        files={p.name:p.read_text()for p in root.glob('*.py')}
        tap=module(WS/'fastpath_numeric_bridge_prepare_v1/qualification_tap_delta.py','actual_tap')
        files=tap.render(files)
        for n in('fastpath_numeric_observer.py','fastpath_numeric_sink.py'):
            files[n]=(WS/'fastpath_numeric_bridge_prepare_v1'/n).read_text()
        files,_=codec.adapt(files)
        out,delta=R.adapt(files)
        self.assertEqual(R.inverse(out,delta),files)
        self.assertIn('del raw',out['fastpath_numeric_sink.py'])
        self.assertIn('SC.require_runtime_admission',out['fastpath_numeric_observer.py'])
        for n in files:
            if n!='fastpath_numeric_sink.py':
                self.assertEqual(out[n],files[n])


if __name__=='__main__':
    unittest.main()
