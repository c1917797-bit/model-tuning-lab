"""Finite host-only input/ABI controls; no real tokenizer, tensor, HTTP or NPU PASS."""
import ast
from dataclasses import asdict
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import hypic32k_input as I
import render_input32k as R


class TokenizerFixture:
    vocab_size=256
    def encode(self,text,add_special_tokens=False):
        assert add_special_tokens is False
        return [ord(x)for x in text]


class InputControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet=I.dataset(TokenizerFixture())
        cls.bundle=R.render()

    def test_original_generator_shared_prefix_and_distinct_suffix(self):
        p=self.packet
        self.assertEqual(len(p['prompt_cases']),42)
        for role in ('warmup','measured','retirement-barrier'):
            ids=I.select(p,role);self.assertEqual(len(ids),32768)
            self.assertEqual(ids[:16384],p['prompt_cases'][0][:16384])
        self.assertNotEqual(I.select(p,'warmup')[16384:],I.select(p,'measured')[16384:])
        self.assertEqual([I.output(x)for x in('smoke8','intermediate160','formal1024')],[8,160,1024])
        with self.assertRaises(ValueError):I.output('C16')

    def test_bad_inputs_and_no_false_historical_identity(self):
        p=dict(self.packet,prompt_cases=list(self.packet['prompt_cases']))
        p['prompt_cases'][2]=list(p['prompt_cases'][2]);p['prompt_cases'][2][0]=True
        with self.assertRaises(ValueError):I.validate(p)
        p=dict(self.packet,prompt_cases=list(self.packet['prompt_cases']))
        p['prompt_cases'][2]=list(p['prompt_cases'][0])
        with self.assertRaises(ValueError):I.validate(p)
        self.assertFalse(self.packet['historical_prompt_bytes_identical'])
        self.assertFalse(self.packet['HYPIC_enabled'])

    def test_real_rendered_request_payload_both_output_modes(self):
        # Executes the REAL derived request() and its nested post wrapper;
        # transport/parser are declared fixtures, not real HTTP/SSE evidence.
        text=self.bundle['files']['performance_service_client.py'].decode()
        fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='request')
        class C:
            @staticmethod
            def need(v,s):
                if not v:raise ValueError(s)
        seen=[]
        def transport(wire,timeout):
            body=json.loads(wire.data);seen.append(body)
            self.assertEqual(len(body['prompt']),32768)
            self.assertNotIn('vllm_xargs',body)
            self.assertNotIn('hypic',json.dumps({k:v for k,v in body.items()if k!='prompt'}).lower())
            return object()
        def capture(response,record,header,count):
            record.update(done=True,token_ids=list(range(count)),
                usage=dict(prompt_tokens=32768,completion_tokens=count))
            return response
        donor=I.generator()
        def completion(args,index,prompt,barrier,count):
            self.assertEqual(prompt.segment_ends,())
            donor._post_json('http://fixture.invalid/v1/completions',
                dict(model='fixture',prompt=prompt.prompt,max_tokens=count,stream=True),10)
            return donor.RequestResult(index=index,ok=True,ttft_ms=1,duration_s=1,
                output_tokens=count,finish_reason='length',requested_output_tokens=count)
        donor._stream_completion=completion
        ns=dict(C=C,Capture=capture,json=json,asdict=asdict)
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'actual-derived-request','exec'),ns)
        for count,role in[(8,'warmup'),(1024,'measured')]:
            ns['request'](donor,SimpleNamespace(),I.select(self.packet,role),0,count,role,transport,[])
        self.assertEqual([x['max_tokens']for x in seen],[8,1024])
        sys.modules.pop(donor.__name__,None)

    def test_native_geometry_server_and_whole_inverse(self):
        b=self.bundle;self.assertEqual(R.inverse(b),b['parent'])
        files=b['files'];name='_geometry32k_fixture'
        spec=importlib.util.spec_from_file_location(name,HERE/'not-materialized.py')
        mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod
        try:
            exec(compile(files['fa_native_geometry.py'],'actual-derived32kgeometry','exec'),mod.__dict__)
            p=mod.plan(32768,1024)
            self.assertEqual((p['max_before'],p['maximum_publication_pages'],p['maximum_scratch_pages']),
                             (33790,264,265))
            with self.assertRaises(ValueError):mod.plan(2048,1024)
            with self.assertRaises(ValueError):mod.require(dict(p))
        finally:sys.modules.pop(name,None)
        tree=ast.parse(files['contract090.py'])
        server=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='server_command')
        literals=[n.value for n in ast.walk(server)if isinstance(n,ast.Constant)]
        self.assertEqual(literals.count('40960'),2)
        self.assertEqual(files['g3_fia_contract.py'],b['parent']['g3_fia_contract.py'])
        self.assertEqual(files['oracle112.py'],b['parent']['oracle112.py'])
        self.assertEqual(files['transaction.py'],b['parent']['transaction.py'])
        self.assertFalse(b['source_ready'])
        self.assertGreater(I.demand(1024)['full_before_FA_minimum_bytes'],384*2**20)

    def test_actual_native_environment_removes_Bole_and_Hypic(self):
        # Actual derived branch with explicit metadata/selector fixtures;
        # this is not source admission or real worker environment evidence.
        import os
        text=self.bundle['files']['server090.py'].decode()
        functions=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and
                   n.name in('environment','apply_environment')]
        m=dict(model_receipt_root='/fixture/receipts',performance_arm='native_ar',performance_profile={})
        class C:
            @staticmethod
            def obj(r):return m
            @staticmethod
            def need(v,s):
                if not v:raise ValueError(s)
        ns=dict(C=C,PERF=SimpleNamespace(select=lambda e,p:object()),P=Path('/fixture/source'),os=os,json=json)
        exec(compile(ast.Module(body=functions,type_ignores=[]),'actual-derived-native-environment','exec'),ns)
        base={'BOLE_THREE_NODE_MODEL_ENABLE':'1','HYPIC_ENABLE':'1','VLLM_PLUGINS':'ascend,hypic'}
        out=ns['environment'](base,{},Path('/fixture/receipts'))
        self.assertEqual(out['VLLM_PLUGINS'],'ascend,dense_opportunity090')
        self.assertFalse(any(k.startswith(('BOLE_','BOLE111_','HYPIC_'))for k in out))
        ns['apply_environment'](base,out)
        self.assertFalse(any(k.startswith(('BOLE_','BOLE111_','HYPIC_'))for k in base))


if __name__=='__main__':unittest.main()
