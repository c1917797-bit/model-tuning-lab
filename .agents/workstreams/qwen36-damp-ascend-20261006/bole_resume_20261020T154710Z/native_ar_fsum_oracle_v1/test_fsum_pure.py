"""NoTorch stdlib controls; actual host/readset/CPU execution remain unexercised."""
import ast
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest

ROOT=Path(__file__).resolve().parent;WORK=ROOT.parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=module('_fsum_pure_common',ROOT/'fsum_common.py');C=D.common()
O=module('_fsum_pure_oracle',ROOT/'fsum_oracle.py')


class FsumTests(unittest.TestCase):
    def test_exact21_actual_terminal_copies_and_successful_predecessor_guards(self):
        folder=WORK/'g1_review_v2/native_ar_numeric_diagnostic_v1_actual'
        refs=json.loads((ROOT/'ACTUAL_NUMDIAG_REFS.json').read_bytes());self.assertEqual(len(refs),21)
        unit_ref=json.loads((ROOT/'ACTUAL_NUMDIAG_UNIT_REF.json').read_bytes())
        def routed(r):
            if r==unit_ref:
                copy=C.ref(folder/'UNIT_TERMINAL.json');self.assertEqual((copy['bytes'],copy['sha256']),(r['bytes'],r['sha256']))
                return copy
            found=[name for name,value in refs.items()if value==r]
            if not found:return r
            copy=C.ref(folder/found[0]);self.assertEqual((copy['bytes'],copy['sha256']),(r['bytes'],r['sha256']))
            return copy
        for r in refs.values():C.checked(routed(r))
        overrides={};observed=[]
        def obj(r):return overrides.get(r['path'],C.obj(routed(r)))
        old=obj(refs['INPUTS.json'])
        def load(r,name):
            self.assertEqual(r,old['files']['numeric_common.py'])
            copy=C.ref(WORK/'bole_service_proposals/native_ar_numeric_diagnostic_v1/numeric_common.py')
            self.assertEqual((copy['bytes'],copy['sha256']),(r['bytes'],r['sha256']))
            def source_guard(_,ir):
                self.assertEqual(ir,refs['INPUTS.json']);observed.append('explicit-offline-NUMdiag-source-load-seam')
            return types.SimpleNamespace(source=source_guard)
        proxy=types.SimpleNamespace(ref=C.ref,obj=obj,checked=lambda r:C.checked(routed(r)),need=C.need,load=load,IMAGE=C.IMAGE)
        result=D.successful_numeric(proxy);self.assertEqual(result[0],refs)
        self.assertEqual(observed,['explicit-offline-NUMdiag-source-load-seam'])
        for name,key,bad in[('RESULT.json','diagnostic_completed',False),('NUMERIC-DIAGNOSTIC.json','native_FA_math_qualified',True),
                ('cpu-consumer/cleanup.json','stopped',False),('cpu-consumer/NUMERIC-DIAGNOSTIC-CHILD.json','exit_code',1)]:
            value=dict(C.obj(routed(refs[name])));value[key]=bad;overrides[refs[name]['path']]=value
            with self.assertRaises(ValueError):D.successful_numeric(proxy)
            overrides.clear()
        unit=C.obj(routed(unit_ref));bad=dict(unit);bad['exit_code']=1;overrides[unit_ref['path']]=bad
        with self.assertRaises(ValueError):D.successful_numeric(proxy)
        overrides.clear();bad=dict(unit);bad['stdout']+='MainPID=123\n';overrides[unit_ref['path']]=bad
        with self.assertRaises(ValueError):D.successful_numeric(proxy)
    def test_preregistered_whole_scalar_work_and_independent_scalar_expressions(self):
        self.assertEqual(O.QK_TERMS,25952256);self.assertEqual(O.PV_TERMS,25952256);self.assertEqual(O.EXP_TERMS,101376)
        self.assertEqual(O.QK_TERMS+O.PV_TERMS,51904512)
        source=(ROOT/'fsum_oracle.py').read_text();tree=ast.parse(source)
        fn=next(v for v in tree.body if isinstance(v,ast.FunctionDef)and v.name=='scalar_reference')
        calls={ast.unparse(v.func)for v in ast.walk(fn)if isinstance(v,ast.Call)}
        self.assertNotIn('t.matmul',calls);self.assertIn('math.fsum',calls);self.assertIn('math.exp',calls)
        self.assertIn('F.actual_native_fa(t,frame)',source);self.assertIn('original_pointwise_bound_preserved=True',source)
        self.assertIn('JOIN_ABS=1e-10;JOIN_REL=1e-12',source)
    def test_binary64_represents_BF16_products_exactly_and_fsum_cancellation(self):
        terms=[]
        # Deterministic binary BF16 values cover normal/subnormal extrema and signs.
        operands=[0.,math.ldexp(1.,-133),math.ldexp(1.9921875,-126),-.00390625,1.,-3.875,math.ldexp(1.9921875,127)]
        for a in operands:
            for b in operands:
                p=a*b;self.assertTrue(math.isfinite(p));self.assertEqual(Fraction.from_float(p),Fraction.from_float(a)*Fraction.from_float(b))
                terms.append(p)
        values=[2.**60,1.,-2.**60,2.**-20,-2.**-21]
        self.assertEqual(Fraction.from_float(math.fsum(values)),sum(map(Fraction.from_float,values)))
        naive=0.
        for value in values:naive+=value
        self.assertNotEqual(naive,math.fsum(values))
    def test_full_shape_scalar_reference_analytic_and_no_sampling_on_bad_shape(self):
        q=[[0.]*O.DIM for _ in range(O.HEADS)]
        k=[[0.]*O.DIM for _ in range(O.KEYS)]
        v=[[1. if d%2==0 else -2. for d in range(O.DIM)]for _ in range(O.KEYS)]
        output,scores,probability=O.scalar_reference(q,k,v)
        self.assertEqual(len(output),6);self.assertEqual(len(scores[0]),132)
        self.assertTrue(all(s==0 for h in scores for s in h))
        for head in output:
            for d,value in enumerate(head):self.assertLess(abs(value-(1. if d%2==0 else -2.)),1e-14)
        with self.assertRaises(ValueError):O.scalar_reference(q,k[:-1],v)
    def test_six_default_help_cold_tensor_import_tripwires(self):
        code='''import builtins,runpy,sys
old=builtins.__import__
def guard(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('forbidden cold tensor import')
 return old(name,*a,**k)
builtins.__import__=guard;p=sys.argv[1];sys.argv=[p,*sys.argv[2:]];runpy.run_path(p,run_name='__main__')
'''
        for name in('prepare_fsum_owner.py','fsum_cpu_owner.py','fsum_oracle.py'):
            for argv in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT/name),*argv],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,r.stderr)
                if not argv:self.assertFalse(json.loads(r.stdout)['enabled'])
    def test_real_prepare_copied_module_and_sourceaudit_metadata_CLI(self):
        with tempfile.TemporaryDirectory(prefix='fsum-metadata-',dir=WORK)as temporary:
            new=Path(temporary)/'control'
            code='''import builtins,importlib.util,json,runpy,sys
from pathlib import Path
packet,new,work=map(Path,sys.argv[1:]);trace=[]
old_import=builtins.__import__
def guarded(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('metadata CLI forbids tensor imports')
 return old_import(name,*a,**k)
builtins.__import__=guarded
refs=json.loads((packet/'ACTUAL_NUMDIAG_REFS.json').read_bytes())
actual=work/'g1_review_v2/native_ar_numeric_diagnostic_v1_actual/INPUTS.json'
original=importlib.util.spec_from_file_location
def spec(name,path,*a,**k):
 s=original(name,path,*a,**k)
 if name in('_fsum_packet_prepare','_fsum_prepared_control','_fsum_host_common'):
  base=s.loader
  class Loader:
   def create_module(self,spec):return base.create_module(spec)
   def exec_module(self,m):
    base.exec_module(m)
    if name=='_fsum_packet_prepare':
     real_common=m.common
     def common():
      C=real_common();old_obj=C.obj;copy=C.ref(actual)
      assert (copy['bytes'],copy['sha256'])==(refs['INPUTS.json']['bytes'],refs['INPUTS.json']['sha256'])
      def obj(r):
       if r==refs['INPUTS.json']:
        trace.append('exact-actual-primary-copy-offline-routing');return old_obj(copy)
       return old_obj(r)
      C.obj=obj;return C
     def forbidden(*a,**k):raise AssertionError('packet module cannot replace copied fullRef')
     m.common=common;m.source=forbidden;m.readset=forbidden
    else:
     def readset(C,y,**k):
      assert Path(m.__file__)==new/'fsum_common.py'
      assert m.source(C,C.ref(new/'INPUTS.json'))==y
      assert y['schema']=='bole.native-ar-fsum-oracle-inputs/v1'and y['actual_NUMdiag_refs']==refs
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
out='/opt/host/vnf/austinov/run-bole-native-ar-fsum-offline'
cli(packet/'prepare_fsum_owner.py',['--prepare','--new-control-root',str(new),'--new-output-root',out])
C=sys.modules['_fsum_prepared_control'].common();ir=C.ref(new/'INPUTS.json')
cli(new/'fsum_cpu_owner.py',['--source-audit','--inputs-ref',json.dumps(ir)])
print(json.dumps(dict(trace=trace,actual_host_readset=False,resources_admitted=False)))
'''
            r=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT),str(new),str(WORK)],capture_output=True,text=True,timeout=20)
            self.assertEqual(r.returncode,0,r.stderr);values=[json.loads(row)for row in r.stdout.splitlines()]
            self.assertEqual(values[-1]['trace'],['exact-actual-primary-copy-offline-routing',
                '_fsum_prepared_control:real-copied-fullRef-source-pass','_fsum_host_common:real-copied-fullRef-source-pass'])
            self.assertTrue(all(v['resources_admitted']is False for v in values));self.assertFalse(values[-1]['actual_host_readset'])
            E=module('_fsum_metadata_copy',new/'fsum_common.py');ir=C.ref(new/'INPUTS.json');E.source(C,ir)
            with self.assertRaises(ValueError):D.source(C,ir)
            bad=C.obj(ir);bad['schema']='bole.native-ar-fsum-oracle-inputs/v0';bad_ref=C.write(new/'BAD.json',bad)
            with self.assertRaises(ValueError):E.source(C,bad_ref)
            with(new/'fsum_oracle.py').open('ab')as f:f.write(b'\n# tamper\n')
            with self.assertRaises(ValueError):E.source(C,ir)
    def test_owner_first_clock_and_real_original_CPU_lifecycle_preserved(self):
        M=module('_fsum_clock',ROOT/'fsum_cpu_owner.py');M.time=types.SimpleNamespace(monotonic=lambda:1000,time=lambda:5000)
        self.assertEqual(M.remaining_phase(C,800,8400),3400);self.assertEqual(M.remaining_phase(C,-1220,6380),1380)
        for start,cut in[(-1221,9999),(1001,9999),(800,8399)]:
            with self.assertRaises(ValueError):M.remaining_phase(C,start,cut)
        text=(ROOT/'fsum_cpu_owner.py').read_text();fn=next(v for v in ast.parse(text).body if isinstance(v,ast.FunctionDef)and v.name=='main')
        self.assertEqual(ast.unparse(fn.body[0]),'entry_start = time.monotonic()')
        self.assertLess(text.index('ctl.name.islower()'),text.index("ctl.observe('saved-native-fsum-CPU-admission',initial=True)"))
        self.assertLess(text.index("ctl.observe('saved-native-fsum-CPU-admission',initial=True)"),text.index("ctl.cpu['guest_cpus']"))
        self.assertLess(text.index("ctl.cpu['guest_cpus']"),text.index('owned_create.create('))
        self.assertIn('mathematics_recomputed=math_recomputed',text)
    def test_compile_safe_load_and_frozen_original_files_unchanged(self):
        for p in ROOT.glob('*.py'):ast.parse(p.read_bytes());compile(p.read_bytes(),str(p),'exec')
        tree=ast.parse((ROOT/'fsum_oracle.py').read_bytes())
        loads=[v for v in ast.walk(tree)if isinstance(v,ast.Call)and ast.unparse(v.func)=='t.load'];self.assertEqual(len(loads),2)
        for call in loads:self.assertEqual({k.arg:ast.literal_eval(k.value)for k in call.keywords},dict(map_location='cpu',weights_only=True))
        for name in('native_ar_numeric_diagnostic_v1','native_ar_saved_requalification_repair_v4'):
            m=json.loads((WORK/'bole_service_proposals'/name/'ADVISORY_MANIFEST.json').read_bytes())
            for r in m['files'].values():self.assertEqual(C.ref(r['path']),r)
        for name in('ar_owner_common.py','ar_saved_namespace.py'):
            self.assertEqual((ROOT/name).read_bytes(),(WORK/'bole_service_proposals/native_ar_numeric_diagnostic_v1'/name).read_bytes())

if __name__=='__main__':unittest.main()
