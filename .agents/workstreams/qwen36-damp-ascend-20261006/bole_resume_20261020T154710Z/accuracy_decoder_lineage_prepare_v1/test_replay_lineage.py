"""Synthetic pure policy/source controls only. No approvals, HTTP, models or generated code."""
import ast
import copy
from pathlib import Path
import types
import unittest
import decoder_replay_contract as R
import render_decoder as D

def fixture():
    # In-memory dictionaries are explicitly synthetic software test operands.
    rr=lambda name:dict(path='/SYNTHETIC/'+name,bytes=1,sha256='0'*64)
    b=dict(schema='bole.current-CPU-replay-binding/v1',source_root='/SYNTHETIC/source',files={'fixture':rr('code')},
        required_readonly_mounts=['/SYNTHETIC/source'],
        phase='smoke',arm='ON',historical_task_source_ref=rr('historical-source'),effective_inputs_ref=rr('effective'),
        plan_ref=rr('plan'),raw_ref=rr('raw'),generation_producer_ref=rr('producer'))
    br=rr('binding');ticket=dict(schema=R.AUTH_SCHEMA,approved=True,start_epoch=100,cutoff_epoch=1000,
        scope=copy.deepcopy(R.SCOPE),binding_ref=br,MAIN_review_ref=rr('review'))
    review=dict(schema=R.REVIEW_SCHEMA,approved=True,scope=copy.deepcopy(R.SCOPE),binding_ref=br,
        source_root=b['source_root'],files=b['files'])
    process=dict(pid=123,start_ticks=7,uid=0,executable='/python',cgroup_sha256='fixture')
    executor=dict(schema='bole.actual-current-CPU-replay-execution/v1',role='cpu-consumer',image_id=R.IMAGE,
        process=process,container_id='f'*64)
    inspect=[dict(Id='f'*64,Image=R.IMAGE,State=dict(Running=True,Pid=123),
        HostConfig=dict(Privileged=False,Devices=[],DeviceRequests=[],DeviceCgroupRules=[],Runtime='runc',NetworkMode='none',ReadonlyRootfs=True),
        Mounts=[dict(Source='/SYNTHETIC/host/source',Destination='/SYNTHETIC/source',RW=False)])]
    plan=dict(phase='smoke',arm='ON',source_ref=b['historical_task_source_ref'],
        effective_inputs_ref=b['effective_inputs_ref'],count=6,model='fixture-model')
    raw=dict(schema='bole.actual-three-task-HTTP-completions/v1',**{k:plan[k]for k in
        ('phase','arm','source_ref','effective_inputs_ref','model')},records=[{'fixture':i}for i in range(6)])
    g=dict(schema='bole.actual-task-generation-provenance/v1',producer_ref=b['generation_producer_ref'],plan_ref=b['plan_ref'],raw_ref=b['raw_ref'],
        HTTP_source_ref=rr('HTTP-source'),authority_ref=rr('generation-authority'),
        owner_ref=rr('owner'),client_ref=rr('client'),release_ref=rr('release'),started_epoch=10,finished_epoch=20)
    hs=dict(authority_ref=g['authority_ref'],plan_ref=b['plan_ref'],phase='smoke',request_count=6)
    owner=dict(schema='bole.actual-task-runtime-owned/v1',primary=None,secondary=[],source_input_before={'x':'sha'},
        source_input_after={'x':'sha'},private_namespace_restored_by_identity=True,
        summary=dict(client_ref=g['client_ref'],model_release_ref=g['release_ref']))
    client=dict(schema='bole.actual-task-normalEOS-cohort-client/v2',source_ref=g['HTTP_source_ref'],primary=None,
        raw_ref=b['raw_ref'],completed_task_requests=6,barrier={'fixture':True})
    release=dict(stopped=True,retained=True,errors=[])
    host=dict(schema='bole.actual-host-CPU-replay-process-binding/v1',container_id='f'*64,
        process=process,host_pid=123,NSpid=[123],host_start_ticks=7,host_cgroup='fixture/'+'f'*64,
        UID=[0]*4,executable='/python')
    return b,br,ticket,review,process,executor,inspect,plan,raw,g,hs,owner,client,release,host

class Controls(unittest.TestCase):
    def ticket(self,f):
        import json
        record=dict(exit_code=0,requested_argv=['/usr/bin/docker','inspect',f[5]['container_id']],
            stdout=json.dumps(f[6]),stderr='')
        return R.ticket_policy(f[2],f[3],f[1],f[0],f[5],record,f[14],200,300,f[4])
    def generation(self,f):
        return R.generation_policy(f[0],f[7],f[8],f[9],f[10],dict(start_epoch=1,cutoff_epoch=30),f[11],f[12],f[13])
    def test_current_CPU_ticket_and_historical_generation_are_distinct(self):
        f=fixture();self.ticket(f);self.generation(f) # generation time10..20 is historical, currentCPU200.
    def test_expired_old_ticket_rejected(self):
        f=fixture();f[2]['cutoff_epoch']=199
        with self.assertRaisesRegex(ValueError,'window'):self.ticket(f)
    def test_new_HTTP_ticket_not_CPU_ticket(self):
        f=fixture();f[2]['schema']='bole.new-HTTP-model-authority/v1'
        with self.assertRaisesRegex(ValueError,'CPU decoder ticket'):self.ticket(f)
    def test_no_current_execution_or_fake_clock(self):
        with self.assertRaisesRegex(ValueError,'old ticket'):
            R.current_authority({'fixture':'old'},seconds=0)
    def test_wrong_source_cohort_arm_and_count_reject(self):
        for which in ('source','cohort','arm','count'):
            f=fixture()
            if which=='source':f[8]['source_ref']={'fixture':'wrong'}
            if which=='cohort':f[8]['effective_inputs_ref']={'fixture':'wrong'}
            if which=='arm':f[8]['arm']='OFF'
            if which=='count':f[8]['records'].pop()
            with self.subTest(which=which),self.assertRaises(ValueError):self.generation(f)
    def test_generation_outside_original_window_rejected(self):
        f=fixture();f[9]['finished_epoch']=31
        with self.assertRaisesRegex(ValueError,'generation really'):self.generation(f)
    def test_currentCPU_does_not_retroactively_authorize_generation(self):
        f=fixture();f[9]['started_epoch']=150;f[9]['finished_epoch']=160
        self.ticket(f)
        with self.assertRaisesRegex(ValueError,'generation really'):self.generation(f)
    def test_wrong_executor_or_device_rejected(self):
        f=fixture();f[5]['process']=dict(f[4],pid=321)
        with self.assertRaisesRegex(ValueError,'execution identity'):self.ticket(f)
        f=fixture();f[6][0]['HostConfig']['Devices']=[{'fixture':'NPU'}]
        with self.assertRaisesRegex(ValueError,'Devices'):self.ticket(f)
    def test_host_PID_and_readonly_mounts_not_guest_claims(self):
        f=fixture();f[14]['NSpid']=[999]
        with self.assertRaisesRegex(ValueError,'host-captured'):self.ticket(f)
        f=fixture();f[6][0]['Mounts'][0]['RW']=True
        with self.assertRaisesRegex(ValueError,'readonly'):self.ticket(f)
    def test_default_Ascend_runtime_device_bind_and_wide_root_reject(self):
        f=fixture();f[6][0]['HostConfig']['Runtime']='ascend'
        with self.assertRaises(ValueError):self.ticket(f)
        for source in ('/','/dev','/dev/davinci4','/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc','/opt'):
            f=fixture();f[6][0]['Mounts'][0]['Source']=source
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'no host broad'):self.ticket(f)
    def test_only_replay_envelope_source_changes(self):
        f=fixture();derived=R.envelope(f[8],{'fixture':'current-source'})
        self.assertEqual(R.inverse_envelope(derived,f[0]['historical_task_source_ref']),f[8])
        self.assertIs(derived['records'],f[8]['records'])
    def test_reversible_complete_gate_and_unchanged_scorer(self):
        b=D.render(Path('/SYNTHETIC/new-source'));self.assertEqual(D.inverse(b),b['originals'])
        for n in ('score_tokens.py','decoder.py','postprocess.py','he_worker.py','he_policy.py'):
            self.assertEqual(b['files'][n],b['originals'][n])
        original=b['originals']['task_contract.py'].decode();node=next(n for n in ast.parse(original).body
            if isinstance(n,ast.FunctionDef)and n.name=='current_authority')
        # Execute only the original primitive clock function, with explicit synthetic IO.
        ns=dict(need=R.need,obj=lambda ref:dict(start_epoch=1,cutoff_epoch=2),OLD_AUTHORITIES=set(),
            time=types.SimpleNamespace(time=lambda:3))
        exec(compile(ast.Module(body=[node],type_ignores=[]),'original-clock-control','exec'),ns)
        with self.assertRaises(ValueError):ns['current_authority']({'sha256':'fixture'})
    def test_entry_never_dispatches_HE_worker_or_HTTP(self):
        tree=ast.parse((Path(__file__).parent/'replay_entry.py').read_bytes())
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)]
        self.assertFalse(any(isinstance(n.func,ast.Name)and n.func.id in('eval','execfile')for n in calls))
        text=(Path(__file__).parent/'replay_entry.py').read_text()
        self.assertIn("full_provenance=False",text);self.assertNotIn('subprocess',text);self.assertNotIn('urllib',text)
        b=D.render(Path('/SYNTHETIC/new-source'))
        self.assertIn('human_eval_code_executed=False',b['files']['score_tokens.py'].decode())
    def test_copied_source_namespace_and_no_context_gate_restore(self):
        import sys
        from unittest.mock import patch
        import replay_entry as E
        b=D.render(Path('/SYNTHETIC/new-source'));virtual={str(Path(b['manifest']['root'])/n):v for n,v in b['files'].items()}
        read=Path.read_bytes
        def bytes_for(path):return virtual[str(path)]if str(path)in virtual else read(path)
        names=('cohort_contract','lineage_http_common','generation_provenance','task_contract','postprocess','decoder','score_tokens')
        marker=object();old={n:sys.modules.get(n,marker)for n in names};old_path=list(sys.path)
        with patch.object(R,'checked',lambda r:Path(r['path'])),patch.object(Path,'read_bytes',bytes_for):
            try:
                with E.source_modules(b['manifest'])as modules:
                    self.assertIs(modules['score_tokens'].C,modules['task_contract'])
                    self.assertIs(modules['score_tokens'].D,modules['decoder'])
                    self.assertIs(modules['decoder'].S,modules['postprocess'])
                    with self.assertRaisesRegex(ValueError,'old ticket'):
                        modules['task_contract'].current_authority({'fixture':'old ticket'})
                    raise RuntimeError('explicit namespace restoration control')
            except RuntimeError as error:self.assertEqual(str(error),'explicit namespace restoration control')
        for n,v in old.items():
            self.assertIs(sys.modules.get(n,marker),v)
        self.assertEqual(sys.path,old_path)
    def test_original_preparation_equality_and_full_GSM_chain_remain(self):
        import json
        from unittest.mock import patch
        import replay_entry as E
        b=D.render(Path('/SYNTHETIC/new-source'));virtual={str(Path(b['manifest']['root'])/n):v for n,v in b['files'].items()}
        read=Path.read_bytes
        def bytes_for(path):return virtual[str(path)]if str(path)in virtual else read(path)
        old=b['original_manifest'];base=json.loads(Path(old['rendered_inputs_ref']['path']).read_bytes())
        # Only renderer asset realization is an explicit fixture here. The
        # original complete verify_inputs body/preparation equality/GSM1319
        # row reconstruction and chain checks actually execute unchanged.
        with patch.object(R,'checked',lambda r:Path(r['path'])),patch.object(Path,'read_bytes',bytes_for):
            with E.source_modules(b['manifest'])as modules:
                c=modules['task_contract'];c.verify_base_inputs=lambda m:base
                with self.assertRaisesRegex(ValueError,'immutable original preparation'):
                    c._historical_verify_inputs(b['manifest'])
                active=R._ACTIVE
                R._ACTIVE=dict(m=b['manifest'],binding=dict(historical_task_source_ref=D.HISTORICAL_SOURCE))
                try:
                    result=c.verify_inputs(b['manifest'])
                    self.assertEqual(result['schema'],'bole.three-task-effective-inputs/v012')
                    self.assertEqual(result['tasks']['GSM8K']['count'],1319)
                    bad=copy.deepcopy(b['manifest']);bad['input_preparation_source_ref']={'fixture':'wrong'}
                    R._ACTIVE=dict(m=bad,binding=dict(historical_task_source_ref=D.HISTORICAL_SOURCE))
                    with self.assertRaisesRegex(ValueError,'derived source changes'):c.verify_inputs(bad)
                finally:R._ACTIVE=active
    def test_generation_clock_requires_actual_host_record_shape(self):
        import generation_provenance as G
        v=dict(routeDecision='peer_direct',targetPeerId=G.PEER,result=dict(record=dict(
            state='completed',exitCode=0,timedOut=False,cancelled=False,id='exec-00000001',stderr='',
            command='/usr/bin/date',args=['+%s.%N'],stdout='1234567890.123456789\n')))
        self.assertEqual(G.clock(v)[1],1)
        wrong=copy.deepcopy(v);wrong['result']['record']['command']='/usr/bin/python3'
        with self.assertRaises(ValueError):G.clock(wrong)
        wrong=copy.deepcopy(v);wrong['result']['record']['stdout']='operator epoch 123\n'
        with self.assertRaises(ValueError):G.clock(wrong)
        wrong=copy.deepcopy(v);wrong['targetPeerId']='other-host'
        with self.assertRaises(ValueError):G.clock(wrong)

if __name__=='__main__':unittest.main()
