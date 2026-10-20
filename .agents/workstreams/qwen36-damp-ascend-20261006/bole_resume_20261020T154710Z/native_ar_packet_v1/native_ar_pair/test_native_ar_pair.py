"""Synthetic source/HTTP controls only; no native model or numerical evidence."""
import contextvars
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0,str(_Path(__file__).resolve().parent))
import pair_contract as C
import consume_pair as R
import pair_entry as E
import native_ar_observer as N
import launch_profile as L


class Tensor:
    def __init__(self,n,width=2,device='cpu',contiguous=True):
        self.n,self.width,self.device,self.contiguous=n,width,SimpleNamespace(type=device),contiguous
    def numel(self):return self.n
    def element_size(self):return self.width
    def is_contiguous(self):return self.contiguous


class Tests(unittest.TestCase):
    def test_default_off_and_help_import_no_torch_or_device(self):
        for name in('pair_entry.py','consume_pair.py','native_ar_server.py',
                    'prepare_native_ar_pair.py','launch_profile.py','assemble_pair_inputs.py'):
            for args in((),('--help',)):
                value=subprocess.run([sys.executable,'-I','-B',str(P/name),*args],capture_output=True,text=True)
                self.assertEqual(value.returncode,0,(name,value.stderr))
                if not args:self.assertEqual(json.loads(value.stdout),dict(enabled=False,NPU=False))

    def test_only_declared_native_ar_mtp_argv_delta(self):
        on=['python','-m','vllm.entrypoints.openai.api_server','--model','/models/Qwen3.6-27B',
            '--max-num-seqs','1','--enforce-eager','--speculative-config',
            '{"method":"mtp","num_speculative_tokens":8}','--no-async-scheduling']
        expected=on[:8]+on[10:]
        self.assertEqual(C.native_argv(on),expected)
        self.assertEqual(on[8],'--speculative-config')

    def test_unknown_duplicate_or_inline_speculation_is_rejected(self):
        for bad in([],['x','--speculative-config','{}'],
                   ['x','--speculative-config','{"method":"mtp","num_speculative_tokens":1}'],
                   ['x','--speculative-config','{"method":"mtp","num_speculative_tokens":8}',
                    '--speculative-config','{}'],
                   ['x','--speculative-config','{"method":"mtp","num_speculative_tokens":8}',
                    '--speculative-config={}']):
            with self.assertRaises(ValueError):C.native_argv(bad)

    def test_exact_token_identity_and_first_mismatch_retained(self):
        self.assertTrue(all(r['token_identity_pass']for r in R.compare_tokens([[1,2],[3,4]],[[1,2],[3,4]])))
        value=R.compare_tokens([[1,2],[3,4]],[[1,9],[8,4]])
        self.assertEqual([r['first_mismatch_ordinal']for r in value],[1,0])
        self.assertEqual([r['matching_prefix_tokens']for r in value],[1,0])

    def test_tokenized_text_roundtrip_or_partial_completion_cannot_replace_ids(self):
        for a,b in(([[1],[2]],[[1,2],[2,3]]),([[1,2],[True,3]],[[1,2],[1,3]]),
                    ([[1,2]],[[1,2]]),([['1',2],[2,3]],[[1,2],[2,3]])):
            with self.assertRaises(ValueError):R.compare_tokens(a,b)

    def test_native_ar_observer_is_default_off_even_without_runtime_objects(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertIsNone(N.install(None,None,source_ref=None,get_forward_context=None,
                                         native_proposer=None,native_get_tp_group=None,publish=None))

    def test_module_local_proxy_delegates_outside_owned_context(self):
        calls=[]
        def original(*args,**kwargs):calls.append((args,kwargs));return 'original-object'
        module=SimpleNamespace(npu_fused_infer_attention_score=original,
                               _npu_paged_attention=original,untouched=object())
        frame=contextvars.ContextVar('synthetic',default=None)
        proxy=N.Proxy(module,None,frame)
        self.assertIs(proxy.untouched,module.untouched)
        self.assertEqual(proxy.npu_fused_infer_attention_score(3,untouched=4),'original-object')
        self.assertEqual(proxy._npu_paged_attention(5),'original-object')
        self.assertIs(module.npu_fused_infer_attention_score,original)
        self.assertEqual(len(calls),2)

    def test_opaque_noncontiguous_device_and_boolean_keys_rejected(self):
        t=SimpleNamespace(Tensor=Tensor);x=Tensor(12)
        self.assertEqual(R.tensor_bytes(t,dict(a=x,b=[x,None,4])),48)
        for bad in(object(),{True:'bad'},Tensor(2,device='npu'),Tensor(2,contiguous=False)):
            with self.assertRaises(ValueError):R.tensor_bytes(t,bad)

    def test_framework_environment_redacts_credentials_and_declares_deltas(self):
        value=L.filtered(dict(VLLM_PLUGINS='ascend,bole_native_ar_pair',
            VLLM_API_KEY='synthetic-secret',ASCEND_FEATURE='same',TORCH_FEATURE='same',
            HCCL_SECRET='synthetic-secret',BOLE_NATIVE_AR_PAIR_ENABLE='1',
            DENSE_OPPORTUNITY090_SOURCE_REF='ignored',UNRELATED_PASSWORD='ignored'))
        self.assertEqual(value['common_environment'],dict(ASCEND_FEATURE='same',TORCH_FEATURE='same'))
        self.assertNotIn('synthetic-secret',json.dumps(value))
        self.assertIs(value['plugin_effect_classification_performed'],False)
        self.assertEqual(value['plugins'],['ascend','bole_native_ar_pair'])
        self.assertEqual(value['declared_algorithm_or_observer_environment_keys'],
                         ['BOLE_NATIVE_AR_PAIR_ENABLE','DENSE_OPPORTUNITY090_SOURCE_REF'])

    def collection_fixture(self,root,variant='native_AR',wrong_count=False):
        scope=dict(schema='bole.c1-two-request-service/v1',prefix=131,request_count=2,
                   max_steps_per_request=1,max_output_tokens=2)
        on=C.write(root/'ON.json',dict(service_experiment=scope))
        inputs=C.write(root/'INPUTS.json',dict(token_ids=list(range(131)),source=on,input_tokens=131,
            tokenizer='/models/Qwen3.6-27B',data_generated_by_actual_tokenizer=True))
        pair=C.write(root/'PAIR.json',dict(synthetic_test_only=True))
        m=dict(files={'pair_entry.py':C.ref(P/'pair_entry.py')},BOLE_source_ref=on)
        seen=[]
        class Response:
            status=200
            def __init__(self,request):self.request=request
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,cap):
                body=json.loads(self.request.data);header=self.request.get_header('X-request-id')
                count=body['max_tokens'];ids=list(range(count))
                if wrong_count:ids=ids[:0]
                return json.dumps(dict(id='cmpl-'+header,usage=dict(prompt_tokens=131,completion_tokens=count),
                    choices=[dict(token_ids=ids,finish_reason='length')])).encode()
        def open_url(request,timeout):
            self.assertEqual(timeout,600);seen.append(json.loads(request.data));return Response(request)
        return pair,(pair if variant=='native_AR'else on),inputs,m,open_url,seen

    def test_pair_entry_uses_one_frozen_actual_id_input_and_explicit_budgets(self):
        for variant in('native_AR','BOLE'):
            with tempfile.TemporaryDirectory()as directory:
                root=Path(directory);sr,vsr,inputs,m,opener,seen=self.collection_fixture(root,variant)
                with patch.object(C,'source',return_value=m):
                    result=E.run(sr,variant,vsr,inputs,root,'http://127.0.0.1:8230',opener)
                ledger=C.obj(result)
                self.assertEqual([r['max_tokens']for r in seen],[2,2,1])
                self.assertTrue(all(r['prompt']==list(range(131))for r in seen))
                self.assertEqual([r['label']for r in ledger['rows']],['tree-1','tree-2','retirement-barrier'])
                self.assertIs(ledger['normal_EOS_qualified'],False)

    def test_partial_actual_http_ids_fail_and_preserve_failure_ledger(self):
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);sr,vsr,inputs,m,opener,_=self.collection_fixture(root,wrong_count=True)
            with patch.object(C,'source',return_value=m):
                with self.assertRaises(ValueError):E.run(sr,'native_AR',vsr,inputs,root,'http://127.0.0.1:8230',opener)
            self.assertTrue((root/'HTTP-FAILURE.json').is_file())

    def test_endpoint_must_be_explicit_owned_loopback(self):
        for url in('https://127.0.0.1:8230','http://foreign.example','http://u:p@127.0.0.1:8230',
                    'http://127.0.0.1:8230/path','http://127.0.0.1:8230?secret=x'):
            with tempfile.TemporaryDirectory()as directory:
                root=Path(directory);sr,vsr,inputs,m,opener,_=self.collection_fixture(root)
                with patch.object(C,'source',return_value=m):
                    with self.assertRaises(ValueError):E.run(sr,'native_AR',vsr,inputs,root,url,opener)

    def test_exact_ref_and_symlink_controls(self):
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);value=C.write(root/'A.json',dict(synthetic=True))
            self.assertEqual(C.obj(value),dict(synthetic=True))
            (root/'A.json').write_text('{}')
            with self.assertRaises(ValueError):C.obj(value)
            (root/'alias').symlink_to(root/'A.json')
            with self.assertRaises(ValueError):C.ref(root/'alias')


if __name__=='__main__':unittest.main()
