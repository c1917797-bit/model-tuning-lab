"""Real cold CLIs/HTTP/serialized identity plumbing, not backend qualification."""
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
import sourceio as C
import smoke_client as HTTP
import consume_model as K
import contract090 as CONTRACT
P=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
 def test_complete_defaultOFF_entrypoints_without_backend(self):
  env=dict(os.environ)
  for k in list(env):
   if k.startswith('BOLE_'):env.pop(k)
  for name in('entry.py','bind_model.py','host090.py','server090.py','smoke_client.py','consume_model.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/name)],env=env,capture_output=True,text=True,timeout=20)
   self.assertEqual(r.returncode,0,(name,r.stderr));self.assertFalse(json.loads(r.stdout)['enabled'])

 def test_actual_complete_command_builder_and_output_contract(self):
  argv=CONTRACT.server_command()
  self.assertEqual(argv[1:3],['-m','vllm.entrypoints.openai.api_server'])
  self.assertNotIn('--async-scheduling',argv)
  for flag in('--enforce-eager','--no-async-scheduling','--no-enable-prefix-caching'):self.assertIn(flag,argv)
  for flag,value in(('--max-model-len','4096'),('--max-num-batched-tokens','4096'),('--max-num-seqs','1'),('--mamba-cache-mode','none')):self.assertEqual(argv[argv.index(flag)+1],value)
  self.assertEqual(json.loads(argv[argv.index('--speculative-config')+1]),dict(method='mtp',num_speculative_tokens=8))
  self.assertEqual(str(CONTRACT.output_argument(CONTRACT.OUTPUT_POSIX)).replace('\\','/'),CONTRACT.OUTPUT_POSIX)
  for bad in(CONTRACT.OUTPUT_POSIX.replace('/','\\'),'relative','/opt/other'):
   with self.assertRaises(ValueError):CONTRACT.output_argument(bad)

 def test_real_HTTP_client_to_first_boundary_and_two_responses(self):
  class Tokenizer:
   vocab_size=1000
   def encode(self,text,add_special_tokens):return list(range(300))
  calls=[]
  class Response:
   status=200
   def __init__(self,b):self.body=b
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,limit):return self.body
  def boundary(request,timeout):
   body=json.loads(request.data);calls.append(body)
   self.assertEqual(body['prompt'],list(range(131)))
   header=dict((k.lower(),v)for k,v in request.header_items())['x-request-id']
   return Response(json.dumps(dict(id='cmpl-'+header,choices=[dict(text='observed')],usage=dict(prompt_tokens=131,completion_tokens=body['max_tokens']))).encode())
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);sr=C.write(root/'SOURCE.json',dict(prepared_only=False))
   HTTP.run(sr,root,Tokenizer(),boundary)
   value=C.obj(C.ref(root/'HTTP_RESULT.json'));self.assertEqual(len(value['rows']),2)
   self.assertEqual([x['max_tokens']for x in calls],[10,1]);self.assertTrue(all(x['ignore_eos']for x in calls))

 def test_actual_serialized_assignment_all4_retirement_and_wrong_suffix_reject(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);sr=C.write(root/'SOURCE.json',dict(prepared_only=False));server='cmpl-bole131-tree';assigned=server+'-0-abcd1234'
   wire=C.write(root/'wire.json',dict(id=server));hr=C.write(root/'http.json',dict(source=sr,rows=[dict(label='tree',header='bole131-tree',response=wire),dict(label='retirement-barrier')]))
   assignment=dict(schema='vllm023.actual-assignment/v1',source_sha256=K.O.ASSIGN_SHA,before_request_id=server+'-0',before_external_req_id=None,after_request_id=assigned,after_external_req_id=server+'-0',disable_request_id_randomization=False)
   journal=[C.write(root/'assignment.json',dict(schema='bole.actual-identity-journal/v1',source=sr,role='frontend',kind='assignment',event=assignment))];snapshots=[];bindings=[]
   for rank in range(4):
    pid=rank+20;identity=dict(pid=pid,start_ticks=100,cgroup='/own/test')
    fields=['R']+['0']*18+['100'];snapshot=dict(pid=pid,source_ref=sr,allow_hf32=False,proc_stat='%d (worker) '%pid+' '.join(fields),cgroup='/own/test')
    snapshots.append(snapshot);bindings.append(dict(host=dict(physical=rank+4,pid=rank+1000),guest=snapshot))
    for seq,finished in((1,False),(2,True)):
     event=dict(schema='vllm023.actual-worker-update/v1',rank=rank,identity=identity,source_sha256=K.O.NPU_SHA,seq=seq,new_req_ids=[]if finished else[assigned],cached_req_ids=[],num_scheduled_tokens={}if finished else{assigned:131},total_num_scheduled_tokens=0 if finished else 131,finished_req_ids=[assigned]if finished else[],requests_before=[assigned]if finished else[],requests_after=[]if finished else[assigned],batch_after=[]if finished else[assigned])
     journal.append(C.write(root/('%d-%d.json'%(rank,seq)),dict(schema='bole.actual-identity-journal/v1',source=sr,role='rank%d'%rank,kind='worker_update',event=event)))
   front=dict(pid=10,start_ticks=99,cgroup='/guest')
   assignment['identity']=front
   # Re-serialize actual captured assignment after binding the frontend identity.
   updated=C.write(root/'assignment-bound.json',dict(schema='bole.actual-identity-journal/v1',source=sr,role='frontend',kind='assignment',event=assignment));journal[0]=updated
   bundle=dict(http=hr,journal=journal,snapshots=snapshots,host_bindings=bindings,
    frontend_binding=dict(guest=front,host=dict(cgroup='/own/cid',start_ticks=99),owned_cid='cid',NSpid=[500,10]))
   actual,b=K.identity_join(sr,bundle);self.assertEqual(actual,assigned);self.assertEqual(set(b),{0,1,2,3})
   assignment['after_request_id']=server+'-0-deadbeef'
   changed=C.write(root/'wrong.json',dict(schema='bole.actual-identity-journal/v1',source=sr,role='frontend',kind='assignment',event=assignment));bundle['journal']=[changed,*journal[1:]]
   with self.assertRaises(ValueError):K.identity_join(sr,bundle)

 def test_owner_full_inverse_and_CPUconsumer_role(self):
  proof=json.loads((P/'OWNER_DERIVATION.json').read_bytes());self.assertTrue(proof['full_inverse_equals_original']);self.assertFalse(proof['budget_change']);self.assertFalse(proof['resource_change'])
  # Compile the actual host, not an isolated builder. The CPU-only arm literal
  # remains the donor's validated Devices[] create/inspect profile.
  compile((P/'host090.py').read_bytes(),str(P/'host090.py'),'exec')
  # Actual runtime source remains R5 byte-for-byte. First prove the entire
  # telemetry inverse to actual R4, then execute the UNCHANGED original gate.
  import telemetry_inverse131r5 as TI
  manifest=json.loads((P/'SOURCE.json').read_bytes());key='HOST_TELEMETRY_EDITS131R5.json'
  plan_ref=manifest['files'][key];plan=(P/key).read_bytes();actual=(P/'host090.py').read_bytes()
  import ref_inverse131r7 as RI
  actual=RI.restore(actual,(P/'HOST_REF_EDITS131R7.json').read_bytes(),manifest['files']['HOST_REF_EDITS131R7.json'])
  body=TI.restore(actual,plan,plan_ref).decode('utf8')
  with self.assertRaises(ValueError):TI.restore(actual+b'\n',plan,plan_ref)
  with self.assertRaises(ValueError):TI.restore(actual,plan+b' ',plan_ref)
  altered=json.loads(plan);altered['edits']=altered['edits'][1:];altered_bytes=json.dumps(altered).encode()
  with self.assertRaises(ValueError):TI.restore(actual,altered_bytes,dict(bytes=len(altered_bytes),sha256=__import__('hashlib').sha256(altered_bytes).hexdigest()))
  self.assertIn("ctl_for('cpu-consumer',cpu=True,extra=extra)",body)
  self.assertIn("'cpu-preflight'if cpu else role",body)
  original=(P/'evidence/original114_host090.py').read_text()
  oldbegin=original.index("   summary['profiles']=[];");oldend=original.index('\n except BaseException as e:primary=repr(e)',oldbegin)
  newbegin=body.index("   ctl.client,ctl.client_argv=spawn(ctl,[str(P/'smoke_client.py')")
  newend=body.index('\n except BaseException as e:primary=repr(e)',newbegin)
  inverse=body[:newbegin]+original[oldbegin:oldend]+body[newend:]
  for before,after in reversed(proof['changed_exact_literals']):
   self.assertEqual(inverse.count(after),1);inverse=inverse.replace(after,before)
  self.assertEqual(inverse,original)

 def test_actual_four_shard_vocabulary_join_and_wrong_global_rejection(self):
  import torch as t
  full=t.tensor([[1.,2.,9.,8.,3.,4.,5.,6.]],dtype=t.float32)
  rows=[dict(policy=dict(lmhead_tp=False,reduce_sample=True,vocab_size=8),
   local=full[:,rank*2:rank*2+2].clone(),global_logits=full.clone(),children=t.tensor([[2,3]]),tokens=[0,2,3],target=t.ones((3,8)))for rank in range(4)]
  self.assertTrue(K.vocabulary_join(t,rows))
  rows[1]['global_logits'][0,0]=99
  with self.assertRaises(ValueError):K.vocabulary_join(t,rows)


if __name__=='__main__':unittest.main()
