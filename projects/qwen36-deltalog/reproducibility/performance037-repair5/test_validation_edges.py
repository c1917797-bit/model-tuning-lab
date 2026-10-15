"""CPU-only reference/atomic interleaving controls; no actual NPU receipts."""
import copy,importlib.util,json,os,sys,tempfile,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
import finite_numeric as F
import snapshot_publication as PUB
P=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class NumericControls(unittest.TestCase):
 def fixture(self,batch=1):
  import torch
  slots=batch+2;st=dict(base=torch.zeros(slots,12,128,128),k_log=torch.zeros(slots,4,7,128,dtype=torch.bfloat16),u_log=torch.zeros(slots,12,7,128),lambda_log=torch.zeros(slots,12,16),decay=torch.zeros(slots,12,16),length=torch.zeros(slots,12,16,dtype=torch.int32))
  i=dict(query=torch.ones(batch,4,128,dtype=torch.bfloat16),key=torch.zeros(batch,4,128,dtype=torch.bfloat16),value=torch.zeros(batch,12,128,dtype=torch.bfloat16),g=torch.zeros(batch,12),beta=torch.zeros(batch,12,dtype=torch.bfloat16),ssm_state_indices=torch.arange(batch,dtype=torch.int32),actual_seq_lengths=torch.tensor([0]+[1]*batch,dtype=torch.int32),scale=128**-.5)
  cap=dict(before=st,inputs=i,output=torch.zeros(batch,12,128,dtype=torch.bfloat16));raw=dict(ids=torch.arange(batch+1,dtype=torch.int32),captures=dict(decode=[cap]))
  return torch,raw,cap,i,st
 def test_actual_geometry_seq_scale_slot_negatives(self):
  torch,raw,cap,i,st=self.fixture(16);self.assertEqual(len(F.capture(torch,raw,16)[2]),16)
  for field,value in(('actual_seq_lengths',torch.arange(17,dtype=torch.int32)),('scale',1.),('ssm_state_indices',torch.zeros(16,dtype=torch.int32)),('query',torch.ones(16,3,128,dtype=torch.bfloat16))):
   wrong=copy.deepcopy(raw);wrong['captures']['decode'][0]['inputs'][field]=value
   with self.assertRaises(ValueError):F.capture(torch,wrong,16)
 def test_direct_RNE_and_independent_state_nan_dead_mask(self):
  torch,raw,cap,i,st=self.fixture();R=load('_oracle_test',P/'dependencies/direct_round013.py');Q=load('_scalar_test',P/'dependencies/numeric_oracle.py')
  # Standalone helper arithmetic, not a fake NPU producer output.
  values=F.reference(torch,Q,R,st,st,i,cap['output'],[0]);self.assertTrue(values[0]['request_pass'])
  dead=copy.deepcopy(st);dead['k_log'][0].fill_(float('nan'));self.assertTrue(F.reference(torch,Q,R,dead,dead,i,cap['output'],[0])[0]['request_pass'])
  bad=copy.deepcopy(st);bad['base'][0,0,0,0]=float('nan')
  with self.assertRaises(ValueError):F.reference(torch,Q,R,bad,st,i,cap['output'],[0])
  truth=torch.full((12,128),1+2**-8+2**-30,dtype=torch.float64);out=R.round_bf16(torch,truth);error,d=R.peer_error(torch,out,truth);self.assertEqual(error,0);self.assertGreater(d['uncast_peak'],.00303)
 def test_flush_only_old_receipt_rejected(self):
  import screen_admission as A
  source={'software-only':'source'};m={'library_ref':{}};o=dict(schema='deltalog.production-validation-owned/v033',source=source,primary=None,secondary=[],stopped_retained=True,cleanup={'label':'cleanup'},numeric={'label':'numeric'})
  table={'owner':o,'cleanup':dict(errors=[],stopped=True,retained=True),'numeric':dict(schema='deltalog.production-flush-validation/v033')}
  with patch.object(A,'source',return_value=m),patch.object(A.A,'obj',side_effect=lambda r:table[r['label']]):
   with self.assertRaises(RuntimeError):A.validate_production({'label':'owner'},{},source)
class PublicationControls(unittest.TestCase):
 def setup_donor(self,root):
  m=PUB.donor();real=m.os;dflags=getattr(real,'O_DIRECTORY',0x10000)
  # Windows lacks directory fsync. Only test directory-fsync ABI/order with an
  # actual temporary file proxy there; Linux same-image uses the real directory.
  if os.name=='nt':
   def op(path,flags):
    if flags&dflags:return os.open(str(root/'dir-fsync-proxy'),os.O_RDWR|os.O_CREAT)
    return os.open(path,flags)
   m.os=types.SimpleNamespace(fdopen=real.fdopen,fsync=real.fsync,link=real.link,open=op,close=real.close,O_RDONLY=real.O_RDONLY,O_DIRECTORY=dflags)
  return m
 def test_paused_stage_not_final_until_complete_then_parse_once(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);dest=root/'worker-1-snapshot-1.json';m=self.setup_donor(root);ready=threading.Event();release=threading.Event();errors=[];real=m.os.fsync;calls=0
   def fsync(fd):
    nonlocal calls
    calls+=1
    if calls==1:ready.set();self.assertTrue(release.wait(5))
    return real(fd)
   m.os=types.SimpleNamespace(**{n:getattr(m.os,n)for n in('fdopen','link','open','close','O_RDONLY','O_DIRECTORY')},fsync=fsync)
   def run():
    try:
     with patch.object(PUB,'donor',return_value=m):PUB.publish(dest,{'CPU-software-only':'complete'})
    except BaseException as e:errors.append(repr(e))
   thread=threading.Thread(target=run);thread.start();self.assertTrue(ready.wait(5));self.assertFalse(dest.exists());self.assertEqual(list(root.glob('worker-*-snapshot-*.json')),[]);release.set();thread.join(5)
   self.assertFalse(errors);self.assertFalse(thread.is_alive());self.assertEqual(json.loads(dest.read_bytes()),{'CPU-software-only':'complete'});self.assertEqual(len(list(root.glob('.worker*.pending-*'))),1);self.assertEqual(calls,2)
 def test_no_overwrite_and_stage_preserved_on_failure(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);dest=root/'worker-1-snapshot-1.json';m=self.setup_donor(root)
   with patch.object(PUB,'donor',return_value=m):PUB.publish(dest,{'first':True})
   original=dest.read_bytes()
   with patch.object(PUB,'donor',return_value=m):
    with self.assertRaises(ValueError):PUB.publish(dest,{'second':True})
   self.assertEqual(dest.read_bytes(),original)
   target=root/'worker-1-snapshot-2.json'
   with patch.object(m.os,'fsync',side_effect=OSError('software fsync fault')),patch.object(PUB,'donor',return_value=m):
    with self.assertRaises(OSError):PUB.publish(target,{'failure':True})
   self.assertFalse(target.exists());self.assertTrue(list(root.glob('.worker-1-snapshot-2.json.pending-*')))
 def test_owner_no_partialJSON_retry_and_sync_metadata_truth(self):
  owner=(P/'worker_snapshot_owner.py').read_text();receipt=(P/'worker_receipt.py').read_text();self.assertNotIn('JSONDecodeError',owner);self.assertIn('synchronization_performed',receipt);self.assertIn('synchronization_outside_timing=True',receipt);self.assertNotIn('synchronization=False',receipt)
  # Call the actual installed Python handler under software signal/proc mocks.
  # This catches imported publisher shadowing by the nested signal handler.
  import worker_receipt as W
  with tempfile.TemporaryDirectory()as td:
   captured=[]
   env={'QWEN36_DELTALOG_SCREEN033_RECEIPT_ROOT':td,'QWEN36_DELTALOG_SCREEN033_SOURCE_REF':'{}','QWEN36_DELTALOG_SCREEN033_QUALIFICATION_REF':'{}'}
   snapshot=lambda:dict(health=dict(synchronization_performed=True))
   with patch.dict(os.environ,env),patch.object(W.signal,'SIGUSR1',10,create=True),patch.object(W.signal,'getsignal',return_value=W.signal.SIG_DFL),patch.object(W.signal,'signal'),patch.object(W.Path,'read_text',return_value='software-only-proc'),patch.object(W,'atomic_publish',side_effect=lambda path,value:captured.append((path,value))):
    callback=W.install(snapshot);callback(10,None)
   self.assertEqual(len(captured),1);self.assertEqual(captured[0][1]['ordinal'],1);self.assertTrue(captured[0][1]['synchronization']);self.assertEqual(captured[0][0].parent,Path(td))
