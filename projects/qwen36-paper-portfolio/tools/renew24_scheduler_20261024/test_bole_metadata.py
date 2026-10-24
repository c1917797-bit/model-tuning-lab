"""Original BOLE metadata ABI, fixtures only; never launch or declare actual release."""
import copy,importlib.util,json,pathlib,tempfile,time,unittest
HERE=pathlib.Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
S=load('scheduler',HERE/'scheduler.py')
A=load('bole_metadata',HERE/'bole_metadata.py')
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='bole-metadata-fixture-');self.root=pathlib.Path(self.tmp.name).resolve()
  self.C=S.io();self.seq=0
  self.out=self.root/'output';self.src=self.root/'source';self.src.mkdir()
  self.files={n:self.C.publish(self.src/n,{'fixture_only':True,'name':n})for n in('host_service.py','qualification_smoke_join.py')}
  self.scope=dict(physical_NPUs=[4,5,6,7],input_tokens=32768,output_tokens=8,generations=2,formal_performance=False,phase_seconds=100,cleanup_seconds=10)
  self.resources=dict(guest_model_GiB=48,guest_CPU_GiB=8,host_GiB=.5,RAMreserve_GiB=8,Docker_reserve_GiB=8.5,whole_seconds=100,shared_cleanup_seconds=10)
  reserves=dict(model_cgroup=48*2**30,independent_CPU_guest=8*2**30,host_controller=2**29,host_RAM=8*2**30,Docker_free=int(8.5*2**30),output_cap=32*2**30)
  self.m=dict(root=str(self.src),output_root=str(self.out),files=self.files,
    qualification_parent_preparation_readset=[],qualification_historical_short_source={'fixture_only':True},short2k_helper_refs=[],
    resources=self.resources,input_resource_profile32k=dict(reserves=reserves))
  review=dict(schema='bole.MAIN-fastpath-short8-qualification-source-review/v1',approved=True,scope=self.scope,source_root=str(self.src),output_root=str(self.out),
    files=self.files,parent_preparation_readset=[],historical_short_source={'fixture_only':True},short2k_helper_refs=[],fixture_only=True)
  ar=dict(schema='bole.MAIN-reviewed-fastpath-short8-qualification-authority/v1',approved=True,start_epoch=100,cutoff_epoch=1000,scope=self.scope,MAIN_review_ref=self.obj(review),fixture_only=True)
  self.m['qualification_authority_ref']=self.obj(ar)
  self.sr=self.C.publish(self.src/'SOURCE_BOUND.json',self.m);template=self.obj({'fixture_only':True,'template':True})
  model=['/usr/bin/env','FIXTURE=1','/usr/bin/python3','-I','-B',str(self.src/'host_service.py'),'--execute','--source-ref',json.dumps(self.sr),'--output',str(self.out)]
  cpu=model.copy();cpu.insert(cpu.index('--source-ref'),'--cpu-only');cpu[-1]+='-CPU'
  self.commands=dict(schema='bole.performance-actual-bound-commands/v1',bound_source=self.sr,source=template,model=model,CPU=cpu,
    consume=['/usr/bin/python3','-I','-B',str(self.src/'qualification_smoke_join.py'),'--consume','--source',self.sr['path'],'--host-result',str(self.out/'RESULT.json'),'--output',str(self.out/'FASTPATH_NUMERIC_SCOPE_RESULT.json')])
  self.cr=self.C.publish(self.src/'COMMANDS.json',self.commands)
 def tearDown(self):self.tmp.cleanup()
 def obj(self,v):
  self.seq+=1;return self.C.publish(self.root/('f%d.json'%self.seq),v)
 def normalize(self,stage='model',**kw):
  args=dict(source_ref=self.sr,commands_ref=self.cr,stage=stage,now=200,cpu_millis=4000,docker_write_bound=2**30);args.update(kw)
  return A.normalize(self.C,**args)
 def test_actual_command_shapes_all_roles_no_fake_ready(self):
  for stage in('CPU','model','consume'):
   v=self.normalize(stage)
   self.assertEqual(v['state'],'preparing');self.assertFalse(v['ready']);self.assertFalse(v['release_verified'])
   self.assertEqual(v['budget']['ram'],int((48.5 if stage=='model'else 8.5)*2**30))
   self.assertEqual(v['wall_seconds'],110)
  self.assertFalse(self.normalize()['standalone_CPU_before_model_required'])
 def test_template_not_bound_and_stale_ref_rejected(self):
  with self.assertRaises(ValueError):self.normalize(source_ref=self.commands['source'])
  pathlib.Path(self.sr['path']).write_bytes(b'changed')
  with self.assertRaises(ValueError):self.normalize()
 def test_expired_or_bool_clock_rejected(self):
  for v in(1000,99,True):
   with self.assertRaises(ValueError):self.normalize(now=v)
 def test_wrong_role_source_output_and_duplicate_operand(self):
  for change in('source','output','duplicate'):
   c=copy.deepcopy(self.commands)
   if change=='source':c['model'][c['model'].index('--source-ref')+1]=json.dumps(c['source'])
   elif change=='output':c['model'][-1]='/'+change
   else:c['model']+=['--source-ref',json.dumps(self.sr)]
   with self.assertRaises(ValueError):self.normalize(commands_ref=self.obj(c))
 def test_original_metadata_registration_to_planner_not_parallel_approval(self):
  v=self.normalize();packet=self.obj(v);accept=self.obj({'fixture_only':True,'original_source_audit_accepted':True})
  parent=dict(id='audit',paper='BOLE',kind='prepare',gate='source-audit',deps=[],state='passed',physical=[],budget=dict(ram=0,cpu_millis=0,disk={}),
    wall_seconds=1,critical_seconds=1,deadline_epoch=1000,ready_at=100,output_root=None,edit_scope='draft/audit',acceptance_ref=accept)
  n=dict(id='model',paper='BOLE',gate='model-screen',deps=['audit'],state='ready',critical_seconds=120,ready_at=100,edit_scope='draft/model',packet_ref=packet,
    prerequisite_refs=[dict(artifact_ref=accept,consumer_ref=accept,acceptance_ref=accept)],**{k:v[k]for k in('physical','budget','kind','output_root','wall_seconds','deadline_epoch')})
  self.assertEqual(S.readiness(n,{'audit':parent,'model':n},self.C,now=200),v)
  n['prerequisite_refs']=[]
  with self.assertRaises(ValueError):S.readiness(n,{'audit':parent,'model':n},self.C,now=200)
 def test_real_historical_old_commands_are_expired_now(self):
  p=HERE.parents[3]/'.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/bole_fa_cache_diagnostic_prepare_v1_20261024/prepared-source-short8-cache-diagnostic-v1'
  self.assertTrue((p/'COMMANDS.json').is_file())
  with self.assertRaisesRegex(ValueError,'expired historical'):
   A.normalize(self.C,source_ref=self.C.reference(p/'SOURCE_BOUND.json'),commands_ref=self.C.reference(p/'COMMANDS.json'),stage='model',now=int(time.time()),cpu_millis=4000,docker_write_bound=2**30)
 def test_unknown_Docker_bound_stays_preparing_and_cannot_enter_READY(self):
  v=self.normalize(docker_write_bound=None)
  self.assertIsNone(v['budget']['disk']['docker']);self.assertTrue(v['missing_registration'])
  self.assertFalse(v['ready'])
 def test_no_original_cleanup_is_a_fresh_release(self):
  self.assertFalse(self.normalize()['release_verified'])
  with self.assertRaises(ValueError):A.checked_old_leaf(self.C,{'path':'/missing','bytes':1,'sha256':'a'*64})
if __name__=='__main__':unittest.main(verbosity=2)
