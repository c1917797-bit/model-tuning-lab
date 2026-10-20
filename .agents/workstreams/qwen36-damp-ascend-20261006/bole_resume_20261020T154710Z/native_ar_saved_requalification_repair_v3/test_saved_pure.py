"""Offline actual-receipt metadata controls; no numerical/device pass fabricated."""
import ast
import copy
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
        for name in ('ar_owner_common.py','ar_saved_namespace.py','derived_math_consumer.py',
                     'CONSUMER_METADATA_DELTA.json','http_provenance.py','saved_preflight.py','saved_consume_entry.py'):
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
        new={n.name:n for n in ast.parse((ROOT/'derived_math_consumer.py').read_bytes()).body if isinstance(n,ast.FunctionDef)}
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
