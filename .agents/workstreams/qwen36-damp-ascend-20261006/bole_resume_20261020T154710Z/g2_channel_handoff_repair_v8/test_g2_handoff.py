"""Exact metadata-copy/readability controls; synthetic fixtures are not live proof."""
import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g2_channel as CH
import g2_contract as G
import g2_finalize as F
import g2_handoff as H


class HandoffTests(unittest.TestCase):
 def fixture(self,mutate=None):
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);base=Path(td.name);out=base/'OUT';receipt=out/'dense/receipts';stream=receipt/'STREAM';stream.mkdir(parents=True);source=base/'SOURCE';source.mkdir();consumer=C.write(source/'g2_consumer.py',dict(synthetic_fixture=True))
  m=dict(output_root=str(out),root=str(source),model_receipt_root=str(receipt),stream_channel_root=str(stream),stream_channel_contract_path=str(stream/'CHANNEL.json'),stream_consumer_source=consumer,default_enabled=False,files={'g2_handoff.py':C.ref(P/'g2_handoff.py'),'g2_stream_owner.py':C.ref(P/'g2_stream_owner.py'),'g2_channel.py':C.ref(P/'g2_channel.py')})
  sr=C.write(source/'SOURCE_BOUND.json',m);identity=dict(pid=123,start_ticks=7,cgroup='synthetic');originals={};inspections={};owners={}
  for role in('consumer','model'):
   cpu=role=='consumer';cid=('a'if cpu else'b')*64;image='sha256:'+'6'*64;leaf=out/('cpu-consumer'if cpu else'dense');leaf.mkdir(exist_ok=True)
   mounts={str(source):[str(source),False]}
   if cpu:mounts.update({str(receipt):[str(receipt),False],str(stream):[str(stream),True],'/adakv-results':[str(stream),True]})
   else:mounts[str(leaf)]=[str(leaf),True]
   owner=dict(cid=cid,image=image,name='synthetic-'+role,source=sr,mounts=mounts)
   devices=[]if cpu else[dict(PathOnHost='/dev/davinci%d'%p,PathInContainer='/dev/davinci%d'%i)for i,p in enumerate((4,5,6,7))]+[dict(PathOnHost='/dev/'+n,PathInContainer='/dev/'+n)for n in('davinci_manager','devmm_svm','hisi_hdc')]
   x=dict(Id=cid,Image=image,Name='/'+owner['name'],State=dict(Running=True,Pid=100 if cpu else 101),Config=dict(Image=image,Labels={'model-tuning-lab.source-manifest-sha256':sr['sha256']}),HostConfig=dict(Memory=(8 if cpu else 32)*2**30,MemorySwap=(8 if cpu else 32)*2**30,NanoCpus=(1 if cpu else 3)*10**9,CpusetCpus='145'if cpu else'0,1,2',ReadonlyRootfs=True,NetworkMode='none',Devices=devices),Mounts=[dict(Destination=k,Source=v[0],RW=v[1])for k,v in mounts.items()])
   if mutate:mutate(role,owner,x)
   owners[role]=owner;inspections[role]=x
   originals[role+'_owner_ref']=C.write(leaf/'OWNED.json',owner)
   inspector=C.write(leaf/'inspect-1.json',dict(exit_code=0,stdout=json.dumps([x])))
   originals[role+'_inspect']={k:inspector[k]for k in('path','sha256')}
  workers=[dict(pid=i+200,start_ticks=3,cgroup='synthetic')for i in range(4)]
  channel=dict(schema='bole.owned-independent-stream-channel/v2',source=sr,scope=G.SCOPE,consumer_source=consumer,consumer_Devices=[],consumer_container_independent=True,host_ownership_audited=True,actual_worker_identities=workers,actual_consumer_identity=identity,root=str(stream),nonce='f'*64,consumer_lifetime=dict(guest=identity,NSpid=[123],host=dict(start_ticks=7,cgroup='/docker/'+owners['consumer']['cid']),owned_cid=owners['consumer']['cid']),consumer_cpu_view=dict(effective_cpus=[145],effective_capacity=1),limits=dict(raw_cap=G.RAW_CAP,metadata_cap=G.METADATA_CAP,frame_logical_cap=G.FRAME_LOGICAL_CAP,frame_wire_cap=G.FRAME_WIRE_CAP,checkpoint_cap=G.CHECKPOINT_CAP),**originals)
  return out,sr,m,originals,channel
 def publish(self,data):
  out,sr,m,originals,channel=data;copied,ledger=H.publish(C,sr,originals);channel=dict(channel,**copied,metadata_handoff=ledger);cr=C.write(Path(m['stream_channel_contract_path']),channel);return channel,cr,ledger
 def test_original_contract_and_full_owner_inspection_reader_work_with_originals_absent(self):
  data=self.fixture();channel,cr,ledger=self.publish(data);out,sr,m,originals,_=data
  for r in originals.values():Path(r['path']).rename(Path(r['path']+'.hidden'))
  self.assertTrue(all(not Path(r['path']).exists()for r in originals.values()))
  self.assertEqual(CH.contract(C,sr,cr),channel);self.assertEqual(F.owned_channel(m,sr,cr),channel)
  self.assertFalse(H.verify(C,sr,channel)['live_identity_inferred_from_stopped_capture'])
 def test_original_inspect_Ref2_is_preserved_but_copies_are_actual_full_Ref3(self):
  data=self.fixture();channel,cr,ledger=self.publish(data);v=C.obj(ledger)
  for role in('consumer_inspect','model_inspect'):
   row=v['roles'][role];self.assertEqual(set(row['original_declared_ref']),{'path','sha256'});self.assertEqual(set(channel[role]),{'path','bytes','sha256'});self.assertGreater(channel[role]['bytes'],0);self.assertEqual(row['original_actual_ref']['sha256'],channel[role]['sha256'])
 def test_missing_role_wrong_hash_and_unknown_original_path_never_publish(self):
  for kind in('missing','hash','path'):
   data=self.fixture();out,sr,m,originals,_=data
   if kind=='missing':originals.pop('model_inspect')
   elif kind=='hash':originals['model_inspect']=dict(originals['model_inspect'],sha256='0'*64)
   else:
    unknown=C.write(out/'unknown.json',dict(synthetic=True));originals['model_inspect']=unknown
   with self.subTest(kind=kind),self.assertRaises(ValueError):H.publish(C,sr,originals)
   self.assertFalse((Path(m['stream_channel_root'])/H.LEDGER).exists())
 def test_changed_complete_copy_rejected_by_original_checked(self):
  data=self.fixture();channel,cr,ledger=self.publish(data);Path(channel['model_owner_ref']['path']).write_text('changed')
  with self.assertRaises(ValueError):CH.contract(C,data[1],cr)
 def test_ledger_original_hash_or_role_mapping_cannot_redirect_unknown_Ref(self):
  for key in('original_actual_ref','copy_ref'):
   data=self.fixture();channel,cr,ledger=self.publish(data);v=C.obj(ledger);v['roles']['model_inspect'][key]=dict(v['roles']['model_inspect'][key],sha256='0'*64)
   path=Path(ledger['path']);path.unlink();new=C.write(path,v);channel['metadata_handoff']=new
   with self.subTest(key=key),self.assertRaises(ValueError):H.verify(C,data[1],channel)
 def test_single_terminal_writer_delegates_all_original_checks_and_preserves_full_guard(self):
  data=self.fixture();out,sr,m,originals,channel=data;w=H.ChannelWriter(C,sr)
  self.assertIs(w.checked,C.checked);self.assertIs(w.obj,C.obj);rename=CH.os.rename
  def ready(old,new):
   self.assertFalse(Path(new).exists())
   for n in[*H.NAMES.values(),H.LEDGER]:C.checked(C.ref(Path(m['stream_channel_root'])/n))
   return rename(old,new)
  with patch.object(C,'write',side_effect=AssertionError('non-atomic terminal C.write forbidden')),patch.object(CH.os,'rename',ready):cr=w.write(m['stream_channel_contract_path'],channel)
  self.assertEqual(w.complete(cr),C.obj(cr)['metadata_handoff']);self.assertFalse(Path(m['stream_channel_contract_path']+'.pending').exists())
  with self.assertRaises(ValueError):w.write(m['stream_channel_contract_path'],channel)
 def test_writer_rejects_foreign_publication_before_any_copy(self):
  data=self.fixture();out,sr,m,originals,channel=data;w=H.ChannelWriter(C,sr)
  with self.assertRaises(ValueError):w.write(out/'foreign.json',channel)
  self.assertFalse(list(Path(m['stream_channel_root']).glob('CHANNEL-METADATA-*')))
 def test_all_full_copy_bytes_remain_in_original_per_rank_metadata_charge(self):
  data=self.fixture();channel,cr,ledger=self.publish(data);sender=CH.Sender(C,data[1],cr,0,channel['actual_worker_identities'][0]);v=C.obj(ledger)
  self.assertGreaterEqual(sender.metadata_bytes(),v['total_copy_bytes']+ledger['bytes']);self.assertEqual(G.METADATA_CAP,64*2**20);self.assertEqual(G.RAW_CAP,2**30)
 def test_original_full_owner_inspection_negative_assertions_are_not_weakened(self):
  for kind in('source','memory','devices','mounts'):
   def mutate(role,owner,x):
    if role!='consumer':return
    if kind=='source':owner['source']={'wrong':'source'}
    elif kind=='memory':x['HostConfig']['Memory']+=1
    elif kind=='devices':x['HostConfig']['Devices']=[dict(PathOnHost='/dev/davinci4',PathInContainer='/dev/davinci0')]
    else:x['Mounts'][0]['RW']=True
   data=self.fixture(mutate);channel,cr,ledger=self.publish(data)
   with self.subTest(kind=kind),self.assertRaises(ValueError):F.owned_channel(data[2],data[1],cr)
 def test_cold_default_OFF_help_and_no_new_ML_import(self):
  for args in([],['--help']):
   q=subprocess.run([sys.executable,'-I','-B',str(P/'g2_handoff_cold.py'),*args],capture_output=True,text=True,timeout=10);self.assertEqual(q.returncode,0,q.stderr)
   if not args:self.assertEqual(json.loads(q.stdout),dict(enabled=False,NPU=False))
  self.assertFalse(any(n=='torch'or n.startswith(('torch_npu','acl'))for n in sys.modules))


if __name__=='__main__':unittest.main()
