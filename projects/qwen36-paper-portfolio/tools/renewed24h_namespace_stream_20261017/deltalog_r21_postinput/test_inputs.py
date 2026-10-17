import ast,base64,copy,hashlib,json,subprocess,sys,tempfile,types,unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import prepare_inputs as M

def bound(t):
 m=copy.deepcopy(t);m['files']['COMMANDS_FINAL.json']=M.MODEL_COMMANDS
 m['command_ticket_binding']=dict(schema='deltalog.cheap-prebind-own-closure/v021',template=M.MODEL_TEMPLATE,ticket=M.MODEL_COMMANDS,resources_admitted=False,qualified=False,NPU=False,source_root_alias_is_preparation_only=False,physical_source_root=t['root'])
 return m

def phase():return dict(schema='deltalog.r21-new-experiment-clock/v1',whole_seconds=3600,cleanup_seconds=270,postverify_seconds=900,margin_seconds=90,work_seconds=2340,cutoff_epoch=1792313000,not_retroactive=True)

class Inputs(unittest.TestCase):
 def fixture(self):
  sr={'actual_fixture_only':'not qualification'};ps={'payload_fixture_only':'not qualification'};cid='a'*64;root='/payload'
  parent=dict(source=sr,status='failed',primary='actual deliberate child failure fixture',secondary=[],elapsed=1200,cleanup_seconds=100,post_work_verification=dict(source_after=True,metadata_after_hash=True,registered_cap_seconds=900,actual_cap_seconds=900),all_created_containers_release_verified=True,owned_containers=[dict(stage='/model/candidate',cid=cid,exact_owned_release_verified=True)])
  x=dict(Id=cid,Image=M.IMAGE,State=dict(Status='exited',Running=False,Pid=0,OOMKilled=False),ExecIDs=None)
  loaded=dict(source=sr,rows=[]);reports=[]
  for rank in range(4):
   pid=100+rank;ns=10+rank;start=1000+rank
   loaded['rows'].append(dict(rank=rank,logical=rank,physical=rank+4,namespace_pid=ns,actual_host_process=dict(pid=pid,start_ticks=start)))
   reports.append((dict(path=root+'/FIRST-DECODE-'+str(ns)+'/FIRST-DECODE-REPORT.json'),dict(source=ps,model_source=sr,namespace_pid=ns,domain=dict(rank=rank,physical=rank+4,cid=cid,host_pid=pid,start_ticks=start))))
  return [sr,ps,parent,x,loaded,dict(cid=cid),reports,root]
 def test_four_actual_identity_shapes_metadata_only(self):M.validate_rows(*self.fixture())
 def test_missing_duplicate_or_old_rank_rejected(self):
  for change in('missing','duplicate','oldpid','duplicatehost','wrongroot','oldsource','wrongcandidate','parentpass','secondary','missingfence','overtime'):
   x=self.fixture()
   if change=='missing':x[6].pop()
   elif change=='duplicate':x[6][3]=copy.deepcopy(x[6][0])
   elif change=='oldpid':x[6][0][1]['domain']['start_ticks']-=1
   elif change=='duplicatehost':
    p=copy.deepcopy(x[4]['rows'][0]['actual_host_process']);x[4]['rows'][1]['actual_host_process']=p;x[6][1][1]['domain'].update(host_pid=p['pid'],start_ticks=p['start_ticks'])
   elif change=='wrongroot':x[6][0][0]['path']='/old/FIRST-DECODE-10/FIRST-DECODE-REPORT.json'
   elif change=='oldsource':x[6][0][1]['model_source']={'old':True}
   elif change=='wrongcandidate':x[2]['owned_containers'][0]['cid']='b'*64
   elif change=='parentpass':x[2]['status']='pass'
   elif change=='secondary':x[2]['secondary']=['failed final fence']
   elif change=='missingfence':x[2]['post_work_verification']['source_after']=False
   else:x[2]['elapsed']=3601
   with self.subTest(change=change),self.assertRaises(ValueError):M.validate_rows(*x)
 def test_wrong_hash_pending_and_exclusive_output(self):
  with self.assertRaises(ValueError):M.checked(None)
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'input.json';r=M.write(p,dict(metadata_fixture=True));self.assertEqual(M.obj(r),dict(metadata_fixture=True))
   with self.assertRaises(FileExistsError):M.write(p,{})
   r['sha256']='0'*64
   with self.assertRaises(ValueError):M.checked(r)
 def test_fresh_I_off_missing_actual_refs(self):
  path=str(Path(M.__file__).resolve())
  x=subprocess.run([sys.executable,'-I','-B',path],capture_output=True,text=True);self.assertEqual(x.returncode,0,x.stderr);self.assertEqual(json.loads(x.stdout),dict(enabled=False,NPU=False))
  x=subprocess.run([sys.executable,'-I','-B',path,'--execute'],capture_output=True,text=True);self.assertNotEqual(x.returncode,0);self.assertIn('actual three Ref3 required',x.stderr)
 def test_exact_R21_pin_old_source_rejected(self):
  import difflib,hashlib
  inv=json.loads((Path(__file__).parent/'INVERSE.json').read_bytes())
  self.assertEqual(''.join(difflib.restore(inv['whole_ndiff'],2)).encode(),Path(M.__file__).read_bytes())
  oldbytes=''.join(difflib.restore(inv['whole_ndiff'],1)).encode();self.assertEqual(hashlib.sha256(oldbytes).hexdigest(),inv['original_collector']['sha256'])
  self.assertEqual(M.MODEL_TEMPLATE,{'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair21-20261017-001/SOURCE_TEMPLATE.json', 'bytes': 243191, 'sha256': 'bd53c08cb9886af01c3f90940f0a1bd16bb18ef70ada7f784d4576568ab63a41'})
  self.assertTrue(M.OUTPUT.as_posix().endswith('/run-dl-firstdecode-input-R21-MAIN-001'))
  self.assertEqual(M.PAYLOAD,{'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-selected-firstdecode-renew24h-20261017-001/SOURCE_MANIFEST.json', 'bytes': 17250, 'sha256': '413dfbf5b8dd3444cfafc19c6ce3e1e49cbb5414fb4ee1202f91a924cb232a29'})
  self.assertEqual(M.KEYS,{'schema','model_source','payload_source','owner_ref','inspect_ref','loaded_ref','reports_ref'})
  old=dict(prepared_only=False,prepared_template=dict(path='/old/R18/SOURCE_TEMPLATE.json',bytes=226639,sha256='87c5ed0c880f07ad03f6284ba6190e7bebc47c324dbbfac6d143467fd3b9942d'))
  old19=dict(prepared_only=False,prepared_template=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-first-real-decode-owned-renew24h-v1-101-repair19-20261017-001/SOURCE_TEMPLATE.json',bytes=234563,sha256='adca9c401d3beaa22fb560c9be9a0f8ec659bacf449f608502877dde32d1ea89'))
  for prior in(old,old19,dict(prepared_only=True,prepared_template=M.MODEL_TEMPLATE)):
   with patch.object(M,'obj',return_value=prior),self.assertRaisesRegex(ValueError,'exact bound R21'):M.prepare({'software':'old-pin-negative-only'},None,None)
  with self.assertRaises(ValueError):M.prepare(None,None,None)
 def test_actual_command_pin_and_bound_registration_negatives(self):
  self.assertEqual(M.MODEL_COMMANDS,dict(path=M.MODEL_TEMPLATE['path'].rsplit('/',1)[0]+'/COMMANDS_FINAL.json',bytes=7825,sha256='345b1414b267fa4d4183bfb3e251d22b169bae0e9feb3add8b31d56c3031a075'))
  t=dict(root='/actual/model',files={'source':'metadata fixture'},runtime_identity={'run':'actual-fixture'},output_root='/actual/output',budgets=dict(phase_seconds=3600),phase_budget_registration=phase())
  c=dict(template=M.MODEL_TEMPLATE,payload_source=M.PAYLOAD,postconsumer_input_ticket=dict(payload_source=M.PAYLOAD,exclusive_new_path=(M.OUTPUT/'INPUT.json').as_posix()),model_output_root=t['output_root'],whole_seconds=3600,phase_budget_registration=phase())
  M.validate_registration(bound(t),t,c)
  for change in('source','command','output','input','runtime'):
   m=bound(t);bad=copy.deepcopy(c)
   if change=='source':m['files']={}
   elif change=='command':bad['template']={'oldR19':True}
   elif change=='output':m['output_root']='/old'
   elif change=='input':bad['postconsumer_input_ticket']['exclusive_new_path']='/workspace/INPUT.json'
   else:m['runtime_identity']={}
   with self.subTest(change=change),self.assertRaises(ValueError):M.validate_registration(m,t,bad)
 def test_typed_snapshot_initial_final_and_partition_negatives(self):
  sr={'fixture_only':True};er={'closed_storage_only':True};ss={'closed_source_only':True};leaf='/P/new-payload';jr=dict(path='/P/MODEL_SNAPSHOTS_LEDGER.R21.json',bytes=1,sha256='a'*64)
  prior=dict(schema='deltalog.closed-released-empty-attempt/v021',numeric_qualified=False,candidate_created=False,prior_lease_terminal=True,actual_payload_bytes=0,fixture_not_live_evidence=True)
  m=dict(output_root='/opt/new',firstdecode_contract=dict(closed_evidence_ref=er,closed_source_ref=ss,closed_readset=dict(prior_released_empty_attempt=prior)));c=dict(payload_leaf=leaf,required_actual_closed_evidence_ref=er)
  p=dict(post_work_verification=dict(storage=dict(model_snapshots_reservation_ref=jr)));b=dict(storage_proof=dict(model_snapshots_reservation_ref=jr))
  j=dict(schema='deltalog.model-snapshots-reservation/v1',source=sr,payload_source=M.PAYLOAD,leaf=leaf,combined_opt_root='/opt/new',budget_bytes=32*2**30,payload_total_cap_bytes=30*2**30,opt_total_cap_bytes=2*2**30,allocated_worker_cap_bytes=15*2**29,legacy_ledger_written=False,numeric_qualified=False,closed_overlay_ref=er,closed_source_ref=ss,prior_released_empty_attempt=prior)
  M.validate_journal(sr,m,c,p,b,jr,j)
  for change in('oldsource','oldjournal','ledger','partition','finalref','closed','promotion'):
   v=copy.deepcopy(j);rr=copy.deepcopy(jr);pp=copy.deepcopy(p)
   if change=='oldsource':v['source']={'oldR19':True}
   elif change=='oldjournal':rr['path']='/P/MODEL_SNAPSHOTS_LEDGER.R19.json'
   elif change=='ledger':v['legacy_ledger_written']=True
   elif change=='partition':v['payload_total_cap_bytes']=32*2**30
   elif change=='finalref':pp['post_work_verification']['storage']['model_snapshots_reservation_ref']={}
   elif change=='closed':v['closed_overlay_ref']={}
   else:v['numeric_qualified']=True
   with self.subTest(change=change),self.assertRaises(ValueError):M.validate_journal(sr,m,c,pp,b,rr,v)

 def test_real_R21_prepared_header_projection_to_strict_bound_only_ticket(self):
  x=json.loads((Path(__file__).parent/'R21_PREPARED_HEADERS_FIXTURE.json').read_bytes())
  self.assertEqual(x['template_ref'],M.MODEL_TEMPLATE);self.assertEqual(x['commands_ref'],M.MODEL_COMMANDS)
  self.assertIsNone(x['bound_model_source_ref']);self.assertIsNone(x['owner_ref']);self.assertIs(x['actual_model_qualified'],False)
  t=x['template_headers'];c=x['commands'];self.assertEqual(len(t['files']),171)
  m=bound(t);self.assertEqual(len(m['files']),172);M.validate_registration(m,t,c)
  for defect in('prepared-files','extra-file','wrong-ticket','replay-alias','phase2700','promote'):
   bad=copy.deepcopy(m)
   if defect=='prepared-files':bad['files'].pop('COMMANDS_FINAL.json')
   elif defect=='extra-file':bad['files']['unreviewed.py']=M.MODEL_COMMANDS
   elif defect=='wrong-ticket':bad['command_ticket_binding']['ticket']=dict(M.MODEL_COMMANDS,sha256='0'*64)
   elif defect=='replay-alias':bad['command_ticket_binding']['source_root_alias_is_preparation_only']=True
   elif defect=='phase2700':bad['phase_budget_registration']['whole_seconds']=2700
   else:bad['command_ticket_binding']['qualified']=True
   with self.subTest(defect=defect),self.assertRaises(ValueError):M.validate_registration(bad,t,c)

 def test_failed_owner_is_legal_but_not_without_real_stop_or_prior_closure(self):
  x=self.fixture();x[2]['elapsed']=3000;M.validate_rows(*x)
  for defect in('running','ExecIDs','OOM','PID','foreignImage','wrongNS'):
   v=self.fixture()
   if defect=='running':v[3]['State']['Running']=True
   elif defect=='ExecIDs':v[3]['ExecIDs']=['active']
   elif defect=='OOM':v[3]['State']['OOMKilled']=True
   elif defect=='PID':v[3]['State']['Pid']=123
   elif defect=='foreignImage':v[3]['Image']='other'
   else:v[6][0][1]['namespace_pid']=987
   with self.subTest(defect=defect),self.assertRaises(ValueError):M.validate_rows(*v)

 def test_unchanged_original_payload_alias_actual_class_three_RW_and_longest_join(self):
  fixture=json.loads((Path(__file__).parent/'PAYLOAD_ALIAS_AST_FIXTURE.json').read_bytes());b=base64.b64decode(fixture['base64'],validate=True);r=fixture['original_ref']
  self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],r['sha256']))
  node=next(n for n in ast.parse(b).body if isinstance(n,ast.ClassDef)and n.name=='AliasIO')
  scope=dict(Path=Path,Q=types.SimpleNamespace(need=M.need));exec(compile(ast.Module(body=[node],type_ignores=[]),r['path'],'exec'),scope)
  budget=dict(host_stage_root='/opt/actual/candidate',guest_stage_root='/adakv-results',host_payload_root='/P/new',guest_payload_root='/adakv-results/model/capture')
  x=dict(Mounts=[dict(Destination=d,Source=s,RW=True)for d,s in(('/opt/actual/candidate','/opt/actual/candidate'),('/adakv-results','/opt/actual/candidate'),('/adakv-results/model/capture','/P/new'))])
  C=scope['AliasIO'];alias=C(x,budget,None);original=dict(path='/adakv-results/model/capture/FIRST-DECODE-10/raw.pt',bytes=123,sha256='a'*64)
  mapped=alias.actual_ref(original);self.assertEqual(Path(mapped['path']),Path('/P/new/FIRST-DECODE-10/raw.pt'));self.assertEqual(mapped['sha256'],original['sha256']);self.assertEqual(original['path'],'/adakv-results/model/capture/FIRST-DECODE-10/raw.pt')
  with self.assertRaises(ValueError):alias.actual_ref(dict(original,path='/adakv-results/model/capture/../outside'))
  for defect in('missing','duplicate','thirdhost','wrongpayload'):
   bad=copy.deepcopy(x)
   if defect=='missing':bad['Mounts'].pop()
   elif defect=='duplicate':bad['Mounts'].append(copy.deepcopy(bad['Mounts'][0]))
   elif defect=='thirdhost':bad['Mounts'].append(dict(Destination='/extra',Source='/foreign',RW=True))
   else:bad['Mounts'][2]['Source']='/wrong'
   with self.subTest(defect=defect),self.assertRaises(ValueError):C(bad,budget,None)

if __name__=='__main__':unittest.main()
