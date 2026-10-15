"""Software-only typed/terminal/dispatch controls; never persisted as NPU PASS."""
import ast,copy,importlib.util,json,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_receiver_software037',P/'receivers/model_smoke_receipt.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
def need(v,m):
 if not v:raise ValueError(m)
def source_identity(config,commands,substrate,validate,pair):
 root='/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/NEW48H/deltalog-production-screen-PF037R5'
 need(commands['remote_root']==root,'actual PF R5 command root')
 need(config['validation_output_root']=='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-production-validation-PF037R5-MAIN-001','actual PF R5 validation output')
 owners=[n.value.value for n in ast.walk(ast.parse(substrate))if isinstance(n,ast.Assign)and isinstance(n.value,ast.Constant)and any(isinstance(t,ast.Attribute)and ast.unparse(t)=='S.OWNER'for t in n.targets)]
 need(owners==['dl-production-screen-PF037R5'],'actual PF R5 owner assignment, not doc/help')
 need("startswith('run-dl-production-validation-PF037R5-')"in validate and "startswith('run-dl-production-screen-PF037R5-')"in pair,'actual PF R5 host output guards')
 rows=[x for x in commands['steps']if x['stage']=='one matched sync screen'];need(len(rows)==1,'one actual paired command')
 args=rows[0]['argv'];need(args[args.index('--output')+1]=='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl-production-screen-PF037R5-MAIN-001','actual PF R5 paired output')
 return True
def fixture():
 sr={'label':'source'};m=dict(root='/softwareMODEL036',output_root='/software-only/output')
 plan=dict(model_diagnostic_source_ref=sr,model_smoke_owner_ref=dict(path=str(Path(m['output_root'])/'RESULT.json'),label='owner'),model_smoke_terminal_ref={'label':'terminal'},qualification_ref={'label':'true-owner035-required-in-real-execution'})
 v=dict(schema='deltalog.actual-owned-dispatch-smoke/v025',source=sr,component_owner=plan['qualification_ref'],primary=None,secondary=[],status='actual-DL-smoke-only',all_created_containers_release_verified=True,owned_containers=[dict(cid=str(i),exact_owned_release_verified=True)for i in range(3)],actual_loaded_workers={'label':'loaded'},independent_smoke_consumer={'label':'consumer'},client={'label':'client'})
 rec=dict(command='/usr/bin/prlimit',args=['--as=536870912:unlimited','--','/usr/bin/python3','-B',m['root']+'/host_ticket.py','--execute','--source-ref',json.dumps(sr)],exitCode=0,state='completed',timedOut=False,cancelled=False)
 dispatch=dict(dispatch_trajectory_pass=True,rows=[dict(rank=i,all48=True,requests={x:dict(prefill=True,decode=9)for x in('a','b')})for i in range(4)])
 consumer=dict(schema='deltalog.model-selected-tensor-independent-consumption/v026',source=sr,actual_loaded_workers=v['actual_loaded_workers'],actual_client=v['client'],selected_modified_decode_pass=True,smoke_dispatch_and_response_pass=True,selected_tensor_ref={'label':'tensor'},dispatch=dispatch,responses=[dict(prompt_tokens=16,output_tokens=10),dict(prompt_tokens=129,output_tokens=10)])
 objects=dict(owner=v,terminal=dict(result=dict(record=rec)),loaded=dict(schema='deltalog.actual-all4-loaded/v004',source=sr,rows=[dict(rank=i)for i in range(4)]),consumer=consumer,tensor=dict(source=sr,primary=None,modified_decode_arithmetic_pass=True,full48_tensor_qualified=False,model_numeric_qualified=False))
 contract=json.loads((P/'receivers/DOMAIN_PINS.json').read_bytes())['selected_model_validation_contract'];objects['consumer']['validation_contract']=contract;objects['tensor']['validation_contract']=contract
 C=types.SimpleNamespace(obj=lambda r:objects[r['label']],checked=lambda r:None,need=need)
 return C,plan,m,objects
class ReceiverControls(unittest.TestCase):
 def run_receipt(self,C,plan,m):
  with patch.object(R,'admit_bridge',return_value=(m,{'software-only':True})):return R.consume(C,plan)
 def test_software_receipt_never_claims_model_or_perf(self):
  C,p,m,o=fixture();v=self.run_receipt(C,p,m);self.assertEqual(v['schema'],'deltalog.actualMODEL036R5-model-diagnostic-smoke/v037-repair5');self.assertFalse(v['performance_ready']);self.assertFalse(v['model_numeric_qualified'])
 def test_failed_or_unreleased_model_owner_rejected(self):
  for key,value in(('primary','failed'),('all_created_containers_release_verified',False)):
   C,p,m,o=fixture();o['owner'][key]=value
   with self.assertRaises(ValueError):self.run_receipt(C,p,m)
 def test_terminal_wrong_source_timeout_or_cancel_rejected(self):
  for key,value in(('timedOut',True),('cancelled',True),('exitCode',1)):
   C,p,m,o=fixture();o['terminal']['result']['record'][key]=value
   with self.assertRaises(ValueError):self.run_receipt(C,p,m)
  C,p,m,o=fixture();o['terminal']['result']['record']['args'][-1]='{}'
  with self.assertRaises(ValueError):self.run_receipt(C,p,m)
 def test_missing_layer_or_decode_request_rejected(self):
  for key,value in(('all48',False),('requests',{'a':dict(prefill=True,decode=8)})):
   C,p,m,o=fixture();o['consumer']['dispatch']['rows'][0][key]=value
   with self.assertRaises(ValueError):self.run_receipt(C,p,m)
 def test_selected_numeric_fail_or_wrong_response_rejected(self):
  C,p,m,o=fixture();o['tensor']['modified_decode_arithmetic_pass']=False
  with self.assertRaises(ValueError):self.run_receipt(C,p,m)
  C,p,m,o=fixture();o['consumer']['responses'][0]['output_tokens']=2
  with self.assertRaises(ValueError):self.run_receipt(C,p,m)
  for key in('consumer','tensor'):
   C,p,m,o=fixture();o[key].pop('validation_contract')
   with self.assertRaisesRegex(ValueError,'contract in BOTH'):self.run_receipt(C,p,m)
 def test_old032_or_future_template_rejected_before_module_import(self):
  pins=json.loads((P/'receivers/DOMAIN_PINS.json').read_bytes());template={'files':pins['model036_files'],'root':'/actual'}
  for mode,prepared in(('actual031-domain-diagnostic-only',False),('actual035-directRNE-domain-diagnostic-only',True)):
   m=dict(schema='deltalog.service023-owned-overlay/v025',prepared_only=prepared,admission_mode=mode)
   C=types.SimpleNamespace(obj=lambda r:m if r.get('label')=='source'else template,checked=lambda r:None,need=need)
   with self.assertRaisesRegex(ValueError,'only actual'):R.admit_bridge(C,dict(model_diagnostic_source_ref={'label':'source'}))
 def test_bind_requires_real_model_receipt_before_manifest_write(self):
  text=(P/'bind_source.py').read_text();tree=ast.parse(text)
  calls=[(n.lineno,ast.unparse(n.func))for n in ast.walk(tree)if isinstance(n,ast.Call)]
  receipt=min(n for n,f in calls if f=='api.consume');write=min(n for n,f in calls if f=='out.open');self.assertLess(receipt,write)
  self.assertIn("m['model_smoke_plan']",text);self.assertIn('actual035160 plus realMODEL036',text)
 def test_final_pins_match_new_contract_and_no_failed_recovery_alias(self):
  pins=json.loads((P/'receivers/DOMAIN_PINS.json').read_bytes());self.assertEqual(pins['model036_template']['sha256'],'82cc86940c1cd77a533415d809649f73847b552926bd1b2504730172c8377470');self.assertEqual(pins['reviewed_domain_template_ref']['sha256'],'e9243ee9acc0f066421dc7e3b11285533a8df3c8478830afe40be6e25f18dd49')
  self.assertEqual(pins['reviewed_domain_files']['domain_consumer.py']['sha256'],'6896942c7ffa586204738b336bd7997026a3c58ea1adea126da847977ece150c');self.assertNotIn('recovery', (P/'screen_admission.py').read_text().lower())
  config=json.loads((P/'CONFIGURATION_TEMPLATE.json').read_bytes());commands=json.loads((P/'COMMANDS.json').read_bytes());substrate=(P/'owned_substrate.py').read_text();validate=(P/'host_validate.py').read_text();pair=(P/'host_pair.py').read_text()
  self.assertTrue(source_identity(config,commands,substrate,validate,pair))
  for old in('PF037R2','PF037R4'):
   bad=copy.deepcopy(config);bad['validation_output_root']=bad['validation_output_root'].replace('PF037R5',old)
   with self.assertRaisesRegex(ValueError,'validation output'):source_identity(bad,commands,substrate,validate,pair)
   with self.assertRaisesRegex(ValueError,'owner assignment'):source_identity(config,commands,substrate.replace("S.OWNER='dl-production-screen-PF037R5'","S.OWNER='dl-production-screen-"+old+"'"),validate,pair)
