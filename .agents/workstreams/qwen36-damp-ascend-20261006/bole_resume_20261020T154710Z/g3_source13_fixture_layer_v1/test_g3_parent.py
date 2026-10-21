"""A prepared source or first-frame success never qualifies the long successor."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g3_parent as G

class ParentTests(unittest.TestCase):
 def fixture(self,source_changes=None):
     import json
     td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);p=Path(td.name)
     consumer=C.write(p/'CONSUMER.json',dict(synthetic=True))
     channel=C.write(p/'CHANNEL.json',dict(synthetic=True))
     helper=C.write(p/'READER.json',dict(synthetic=True))
     final_inputs=C.write(p/'FINAL-INPUTS.json',dict(synthetic=True))
     m=dict(service_experiment=copy.deepcopy(G.SCOPE),prepared_only=False,default_enabled=False,
         files={'g2_consumer.py':consumer},service_required_sameimage_software_cases=349)
     m.update(source_changes or {})
     sr=C.write(p/'SOURCE.json',m)
     report=dict(schema='bole.actual-G2-stream-attribution/v2',source=sr,scope=m['service_experiment'],
         channel=channel,service_complete=True,completed_request_count=2,component_checks_pass=True,
         scheduler_committed_independently=True,all4_worker_retirement_verified=True,
         every_frame_independently_consumed=True,model_ready=False,successful_raw_replay_available=False,
         ranks=[dict(rank=rank,all_frames_consumed=True,
             coverage_proof=dict(all_coverage=True,complete_output_tokens=8,request_count=2,
                 final_pending_by_retirement=True,target_step_count=4),
             final_metadata_bytes=0,slot_reuse_observed=dict(FA=False,GDN=False),
             requests=[dict(generation=generation,request='fixture-%d-%d'%(rank,generation),
                 prefix_token_ids=list(range(131)),observation={},steps=2,processed_tokens=3,
                 output_token_ids=[7,11,13,17],next_counter_ACKs=1,component_checks_pass=True)
                 for generation in(1,2)])for rank in range(4)])
     report.update({key:False for key in G.QFALSE})
     attribution=C.write(p/'ATTRIBUTION.json',report)
     own=C.write(p/'OWNER.json',dict(source=sr,primary=None,secondary=[],source_before={'fixture':'unchanged'},
         source_after={'fixture':'unchanged'},cpu_only=False,summary=dict(independent=attribution)))
     terminal=C.write(p/'UNIT.json',dict(schema='bole.actual-finite-unit-terminal/v1',observed_epoch=0.,
         properties=dict(ActiveState='active',ControlPID='0',ExecMainStatus='0',
             Id='bole-g2-v13-model-20261020t154710z.service',MainPID='0',Restart='no',
             Result='success',SubState='exited',Type='exec')))
     exit_value=dict(schema='bole.actual-stream-consumer-exit/v2',source=sr,channel_ref=channel,
         completed=True,source_unchanged=True,primary=None,traceback=None,actual_frame_batches=9,
         ACKs=[helper for _ in range(36)],requests=[{} for _ in range(4)],consumer_source=consumer)
     exit_value.update({key:False for key in G.QFALSE})
     consumer_exit=C.write(p/'CONSUMER-EXIT.json',exit_value)
     refs=dict(unit_terminal_ref=terminal,original_attribution_ref=attribution,
         finalizer_inputs_ref=final_inputs,consumer_exit_ref=consumer_exit,reader_ref=helper,
         stage_qualification_ref=helper,stage_reader_ref=helper)
     self.assertEqual(set(refs),set(G.QTYPED))
     q=dict(schema='bole.actual-G2-v13-full-MODEL-metadata-independent-qualification/v1',
         source=sr,result_ref=own,source_readset_count=4088,derived_frame_count=36,
         helper_refs=dict(protocol=helper,roles=helper),independent_readback_refs=[consumer,channel,helper],**refs)
     q.update({key:True for key in G.QTRUE});q.update({key:False for key in G.QFALSE})
     rr=C.write(p/'QUALIFICATION.json',q)
     audit=copy.deepcopy(C.obj(G.ACTUAL['source_audit']))
     inner=json.loads(audit['stdout']);inner['source']=sr
     audit['stdout']=json.dumps(inner,sort_keys=True,allow_nan=False)
     ar=C.write(p/'AUDIT.json',audit)
     return p,sr,m,own,rr,ar
 def test_only_actual_complete_parent_plus_independent_corrected_source_audit_admits(self):
  p,sr,m,own,rr,ar=self.fixture();self.assertTrue(G.qualified(sr,m,own,rr,source_audit_ref=ar))
 def test_pending_source_only_CPU_only_or_first_frame_parent_never_admits(self):
     p,sr,m,own,rr,ar=self.fixture()
     with self.assertRaises((ValueError,TypeError)):
         G.qualified(sr,m,None,None,source_audit_ref=ar)
     for field,value in(('prepared_only',True),('service_experiment',dict(m['service_experiment'],max_output_tokens=1024))):
         p,sr,m,own,rr,ar=self.fixture({field:value})
         with self.subTest(field=field),self.assertRaises(ValueError):
             G.qualified(sr,m,own,rr,source_audit_ref=ar)
     p,sr,m,own,rr,ar=self.fixture()
     o=C.obj(own);o['cpu_only']=True;own2=C.write(p/'CPU.json',o)
     q=C.obj(rr);q['result_ref']=own2;rr2=C.write(p/'CPU-QUALIFICATION.json',q)
     with self.assertRaises(ValueError):
         G.qualified(sr,m,own2,rr2,source_audit_ref=ar)
 def test_missing_late_coverage_retirement_or_source_audit_failure_remains_blocking(self):
     import json
     for field in('coverage','retirement','component','audit'):
         p,sr,m,own,rr,ar=self.fixture();q=C.obj(rr);o=C.obj(own)
         report=C.obj(q['original_attribution_ref'])
         if field=='coverage':report['ranks'][3]['coverage_proof']['all_coverage']=False
         elif field=='retirement':report['all4_worker_retirement_verified']=False
         elif field=='component':report['ranks'][2]['requests'][1]['component_checks_pass']=False
         else:
             audit=C.obj(ar);inner=json.loads(audit['stdout'])
             inner['original_math_ACK_cap_argv_transport_resources_unchanged']=False
             audit['stdout']=json.dumps(inner,sort_keys=True,allow_nan=False)
             ar=C.write(p/'AUDIT-FAILED.json',audit)
         attrib2=C.write(p/'ATTRIBUTION-ALTERED.json',report)
         o['summary']['independent']=attrib2;own2=C.write(p/'OWNER-ALTERED.json',o)
         q['original_attribution_ref']=attrib2;q['result_ref']=own2
         rr2=C.write(p/'QUALIFICATION-ALTERED.json',q)
         with self.subTest(field=field),self.assertRaises(ValueError):
             G.qualified(sr,m,own2,rr2,source_audit_ref=ar)

if __name__=='__main__':unittest.main()
