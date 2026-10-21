"""Stdlib-only controls; local tests never import Torch or certify real masks."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
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
    def test_original025_observe_resources_initialize_before_profile_create(self):
        base=WORK/'g1_review_v2';original_class={}
        for name,size,digest in(
            ('host_run_h8',None,'4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20'),
            ('safety_host',22338,'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30'),
            ('host_once',18170,'36844e41895b95e810b54ecae32994a96b21258ae8ad8d88fccaac19f035cf8c')):
            r=C.ref(base/(name+'.py'));self.assertEqual(r['sha256'],digest)
            if size is not None:self.assertEqual(r['bytes'],size)
        for name in('host_run_h8','safety_host','host_once'):
            original_class[name]=ast.parse((base/(name+'.py')).read_bytes())
        def function(tree,name):return next(v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name==name)
        def cls(tree):return next(v for v in tree.body if isinstance(v,ast.ClassDef)and v.name=='Controller')
        def methods(node,names):return [copy.deepcopy(v)for v in node.body if isinstance(v,ast.FunctionDef)and v.name in names]
        def compile_nodes(nodes,namespace):
            tree=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]));exec(compile(tree,'<exact-original025-methods>','exec'),namespace)
        # Original primary sources are copied whole; only external I/O is an
        # explicit fixture. No original admission/observe/resource method text
        # is changed. The constructor must really begin with cpu=None.
        def run(packet,wrong_CPU=False,observation_failure=False):
            temp=tempfile.TemporaryDirectory(prefix='mask-v4-lifecycle-',dir=WORK);self.addCleanup(temp.cleanup)
            leaf=Path(temp.name)/'cpu-consumer';leaf.mkdir();events=[]
            h=types.SimpleNamespace(protected=lambda text:{'fixture_protected0_3':True},
                legacy=lambda:types.SimpleNamespace(process_rows=lambda text:[]),idle_one=lambda text,card:None)
            bg=dict(frozen=lambda:h,time=time,PHASE_SECONDS=3600)
            bcls=copy.deepcopy(cls(original_class['host_run_h8']));bcls.bases=[];bcls.keywords=[];bcls.decorator_list=[]
            bcls.body=methods(bcls,{'__init__'});compile_nodes([bcls],bg)
            host=dict(effective_capacity=1,effective_cpus=[166],quota_ancestors=[])
            daemon=dict(effective_capacity=6,effective_cpus=list(range(145,151))if wrong_CPU else list(range(6)),quota_ancestors=[])
            H=types.SimpleNamespace(Controller=bg['Controller'],cpu_view=lambda pid:host,daemon_view=lambda:daemon)
            def path(value):
                if str(value)=='/proc/meminfo':return types.SimpleNamespace(read_text=lambda:
                    'MemAvailable: 134217728 kB\nMemTotal: 134217728 kB\nHugetlb: 0 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n')
                return Path(value)
            c=types.SimpleNamespace(require=C.need,write=C.write)
            sg=dict(H=H,c=c,PHASE=3600,time=time,os=os,json=json,Path=path,SMI='/fixture/npu-smi',DOCKER='/fixture/docker',
                PHYSICAL=(4,5,6,7),RESERVE=8*2**30,HOST_MEM=512*2**20,MEM=32*2**30,WORKSPACE=32*2**30,
                shutil=types.SimpleNamespace(disk_usage=lambda p:types.SimpleNamespace(free=100*2**30)),
                fd_holders=lambda:[],protected_boundary=lambda *a:dict(explicit_offline_boundary_fixture=True),
                actual_hbm=lambda text,card:dict(explicit_offline_HBM_fixture=True,physical=card))
            scls=copy.deepcopy(cls(original_class['safety_host']));scls.body=methods(scls,{'__init__','resources','observe'})
            compile_nodes([copy.deepcopy(function(original_class['safety_host'],'cpu_admission')),scls],sg)
            S=types.SimpleNamespace(Controller=sg['Controller'])
            def call(self,label,argv,**kw):
                events.append('original-observe:'+label)
                if observation_failure and label=='smi':raise RuntimeError('explicit observation failure fixture')
                output=json.dumps(dict(NCPU=192))if label=='engine'else('fixture SMI'if label!='running'else'')
                return dict(stdout=output,observed_utc='2026-10-20T00:00:00+00:00'),dict(explicit_offline_command_fixture=label)
            S.Controller.call=call
            hg=dict(c=c);compile_nodes([copy.deepcopy(function(original_class['host_once'],'controller'))],hg)
            joint=types.SimpleNamespace(rss=lambda:dict(aggregate_rss_kib=1024))
            main=next(n for n in ast.parse((packet/'mask_cpu_owner.py').read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='main')
            sequence=next(n.body for n in ast.walk(main)if isinstance(n,ast.Try)and any(
                isinstance(v,ast.Expr)and isinstance(v.value,ast.Call)and ast.unparse(v.value.func)=='owned_create.create'for v in n.body))
            first=next(i for i,n in enumerate(sequence)if isinstance(n,ast.Assign)and ast.unparse(n.targets[0])=='ctl')
            last=next(i for i,n in enumerate(sequence)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and ast.unparse(n.value.func)=='owned_create.create')
            env=dict(H=types.SimpleNamespace(controller=hg['controller']),S=S,joint=joint,argparse=types.SimpleNamespace(Namespace=types.SimpleNamespace),
                leaf=leaf,start=time.monotonic(),C=C,c=c,ir={},refs=[],Path=Path,__file__=str(packet/'mask_cpu_owner.py'),
                owned_create=types.SimpleNamespace(create=lambda *a:events.append('simulated-create-boundary')))
            error=None
            try:compile_nodes(copy.deepcopy(sequence[first:last+1]),env)
            except Exception as e:error=e
            return env['ctl'],events,error
        old=WORK/'bole_service_proposals/native_ar_mask_diagnostic_v3'
        ctl,events,error=run(old);self.assertIsInstance(error,TypeError);self.assertIsNone(ctl.cpu);self.assertEqual(events,[])
        ctl,events,error=run(ROOT);self.assertIsNone(error);self.assertEqual(ctl.cpu['guest_cpus'],[0,1,2,3])
        self.assertEqual(events,['original-observe:smi','original-observe:running','original-observe:engine','simulated-create-boundary'])
        ctl,events,error=run(ROOT,wrong_CPU=True);self.assertIsInstance(error,ValueError)
        self.assertEqual(ctl.cpu['guest_cpus'][:1],[145]);self.assertNotIn('simulated-create-boundary',events)
        ctl,events,error=run(ROOT,observation_failure=True);self.assertIsInstance(error,RuntimeError)
        self.assertIsNone(ctl.cpu);self.assertNotIn('simulated-create-boundary',events)
    def test_actual_mask_v3_failure_primary_copies_and_no_create(self):
        folder=WORK/'g1_review_v2/native_ar_mask_v3_failure'
        refs=json.loads((ROOT/'ACTUAL_MASK_V3_FAILURE_REFS.json').read_bytes())
        self.assertEqual(refs,json.loads((folder/'ACTUAL_REFS.json').read_bytes()))
        for name,r in refs.items():
            a=C.ref(folder/name);self.assertEqual((a['bytes'],a['sha256']),(r['bytes'],r['sha256']))
        result=json.loads((folder/'RESULT.json').read_bytes())
        self.assertIn('NoneType',result['primary']['error']);self.assertIn("ctl.cpu['guest_cpus']",result['primary']['traceback'])
        self.assertEqual(result['summary'],{});self.assertEqual(result['secondary'],[]);self.assertEqual(result['cleanup_spent'],0)
        self.assertEqual(len(result['source_before']),791);self.assertEqual(result['source_before'],result['source_after'])
        self.assertFalse(result['diagnostic_completed'])
    def metadata_cli_roundtrip(self):
        temporary=tempfile.TemporaryDirectory(prefix='mask-v3-metadata-',dir=WORK)
        self.addCleanup(temporary.cleanup);new=Path(temporary.name)/'control'
        code='''import builtins,importlib.util,json,runpy,sys
from pathlib import Path
packet,new,work=map(Path,sys.argv[1:]);trace=[]
old_import=builtins.__import__
def guarded(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('metadata CLI cannot import tensor runtimes')
 return old_import(name,*a,**k)
builtins.__import__=guarded
owner=json.loads((work/'g1_review_v2/native_ar_saved_v3_failure/RESULT.json').read_bytes())
actual=json.loads((work/'g1_review_v2/native_ar_v5_saved/OWNER_INPUTS.json').read_bytes())
original=importlib.util.spec_from_file_location
def spec(name,path,*a,**k):
 s=original(name,path,*a,**k)
 if name in('_mask_prepare','_mask_prepared_control','_mask_host_common'):
  base=s.loader
  class Loader:
   def create_module(self,spec):return base.create_module(spec)
   def exec_module(self,m):
    base.exec_module(m)
    if name=='_mask_prepare':
     def prior(C,y):
      assert y['actual_v3_failure_refs']==json.loads((packet/'ACTUAL_V3_FAILURE_REFS.json').read_bytes())
      trace.append('explicit-offline-predecessor-only-seam')
      return owner,None,None,actual,None,None
     def forbidden(*a,**k):raise AssertionError('packet source/readset reused after copy')
     m.prior=prior;m.source=forbidden;m.readset=forbidden
    else:
     def readset(C,y,**k):
      assert Path(m.__file__)==new/'diag_common.py'
      assert m.source(C,C.ref(new/'INPUTS.json'))==y
      assert y['schema']=='bole.native-ar-mask-diagnostic-inputs/v1'
      trace.append(name+':actual-copied-source-pass')
      return None,None,None,list(y['files'].values()),dict(offline_readset_fixture_only=True)
     m.readset=readset
  s.loader=Loader()
 return s
importlib.util.spec_from_file_location=spec
def cli(path,args):
 sys.argv=[str(path),*args]
 try:runpy.run_path(str(path),run_name='__main__')
 except SystemExit as e:
  if e.code not in(None,0):raise
out='/opt/host/vnf/austinov/run-bole-native-ar-mask-v3-offline'
cli(packet/'prepare_mask_owner.py',['--prepare','--new-control-root',str(new),'--new-output-root',out])
# Use the original real Ref helper and actual generated INPUTS, not an assertion
# that source-audit or admission occurred on the host.
C=sys.modules['_mask_prepared_control'].common();ir=C.ref(new/'INPUTS.json')
cli(new/'mask_cpu_owner.py',['--source-audit','--inputs-ref',json.dumps(ir)])
print(json.dumps(dict(test_trace=trace,actual_host_readset=False,resources_admitted=False)))
'''
        result=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT),str(new),str(WORK)],
            capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)
        rows=[json.loads(row)for row in result.stdout.splitlines()]
        trace=next(v for v in rows if 'test_trace'in v)
        self.assertEqual(trace['test_trace'],['explicit-offline-predecessor-only-seam',
            '_mask_prepared_control:actual-copied-source-pass','_mask_host_common:actual-copied-source-pass'])
        self.assertTrue(all(v.get('resources_admitted')is False for v in rows))
        self.assertFalse(trace['actual_host_readset'])
        y=C.obj(C.ref(new/'INPUTS.json'))
        return new,y
    def test_real_prepare_and_sourceaudit_CLI_metadata_roundtrip(self):
        new,y=self.metadata_cli_roundtrip()
        E=load('_mask_copied_source_roundtrip',new/'diag_common.py')
        self.assertEqual(E.source(C,C.ref(new/'INPUTS.json')),y)
        self.assertEqual(y['schema'],'bole.native-ar-mask-diagnostic-inputs/v1')
        self.assertEqual(y['actual_original_CPU_profile_refs'],json.loads((ROOT/'ACTUAL_CPU_PROFILE_REFS.json').read_bytes()))
        self.assertFalse(y['NPU']);self.assertFalse(y['formal_success'])
    def test_copied_source_preserves_full_path_schema_and_SHA_rejection(self):
        new,y=self.metadata_cli_roundtrip()
        E=load('_mask_copied_source_negative',new/'diag_common.py');ir=C.ref(new/'INPUTS.json')
        with self.assertRaises(ValueError):D.source(C,ir)
        wrong=dict(y,schema='bole.native-ar-mask-diagnostic-inputs/v2')
        with self.assertRaises(ValueError):E.source(C,C.write(new/'WRONG-SCHEMA.json',wrong))
        wrong=dict(y,files=dict(y['files'],**{'diag_common.py':C.ref(ROOT/'diag_common.py')}))
        with self.assertRaises(ValueError):E.source(C,C.write(new/'WRONG-PATH.json',wrong))
        # The real loader must reject a changed prepared source, even if its
        # basename is correct. This is an isolated temporary test leaf only.
        ref=C.ref(new/'diag_common.py')
        with (new/'diag_common.py').open('ab')as f:f.write(b'\n# isolated negative control\n')
        with self.assertRaises(ValueError):C.load(ref,'_mask_tampered_source_must_reject')
    def test_actual_host_diagnostic_causally_isolates_path_identity(self):
        p=WORK/'g1_review_v2/native_ar_mask_v2_prepare_failure/PREPARED_MODULE_DIAGNOSTIC.json'
        self.assertEqual(p.read_bytes(),(ROOT/'ACTUAL_V2_PREPARED_MODULE_DIAGNOSTIC.json').read_bytes())
        v=json.loads(p.read_bytes());a=v['packet_module_ref'];b=v['prepared_module_ref']
        self.assertEqual(v['input_module_ref'],b);self.assertNotEqual(a['path'],b['path'])
        local=C.ref(WORK/'bole_service_proposals/native_ar_mask_diagnostic_v2/diag_common.py')
        self.assertEqual((a['bytes'],a['sha256']),(b['bytes'],b['sha256']))
        self.assertEqual((a['bytes'],a['sha256']),(local['bytes'],local['sha256']))
        self.assertEqual(v['input_schema'],'bole.native-ar-mask-diagnostic-inputs/v1')
        self.assertFalse(v['packet_source_pass']);self.assertTrue(v['prepared_source_pass'])
        for key in('complete_readset_audited','resources_admitted','container_created','NPU','formal_success'):
            self.assertFalse(v[key])
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
        for packet in('native_ar_mask_diagnostic_v1','native_ar_mask_diagnostic_v2','native_ar_mask_diagnostic_v3',
                      'native_ar_saved_requalification_repair_v3','common_plugin_effects_owner_v2'):
            v=json.loads((WORK/'bole_service_proposals'/packet/'ADVISORY_MANIFEST.json').read_text())
            for r in v['files'].values():
                raw=Path(r['path']).read_bytes();self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(r['bytes'],r['sha256']))

if __name__=='__main__':unittest.main()
