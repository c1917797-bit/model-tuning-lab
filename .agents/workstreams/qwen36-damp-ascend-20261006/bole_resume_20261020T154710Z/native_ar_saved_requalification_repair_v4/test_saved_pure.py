"""Offline actual-receipt metadata controls; no numerical/device pass fabricated."""
import ast
import copy
import hashlib
import types
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent;WORK=ROOT.parents[1]
spec=importlib.util.spec_from_file_location('_test_saved_v2_common',ROOT/'saved_common.py')
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B);C=B.common()
spec=importlib.util.spec_from_file_location('_test_actual_HTTP_shape',ROOT/'http_provenance.py')
HP=importlib.util.module_from_spec(spec);spec.loader.exec_module(HP)

class OfflineReceiptView:
    """Routes canonical refs to exact copied bytes for HTTP-shape unit tests.

    g1_pass returns already qualified primary documents solely for the unit
    test, without exercising host source/releases or claiming qualification.
    Actual execution always uses unchanged C.g1_pass and the full G1 reader.
    """
    need=staticmethod(C.need)
    def __init__(self):
        self.refs=json.loads((ROOT/'ACTUAL_FAILURE_REFS.json').read_text())
        self.mapping={r['path']:WORK/'g1_review_v2/native_ar_saved_v1_failure'/n for n,r in self.refs.items()}
        self.on=json.loads((WORK/'g1_review_v2/qualification/SOURCE_BOUND.json').read_text())
        self.owner=json.loads((WORK/'g1_review_v2/qualification/RESULT.json').read_text())
        self.bundle=json.loads((WORK/'g1_review_v2/qualification/CONSUMER_INPUTS.json').read_text())
        self.report=json.loads((WORK/'g1_review_v2/qualification/ATTRIBUTION.json').read_text())
        self.mapping[self.owner['summary']['actual_client_terminal']['path']]=WORK/'g1_review_v2/qualification/CLIENT-TERMINAL.json'
        self.mapping[self.on['files']['service_client.py']['path']]=WORK/'bole_service_proposals/g1_multi_request/service_client.py'
    def checked(self,r):
        p=self.mapping[r['path']];a=C.ref(p)
        C.need(a['sha256']==r['sha256']and('bytes'not in r or a['bytes']==r['bytes']),'actual copied primary wholeSHA')
        return p
    def obj(self,r):return json.loads(self.checked(r).read_bytes())
    def g1_pass(self,*refs):return self.on,self.owner,self.bundle,self.report

class SavedTests(unittest.TestCase):
    def test_actual_prepare_and_sourceaudit_CLI_copied_module_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix='saved-v4-roundtrip-',dir=WORK)as temporary:
            new=Path(temporary)/'control'
            code='''import ast,builtins,copy,importlib.util,json,runpy,sys
from pathlib import Path
packet,new,work=map(Path,sys.argv[1:]);trace=[]
oldimport=builtins.__import__
def guard(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('metadata-only CLI fixture cannot import tensor runtimes')
 return oldimport(name,*a,**k)
builtins.__import__=guard
base=work/'g1_review_v2/native_ar_v5_saved'
actual=json.loads((packet/'ACTUAL_SAVED_REFS.json').read_bytes())
objects={name:json.loads((base/name).read_bytes())for name in actual}
x=objects['OWNER_INPUTS.json'];m=objects['AR_SOURCE_BOUND.json']
def prior(C,refs):
 assert refs==actual
 return objects,x,m
original=importlib.util.spec_from_file_location
def spec(name,path,*a,**k):
 s=original(name,path,*a,**k)
 if name in('_saved_prepare_common','_saved_v4_prepared_common','_saved_host_common'):
  old=s.loader
  class Loader:
   def create_module(self,spec):return old.create_module(spec)
   def exec_module(self,module):
    old.exec_module(module)
    if name=='_saved_prepare_common':
     module.prior=prior
     def fail(*a,**k):raise AssertionError('packet module reused after source copy')
     module.source=fail;module.readset=fail
    else:
     original_readset=module.readset
     def readset(C,y,**kw):
      assert Path(module.__file__)==new/'saved_common.py'
      assert module.source(C,C.ref(new/'INPUTS.json'))==y
      # Execute the real readset's prior+new metadata/schema guard. Only the
      # prior replay and evidence expansion are declared offline seams.
      fn=next(v for v in ast.parse(Path(module.__file__).read_bytes()).body if isinstance(v,ast.FunctionDef)and v.name=='readset')
      namespace=dict(C=C,y=y,prior=prior,LOCK=module.LOCK,Path=Path)
      exec(compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(fn.body[:2]),type_ignores=[])),'<real-source-ticket-guard>','exec'),namespace)
      assert y['schema']=='bole.native-ar-saved-requalification-inputs/v4'
      trace.append(name+':exact-prepared-source-pass')
      return x,m,{},list(y['files'].values()),dict(explicit_offline_readset_fixture=True)
     module.readset=readset
  s.loader=Loader()
 return s
importlib.util.spec_from_file_location=spec
def cli(path,args):
 sys.argv=[str(path),*args]
 try:runpy.run_path(str(path),run_name='__main__')
 except SystemExit as error:
  if error.code not in(None,0):raise
cli(packet/'prepare_saved_owner.py',['--execute','--new-control-root',str(new),'--new-output-root','/opt/host/vnf/austinov/run-bole-native-ar-saved-v4-offline'])
C=sys.modules['_saved_v4_prepared_common'].common();ir=C.ref(new/'INPUTS.json')
cli(new/'saved_cpu_owner.py',['--source-audit','--inputs-ref',json.dumps(ir)])
print(json.dumps(dict(trace=trace,actual_host_full_readset=False,resources_admitted=False)))
'''
            r=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT),str(new),str(WORK)],capture_output=True,text=True,timeout=20)
            self.assertEqual(r.returncode,0,r.stderr)
            rows=[json.loads(line)for line in r.stdout.splitlines()]
            trace=next(v for v in rows if 'trace'in v)
            self.assertEqual(trace['trace'],['_saved_v4_prepared_common:exact-prepared-source-pass','_saved_host_common:exact-prepared-source-pass'])
            self.assertFalse(trace['actual_host_full_readset']);self.assertFalse(trace['resources_admitted'])
    def mask_context(self):
        p=WORK/'g1_review_v2/native_ar_mask_v4_actual'
        refs=json.loads((ROOT/'ACTUAL_MASK_V4_REFS.json').read_bytes())
        values={name:json.loads((p/name).read_bytes())for name in refs}
        ar=json.loads((WORK/'g1_review_v2/native_ar_v5_saved/NATIVE-AR-BUNDLE.json').read_bytes())
        spec=importlib.util.spec_from_file_location('_test_exact_actual_mask_chain',ROOT/'mask_evidence.py')
        E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
        return p,refs,values,ar,E
    def test_actual_mask13_primary_copies_and_all128_metadata(self):
        p,refs,values,ar,E=self.mask_context()
        for name,r in refs.items():
            a=C.ref(p/name);self.assertEqual((a['bytes'],a['sha256']),(r['bytes'],r['sha256']))
        proof=E.metadata(C,values,refs,ar)
        self.assertEqual(proof['frame_count'],128);self.assertEqual(proof['q1_KV132_visible_keys'],132)
        self.assertEqual(proof['mask_SHA'],E.MASK_SHA);self.assertFalse(proof['mathematical_qualification'])
    def test_actual_metadata_missing_frame_source_release_ABI_mutations_reject(self):
        _,refs,values,ar,E=self.mask_context()
        mutations=[lambda v:v['cpu-consumer/MASKS.json']['ranks'][3]['frames'].pop(),
            lambda v:v['cpu-consumer/MASKS.json']['ranks'][1]['frames'][20]['mask'].update(contiguous_byte_sha256='0'*64),
            lambda v:v['cpu-consumer/MASKS.json']['ranks'][0]['frames'][31]['parameters'].update(sparse_mode=2),
            lambda v:v['cpu-consumer/MASKS.json']['ranks'][2]['frames'][0]['explicit_kwargs_keys'].append('pse_shift'),
            lambda v:v['cpu-consumer/cleanup.json'].update(stopped=False),
            lambda v:v['RESULT.json'].update(source_after={}),
            lambda v:v['cpu-consumer/OWNED.json'].update(source=ar['source'])]
        for mutate in mutations:
            bad=copy.deepcopy(values);mutate(bad)
            with self.assertRaises(ValueError):E.metadata(C,bad,refs,ar)
    def test_fullmask_guard_offline_byte_fixture_rejects_far_corruption(self):
        # Explicit stdlib byte fixture exercises the actual guard expression;
        # real Torch controls are mandatory in the future Devices[] child.
        full=b''.join(bytes(i+1)+b'\1'*(2047-i)for i in range(2048))
        self.assertEqual(hashlib.sha256(full).hexdigest(),'d016ca7be6be829fd102f03317c3eed915d3df3d3fd54279a8858caea2dd57de')
        class Tensor:
            ndim=2
            def __init__(self,raw=full,dtype='int8',shape=(2048,2048),stride=(2048,1),offset=0,contiguous=True):
                self.raw=raw;self.dtype=dtype;self.shape=shape;self._stride=stride;self._offset=offset;self.contiguous=contiguous
            def is_contiguous(self):return self.contiguous
            def stride(self):return self._stride
            def storage_offset(self):return self._offset
        T=types.SimpleNamespace(int8='int8',ones=lambda *a,**k:None,triu=lambda *a,**k:Tensor(),equal=lambda a,b:a.raw==b.raw)
        tree=ast.parse((ROOT/'derived_math_consumer.py').read_bytes())
        guard=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and len(n.args)==2 and
            isinstance(n.args[1],ast.Constant)and n.args[1].value=='exact actual full int8 upper2048 template; q1 right-down sees all132 keys')
        code=compile(ast.Expression(guard.args[0]),'<actual-fullmask-guard>','eval')
        accepts=lambda mask:bool(eval(code,dict(t=T,mask=mask)))
        self.assertTrue(accepts(Tensor()))
        bad=bytearray(full);bad[1733*2048+1000]=1
        for value in(Tensor(raw=bytes(bad)),Tensor(dtype='bool'),Tensor(shape=(132,132)),Tensor(stride=(1,2048)),Tensor(offset=1),Tensor(contiguous=False)):
            self.assertFalse(accepts(value))
    def test_cold_entry_clock_preserves_single_phase_and_cleanup_reserve(self):
        spec=importlib.util.spec_from_file_location('_test_saved_v4_clock',ROOT/'saved_cpu_owner.py')
        M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
        M.time=types.SimpleNamespace(monotonic=lambda:1000,time=lambda:5000)
        self.assertEqual(M.remaining_phase(C,800,8400),3400)
        self.assertEqual(M.remaining_phase(C,-1220,6380),1380)
        for start,cutoff in[(-1221,9999),(1001,9999),(800,8399)]:
            with self.assertRaises(ValueError):M.remaining_phase(C,start,cutoff)
        fn=next(n for n in ast.parse((ROOT/'saved_cpu_owner.py').read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='main')
        self.assertEqual(ast.unparse(fn.body[0]),'entry_start = time.monotonic()')
    def test_all_frozen_saved_and_mask_packets_unchanged(self):
        for name in('native_ar_saved_requalification_repair_v3','native_ar_mask_diagnostic_v1','native_ar_mask_diagnostic_v2',
                     'native_ar_mask_diagnostic_v3','native_ar_mask_diagnostic_v4'):
            m=json.loads((WORK/'bole_service_proposals'/name/'ADVISORY_MANIFEST.json').read_bytes())
            for r in m['files'].values():
                self.assertEqual(C.ref(r['path']),r)
    def test_actual_second_failure_and_successful_G1_authority_bytes(self):
        refs=json.loads((ROOT/'ACTUAL_V2_FAILURE_REFS.json').read_text())
        p=WORK/'g1_review_v2/native_ar_saved_v2_failure'
        for name,r in refs.items():
            a=C.ref(p/name)
            self.assertEqual((a['bytes'],a['sha256']),(r['bytes'],r['sha256']))
        owner=json.loads((p/'G1_OWNER_RESULT.json').read_text())
        owned=json.loads((p/'G1_CPU_OWNED.json').read_text())
        self.assertEqual(owner['source_before'],owner['source_after'])
        self.assertEqual(len(owner['source_before']),385)
        failed=json.loads((p/'RESULT.json').read_text())
        self.assertIsNotNone(failed['primary']);self.assertFalse(failed['independent_numeric_requalification_pass'])
        self.assertEqual(failed['secondary'],[]);self.assertEqual(failed['source_before'],failed['source_after'])
        self.assertNotIn('independent',failed['summary'])
        known={
            '/opt/host/vnf/austinov/run-bole-native-conv-calibration118-MAIN-20261016-001/mask/numeric/numeric/result/conv/STAGE_RESULT.json':
                '673b5cdb02f78c24352bae8b927f18db9c2957e7642a1a6bc28ff4483e01392b',
            '/opt/host/vnf/austinov/run-bole-native-conv-abi118repair1-MAIN-20261016-001/mask/numeric/numeric/result/ACTUAL_DEVICE_CONV_ABI.json':
                'c68ec52dff3bda1162c891b26ac9d6fd8673aacff5c74c72f575ffcd3805dbf6'}
        for path,digest in known.items():
            self.assertEqual(owner['source_before'][path],digest)
            self.assertEqual(owned['mounts'][path],[path,False])
    def test_complete_source_closure_uses_original_streaming_ref_and_rejects_changes(self):
        # Synthetic temporary files exercise enumeration only; no actual host,
        # installed-source, admission or mathematical success is asserted.
        with tempfile.TemporaryDirectory(dir=ROOT)as directory:
            refs=[]
            for i in range(385):
                p=Path(directory)/str(i);p.write_bytes(str(i).encode());refs.append(C.ref(p))
            before={r['path']:r['sha256']for r in refs};owner=dict(source_before=before,source_after=dict(before))
            result=B.reopen_g1_source_map(C,owner)
            self.assertEqual(result,sorted(refs,key=lambda r:r['path']))
            Path(refs[24]['path']).write_bytes(b'changed')
            with self.assertRaises(ValueError):B.reopen_g1_source_map(C,owner)
            for value in (dict(owner,source_before=dict(list(before.items())[:-1])),
                          dict(owner,source_after={}),dict(owner,source_before={**before,'/absent/unknown':'0'*64},source_after={**before,'/absent/unknown':'0'*64})):
                with self.assertRaises(ValueError):B.reopen_g1_source_map(C,value)
            unknown=dict(list(before.items())[:-1]);unknown['/absent/unknown']='0'*64
            with self.assertRaises((ValueError,FileNotFoundError)):
                B.reopen_g1_source_map(C,dict(source_before=unknown,source_after=dict(unknown)))
    def test_frozen_math_and_runtime_entries_remain_byte_equal_to_repair_v2(self):
        old=WORK/'bole_service_proposals/native_ar_saved_requalification_repair_v2'
        for name in ('ar_owner_common.py','ar_saved_namespace.py','http_provenance.py','saved_preflight.py'):
            self.assertEqual((ROOT/name).read_bytes(),(old/name).read_bytes())
    def test_cold_default_help_no_tensor_imports(self):
        code="""import builtins,runpy,sys
old=builtins.__import__
def guard(name,*a,**k):
 if name.split('.')[0]in('torch','torch_npu','triton'):raise RuntimeError('forbidden cold import')
 return old(name,*a,**k)
builtins.__import__=guard;p=sys.argv[1];sys.argv=[p,*sys.argv[2:]];runpy.run_path(p,run_name='__main__')
"""
        for name in ('prepare_saved_owner.py','saved_cpu_owner.py','saved_preflight.py','saved_consume_entry.py'):
            for args in ([],['--help']):
                p=subprocess.run([sys.executable,'-I','-B','-c',code,str(ROOT/name),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(p.returncode,0,p.stderr)
                if not args:self.assertFalse(json.loads(p.stdout)['enabled'])
    def test_original_namespace_byte_equal(self):
        original=WORK/'bole_service_proposals/native_ar_owner_repair_v5/ar_host_namespace.py'
        self.assertEqual((ROOT/'ar_saved_namespace.py').read_bytes(),original.read_bytes())
    def test_derivative_full_inverse_and_all_math_AST(self):
        delta=json.loads((ROOT/'CONSUMER_METADATA_DELTA.json').read_text())
        inverse=(ROOT/'derived_math_consumer.py').read_text()
        for pair in reversed(delta['edits']):
            self.assertEqual(inverse.count(pair['after']),1);inverse=inverse.replace(pair['after'],pair['before'])
        original=WORK/'bole_service_proposals/native_ar_pair/consume_pair.py'
        self.assertEqual(inverse.encode(),original.read_bytes())
        old={n.name:n for n in ast.parse(original.read_bytes()).body if isinstance(n,ast.FunctionDef)}
        restored=(ROOT/'derived_math_consumer.py').read_text()
        mask_edit=delta['edits'][-1];restored=restored.replace(mask_edit['after'],mask_edit['before'],1)
        new={n.name:n for n in ast.parse(restored).body if isinstance(n,ast.FunctionDef)}
        for name in ('identity_join','same_bits','tensor_bytes','assemble','actual_native_fa','compare_tokens'):
            self.assertEqual(ast.dump(old[name]),ast.dump(new[name]))
    def test_all_actual_failure_primary_files_whole_SHA(self):
        refs=json.loads((ROOT/'ACTUAL_FAILURE_REFS.json').read_text())
        for name,r in refs.items():
            a=C.ref(WORK/'g1_review_v2/native_ar_saved_v1_failure'/name)
            self.assertEqual((a['bytes'],a['sha256']),(r['bytes'],r['sha256']))
        old=json.loads((WORK/'g1_review_v2/native_ar_saved_v1_failure/saved_v1/RESULT.json').read_text())
        self.assertIsNotNone(old['primary']);self.assertEqual(old['secondary'],[])
        self.assertFalse(old['independent_numeric_requalification_pass'])
        self.assertNotIn('independent',old['summary'])
    def http_context(self):
        view=OfflineReceiptView();p=WORK/'g1_review_v2/native_ar_v5_saved'
        x=json.loads((p/'OWNER_INPUTS.json').read_text());m=json.loads((p/'AR_SOURCE_BOUND.json').read_text())
        y=dict(actual_prior_cpu_failure_refs=view.refs)
        frozen=dict(json.loads((WORK/'g1_review_v2/INPUTS_G1.json').read_text()),reference=x['frozen_inputs'])
        tree=ast.parse((ROOT/'derived_math_consumer.py').read_bytes())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='http_tokens')
        scope=dict(C=view,_SAVED_METADATA=y,_http_provenance=lambda PC,s,b,v,sc,h,f,t:HP.validate(view,x,m,y,s,b,v,sc,h,f))
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-http-shape-unit','exec'),scope)
        return view,x,m,y,frozen,scope['http_tokens']
    def test_actual_both_HTTP_formats_and_all_six_response_shapes(self):
        view,x,m,y,frozen,run=self.http_context()
        ar=dict(http=view.refs['AR/HTTP_RESULT.json']);on=dict(http=view.refs['BOLE/HTTP_RESULT.json'])
        self.assertNotIn('inputs_ref',view.obj(on['http']))
        self.assertEqual(run(x['AR_source'],ar,'bole.actual-native-ar-smoke-HTTP/v1','bole-native-ar-131-',frozen),[[79091,1204],[79091,1204]])
        self.assertEqual(run(m['BOLE_source_ref'],on,'bole.actual-c1-two-request-service-HTTP/v1','bole-g1-131-',frozen),[[79091,1204],[79091,1204]])
    def test_G1_receipt_must_not_gain_invented_inputs_ref(self):
        view,x,m,y,frozen,_=self.http_context();bundle=dict(http=view.refs['BOLE/HTTP_RESULT.json'])
        value=view.obj(bundle['http']);value['inputs_ref']=frozen['reference']
        with self.assertRaises(ValueError):HP.validate(view,x,m,y,m['BOLE_source_ref'],bundle,value,'bole.actual-c1-two-request-service-HTTP/v1','bole-g1-131-',frozen)
    def test_actual_prompts_still_required(self):
        view,x,m,y,frozen,run=self.http_context();wrong=copy.deepcopy(frozen);wrong['token_ids'][0]+=1
        for key,source,schema,prefix in [('AR',x['AR_source'],'bole.actual-native-ar-smoke-HTTP/v1','bole-native-ar-131-'),('BOLE',m['BOLE_source_ref'],'bole.actual-c1-two-request-service-HTTP/v1','bole-g1-131-')]:
            with self.assertRaises(ValueError):run(source,dict(http=view.refs[key+'/HTTP_RESULT.json']),schema,prefix,wrong)
    def test_exact_full_ref_resolution_and_unknown_rejection(self):
        with tempfile.TemporaryDirectory(dir=ROOT)as directory:
            path=Path(directory)/'copy.py';path.write_text('x=1\n');host=C.ref(path)
            installed=dict(host,path=str(Path(directory)/'absent'/'installed.py'));mapping={installed['path']:dict(installed=installed,host=host)}
            refs,resolved=B.collect(C,{'snapshot':installed},mapping)
            self.assertEqual(refs,[host]);self.assertEqual(len(resolved),1)
            for bad in (dict(installed,sha256='0'*64),{k:installed[k]for k in('path','sha256')},dict(installed,path=str(Path(directory)/'absent'/'unknown.py'))):
                with self.assertRaises((ValueError,FileNotFoundError)):B.collect(C,bad,mapping)
    def test_no_actual_MAIN_lock_claim_locally(self):
        with self.assertRaises((ValueError,FileNotFoundError)):B.held_main_lock(C)

if __name__=='__main__':unittest.main()
