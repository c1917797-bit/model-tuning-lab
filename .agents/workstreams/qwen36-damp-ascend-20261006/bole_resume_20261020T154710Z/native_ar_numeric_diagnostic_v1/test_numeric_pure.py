"""Stdlib source/actual-receipt controls, no tensor inspection or admission."""
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
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=module('_numeric_pure_common',ROOT/'numeric_common.py');C=D.common()


class NumericTests(unittest.TestCase):
    def test_all20_actual_primary_copies_whole_SHA_and_failure_distribution(self):
        p=WORK/'g1_review_v2/native_ar_saved_v4_failure';refs=json.loads((ROOT/'ACTUAL_NUMERIC_V4_REFS.json').read_bytes())
        self.assertEqual(len(refs),20)
        for name,r in refs.items():
            a=C.ref(p/name);self.assertEqual((a['bytes'],a['sha256']),(r['bytes'],r['sha256']))
        failures=[];disagreement=[]
        for rank in range(4):
            v=json.loads((p/('cpu-consumer/RANK-%d.json'%rank)).read_bytes())
            self.assertEqual(len(v['requests']),2)
            for request in v['requests']:
                self.assertEqual(len(request['FA']),16)
                for frame in request['FA']:
                    a,b=(frame['checks'][k]for k in('FP32','FP64'))
                    if not b['pointwise_pass']:failures.append((rank,request['generation'],frame['layer']))
                    if a['pointwise_pass']!=b['pointwise_pass']:disagreement.append(frame['layer'])
        self.assertEqual(len(failures),16);self.assertEqual(disagreement,[])
        self.assertEqual([sum(v[0]==rank for v in failures)for rank in range(4)],[2,4,5,5])
    def test_reference_expressions_and_original_bound_unchanged(self):
        old=ast.parse((WORK/'bole_service_proposals/native_ar_saved_requalification_repair_v4/derived_math_consumer.py').read_bytes())
        oldfn=next(v for v in old.body if isinstance(v,ast.FunctionDef)and v.name=='actual_native_fa')
        new=ast.parse((ROOT/'numeric_diagnostic.py').read_bytes());fn=next(v for v in new.body if isinstance(v,ast.FunctionDef)and v.name=='reference')
        def expression(tree,name):
            return next(v.value for v in ast.walk(tree)if isinstance(v,ast.Assign)and isinstance(v.targets[0],ast.Name)and v.targets[0].id==name)
        for name in('scores','probability'):
            self.assertEqual(ast.dump(expression(oldfn,name)),ast.dump(expression(fn,name)))
        old_append=next(v for v in ast.walk(oldfn)if isinstance(v,ast.Expr)and ast.unparse(v).startswith('values.append('))
        new_append=next(v for v in ast.walk(fn)if isinstance(v,ast.Expr)and ast.unparse(v).startswith('values.append('))
        self.assertEqual(ast.dump(old_append),ast.dump(new_append))
        self.assertEqual(ast.unparse(expression(new,'bound')),"0.001 + 0.01 * truth.double().abs()")
    def test_real_actual_prior_chain_metadata_with_explicit_frozen_source_load_seam(self):
        folder=WORK/'g1_review_v2/native_ar_saved_v4_failure'
        refs=json.loads((ROOT/'ACTUAL_NUMERIC_V4_REFS.json').read_bytes())
        def routed(r):
            found=[name for name,value in refs.items()if value==r]
            if not found:return r
            copy=C.ref(folder/found[0]);self.assertEqual((copy['bytes'],copy['sha256']),(r['bytes'],r['sha256']))
            return copy
        overrides={};observed=[]
        def obj(r):
            v=C.obj(routed(r))
            return overrides.get(r['path'],v)
        old=obj(refs['INPUTS.json'])
        def load(r,name):
            self.assertEqual(r,old['files']['saved_common.py'])
            source=WORK/'bole_service_proposals/native_ar_saved_requalification_repair_v4/saved_common.py'
            copy=C.ref(source);self.assertEqual((copy['bytes'],copy['sha256']),(r['bytes'],r['sha256']))
            def source_guard(_,ir):
                self.assertEqual(ir,refs['INPUTS.json']);observed.append('explicit-offline-old-source-load-seam')
            return types.SimpleNamespace(source=source_guard)
        proxy=types.SimpleNamespace(ref=C.ref,obj=obj,checked=lambda r:C.checked(routed(r)),need=C.need,load=load,IMAGE=C.IMAGE)
        y=dict(actual_numeric_v4_refs=refs)
        result=D.prior(proxy,y)
        self.assertEqual(result[0],refs);self.assertEqual(observed,['explicit-offline-old-source-load-seam'])
        for name,key,bad in[('cpu-consumer/ATTRIBUTION.json','native_AR_actual_PA_FIA_pointwise_pass',True),
                ('cpu-consumer/BOLE-INDEPENDENT-GATE/ATTRIBUTION.json','G1_experiment_pass',False),
                ('cpu-consumer/cleanup.json','stopped',False)]:
            value=dict(C.obj(routed(refs[name])));value[key]=bad;overrides[refs[name]['path']]=value
            with self.assertRaises(ValueError):D.prior(proxy,y)
            overrides.clear()
    def test_default_help_six_cold_tensor_import_tripwires(self):
        code='''import builtins,runpy,sys
old=builtins.__import__
def guard(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('forbidden cold tensor import')
 return old(name,*a,**k)
builtins.__import__=guard;p=sys.argv[1];sys.argv=[p,*sys.argv[2:]];runpy.run_path(p,run_name='__main__')
'''
        for name in('prepare_numeric_owner.py','numeric_cpu_owner.py','numeric_diagnostic.py'):
            for argv in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT/name),*argv],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,r.stderr)
                if not argv:self.assertFalse(json.loads(r.stdout)['enabled'])
    def test_CPU_safe_load_all_frames_and_nonqualification_flags(self):
        for p in ROOT.glob('*.py'):ast.parse(p.read_bytes());compile(p.read_bytes(),str(p),'exec')
        tree=ast.parse((ROOT/'numeric_diagnostic.py').read_bytes())
        loads=[v for v in ast.walk(tree)if isinstance(v,ast.Call)and ast.unparse(v.func)=='t.load']
        self.assertEqual(len(loads),1);kw={v.arg:ast.literal_eval(v.value)for v in loads[0].keywords}
        self.assertEqual(kw,dict(map_location='cpu',weights_only=True))
        for v in ast.walk(tree):
            if isinstance(v,ast.keyword)and v.arg in('native_FA_math_qualified','native_AR_numeric_pass','formal_success','common_effects_pass'):
                self.assertIsInstance(v.value,ast.Constant);self.assertIs(v.value.value,False)
        text=(ROOT/'numeric_diagnostic.py').read_text()
        self.assertIn('F.actual_native_fa(t,frame)',text);self.assertIn('for frame in request[\'FA\']',text)
        self.assertIn("total<=128*2**20",text)
    def test_original025_namespace_and_common_bytes_unchanged(self):
        old=WORK/'bole_service_proposals/native_ar_mask_diagnostic_v4'
        for name in('ar_owner_common.py','ar_saved_namespace.py'):
            self.assertEqual((ROOT/name).read_bytes(),(old/name).read_bytes())
    def test_real_prepare_copied_module_and_sourceaudit_metadata_CLI(self):
        with tempfile.TemporaryDirectory(prefix='numdiag-metadata-',dir=WORK)as temporary:
            new=Path(temporary)/'control'
            code='''import builtins,importlib.util,json,runpy,sys
from pathlib import Path
packet,new,work=map(Path,sys.argv[1:]);trace=[]
old_import=builtins.__import__
def guarded(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('metadata CLI forbids tensor imports')
 return old_import(name,*a,**k)
builtins.__import__=guarded
refs=json.loads((packet/'ACTUAL_NUMERIC_V4_REFS.json').read_bytes())
actual=work/'g1_review_v2/native_ar_saved_v4_failure/INPUTS.json'
original=importlib.util.spec_from_file_location
def spec(name,path,*a,**k):
 s=original(name,path,*a,**k)
 if name in('_numeric_packet_prepare','_numeric_prepared_control','_numeric_host_common'):
  base=s.loader
  class Loader:
   def create_module(self,spec):return base.create_module(spec)
   def exec_module(self,m):
    base.exec_module(m)
    if name=='_numeric_packet_prepare':
     real_common=m.common
     def common():
      C=real_common();old_obj=C.obj;copy=C.ref(actual)
      assert (copy['bytes'],copy['sha256'])==(refs['INPUTS.json']['bytes'],refs['INPUTS.json']['sha256'])
      def obj(r):
       if r==refs['INPUTS.json']:
        trace.append('exact-actual-primary-copy-offline-routing');return old_obj(copy)
       return old_obj(r)
      C.obj=obj;return C
     def forbidden(*a,**k):raise AssertionError('packet source/readset cannot replace copied identity')
     m.common=common;m.source=forbidden;m.readset=forbidden
    else:
     def readset(C,y,**k):
      assert Path(m.__file__)==new/'numeric_common.py'
      assert m.source(C,C.ref(new/'INPUTS.json'))==y
      assert y['schema']=='bole.native-ar-numeric-diagnostic-inputs/v1'
      assert y['actual_numeric_v4_refs']==refs
      trace.append(name+':real-copied-fullRef-source-pass')
      return None,None,None,list(y['files'].values()),dict(explicit_offline_upstream_readset_only=True)
     m.readset=readset
  s.loader=Loader()
 return s
importlib.util.spec_from_file_location=spec
def cli(path,args):
 sys.argv=[str(path),*args]
 try:runpy.run_path(str(path),run_name='__main__')
 except SystemExit as e:
  if e.code not in(None,0):raise
out='/opt/host/vnf/austinov/run-bole-native-ar-numdiag-offline'
cli(packet/'prepare_numeric_owner.py',['--prepare','--new-control-root',str(new),'--new-output-root',out])
C=sys.modules['_numeric_prepared_control'].common();ir=C.ref(new/'INPUTS.json')
cli(new/'numeric_cpu_owner.py',['--source-audit','--inputs-ref',json.dumps(ir)])
print(json.dumps(dict(trace=trace,actual_host_readset=False,resources_admitted=False)))
'''
            r=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT),str(new),str(WORK)],capture_output=True,text=True,timeout=20)
            self.assertEqual(r.returncode,0,r.stderr)
            values=[json.loads(row)for row in r.stdout.splitlines()]
            last=values[-1];self.assertEqual(last['trace'],['exact-actual-primary-copy-offline-routing',
                '_numeric_prepared_control:real-copied-fullRef-source-pass','_numeric_host_common:real-copied-fullRef-source-pass'])
            self.assertFalse(last['actual_host_readset']);self.assertTrue(all(v['resources_admitted']is False for v in values))
            E=module('_numeric_metadata_copy',new/'numeric_common.py');ir=C.ref(new/'INPUTS.json');y=E.source(C,ir)
            self.assertEqual(y['files']['numeric_common.py'],C.ref(new/'numeric_common.py'))
            self.assertEqual(y['schema'],'bole.native-ar-numeric-diagnostic-inputs/v1')
            with self.assertRaises(ValueError):D.source(C,ir)  # Equal bytes cannot substitute a different absolute module path.
            bad=dict(y);bad['schema']='bole.native-ar-numeric-diagnostic-inputs/v0'
            bad_ref=C.write(new/'BAD-SCHEMA.json',bad)
            with self.assertRaises(ValueError):E.source(C,bad_ref)
            with(new/'numeric_diagnostic.py').open('ab')as stream:stream.write(b'\n# tamper control\n')
            with self.assertRaises(ValueError):E.source(C,ir)
    def test_original_observe_assigns_CPU_before_new_profile_guard_and_create(self):
        text=(ROOT/'numeric_cpu_owner.py').read_text()
        self.assertLess(text.index("ctl.name.islower()"),text.index("ctl.observe('saved-native-numeric-CPU-admission',initial=True)"))
        self.assertLess(text.index("ctl.observe('saved-native-numeric-CPU-admission',initial=True)"),text.index("ctl.cpu['guest_cpus']"))
        self.assertLess(text.index("ctl.cpu['guest_cpus']"),text.index('owned_create.create('))
        self.assertIn('mathematics_recomputed=math_recomputed',text)
        self.assertIn('summary={};math_recomputed=False',text)
    def test_cold_entry_phase_has_no_renewal(self):
        M=module('_numeric_pure_clock',ROOT/'numeric_cpu_owner.py');M.time=types.SimpleNamespace(monotonic=lambda:1000,time=lambda:5000)
        self.assertEqual(M.remaining_phase(C,800,8400),3400)
        self.assertEqual(M.remaining_phase(C,-1220,6380),1380)
        for start,cut in[(-1221,9999),(1001,9999),(800,8399)]:
            with self.assertRaises(ValueError):M.remaining_phase(C,start,cut)
        fn=next(v for v in ast.parse((ROOT/'numeric_cpu_owner.py').read_bytes()).body if isinstance(v,ast.FunctionDef)and v.name=='main')
        self.assertEqual(ast.unparse(fn.body[0]),'entry_start = time.monotonic()')
    def test_frozen_numeric_v4_and_mask_v4_manifests_preserved(self):
        for name in('native_ar_saved_requalification_repair_v4','native_ar_mask_diagnostic_v4'):
            m=json.loads((WORK/'bole_service_proposals'/name/'ADVISORY_MANIFEST.json').read_bytes())
            for r in m['files'].values():self.assertEqual(C.ref(r['path']),r)

if __name__=='__main__':unittest.main()
