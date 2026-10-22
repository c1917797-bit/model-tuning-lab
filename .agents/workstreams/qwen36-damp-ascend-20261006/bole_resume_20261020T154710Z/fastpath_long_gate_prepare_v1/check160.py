"""Actual generated160 producer/reader function controls; synthetic software only."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import long_gate_primitives as L
import check_long_gate as F
import render160 as R


class C:
    need=staticmethod(L.need)
    ref=staticmethod(F.ref)
    @staticmethod
    def checked(r):
        L.need(F.ref(r['path'])==r,'exact actual software fixture Ref')
        return Path(r['path'])
    @classmethod
    def obj(cls,r):return json.loads(cls.checked(r).read_bytes())


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(HERE.parent/'fastpath_numeric_bridge_prepare_v1'))
        import qualification_short_prepare as Q
        cls.short=Q.render();cls.long=R.render(cls.short)

    def test_domain_source_and_math_unchanged(self):
        self.assertEqual(R.inverse(self.long,self.short),self.short['files'])
        for n in('core112.py','transaction.py','tp_consensus.py','service_runner.py','g2_numeric.py','oracle112.py','independent_model.py'):
            self.assertEqual(self.short['files'][n],self.long['files'][n])
        self.assertEqual(self.long['manifest']['service_experiment']['max_output_tokens'],160)
        self.assertEqual(self.long['manifest']['profile']['HTTP_output_tokens'],160)
        self.assertFalse(self.long['execution_ready'])
        self.assertTrue(self.long['manifest']['qualification_execution_authority_pending'])
        with self.assertRaises(ValueError):R.render(dict(self.short,prepared_only=False))

    def select_namespace(self):
        text=self.long['files']['short_state_digest.py'].decode();tree=ast.parse(text)
        decl=next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='DECLARATION'for t in n.targets))
        ns=dict(SCHEMA='bole.two-generation-short-state-digest/v1',FLAG='BOLE_SHORT_STATE_DIGEST_ENABLE',need=L.need)
        ns['DECLARATION']=eval(compile(ast.Expression(decl),'actual160-declaration','eval'),ns)
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='select')
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual160-select','exec'),ns)
        return ns

    def test_actual_domain_entry_default_off_wrong_profile(self):
        ns=self.select_namespace();select=ns['select'];flag=ns['FLAG']
        self.assertIsNone(select({},None))
        self.assertEqual(select({flag:'1'},self.long['manifest']['short_state_digest_profile'])['output_tokens'],160)
        with self.assertRaises(ValueError):select({flag:'1'},self.short['manifest']['short_state_digest_profile'])

    def test_actual_store_emit_reader_roundtrip_and_bad_profile(self):
        with tempfile.TemporaryDirectory(prefix='bole160-software-fixture-')as directory:
            root=Path(directory);report=F.fixture_report()
            context=dict(C=C,metadata_bytes=0,used=0)
            def durable(path,value):
                data=L.canonical(value)
                with path.open('xb')as stream:stream.write(data)
                context['metadata_bytes']+=len(data)
                return F.ref(path)
            envelope_ref=L.store_report(context,root,'G1-O0',report,durable_json=durable)
            recovered,envelope=L.read_report(C,envelope_ref)
            self.assertEqual(recovered,report)
            profile=self.long['manifest']['short_state_digest_profile']
            record=dict(request='fixture-r',length=131,version=0,tokens=[0,0,0],
                actual_collect_observation_only=False,processed_nodes=[0],emitted_tokens=[0],
                rows_reference=L.compact_rows_reference(report,envelope['wire'],envelope['codec']))
            tree=ast.parse(self.long['files']['short_state_digest.py'])
            klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Probe')
            emit=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='emit')
            ns=dict(SCHEMA='bole.two-generation-short-state-digest/v1',need=L.need,canonical=L.canonical,
                CAP=256*1024,TOTAL_CAP=10*2**20,hashlib=hashlib,PERF=types.SimpleNamespace(metadata_value=lambda x:x))
            exec(compile(ast.Module(body=[emit],type_ignores=[]),'actual-generated160-STATE-emit','exec'),ns)
            def publish(path,value):
                with path.open('xb')as stream:stream.write(L.canonical(value))
            owner=types.SimpleNamespace(failed=False,source=report['source'],profile=profile,rank=0,root=root,bytes=0,publish=publish)
            value=ns['emit'](owner,'STEP',1,0,record)
            self.assertLessEqual(len(L.canonical(value)),L.COMPACT_STATE_CAP)
            state=root/'STATE-STEP-G1-O0-R0.json'
            tree=ast.parse(self.long['files']['compare_state_digest.py'])
            obj=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='obj')
            ns=dict(need=L.need,ref=F.ref,json=json,Path=Path,SCHEMA='bole.two-generation-short-state-digest/v1',
                LONG=L,hashlib=hashlib,_BOUND_PROFILE=profile,_TRANSPORT_READSET=[])
            exec(compile(ast.Module(body=[obj],type_ignores=[]),'actual-generated160-STATE-reader-obj','exec'),ns)
            restored=ns['obj'](F.ref(state))
            self.assertEqual(restored['profile'],profile)
            self.assertEqual(restored['record']['rows'],report['selected_write_digests'])
            self.assertEqual(ns['_TRANSPORT_READSET'],[envelope['wire']])
            value['profile']['sha256']='0'*64
            wrong=root/'bad-profile.json'
            with wrong.open('xb')as stream:stream.write(L.canonical(value))
            with self.assertRaises(ValueError):ns['obj'](F.ref(wrong))

    def test_budget_rejection_precedes_wire_create(self):
        with tempfile.TemporaryDirectory(prefix='bole160-software-fixture-')as directory:
            root=Path(directory);c=dict(C=C,metadata_bytes=L.METADATA_CAP-1,used=0)
            with self.assertRaises(ValueError):L.store_report(c,root,'overflow',F.fixture_report(),durable_json=lambda p,v:None)
            self.assertEqual(list(root.iterdir()),[])


if __name__=='__main__':
    if sys.argv[1:]!=['--check']:raise SystemExit('default OFF: pure software --check only')
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps(dict(schema='bole.actual-generated160-software-controls/v1',tests=r.testsRun,
        errors=len(r.errors),failures=len(r.failures),synthetic_software_fixtures=True,
        prepared_only=True,execution_ready=False,NPU=False,numerical_qualified=False),sort_keys=True))
    raise SystemExit(not r.wasSuccessful())
