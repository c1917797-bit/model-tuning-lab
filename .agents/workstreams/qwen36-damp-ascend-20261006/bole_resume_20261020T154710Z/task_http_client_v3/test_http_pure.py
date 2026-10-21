"""Synthetic software controls only. No actual HTTP/model/native imports/execution."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import http_common as C
import http_client as H
import native_finish_observer as O
import consume_lifecycle as R
import client_entry as Entry


def fixture(*,output=None,ignore=False,max_tokens=2048,generation=None):
    generation=generation or dict(eos_token_id=[248046,248048]);tokens=[9,248046]if output is None else output
    body=dict(model='synthetic-model',prompt=[1,2,3],max_tokens=max_tokens,ignore_eos=ignore,temperature=0,top_p=1,seed=0,n=1,stream=False,return_token_ids=True)
    extras=set(generation['eos_token_id'])-{248046}
    p=dict(ignore_eos=ignore,eos_token_id=None if ignore else 248046,stop_token_ids=[]if ignore else sorted(extras),
        all_stop_token_ids=sorted(extras|{248046}),stop=[],min_tokens=0,max_tokens=max_tokens,temperature=0,top_p=1,seed=0,n=1,
        output_kind='RequestOutputKind.FINAL_ONLY',repetition_detection=None,presence_penalty=0,frequency_penalty=0,repetition_penalty=1)
    last=tokens[-1];reason='stop'if not ignore and last in{248046,*extras}else'length';stop=last if not ignore and last in extras else None
    after=dict(request_id='synthetic-internal',object_id=123,status='FINISHED_STOPPED'if reason=='stop'else'FINISHED_LENGTH_CAPPED',
        stop_reason=stop,num_output_tokens=len(tokens),num_tokens=3+len(tokens),request_max_tokens=max_tokens,pooling=False,resumable=False,
        prompt_embeds=False,parameters=p,prompt_token_ids=body['prompt'],output_token_ids=tokens,all_token_ids=body['prompt']+tokens,last_token_id=last)
    before={k:copy.deepcopy(v)for k,v in after.items()if k not in{'prompt_token_ids','output_token_ids','all_token_ids'}}
    before.update(status='RUNNING',stop_reason=None)
    step=dict(before=before,after=after,max_model_len=8192,returned=True)
    request=dict(request_id='synthetic-client',body=body)
    choice=dict(index=0,token_ids=tokens,text='synthetic decoded text',finish_reason=reason,stop_reason=stop)
    response=dict(status=200,request_id=request['request_id'],body=dict(id='cmpl-synthetic',model=body['model'],choices=[choice],
        usage=dict(prompt_tokens=3,completion_tokens=len(tokens),total_tokens=3+len(tokens))))
    rid=after['request_id'];front=dict(request_id=rid,external_req_id='cmpl-synthetic-0',object_id=333,prompt_token_ids=body['prompt'],
        output_kind='RequestOutputKind.FINAL_ONLY',max_tokens_param=max_tokens,output_token_ids=tokens,text=choice['text'],finish_reason=reason,
        stop_reason=stop,input_finish_reason=reason,input_stop_reason=stop)
    update=dict(request_id=rid,object_id=123,before_output_count=len(tokens)-1,proposed_token_ids=[last,77],returned_token_ids=[last],native_list_after=[last],stopped=True)
    kv=dict(request_id=rid,object_id=123,original_returned_None=True)
    blocks=dict(request_id=rid,object_id=123,present_before=True,present_after=False)
    free=dict(request_id=rid,object_id=123,finished_req_id_after=True,request_present_after=False)
    engine=dict(request_id=rid,new_token_ids=[last],finish_reason=reason,stop_reason=stop)
    workers=[dict(request_id=rid,scheduler_finished_req_ids=[rid],present_before=True,object_id=444+n,prompt_token_ids=body['prompt'],present_after=False,batch_present_after=False,rank=n)for n in range(4)]
    return [request,response,front,step,update,kv,blocks,free,engine,workers,generation]


class Stop(unittest.TestCase):
    def check(self,*args,**kwargs):return R.validate_one(*fixture(*args,**kwargs))
    def test_primaryEOS_and_native_trim_join(self):self.assertEqual(self.check()['cause'],'primary-EOS')
    def test_secondary_checkpointEOS(self):self.assertEqual(self.check(output=[9,248048])['cause'],'checkpoint-secondary-EOS')
    def test_EOS_has_priority_at_full2048_cap(self):self.assertEqual(self.check(output=[9]*2047+[248046])['cause'],'primary-EOS')
    def test_real_full2048_budget_is_length(self):self.assertEqual(self.check(output=[9]*2048)['cause'],'output-budget')
    def test_barrier_ignoreEOS_emittingEOS_is_still_length(self):self.assertEqual(self.check(output=[248046],ignore=True,max_tokens=1)['finish_reason'],'length')
    def test_earlierEOS_cannot_be_followed_by_tokens(self):
        with self.assertRaises(ValueError):self.check(output=[248046,248046])
    def test_short_unjustified_length_is_rejected(self):
        with self.assertRaises(ValueError):self.check(output=[9,10])
    def test_extra_native_stopIDs_not_in_checkpoint_are_rejected(self):
        f=fixture();f[3]['after']['parameters']['stop_token_ids'].append(17);f[3]['before']['parameters']['stop_token_ids'].append(17)
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_minimum_context_cannot_be4096(self):
        f=fixture();f[3]['max_model_len']=4096
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_actual_counter_mismatch_rejected(self):
        f=fixture();f[3]['after']['num_tokens']+=1
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_frontend_stop_override_or_dropped_tokens_rejected(self):
        for key,value in(('stop_reason','stop string'),('output_token_ids',[9])):
            f=fixture();f[2][key]=value
            with self.assertRaises(ValueError):R.validate_one(*f)
    def test_native_tail_trim_must_equal_real_return_and_engine(self):
        f=fixture();f[4]['native_list_after']=[248046,77]
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_worker_must_have_actual_current_request_before_retirement(self):
        f=fixture();f[9][0]['present_before']=False
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_worker_request_or_batch_remaining_is_rejected(self):
        f=fixture();f[9][3]['batch_present_after']=True
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_duplicate_rank_is_rejected(self):
        f=fixture();f[9][3]['rank']=2
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_optional_barrier_retirement_never_invents_workers(self):
        f=fixture(output=[9],ignore=True,max_tokens=1);f[9]=[]
        self.assertIs(R.validate_one(*f,require_workers=False)['all4_worker_retired'],False)
        with self.assertRaises(ValueError):R.validate_one(*f)
    def test_HTTP_external_internal_request_join(self):
        f=fixture();f[2]['external_req_id']='cmpl-foreign-0'
        with self.assertRaises(ValueError):R.validate_one(*f)


class Software(unittest.TestCase):
    def test_literal_loopback_only(self):
        H.endpoint('http://127.0.0.1:9999/v1/completions');H.endpoint('http://[::1]:9999/v1/completions')
        for url in('https://127.0.0.1:9/v1/completions','http://localhost:9/v1/completions','http://example.com:9/v1/completions','http://127.0.0.1:9/v1/completions?x=1','http://user@127.0.0.1:9/v1/completions'):
            with self.assertRaises(ValueError,msg=url):H.endpoint(url)
    def test_duplicate_and_nonfinite_JSON_rejected(self):
        for text in('{"a":1,"a":2}','{"a":NaN}','{"a":Infinity}'):
            with self.assertRaises(ValueError):C.parse(text)
    def test_actual_HTTP_validation_rejects_truncation(self):
        f=fixture();body=f[0]['body'];response=dict(status=200,raw_body=C.canonical(f[1]['body']))
        H.validate_response(body,response)
        value=copy.deepcopy(f[1]['body']);value['choices'][0]['finish_reason']='length'
        with self.assertRaises(ValueError):H.validate_response(body,dict(status=200,raw_body=C.canonical(value)))
    def test_defaultOFF_and_help_no_dispatch(self):
        for n in('prepare_http','http_client','client_entry','bind_processes','consume_lifecycle','native_finish_observer'):
            for extra in([],['--help']):
                r=subprocess.run([sys.executable,'-I','-B',str(P/(n+'.py')),*extra],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,(n,extra,r.stderr))
                if not extra:self.assertIs(C.parse(r.stdout)['enabled'],False)
    def test_no_toplevel_inference_or_tokenizer_import(self):
        for p in P.glob('*.py'):
            for n in ast.parse(p.read_bytes()).body:
                names=[a.name for a in n.names]if isinstance(n,ast.Import)else[n.module or'']if isinstance(n,ast.ImportFrom)else[]
                self.assertFalse(any(s.split('.')[0]in{'torch','torch_npu','vllm','vllm_ascend','transformers','tokenizers'}for s in names),p.name)
    def test_frozen_native_expected_inventory(self):
        self.assertEqual(C.ref(P/'NATIVE_SOURCE_EXPECTED.json')['sha256'],C.NATIVE_EXPECTED_SHA)
        self.assertEqual(C.ref(P/'CPU_OWNER_EXPECTED.json')['sha256'],C.CPU_EXPECTED_SHA)
        e=C.obj(C.ref(P/'NATIVE_SOURCE_EXPECTED.json'));self.assertEqual(e['scheduler']['bytes'],111874)
    def test_guard_compares_actual_loaded_code_not_just_filename(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'fixture.py';p.write_text('def actual(x):\n    return x+1\n');r=C.ref(p)
            s=importlib.util.spec_from_file_location('_synthetic_http_guard',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
            O.guard(m.actual,r,'actual')
            different={};exec(compile('def actual(x):\n    return x+2\n',str(p),'exec'),different);m.actual.__code__=different['actual'].__code__
            with self.assertRaisesRegex(ValueError,'actual loaded native code'):O.guard(m.actual,r,'actual')
    def test_inverse_restores_absent_attribute_and_refuses_foreign_override(self):
        class A:value=1
        a=A();h=O.Hooks(types.SimpleNamespace(close=lambda:'synthetic-ref'));h.set(a,'value',2)
        self.assertEqual(h.close(),'synthetic-ref');self.assertNotIn('value',vars(a));self.assertEqual(a.value,1)
        h=O.Hooks(types.SimpleNamespace(close=lambda:None));h.set(a,'value',2);a.value=3
        with self.assertRaises(ValueError):h.close()
    def test_owned_inspect_uses_original_owner_label_and_same_fullCID(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);source=C.write(root/'model-source',dict(synthetic=True));cid='c'*64;name='synthetic-dense'
            labels={'model-tuning-lab.owner':'original-owner-v7','model-tuning-lab.run':name,'model-tuning-lab.arm':'dense',
                'model-tuning-lab.source-manifest-sha256':source['sha256'],'model-tuning-lab.controller-sha256':'a'*64}
            argv=['/usr/bin/docker','create','--name',name]
            for k,v in labels.items():argv.extend(['--label',k+'='+v])
            argv.extend([C.IMAGE,'-c','exec /bin/sleep infinity'])
            cr=C.write(root/'creation',dict(exit_code=0,stdout=cid+'\n',requested_argv=argv))
            e=dict(cid=cid,name=name,arm='dense',image=C.IMAGE,source=source,host_sha256='a'*64,create_receipt=cr)
            own=C.write(root/'OWNED',e)
            value=dict(Id=cid,Name='/'+name,Image=C.IMAGE,Config=dict(Image=C.IMAGE,Labels=labels))
            raw=C.write(root/'inspect',dict(exit_code=0,requested_argv=['/usr/bin/docker','inspect',cid],stdout=json.dumps([value])))
            self.assertEqual(C.owned_inspect(own,raw)[0],e)
            value['Config']['Labels']['model-tuning-lab.owner']='observed-foreign-value'
            bad=C.write(root/'wrong-inspect',dict(exit_code=0,requested_argv=['/usr/bin/docker','inspect',cid],stdout=json.dumps([value])))
            with self.assertRaises(ValueError):C.owned_inspect(own,bad)

    def test_model_owner_failure_or_unrestored_namespace_rejected(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);binding=C.write(root/'binding',{})
            o=dict(schema='bole.actual-task-runtime-owned/v1',task_normalEOS_smoke_source_ref={'synthetic':'source'},primary=None,
                secondary=[],source_input_before={},source_input_after={},private_namespace_restored_by_identity=False)
            owner=C.write(root/'owner',o)
            with self.assertRaisesRegex(ValueError,'completed inverse'):R.owner_join({'synthetic':'source'},{},None,None,binding,owner)

    def test_incomplete_journal_not_certified(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'journal';p.write_text('{"event":"header"}')
            with self.assertRaises(ValueError):R.journal(C.ref(p),{},'scheduler')


class CPUv14Metadata(unittest.TestCase):
    def fixture(self):
        return dict(schema='bole.actual-finite-task-CPU-owner/v5',primary=None,secondary=[],diagnostic_only=False,
            qualification_profile=C.CPU_PROFILE,decoder_packet_manifest_sha256=C.TASK_PACKET_MANIFEST_SHA,
            source_image_CPU_owner_software_controls_verified=True,private_namespace_restored_by_identity=True,
            source_input_before={'synthetic':'a'},source_input_after={'synthetic':'a'},NPU=False,model_executed=False,
            HTTP_executed=False,task_score_produced=False)

    def test_synthetic_full_status_still_requires_actual_evidence(self):
        value=self.fixture();C.CPU_status(value)
        with tempfile.TemporaryDirectory()as tmp:
            r=C.write(Path(tmp)/'boolean-only-fixture',value)
            with self.assertRaises(ValueError):C.CPU_proof(r,{'synthetic':'source'})

    def test_diagnostic_or_old_owner_rejected_despite_true_software_flag(self):
        for key,value in(('schema','bole.actual-finite-task-CPU-owner/v2'),('diagnostic_only',True),
                          ('qualification_profile','import-probe')):
            v=self.fixture();v[key]=value
            with self.assertRaises(ValueError,msg=key):C.CPU_status(v)

    def test_wrong_decoder_lineage_or_unrestored_source_rejected(self):
        for key,value in(('decoder_packet_manifest_sha256','0'*64),('private_namespace_restored_by_identity',False),
                          ('source_input_after',{'synthetic':'changed'}),('secondary',['cleanup error'])):
            v=self.fixture();v[key]=value
            with self.assertRaises(ValueError,msg=key):C.CPU_status(v)

    def test_full_CPU_audit_requires_complete_source_join_and_zero_denial(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp);source={'synthetic':'unbound-source'}
            def save(name,events):
                p=root/name;p.write_text(''.join(json.dumps(dict(schema='bole.actual-tokenizer-import-audit-event/v1',
                    ordinal=n,event=kind,payload=payload))+'\n'for n,(kind,payload)in enumerate(events)));return C.ref(p)
            events=[('entry',dict(source_ref=source)),('closed',dict(forbidden_attempts=[],software_qualification_accepted=False))]
            C.CPU_audit(save('complete',events),source)
            for n,bad in enumerate((events[:1],[events[0],('forbidden-import-denied',dict(module='triton')),events[1]])):
                with self.assertRaises(ValueError):C.CPU_audit(save('bad'+str(n),bad),source)
            with self.assertRaises(ValueError):C.CPU_audit(save('wrong-source',events),{'synthetic':'other'})

    def test_v14_exact19_code_inventory_and_new_decoder_pin(self):
        expected=C.obj(C.ref(P/'CPU_OWNER_EXPECTED.json'))
        self.assertEqual(len(expected),19);self.assertIn('he_admission.py',expected);self.assertIn('he_diagnostic_gate.py',expected)
        self.assertEqual(C.CPU_PROFILE,'full-v012-public-backend-network-isolation-python312/v4')
        self.assertEqual(C.TASK_PACKET_MANIFEST_SHA,'248fe4f5ddd17cb9bad494d05e692ba0edee95fe4cb5c78bebcb58fc0a0a2129')

    def test_current_owner_inherited_lock_kernel_and_fd_rows_must_join(self):
        owner=dict(actual_host_pid=90,actual_host_start_ticks=123);path='/exact/MAIN_ADMISSION.lock'
        policy=dict(serial_schedule=dict(external_lock_path=path));identity=dict(device_major=0,device_minor=45,inode=1001)
        line='1: FLOCK ADVISORY WRITE 90 00:2d:1001 0 EOF'
        value=dict(schema='bole.actual-inherited-MAIN-lock-observation/v1',lock_path=path,owner_pid=90,owner_start_ticks=123,
            capture_phase='before-sandbox-create',acquired_or_released_lock=False,file_identity=identity,
            proc_locks_matching_lines=[line],inherited_fds=[dict(link=path,file_identity=identity,regular_file=True,fdinfo='lock:\t'+line+'\n')])
        C.CPU_lock(value,policy,owner)
        for key,replacement in(('owner_pid',91),('owner_start_ticks',1),('inherited_fds',[]),
                                 ('proc_locks_matching_lines',[line.replace('WRITE','READ')])):
            v=copy.deepcopy(value);v[key]=replacement
            with self.assertRaises(ValueError,msg=key):C.CPU_lock(v,policy,owner)

    def test_HTTP_four_execution_files_remain_byteexact_when_predecessor_available(self):
        old=P.parent/'task_http_client_v2'
        if old.is_dir():
            for n in('http_client.py','native_finish_observer.py','bind_processes.py','consume_lifecycle.py'):
                self.assertEqual((P/n).read_bytes(),(old/n).read_bytes(),n)


class ClientProcessOptIn(unittest.TestCase):
    def source(self):return dict(files={n:C.ref(P/n)for n in C.FILES})
    def test_shim_sets_actual_process_env_before_original_runpy_and_rebuilds_argv(self):
        seen={};source=self.source();old=list(sys.argv)
        def run(path,run_name):
            seen.update(path=path,name=run_name,env=os.environ.get('BOLE_TASK_HTTP_MAIN_ENABLE'),argv=list(sys.argv));return {'synthetic':True}
        with patch.object(C,'source',return_value=source),patch.object(Entry.runpy,'run_path',side_effect=run),patch.dict(os.environ,{},clear=True):
            Entry.dispatch({'synthetic':'source'},'http://127.0.0.1:9/v1/completions',Path('/synthetic/output'))
            self.assertNotIn('BOLE_TASK_HTTP_MAIN_ENABLE',os.environ)
        self.assertEqual(seen['env'],'1');self.assertEqual(seen['name'],'__main__');self.assertEqual(seen['path'],str(P/'http_client.py'))
        self.assertEqual(seen['argv'],[str(P/'http_client.py'),'--execute','--source-ref','{"synthetic":"source"}',
            '--url','http://127.0.0.1:9/v1/completions','--output','/synthetic/output'])
        self.assertEqual(sys.argv,old)
    def test_source_identity_rejected_before_env_or_cli_dispatch(self):
        source=self.source();source['files']['client_entry.py']=source['files']['http_client.py']
        with patch.object(C,'source',return_value=source),patch.object(Entry.runpy,'run_path')as run,patch.dict(os.environ,{},clear=True):
            with self.assertRaises(ValueError):Entry.dispatch({'synthetic':'source'},'http://127.0.0.1:9/v1/completions',Path('/synthetic/output'))
            run.assert_not_called();self.assertNotIn('BOLE_TASK_HTTP_MAIN_ENABLE',os.environ)
    def test_wrong_original_path_or_whole_client_digest_rejected(self):
        source=self.source();source['files']['http_client.py']=source['files']['client_entry.py']
        with patch.object(C,'source',return_value=source),patch.object(Entry.runpy,'run_path')as run:
            with self.assertRaises(ValueError):Entry.dispatch({'synthetic':'source'},'http://127.0.0.1:9/v1/completions',Path('/synthetic/output'))
            run.assert_not_called()
    def test_original_client_without_client_process_optin_rejects_before_request(self):
        # A server-side env dict is deliberately not placed into this process.
        server_env={'BOLE_TASK_HTTP_MAIN_ENABLE':'1'};self.assertEqual(server_env['BOLE_TASK_HTTP_MAIN_ENABLE'],'1')
        with patch.object(C,'source',return_value={'plan_ref':{},'CPU_owner_ref':{}}),patch.object(C,'plan',return_value=({'source_ref':{}},[])),\
                patch.object(C,'CPU_proof',return_value={}),patch.object(H,'wire')as wire,patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'actual-model smoke opt-in'):H.execute({},'http://127.0.0.1:9/v1/completions',Path('/synthetic/output'))
            wire.assert_not_called()
    def test_shim_restores_argv_and_environment_even_when_original_cli_exits(self):
        old=list(sys.argv);source=self.source()
        with patch.object(C,'source',return_value=source),patch.object(Entry.runpy,'run_path',side_effect=SystemExit(7)),\
                patch.dict(os.environ,{'BOLE_TASK_HTTP_MAIN_ENABLE':'original-value'},clear=True):
            with self.assertRaises(SystemExit):Entry.dispatch({},'http://127.0.0.1:9/v1/completions',Path('/synthetic/output'))
            self.assertEqual(os.environ['BOLE_TASK_HTTP_MAIN_ENABLE'],'original-value');self.assertEqual(sys.argv,old)
    def test_eight_source_files_and_exact_successful14_ref_no_planned_G2(self):
        self.assertEqual(len(C.FILES),8);self.assertIn('client_entry.py',C.FILES)
        self.assertEqual(C.SUPPORTED_CPU_OWNER_REF['sha256'],'8403c75bdcdb74df6801b06c2e552fe0eec70a9053ddb663432fe4323be92dc5')
        self.assertEqual(C.SUPPORTED_CPU_INPUTS_REF['sha256'],'91d364a8729efde66b9c6fa062c10fdc5f17669ab3a49639af03dc21297be394')


if __name__=='__main__':unittest.main()
