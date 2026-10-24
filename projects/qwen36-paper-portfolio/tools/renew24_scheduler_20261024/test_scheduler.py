"""Synthetic state/receipt regressions with real parent Ref reader. No device claims."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('renew_scheduler',HERE/'scheduler.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='renew24-decision-fixture-')
  self.root=Path(self.tmp.name).resolve();self.B=S.io();self.seq=0
  self.policy=dict(start_epoch=100,cutoff_epoch=1000,fresh_seconds=30,allow_disjoint=True,
   ram_reserve=8,disk_reserve={'docker':9,'output':10},scheduler_ram=1)
  self.snap=dict(at=100,unknown_operations=[],usage={},cards={str(p):'idle'for p in range(4,8)},
   portfolio_ram_cap=100,portfolio_cpu_millis=4000,mem_available=108,disk_free={'docker':109,'output':110})
 def tearDown(self):self.tmp.cleanup()
 def obj(self,value):
  self.seq+=1;return self.B.publish(self.root/('f%d.json'%self.seq),dict(value,fixture_only=True))
 def node(self,id='a',paper='BOLE',kind='single',physical=None,deps=None,state='ready',ram=20,wall=20,critical=20):
  physical=([4]if kind=='single'else([4,5,6,7]if kind in S.EXCLUSIVE else[]))if physical is None else physical
  b=dict(ram=ram,cpu_millis=1000,disk={'docker':1,'output':2})
  source=self.obj({'source':id});entry=self.obj({'entry':id});adapter=self.obj({'adapter':id})
  predecessor=self.obj({'actual_fixture_consumer':id})
  n=dict(id=id,paper=paper,kind=kind,gate='npu-numerical',deps=deps or[],state=state,physical=physical,budget=b,
   wall_seconds=wall,critical_seconds=critical,deadline_epoch=900,ready_at=100,output_root=str(self.root/(id+'-fresh')),
   edit_scope='draft/'+id,acceptance_ref=predecessor if state=='passed'else None)
  ticket=dict(id=id,source_ref=source,entry_ref=entry,adapter_ref=adapter,
   argv=['/usr/bin/python3',entry['path'],source['sha256']],output_root=n['output_root'],
   owner='fixture-'+id,image='sha256:'+'a'*64,physical=physical,protected=[0,1,2,3],
   wall_seconds=wall,cutoff_epoch=900,result_name='RESULT.json')
  review=dict(schema='main.reviewed-stage-admission/v1',reviewed_by='MAIN',gate='npu-numerical',ready_for_gate=True,
   state='ACTUAL_PREREQUISITES_CONSUMED',missing=[],ticket_id=id,joint_demand=b,stage_kind=kind,
   actual_prerequisites=[dict(artifact_ref=source,consumer_ref=adapter,acceptance_ref=predecessor)])
  review.update({k:ticket[k]for k in('source_ref','entry_ref','adapter_ref','argv','output_root','owner')})
  review['stage_policy']={k:ticket[k]for k in('image','physical','protected','wall_seconds','cutoff_epoch','result_name')}
  ticket['review_ref']=self.obj(review);n['packet_ref']=self.obj(ticket);return n
 def rewrite_review(self,n,fn):
  t=self.B.obj(n['packet_ref']);r=self.B.obj(t['review_ref']);fn(r);t['review_ref']=self.obj(r);n['packet_ref']=self.obj(t)
 def plan(self,nodes,leases=None):
  return S.plan(nodes,leases or[],self.snap,100,self.policy,self.B)
 def lease(self,n,state='running',end=140):
  n['state']=state
  return dict(id='lease-'+n['id'],node=n['id'],physical=n['physical'],budget=n['budget'],packet_ref=n['packet_ref'],kind=n['kind'],state=state,latest_release_epoch=end)
 def usage(self,l,ram=0,disk=None):
  self.snap['usage'][l['id']]=dict(ram=ram,cpu_millis=1000,disk=disk or{})
 def test_preparing_is_not_ready_and_missing_does_not_starve(self):
  a=self.node(state='preparing');b=self.node('b','MXR',physical=[6])
  p=self.plan([a,b]);self.assertEqual([x['node']for x in p['proposals']],['b']);self.assertFalse(p['dispatch_executed'])
 def test_real_parent_hash_guard_and_consumer_refs(self):
  n=self.node();t=self.B.obj(n['packet_ref']);r=self.B.obj(t['review_ref'])
  Path(r['actual_prerequisites'][0]['consumer_ref']['path']).write_bytes(b'tampered')
  self.assertEqual(self.plan([n])['proposals'],[])
 def test_actual_DAG_edge_not_generic_pass(self):
  a=self.node(state='passed');b=self.node('b',deps=['a'])
  self.assertEqual(self.plan([a,b])['proposals'],[])
  self.rewrite_review(b,lambda r:r['actual_prerequisites'].append(dict(artifact_ref=a['acceptance_ref'],consumer_ref=a['acceptance_ref'],acceptance_ref=a['acceptance_ref'])))
  self.assertEqual([x['node']for x in self.plan([a,b])['proposals']],['b'])
 def test_disjoint_pack_and_joint_RAM(self):
  nodes=[self.node(),self.node('b','MXR',physical=[6])]
  self.assertEqual(len(self.plan(nodes)['proposals']),2)
  self.snap['portfolio_ram_cap']=40
  self.assertEqual(len(self.plan(nodes)['proposals']),1)
 def test_overlap_cannot_pack(self):
  self.assertEqual(len(self.plan([self.node(),self.node('b','MXR')])['proposals']),1)
 def test_explicit_disjoint_permission(self):
  self.policy['allow_disjoint']=False
  self.assertEqual(len(self.plan([self.node(),self.node('b','MXR',physical=[6])])['proposals']),1)
 def test_unknown_holds_lease_and_reserved_resources(self):
  a=self.node();a['state']='unknown';l=self.lease(a,'unknown');self.usage(l)
  b=self.node('b','MXR');p=self.plan([a,b],[l])
  self.assertEqual(p['proposals'],[]);self.assertEqual(l['state'],'unknown')
 def test_unknown_disjoint_known_usage_does_not_free_or_global_block(self):
  a=self.node();a['state']='unknown';l=self.lease(a,'unknown');self.usage(l)
  b=self.node('b','MXR',physical=[6])
  self.assertEqual([x['node']for x in self.plan([a,b],[l])['proposals']],['b'])
 def test_missing_lease_usage_rejects(self):
  a=self.node();l=self.lease(a);b=self.node('b','MXR',physical=[6])
  self.assertEqual(self.plan([a,b],[l])['proposals'],[])
 def test_ordinary_RAM_remaining_not_double_charge_actual_usage(self):
  a=self.node(ram=40);l=self.lease(a);self.usage(l,ram=35)
  b=self.node('b','MXR',physical=[6],ram=20);self.snap['mem_available']=34
  self.assertEqual([x['node']for x in self.plan([a,b],[l])['proposals']],['b'])
  self.snap['mem_available']=33
  self.assertEqual(self.plan([a,b],[l])['proposals'],[])
 def test_both_filesystems_and_CPU_checked(self):
  a=self.node();b=self.node('b','MXR',physical=[6])
  self.snap['disk_free']['docker']=10
  self.assertEqual(len(self.plan([a,b])['proposals']),1)
  self.snap['disk_free']['docker']=109;self.snap['portfolio_cpu_millis']=1000
  self.assertEqual(len(self.plan([a,b])['proposals']),1)
 def test_exclusive_reserves_earliest_start_backfill_fits(self):
  active=self.node('active',physical=[7]);active['state']='running';l=self.lease(active,end=130);self.usage(l)
  x=self.node('tp','BOLE','tp4',wall=100,critical=1)
  short=self.node('short','MXR',physical=[6],wall=20)
  long=self.node('long','GoodEnough',physical=[5],wall=40)
  p=self.plan([active,x,short,long],[l])
  self.assertIsNone(p['exclusive_reservation'])
  self.assertEqual(p['exclusive_pending']['backfill_until'],130)
  self.assertFalse(p['exclusive_pending']['safe_start_proven'])
  self.assertEqual([x['node']for x in p['proposals']],['short'])
 def test_exclusive_now_blocks_all_overlapping_CPU_and_devices(self):
  x=self.node('tp',kind='tp4',wall=100,critical=1)
  p=self.plan([x,self.node('cpu',kind='cpu'),self.node('single',physical=[6])])
  self.assertEqual([x['node']for x in p['proposals']],['tp'])
 def test_fixed_window_stale_and_full_cleanup_budget(self):
  n=self.node(wall=801);self.assertEqual(self.plan([n])['proposals'],[])
  self.snap['at']=69;self.assertEqual(self.plan([self.node('fresh')])['proposals'],[])
 def test_failed_release_next_and_original_failure_retained(self):
  a=self.node();l=self.lease(a);ticket=self.B.obj(a['packet_ref'])
  tr=self.obj(dict(schema='main.serial-child-terminal/v1',reaped=True,exit_code=1,source_ref=ticket['source_ref'],argv=ticket['argv'],AW_terminal_claimed=False))
  Path(a['output_root']).mkdir();result_ref=self.B.publish(Path(a['output_root'])/'RESULT.json',{'fixture_only':True,'primary':'actual fixture error'})
  rr=self.obj(dict(schema='main.serial-exact-owned-release/v1',source_ref=ticket['source_ref'],owner=ticket['owner'],child_terminal_ref=tr,exact_owned_release=True,physical_idle=[4],external_stopped=False,AW_terminal_claimed=False,original_result_ref=result_ref,original_failed=True))
  out,leases=S.released([a], [l],l['id'],tr,rr,self.B)
  self.assertEqual((out[0]['state'],leases),('repair',[]))
  self.assertEqual([x['node']for x in self.plan(out+[self.node('b','MXR',physical=[6])])['proposals']],['b'])
  self.assertEqual(a['state'],'running')
 def test_unknown_wrong_owner_release_never_frees(self):
  a=self.node();l=self.lease(a);t=self.B.obj(a['packet_ref'])
  tr=self.obj(dict(schema='main.serial-child-unknown/v1'))
  with self.assertRaises((ValueError,KeyError)):S.released([a],[l],l['id'],tr,self.obj({}),self.B)
  self.assertEqual(l['state'],'running')
 def test_refill_diversity_scope_and_completed_handle(self):
  a=self.node('a',kind='prepare',state='preparing');b=self.node('b','MXR','prepare',state='preparing')
  c=self.node('c','DeltaLog','prepare',state='preparing');c['edit_scope']='draft/a/child'
  agents=[dict(id='worker-a',status='running',node='a'),dict(id='worker-b',status='completed',node=None),dict(id='worker-c',status='idle',node=None)]
  r=S.refill([a,b,c],agents)
  self.assertEqual(r,[dict(agent='worker-b',node='b',action='FOLLOWUP_REQUIRED_NOT_SENT')])
 def test_duplicate_and_cycles(self):
  a=self.node()
  with self.assertRaises(ValueError):S.nodes_checked([a,a])
  b=self.node('b');a['deps']=['b'];b['deps']=['a']
  with self.assertRaises(ValueError):S.nodes_checked([a,b])
 def test_resource_ineligible_TP4_does_not_starve_fitting_single(self):
  x=self.node('tp',kind='tp4',critical=1,ram=80);n=self.node('small','MXR',physical=[6],ram=20)
  self.snap['mem_available']=50
  p=self.plan([x,n]);self.assertIsNone(p['exclusive_reservation']);self.assertIsNone(p['exclusive_pending'])
  self.assertEqual([r['node']for r in p['proposals']],['small'])
  self.snap['mem_available']=108;self.snap['disk_free']['output']=13
  x['budget']['disk']['output']=50
  self.rewrite_review(x,lambda r:r.update(joint_demand=x['budget']))
  p=self.plan([x,n]);self.assertIsNone(p['exclusive_reservation']);self.assertEqual([r['node']for r in p['proposals']],['small'])
 def test_external_busy_or_unknown_card_cannot_reserve_now(self):
  x=self.node('tp',kind='tp4',critical=1);n=self.node('small','MXR',physical=[6])
  self.snap['cards']['4']='unknown'
  p=self.plan([x,n]);self.assertIsNone(p['exclusive_reservation']);self.assertEqual([r['node']for r in p['proposals']],['small'])
 def test_stale_or_unknown_resource_cannot_claim_safe_start(self):
  x=self.node('tp',kind='tp4',critical=1);n=self.node('small','MXR',physical=[6])
  self.snap['unknown_operations']=['lost-operation']
  p=self.plan([x,n]);self.assertIsNone(p['exclusive_reservation']);self.assertEqual(p['proposals'],[])
 def test_active_CPU_lease_cannot_be_proposed_twice(self):
  a=self.node('cpu',kind='cpu');l=self.lease(a);self.usage(l)
  b=self.node('next','MXR',kind='cpu')
  self.assertEqual([r['node']for r in self.plan([a,b],[l])['proposals']],['next'])
  a['state']='ready'
  with self.assertRaises(ValueError):self.plan([a,b],[l])
 def test_completed_handle_does_not_repeat_unacknowledged_delivery(self):
  a=self.node('delivered',kind='prepare',state='preparing')
  b=self.node('independent','MXR',kind='prepare',state='preparing')
  r=S.refill([a,b],[dict(id='done',status='completed',node='delivered')])
  self.assertEqual(r,[dict(agent='done',node='independent',action='FOLLOWUP_REQUIRED_NOT_SENT')])
 def test_no_arbitrary_executor_and_true_default_cli(self):
  p=subprocess.run([sys.executable,'-I','-B',str(HERE/'scheduler.py')],capture_output=True,text=True,timeout=5)
  self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),dict(default_enabled=False,dispatch_executed=False))
  p=subprocess.run([sys.executable,'-I','-B',str(HERE/'scheduler.py'),'--execute'],capture_output=True,text=True,timeout=5)
  self.assertNotEqual(p.returncode,0)
if __name__=='__main__':unittest.main(verbosity=2)
