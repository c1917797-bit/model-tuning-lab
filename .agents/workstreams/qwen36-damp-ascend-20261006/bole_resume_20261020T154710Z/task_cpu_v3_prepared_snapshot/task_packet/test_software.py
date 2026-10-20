"""Pure synthetic controls; no tokenizer/model/HTTP/container/generated-code execution."""
import copy
import gzip
import os
from unittest.mock import patch
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import task_contract as C
import postprocess as S
import decoder as D
import he_policy as H
import score_tokens as T
import compare_components as Q
import stage_he as J
import consume_results as R


class GSMRestoration(unittest.TestCase):
    def setUp(self):
        self.original=json.loads((P/'fixtures/GSM_ORIGINAL_FIRST_ROW.json').read_bytes())['row']
        self.old=json.loads((P/'fixtures/GSM_RENDER011_FIRST_ROW.json').read_bytes())['row']

    def test_exact_existing_first_row_only_fixed12_token_insertion(self):
        row=C.restored_gsm_row(self.original,self.old)
        self.assertEqual(row['prompt_token_ids'],self.original['prompt_token_ids'])
        self.assertEqual(len(row['prompt_token_ids'])-len(self.old['prompt_token_ids']),12)
        self.assertEqual(row['base_render011_row_sha256'],C.digest(self.old))
        self.assertTrue(row['original_token_ids_reused'])

    def test_question_change_rejected(self):
        value=copy.deepcopy(self.original);value['gold_row']['question']+=' changed'
        with self.assertRaises(ValueError):C.restored_gsm_row(value,self.old)

    def test_gold_change_rejected(self):
        value=copy.deepcopy(self.original);value['gold_row']['answer']='#### 999'
        with self.assertRaises(ValueError):C.restored_gsm_row(value,self.old)

    def test_one_instruction_token_change_rejected(self):
        value=copy.deepcopy(self.original);value['prompt_token_ids'][-10]=42
        with self.assertRaises(ValueError):C.restored_gsm_row(value,self.old)

    def test_think_frame_change_rejected(self):
        value=copy.deepcopy(self.old);value['prompt_token_ids'][-2]=42
        with self.assertRaises(ValueError):C.restored_gsm_row(self.original,value)

    def test_extra_EOS_rejected(self):
        value=copy.deepcopy(self.old);value['prompt_token_ids'][10]=248046
        with self.assertRaises(ValueError):C.restored_gsm_row(self.original,value)


class Extraction(unittest.TestCase):
    def test_original_whole_scorer_hash(self):
        self.assertEqual(C.ref(P/'frozen/gsm_scorer.py')['sha256'],S.GSM_SHA)

    def test_GSM_comma_only_normalization(self):
        self.assertTrue(S.gsm_grade('work\n#### 1,200',{'answer':'#### 1200'})['correct'])
        self.assertFalse(S.gsm_grade('#### 1.0',{'answer':'#### 1'})['correct'])

    def test_GSM_no_unmarked_or_last_answer_fallback(self):
        self.assertFalse(S.gsm_grade('the answer is 18',{'answer':'#### 18'})['correct'])
        self.assertFalse(S.gsm_grade('#### 4\n#### 18',{'answer':'#### 18'})['correct'])

    def test_MMLU_leading_boundaries(self):
        for text in('A','A. reason','A) reason','\n\nAnswer: A reason'):
            self.assertTrue(S.mmlu_grade(text,'A')['correct'],text)
        for text in('AB','Apple','a','answer: A','The answer is A','Reason\nA','(A)','A: reason'):
            self.assertFalse(S.mmlu_grade(text,'A')['correct'],text)

    def test_HE_exact_fence_and_prompt_only(self):
        prompt='def f():\n';body='    return 7\n'
        result=S.human_eval_completion('```python\n'+prompt+body+'\n```',prompt)
        self.assertEqual(result['completion'],body)
        self.assertTrue(result['outer_single_fence_removed'])
        self.assertTrue(result['exact_original_prompt_prefix_removed'])
        self.assertFalse(result['indentation_rewritten'])

    def test_HE_no_fuzzy_or_indent_repair(self):
        prompt='def f():\n';text='def f( ):\nreturn 7\n'
        self.assertEqual(S.human_eval_completion(text,prompt)['completion'],text)
        text='Explanation\n```python\n    return 7\n```'
        self.assertEqual(S.human_eval_completion(text,prompt)['completion'],text)

    def test_HE_multiple_fences_unchanged(self):
        text='```python\na\n```\n```python\nb\n```'
        self.assertEqual(S.human_eval_completion(text,'def f():\n')['completion'],text)

    def test_HE_preserves_internal_blanklines(self):
        body='    # comment\n\n    return 1\n'
        self.assertEqual(S.human_eval_completion('```\n'+body+'\n```','def f():\n')['completion'],body)


class DecoderAlgorithmOnly(unittest.TestCase):
    class Fake:
        """Algorithm fixture; intentionally never claimed to be the real tokenizer."""
        def encode(self,text,**_):return [ord(c)for c in text]
        def decode(self,ids,**_):return ''.join(chr(x)for x in ids if x!=248046)

    def test_synthetic_control_flags_never_task_score(self):
        result=D.controls(self.Fake())
        self.assertFalse(result['task_score_produced']);self.assertFalse(result['task_model_output_consumed'])
        self.assertEqual(result['postprocess_controls']['GSM_correct_flags'],[True,False,False,False])

    def test_bool_and_overlong_token_list_rejected(self):
        with self.assertRaises(ValueError):D.decode(self.Fake(),[True])
        with self.assertRaises(ValueError):D.decode(self.Fake(),[1]*2049)


class RawWire(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.row={'id':'synthetic','prompt_token_ids':[10,20]}
        self.req=dict(request_id='synthetic-only',body=T.request_body(self.row,'model'))
        self.res=dict(status=200,request_id='synthetic-only',body=dict(model='model',id='cmpl-synthetic-only',
            choices=[dict(index=0,token_ids=[30,248046],text='synthetic',finish_reason='stop')],
            usage=dict(prompt_tokens=2,completion_tokens=2,total_tokens=4)))

    def tearDown(self):self.tmp.cleanup()

    def run_case(self):
        for name,value in(('request',self.req),('response',self.res)):
            (self.root/name).write_bytes(C.canonical(value))
        record=dict(task='GSM8K',id='synthetic',request_ref=C.ref(self.root/'request'),response_ref=C.ref(self.root/'response'))
        return T.completion(record,'GSM8K',self.row,'model')

    def test_complete_raw_record_keeps_worker_proof_false(self):
        _,_,proof=self.run_case();self.assertTrue(proof['returned_EOS_observed'])
        self.assertFalse(proof['actual_worker_normal_EOS_cause_proven'])

    def test_changed_frozen_prompt_rejected(self):
        self.req['body']['prompt']=[10]
        with self.assertRaises(ValueError):self.run_case()

    def test_extra_stop_or_mintokens_rejected(self):
        self.req['body']['min_tokens']=2048
        with self.assertRaises(ValueError):self.run_case()

    def test_bool_seed_not_int_seed(self):
        self.req['body']['seed']=False
        with self.assertRaises(ValueError):self.run_case()

    def test_truncated_returned_ids_usage_rejected(self):
        self.res['body']['choices'][0]['token_ids']=[30]
        with self.assertRaises(ValueError):self.run_case()

    def test_tokens_after_EOS_rejected(self):
        self.res['body']['choices'][0]['token_ids']=[248046,30]
        with self.assertRaises(ValueError):self.run_case()

    def test_length_must_be_real_cap(self):
        self.res['body']['choices'][0]['finish_reason']='length'
        with self.assertRaises(ValueError):self.run_case()

    def test_empty_normal_stop_is_recorded(self):
        self.res['body']['choices'][0].update(token_ids=[],text='',finish_reason='stop')
        self.res['body']['usage'].update(completion_tokens=0,total_tokens=2)
        _,_,proof=self.run_case();self.assertFalse(proof['returned_EOS_observed'])


class SandboxPolicy(unittest.TestCase):
    def setUp(self):
        self.image='sha256:'+'a'*64;self.cid='c'*64
        self.command=H.argv('bole-he-synthetic',self.image,'/public/source','/public/suite','/public/inputs','b'*64,'controls')
        h=dict(Runtime='runc',NetworkMode='none',IpcMode='private',PidMode='',UTSMode='',Privileged=False,
            ReadonlyRootfs=True,Devices=[],DeviceRequests=None,DeviceCgroupRules=None,VolumesFrom=None,Links=None,
            PortBindings={},ExtraHosts=None,CapAdd=None,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],
            Memory=2*2**30,MemorySwap=2*2**30,NanoCpus=10**9,PidsLimit=64,Tmpfs={'/tmp':H.TMPFS},
            Ulimits=[dict(Name='nofile',Soft=128,Hard=128),dict(Name='fsize',Soft=8388608,Hard=8388608)])
        self.value=[dict(Id=self.cid,Image=self.image,Path='/usr/bin/env',Args=self.command[self.command.index(self.image)+1:],
            Config=dict(User='65534:65534',WorkingDir='/tmp'),HostConfig=h,
            State=dict(Running=False,ExitCode=0,OOMKilled=False,Error='',StartedAt='start',FinishedAt='finish'),
            Mounts=[dict(Destination='/'+name,Source='/public/'+name,Type='bind',RW=False,Propagation='rprivate')
                    for name in('source','suite','inputs')])]

    def inspect(self):return H.inspect_actual(self.value,expected_id=self.cid,expected_image=self.image,
        expected_argv=self.command,source_root='/public/source',suite_root='/public/suite',input_root='/public/inputs')

    def test_exact_policy_is_only_pure_fixture(self):
        self.assertTrue(self.inspect()['actual_sandbox_identity_and_limits_verified'])
        self.assertIn('--runtime',self.command);self.assertIn('runc',self.command)
        self.assertEqual(self.command[self.command.index(self.image)+1],'-i')

    def test_network_bridge_rejected(self):
        self.value[0]['HostConfig']['NetworkMode']='bridge'
        with self.assertRaises(ValueError):self.inspect()

    def test_NPU_device_rejected(self):
        self.value[0]['HostConfig']['Devices']=[dict(PathOnHost='/dev/davinci0')]
        with self.assertRaises(ValueError):self.inspect()

    def test_writable_mount_rejected(self):
        self.value[0]['Mounts'][0]['RW']=True
        with self.assertRaises(ValueError):self.inspect()

    def test_root_and_secret_mount_rejected(self):
        self.value[0]['Mounts'].append(dict(Destination='/secrets',Source='/root',Type='bind',RW=False))
        with self.assertRaises(ValueError):self.inspect()

    def test_no_resource_limit_rejected(self):
        self.value[0]['HostConfig']['Memory']=0
        with self.assertRaises(ValueError):self.inspect()

    def test_wrong_container_or_OOM_rejected(self):
        self.value[0]['Id']='d'*64
        with self.assertRaises(ValueError):self.inspect()
        self.value[0]['Id']=self.cid;self.value[0]['State']['OOMKilled']=True
        with self.assertRaises(ValueError):self.inspect()


class FullCountComparison(unittest.TestCase):
    def test_both_pp_and_relative_bounds(self):
        self.assertTrue(Q.loss_gate(1000,990,1319)['component_loss_gate_pass'])
        # <=1pp can still exceed the relative1% limit.
        result=Q.loss_gate(100,98,1319)
        self.assertTrue(result['absolute_drop_at_most_one_pp'])
        self.assertFalse(result['relative_drop_at_most_one_percent'])

    def test_zero_baseline_is_undefined_not_pass(self):
        result=Q.loss_gate(0,0,164)
        self.assertFalse(result['relative_comparison_defined'])
        self.assertFalse(result['component_loss_gate_pass'])

    def test_improvement_is_no_drop(self):
        self.assertTrue(Q.loss_gate(100,120,164)['component_loss_gate_pass'])


class PublicStageOnly(unittest.TestCase):
    """Synthetic file-staging/reader controls, no official code execution."""
    def test_frozen_public_copy_permissions_and_extra_file_rejection(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary);suite=root/'original-suite';(suite/'data').mkdir(parents=True)
            (suite/'human_eval').mkdir()
            (suite/'human_eval/dummy.py').write_text('# synthetic fixture, never imported\n')
            problems=[dict(task_id='HumanEval/'+str(i),prompt='def f():\n',canonical_solution='    return 7\n',test='',entry_point='f')for i in range(164)]
            dataset=suite/'data/HumanEval.jsonl.gz'
            with gzip.open(dataset,'wt')as stream:
                for value in problems:stream.write(json.dumps(value)+'\n')
            package=dict(repository='synthetic-only',commit='not-an-actual-benchmark',dataset_ref=C.ref(dataset),
                files=[C.ref(suite/'human_eval/dummy.py')])
            pr=C.write(root/'package',package);ar=C.write(root/'synthetic-authority',{'synthetic_fixture_only':True})
            sr=C.write(root/'synthetic-source',{'synthetic_fixture_only':True})
            m=dict(human_eval_package_ref=pr,authority_ref=ar,effective_inputs_ref=None,image_id='sha256:'+'a'*64,
                files={name:C.ref(P/name)for name in('he_worker.py','task_contract.py')})
            old=os.umask(0o077)
            try:
                with patch.object(C,'source',return_value=m),patch.object(C,'verify_inputs',return_value={}),patch.object(C,'cpu_runtime'),patch.object(C,'current_authority'):
                    reference=J.run(sr,root/'public','controls')
                    staged=C.obj(reference)
                    for name in('source','suite','inputs'):
                        self.assertEqual((root/'public'/name).stat().st_mode&0o777,0o755)
                    self.assertEqual((root/'public/suite/human_eval/dummy.py').stat().st_mode&0o777,0o644)
                    R.staged(sr,reference)
                    (root/'public/suite/unexpected-secret').write_text('synthetic-only')
                    with self.assertRaises(ValueError):R.staged(sr,reference)
            finally:os.umask(old)


class SourceAndCLI(unittest.TestCase):
    def test_order_never_missing_or_reordered(self):
        cases=[('GSM8K',{'id':'a'}),('MMLU',{'id':'b'})]
        with self.assertRaises(ValueError):C.exact_order([dict(task='GSM8K',id='a')],cases)
        with self.assertRaises(ValueError):C.exact_order([dict(task='MMLU',id='b'),dict(task='GSM8K',id='a')],cases)

    def test_old_authority_hash_rejected_before_reopening(self):
        for sha in C.OLD_AUTHORITIES:
            with self.assertRaises(ValueError):C.current_authority(dict(sha256=sha))

    def test_all_entrypoints_default_OFF_and_help(self):
        for name in('prepare_packet','restore_GSM_inputs','decoder','request_plan','score_tokens','compare_components','stage_he','he_worker','consume_results'):
            for extra in([],['--help']):
                result=subprocess.run([sys.executable,'-I','-B',str(P/(name+'.py')),*extra],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,(name,extra,result.stderr))
                if not extra:self.assertIs(json.loads(result.stdout)['enabled'],False)


if __name__=='__main__':unittest.main()
