"""Synthetic file/lifecycle controls, never evidence of model execution."""
import ast
import copy
import importlib.util
import json
import pickle
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g2_contract as G2
import g2_channel as CH
import g2_reports as R
import g2_host_adapter as HA


class StreamTests(unittest.TestCase):
 def fixture(self):
  directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup);root=Path(directory.name)
  receipt=root/'receipts';receipt.mkdir();stream=receipt/'STREAM';stream.mkdir()
  sourcefile=root/'reader.py';sourcefile.write_text('exact source\n');consumer=C.ref(sourcefile)
  own=C.write(root/'owner.json',{'owner':'fixture'})
  workers=[dict(pid=i+10,start_ticks=5,cgroup='fixture')for i in range(4)]
  m=dict(stream_consumer_source=consumer,stream_channel_root=str(stream),model_receipt_root=str(receipt))
  sr=C.write(root/'source.json',m)
  cr=C.write(stream/'CHANNEL.json',dict(schema='bole.owned-independent-stream-channel/v2',source=sr,
    scope=G2.SCOPE,consumer_source=consumer,consumer_Devices=[],consumer_container_independent=True,
    host_ownership_audited=True,actual_worker_identities=workers,root=str(stream),nonce='f'*64,
    consumer_owner_ref=own,model_owner_ref=own,limits=dict(raw_cap=G2.RAW_CAP,
      metadata_cap=G2.METADATA_CAP,frame_logical_cap=G2.FRAME_LOGICAL_CAP,
      frame_wire_cap=G2.FRAME_WIRE_CAP,checkpoint_cap=G2.CHECKPOINT_CAP)))
  sender=CH.Sender(C,sr,cr,0,workers[0]);t=NS(save=lambda v,f:pickle.dump(v,f));return sender,t,stream
 def ack(self,sender,stream,mutate=None):
  manifest=C.obj(C.ref(stream/'FRAME-RANK-0-000000.json'))
  report=R.summarize(sender.source,manifest,dict(component_checks_pass=True))
  reportref=CH.write(stream/'REPORT-RANK-0-000000.json',report)
  ack=dict(schema='bole.actual-independent-frame-ACK/v2',source=sender.source,
    consumer_source=sender.value['consumer_source'],channel_ref=sender.channel_ref,
    nonce=manifest['nonce'],rank=0,sequence=0,kind='open',raw=manifest['raw'],
    logical_tensor_bytes=0,previous_ack=None,complete_frame_consumed=True,passed=True,
    model_ready=False,formal_success=False,coverage=manifest['coverage'],
    oracle_report=reportref,oracle_report_sha256=reportref['sha256'])
  if mutate:mutate(ack)
  return CH.write(stream/'ACK-RANK-0-000000.json',ack)
 def test_missing_ACK_retains_raw_without_sequence_progress(self):
  sender,t,root=self.fixture()
  with patch.object(G2,'ACK_TIMEOUT_SECONDS',0),self.assertRaisesRegex(ValueError,'timeout'):
   sender.send(t,dict(payload={'all':'raw'},logical_tensor_bytes=0),kind='open',coverage={'g':1})
  self.assertTrue(sender.active.is_file());self.assertEqual(sender.sequence,0);self.assertEqual(sender.events,[])
 def test_failed_ACK_retains_exact_complete_raw(self):
  sender,t,root=self.fixture()
  with patch.object(CH.time,'sleep',lambda _:self.ack(sender,root,lambda a:a.update(passed=False))),self.assertRaises(ValueError):
   sender.send(t,dict(payload={'all':'raw'},logical_tensor_bytes=0),kind='open',coverage={'g':1})
  self.assertEqual(pickle.loads(sender.active.read_bytes())['payload'],{'all':'raw'})
  self.assertEqual(sender.sequence,0);self.assertFalse(list(root.glob('RELEASE-*')))
 def test_exact_durable_successful_ACK_releases_and_advances_once(self):
  sender,t,root=self.fixture()
  with patch.object(CH.time,'sleep',lambda _:self.ack(sender,root)):
   event=sender.send(t,dict(payload={'all':'raw'},logical_tensor_bytes=0),kind='open',coverage={'g':1})
  self.assertIsNone(sender.active);self.assertEqual(sender.sequence,1)
  self.assertEqual(sender.previous_ack,event['ack']);self.assertFalse(list(root.glob('*.pt')))
  self.assertTrue(C.obj(event['release'])['released_after_successful_ACK'])
 def test_wrong_raw_source_coverage_or_oracle_hash_never_releases(self):
  for key in('source','raw','coverage','oracle_report_sha256'):
   with self.subTest(key=key):
    sender,t,root=self.fixture()
    def mutate(a):a[key]={'wrong':1}if key!='oracle_report_sha256'else'0'*64
    with patch.object(CH.time,'sleep',lambda _:self.ack(sender,root,mutate)),self.assertRaises(ValueError):
     sender.send(t,dict(payload={},logical_tensor_bytes=0),kind='open',coverage={'g':1})
    self.assertTrue(sender.active.is_file());self.assertEqual(sender.sequence,0)
 def test_changed_durable_oracle_report_rejects_before_release(self):
  sender,t,root=self.fixture()
  def callback(_):
   self.ack(sender,root);(root/'REPORT-RANK-0-000000.json').write_text('{}')
  with patch.object(CH.time,'sleep',callback),self.assertRaises(ValueError):
   sender.send(t,dict(payload={},logical_tensor_bytes=0),kind='open',coverage={})
  self.assertTrue(sender.active.is_file())
 def test_failure_capture_is_never_acknowledged_released_or_retried(self):
  sender,t,root=self.fixture();r=sender.retain_failure(t,dict(payload={'fault':7},logical_tensor_bytes=0),{'failed':1})
  self.assertEqual(sender.retain_failure(t,{},{}),r);self.assertEqual(sender.sequence,0)
  self.assertEqual(C.obj(C.ref(root/'FRAME-RANK-0-000000.json'))['kind'],'failure')
  self.assertFalse(list(root.glob('ACK-*')));self.assertEqual(pickle.loads(C.checked(r).read_bytes())['payload'],{'fault':7})
 def test_oversized_logical_frame_is_rejected_before_serialization(self):
  sender,t,root=self.fixture()
  with self.assertRaisesRegex(ValueError,'bounded'):
   sender.send(t,dict(logical_tensor_bytes=G2.FRAME_LOGICAL_CAP+1),kind='open',coverage={})
  self.assertFalse(list(root.glob('*.pt')))
 def test_step_ACK_requires_all_original_oracles_and_whole_arenas(self):
  sender,t,root=self.fixture()
  with patch.object(CH.time,'sleep',lambda _:self.ack(sender,root)):
   sender.send(t,dict(payload={},logical_tensor_bytes=0),kind='open',coverage={})
  manifest=C.obj(sender.events[0]['manifest']);ack=C.obj(sender.events[0]['ack'])
  manifest['kind']=ack['kind']='step';ack['gates']={'layers':64}
  with self.assertRaisesRegex(ValueError,'every actual target'):
   CH.validate_ack(ack,manifest,consumer_source=sender.value['consumer_source'],channel_ref=sender.channel_ref,previous_ack=None)
 def test_model3_and_consumer1_leave_original_two_CPU_reserve(self):
  host=dict(effective_cpus=[166],effective_capacity=1)
  daemon=dict(effective_cpus=[0,1,2,3,144,145,166])
  baseline=dict(host_cpu=166,guest_cpus=[0,1,2,3],reserve_cpus=[144,145],guest_cpu_budget=4,reserve_cpu_budget=2)
  got=HA.cpu_admission(lambda h,d:baseline,host,daemon)
  self.assertEqual(got['guest_cpus'],[0,1,2]);self.assertEqual(got['reserve_cpus'],[3,144])
  self.assertEqual(got['stream_consumer_cpus'],[145]);self.assertEqual(sum(HA.CPU_PROFILE[k]for k in('host_budget','model_budget','consumer_budget','reserve_budget')),7)
 def test_missing_reserved_or_consumer_CPU_fails_closed(self):
  for missing in(0,3,144,145,166):
   with self.subTest(missing=missing),self.assertRaises(ValueError):
    HA.cpu_admission(lambda h,d:{},dict(effective_cpus=[166],effective_capacity=1),dict(effective_cpus=[p for p in(0,1,2,3,144,145,166)if p!=missing]))
 def test_131_plus1024_proves_initial_capacity_not_physical_growth_or_task5199(self):
  result=G2.capacity(1153,12,budget=1024)
  self.assertEqual(result['initial_kernel_capacity'],1536);self.assertEqual(result['active_kernel_pages'],10)
  self.assertFalse(result['physical_allocation_growth_proven'])
  with self.assertRaises(ValueError):G2.capacity(5198,12,budget=5199)
 def test_smoke_output4_requires_multiple_steps_and_exact_remaining_budget(self):
  self.assertEqual(G2.SCOPE['max_output_tokens'],4);self.assertEqual(G2.SCOPE['max_steps_per_request'],3)
  source=(P/'live_owner.py').read_text();self.assertIn('2<=self.steps<=self.max_steps',source)
  self.assertIn('final_ack_by_retirement_pending=self.pending is not None',source)
  self.assertNotIn('self.pending=None',source[source.index(' def retire('):])
 def test_report_preserves_bounds_coverage_and_full_result_hash_with_bounded_metadata(self):
  manifest=dict(raw={'sha256':'f'*64},coverage={'ordinal':2},kind='step')
  full=dict(rows=[dict(layer=i,FP32_output=dict(peak_abs=.0001,relative_l2=.00001,passed=True))for i in range(64)])
  report=R.summarize({'source':1},manifest,full)
  self.assertTrue(report['passed']);self.assertEqual(report['coverage'],manifest['coverage'])
  self.assertIn('2e-5+2e-4',report['bound_sources']['GDN']);self.assertLess(len(json.dumps(report)),G2.REPORT_CAP)
 def test_numerical_conv_and_native_MTP_functions_stay_AST_exact(self):
  parent=P.parent/'g1_multi_request/consumer_proposal/consume_service.py'
  if not parent.exists():
   # Frozen deployed manifests carry exact parent reader Ref; no broad lookup.
   m=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'));parent=C.checked(C.obj(m['g2_predecessor']['source'])['files']['consume_service.py'])
  def funcs(p):return{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
  a,b=funcs(parent),funcs(P/'g2_numeric.py')
  for name in('conv_math','mtp_join','tp_logits','tp_owner_agreement'):self.assertEqual(a[name],b[name],name)
 def test_all_new_CLI_are_cold_default_OFF(self):
  for name in('g2_consumer.py','g2_finalize.py','host_service.py','service_client.py','server090.py'):
   for mode in([],['--help']):
    q=subprocess.run([sys.executable,'-I','-B',str(P/name),*mode],capture_output=True,text=True,timeout=10)
    self.assertEqual(q.returncode,0,name+q.stderr)
    if not mode:self.assertIs(json.loads(q.stdout)['enabled'],False)


if __name__=='__main__':unittest.main()
