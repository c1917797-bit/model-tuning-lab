"""Stdlib-only controls; local tests never import Torch or certify real masks."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT=Path(__file__).resolve().parent;WORK=ROOT.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=load('_pure_mask_diag_common',ROOT/'diag_common.py');C=D.common()
M=load('_pure_mask_cpu_owner',ROOT/'mask_cpu_owner.py')
X=load('_pure_mask_metadata',ROOT/'mask_diagnostic.py')

class DiagTests(unittest.TestCase):
    def test_actual_original_CPU_profile_receipts(self):
        refs=json.loads((ROOT/'ACTUAL_CPU_PROFILE_REFS.json').read_text())
        failure=json.loads((ROOT/'ACTUAL_V3_FAILURE_REFS.json').read_text())
        root=WORK/'g1_review_v2/native_ar_saved_v3_failure'
        for name,r in refs.items():
            a=C.ref(root/'cpu-consumer'/name)
            self.assertEqual((a['bytes'],a['sha256']),(r['bytes'],r['sha256']))
        mapping={r['path']:root/'cpu-consumer'/n for n,r in refs.items()}
        mapping.update({r['path']:root/n for n,r in failure.items()})
        class Offline:
            need=staticmethod(C.need);ref=staticmethod(C.ref);IMAGE=C.IMAGE
            @staticmethod
            def obj(reference):
                p=mapping.get(reference['path'],Path(reference['path']));actual=C.ref(p)
                C.need((actual['bytes'],actual['sha256'])==(reference['bytes'],reference['sha256']),'exact copied source/profile whole SHA')
                return json.loads(p.read_bytes())
        owner=json.loads((root/'RESULT.json').read_text())
        basis=D.original_CPU_profile(Offline,dict(actual_original_CPU_profile_refs=refs,actual_v3_failure_refs=failure),owner)
        self.assertEqual(basis['original_guest_cpus'],[0]);self.assertEqual(basis['effective_capacity'],1)
        self.assertFalse(basis['task_CPU145_profile_substituted'])
    def test_actual_CPU0_regresses_old145_guard_and_new_guard_accepts_it(self):
        receipt=json.loads((WORK/'g1_review_v2/native_ar_saved_v3_failure/cpu-consumer/OWNED.json').read_text())
        ctl=types.SimpleNamespace(cpu=dict(guest_cpus=receipt['guest_cpus']))
        old=WORK/'bole_service_proposals/native_ar_mask_diagnostic_v1/mask_cpu_owner.py'
        for path,expected in[(old,False),(ROOT/'mask_cpu_owner.py',True)]:
            tree=ast.parse(path.read_bytes())
            checks=[n for n in ast.walk(tree)if isinstance(n,ast.Compare)and
                "ctl.cpu['guest_cpus'][:1]"in ast.unparse(n)]
            self.assertEqual(len(checks),1)
            observed=eval(compile(ast.Expression(body=checks[0]),str(path),'eval'),{'ctl':ctl})
            self.assertIs(observed,expected)
    def test_mask_metadata_and_original025_bytes_unchanged_from_v1(self):
        old=WORK/'bole_service_proposals/native_ar_mask_diagnostic_v1'
        for name in('mask_diagnostic.py','ar_owner_common.py','ar_saved_namespace.py'):
            self.assertEqual((ROOT/name).read_bytes(),(old/name).read_bytes())
    def test_cold_default_help_no_tensor_imports(self):
        code="""import builtins,sys,runpy
old=builtins.__import__
def guard(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('forbidden local/cold tensor import')
 return old(name,*a,**k)
builtins.__import__=guard;p=sys.argv[1];sys.argv=[p,*sys.argv[2:]];runpy.run_path(p,run_name='__main__')
"""
        for name in('prepare_mask_owner.py','mask_cpu_owner.py','mask_diagnostic.py'):
            for args in([],['--help']):
                p=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT/name),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(p.returncode,0,p.stderr)
                if not args:self.assertFalse(json.loads(p.stdout)['enabled'])
    def test_actual_failure_and_passed_G1_copies_whole_SHA(self):
        refs=json.loads((ROOT/'ACTUAL_V3_FAILURE_REFS.json').read_text())
        base=WORK/'g1_review_v2/native_ar_saved_v3_failure'
        for name,r in refs.items():
            a=C.ref(base/name);self.assertEqual((a['bytes'],a['sha256']),(r['bytes'],r['sha256']))
        owner=json.loads((base/'RESULT.json').read_text());self.assertIsNotNone(owner['primary'])
        self.assertEqual(owner['secondary'],[]);self.assertEqual(owner['source_before'],owner['source_after'])
        self.assertFalse(owner['independent_numeric_requalification_pass'])
        gate=json.loads((base/'cpu-consumer/BOLE-INDEPENDENT-GATE/ATTRIBUTION.json').read_text())
        self.assertTrue(gate['G1_experiment_pass']);self.assertTrue(gate['component_checks_pass'])
        self.assertFalse(gate['native_AR_greedy_comparison_performed']);self.assertIsNone(gate['greedy_identity_pass'])
    def test_mask_primary_source_and_all_four_actual_headers(self):
        root=WORK/'g1_review_v2/native_ar_mask_sources_v1';record=json.loads((ROOT/'MASK_SOURCE_COPY_RECORD.json').read_text())
        actual=C.ref(root/'attention_mask.py');r=record['runtime_ref'];copy=record['snapshot_ref']
        self.assertEqual((actual['bytes'],actual['sha256']),(r['bytes'],r['sha256']))
        self.assertEqual((copy['bytes'],copy['sha256']),(r['bytes'],r['sha256']));self.assertNotEqual(copy['path'],r['path'])
        self.assertEqual(len(record['headers']),4)
        for rank,row in enumerate(record['headers']):
            a=C.ref(root/('NATIVE-AR-RANK-%d.json'%rank));self.assertEqual((a['bytes'],a['sha256']),(row['ref']['bytes'],row['ref']['sha256']))
            v=json.loads(row['text']);self.assertEqual(v['rank'],rank);self.assertEqual(v['raw']['bytes'],152915063)
    def test_primary_AST_declares_int8_upper2048_for_nonpooling(self):
        p=WORK/'g1_review_v2/native_ar_mask_sources_v1/attention_mask.py';tree=ast.parse(p.read_bytes())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='AttentionMaskBuilder')
        f={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
        expr=ast.unparse(f['get_splitfuse_attn_mask'])
        self.assertIn('torch.triu(torch.ones(2048, 2048), diagonal=1).to(torch.int8).to(self.device)',expr)
        self.assertEqual(ast.unparse(f['get_attention_mask'].body[-1]),'return self.get_splitfuse_attn_mask()')
    def test_original_helpers_byte_equal(self):
        old=WORK/'bole_service_proposals/native_ar_saved_requalification_repair_v3'
        for name in('ar_owner_common.py','ar_saved_namespace.py'):
            self.assertEqual((ROOT/name).read_bytes(),(old/name).read_bytes())
    def test_AST_compile_and_load_only_weights_CPU(self):
        for p in ROOT.glob('*.py'):compile(p.read_bytes(),str(p),'exec');ast.parse(p.read_bytes())
        tree=ast.parse((ROOT/'mask_diagnostic.py').read_bytes())
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='load']
        self.assertEqual(len(calls),1);kw={k.arg:k.value for k in calls[0].keywords}
        self.assertEqual(ast.literal_eval(kw['map_location']),'cpu');self.assertIs(ast.literal_eval(kw['weights_only']),True)
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):self.assertFalse(any(v.name in('torch_npu','triton')for v in n.names))
    def test_every_qualification_flag_is_literal_false(self):
        for name in('mask_diagnostic.py','mask_cpu_owner.py'):
            tree=ast.parse((ROOT/name).read_bytes())
            keys={'mask_semantics_qualified','native_FA_math_qualified','native_AR_numeric_pass','common_effects_pass','formal_success'}
            found=[]
            for n in ast.walk(tree):
                if isinstance(n,ast.keyword)and n.arg in keys:
                    self.assertIsInstance(n.value,ast.Constant);self.assertIs(n.value.value,False);found.append(n.arg)
            self.assertTrue(keys<=set(found))
    def test_original_phase_consumed_by_cold_hashing(self):
        original=M.time
        class Fake:
            @staticmethod
            def monotonic():return 1000
            @staticmethod
            def time():return 5000
        try:
            M.time=Fake;self.assertEqual(M.remaining_phase(C,800,8400),3400)
            self.assertEqual(M.remaining_phase(C,-1400,6200),1200)
            for start,cutoff in[(-1401,9999),(1001,9999),(800,8399)]:
                with self.assertRaises(ValueError):M.remaining_phase(C,start,cutoff)
        finally:M.time=original
        fn=next(n for n in ast.parse((ROOT/'mask_cpu_owner.py').read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='main')
        self.assertEqual(ast.unparse(fn.body[0]),'entry_start = time.monotonic()')
    def test_no_MAIN_lock_claim_locally(self):
        with self.assertRaises((ValueError,FileNotFoundError)):D.held_main_lock(C)
    def test_primitive_counter_does_not_allow_opaque_values(self):
        class Tensor:
            def numel(self):return 3
            def element_size(self):return 4
        class Types:pass
        Types.Tensor=Tensor
        self.assertEqual(X.primitive_tensor_bytes(Types,{'x':[Tensor(),None,4],'y':Tensor()}),24)
        with self.assertRaises(ValueError):X.primitive_tensor_bytes(Types,object())
    def test_unchanged_frozen_saved_v3_and_common_v2_manifest_refs(self):
        for packet in('native_ar_saved_requalification_repair_v3','common_plugin_effects_owner_v2'):
            v=json.loads((WORK/'bole_service_proposals'/packet/'ADVISORY_MANIFEST.json').read_text())
            for r in v['files'].values():
                raw=Path(r['path']).read_bytes();self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(r['bytes'],r['sha256']))

if __name__=='__main__':unittest.main()
