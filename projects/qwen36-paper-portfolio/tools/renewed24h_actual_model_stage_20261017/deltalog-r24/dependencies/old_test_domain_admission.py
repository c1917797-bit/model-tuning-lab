"""In-memory SOFTWARE ABI controls only; no mocked receipt is persisted as evidence."""
import copy,unittest
from unittest.mock import patch
import importlib.util
from pathlib import Path
import owner_overlay as O
_spec=importlib.util.spec_from_file_location('actual053_shared052',Path(__file__).resolve().parent/'plugin/qwen36_deltalog_service/split_qualification.py');D=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(D);D.C=O

def fixture():
 refs={k:{'label':k}for k in('source','template','owner','ownersource','producer','pair','old','domain','library')}
 pin={'domain_consumer.py':{'label':'pinned'}}
 sc=dict(schema='deltalog.deadpayload-native-bridge-source/v024',default_enabled=False,prepared_only=False,files=pin,prepared_template=refs['template'],root='/actual035',library_ref=refs['library'])
 contract=dict(D.SOURCE_CONTRACT);sc['validation_contract']=contract
 debug={k:{'label':k}for k in('debug_library','debug_build_ref','debug_kernel_source_ref')};sc.update(debug)
 records=[];rows=[]
 for batch in(1,16):
  for step in range(160):
   rec=dict(kind='mixed',batch=batch,step=step,raw={'label':'B%dS%d'%(batch,step)})
   requests=[]
   for kind,count in(('independent-decode',batch),('whole-core-native-peer',batch+1)):
    for j in range(count):
     item=dict(kind=kind,request=j,state_error=7.92e-7,output_error=.00303,request_pass=True)
     if kind=='independent-decode':item.update(uncast_CPU64_output_error=.004,BF16_RNE_floor=.003,actual_precast=dict(request_row=j,peak=.00303,relative_l2=2**-13,passed=True),cast_bitwise=True)
     requests.append(item)
   rows.append(dict(record=rec,domain_checks_pass=True,all_requests_pass=True,runtime_operand_immutability_pass=True,per_request=requests,transition=dict(local_transition_pass=True,missing=[]),metrics={k:True for k in('conv_bitwise','untouched_bitwise','guard_bitwise','inputs_bitwise','pointers_bitwise','prefill_aux_reset_bitwise')}));records.append(rec)
  for partial in(False,True):
   rec=dict(kind='dead_flush',batch=batch,partial=partial);rows.append(dict(record=rec,domain_checks_pass=True,metrics=dict(length0=not partial,partial_live=partial)));records.append(rec)
  for length in(1,7):
   rec=dict(kind='copy',batch=batch,length=length);rows.append(dict(record=rec,domain_checks_pass=True,metrics=dict(descriptors_exact=True)));records.append(rec)
 old=dict(schema='deltalog.fresh-bridge-consumption/v5',source=refs['source'],producer=refs['producer'],pass_gate=False,primary='original uncast threshold FAIL retained')
 retained=dict(pass_gate=False,primary=old['primary']);anchors={'1':{'label':'anchor1'},'16':{'label':'anchor16'}}
 domain=dict(schema='deltalog.direct-RNE-domain-audit/v035',source=refs['source'],producer=refs['producer'],original_strict_consumer=refs['old'],original_strict_result_preserved=retained,validation_contract=D.CONTRACT,domain_checks_pass=True,missing_evidence=[],failures=[],prefill_CPU64_diagnostic_only=True,old_thresholds_unchanged=True,anchors=anchors,rows=rows)
 domain.update({k:False for k in('complete_proof','diagnostic_qualified','model_ready','performance_ready','NPU_reexecuted','MXR_qualification')})
 pair=dict(schema='deltalog.diagnostic-consumption/v043',source=refs['source'],actual_result=refs['producer'],diagnostic_capture_complete=True,domain_checks_pass=True,complete_proof=False,NPU_reexecuted=False,original_strict_consumer=refs['old'],domain_consumer=refs['domain'],original_strict_result_preserved=retained,validation_contract=D.CONTRACT,initial_anchor_refs=anchors)
 owner=dict(schema='deltalog.diagnostic-owned-host/v035',source=refs['ownersource'],target_source=refs['source'],stage='numeric',steps=160,physical=[5],NPU=True,primary=None,secondary=[],stopped_retained=True,resource_admitted=True,diagnostic_capture_complete=True,bridge_primitive_gate_pass=False,model_ready=False,result=refs['producer'],independent_consumer=refs['pair'])
 prod=dict(source=refs['source'],steps=160,primary=None,NPU=True,graph=False,fullmodel=False,records=records)
 sidecars=[dict(path='/raw/sidecar-%d.pt'%i,bytes=i+1,sha256='%064d'%i)for i in range(351)]
 controls=[dict(case=name,raw=sidecars[320+i])for i,name in enumerate(('normal','tiny','subnormal','positive-zero','negative-zero','cancellation','overflow','finite-final-normalized-query','finite-final-unscaled-query','cancellation-permuted','gqa-vtile-witness','original-B16-step80','original-B16-step137'))]
 prod.update(actual_sidecar_records=sidecars,actual_mixed_sidecar_records=sidecars[:320],boundary_controls=controls)
 domain.update(actual_sidecar_rows=[dict(raw=r,passed=True)for r in sidecars],boundary_controls=controls)
 objects=dict(source=sc,template=dict(files=pin,root='/actual035',validation_contract=contract),owner=owner,ownersource=sc,producer=prod,pair=pair,old=old,domain=domain)
 owner['source']=refs['source']
 m=dict(admission_mode=D.MODE,prepared_only=False,reviewed_domain_files=pin,bridge024_source_ref=refs['source'],reviewed_domain_template_ref=refs['template'],library_ref=refs['library'],bridge024_owner_ref=refs['owner'])
 m.update(debug)
 for key in('build','kernel','cpu_owner','CPU','plan'):refs[key]={'label':key}
 sc.update(split_build_ref=refs['build'],split_kernel_source_ref=refs['kernel'],debug_build_ref=refs['build'])
 m.update(production_build_ref=refs['build'],debug_build_ref=refs['build'],split_kernel_source_ref=refs['kernel'],component_cpu_owner_ref=refs['cpu_owner'])
 prod['plan']=refs['plan']
 arts=[dict(arm=a,library=lib)for a,lib in zip(('split_scale_v051','split_scale_sidecar_v051'),(m['library_ref'],m['debug_library']))]
 meta=dict(schema='deltalog.split-scale-actual-Meta/v051',build=refs['build'],source=refs['kernel'],libraries=[m['library_ref'],m['debug_library']],pass_gate=True,NPU=False,rows=[dict(arm=a,batch=n,arguments=13 if a=='split_scale_v051'else 14,shape=[n,12,128],dtype='torch.bfloat16')for a in('split_scale_v051','split_scale_sidecar_v051')for n in(1,16)])
 objects.update(build=dict(schema='deltalog-split-scale-actual-build/v051',primary=None,source_manifest=refs['kernel'],NPU=False,Devices=[],artifacts=arts,commands=[dict(exit_code=0,error=None)]),cpu_owner=dict(schema='deltalog.diagnostic-owned-host/v035',source=refs['source'],target_source=refs['source'],stage='cpu',physical=[],NPU=False,primary=None,secondary=[],stopped_retained=True,result=refs['CPU']),CPU=dict(source=refs['source'],pass_gate=True,NPU=False,actual_precast_meta=meta),plan=dict(source=refs['source'],cpu_preflight=refs['CPU']))
 return m,objects

class Controls(unittest.TestCase):
 def test_new_library_build_Meta_and_CPU_owner_source_refuse(self):
  for kind in('oldbuild','Meta','row','CPU','plan'):
   m,o=fixture()
   if kind=='oldbuild':o['build']['schema']='deltalog-key-projection-actual-build/v010'
   elif kind=='Meta':o['CPU']['actual_precast_meta']['libraries']=[]
   elif kind=='row':o['CPU']['actual_precast_meta']['rows'][0]['arguments']=14
   elif kind=='CPU':o['cpu_owner']['source']={'label':'wrong'}
   else:o['plan']['cpu_preflight']={'label':'wrong'}
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def run_fixture(self,m,objects):
  with patch.object(D.C,'obj',side_effect=lambda r:objects[r['label']]),patch.object(D.C,'obj_file',return_value=None):return D.consume(m)
 def test_default_off(self):
  with self.assertRaisesRegex(ValueError,'explicit035'):D.consume({})
 def test_missing_pins(self):
  with self.assertRaisesRegex(ValueError,'reviewed035'):D.consume(dict(admission_mode=D.MODE))
 def test_unbound_no_IO(self):
  with self.assertRaisesRegex(ValueError,'unbound'):D.consume(dict(admission_mode=D.MODE,reviewed_domain_files={'p':{}},prepared_only=True))
 def test_exact_software_fixture_retains_old_fail_scope(self):
  m,o=fixture();v=self.run_fixture(m,o);self.assertTrue(v['diagnostic_smoke_admitted']);self.assertFalse(v['model_numeric_qualified']);self.assertFalse(o['old']['pass_gate'])
 def test_actual_owner_failure_or16_rejects(self):
  for k,v in(('primary','failed'),('steps',16),('stopped_retained',False)):
   m,o=fixture();o['owner'][k]=v
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_old_contract_or_wrong_seed_refuses(self):
  for target in('source','pair','domain'):
   m,o=fixture();o[target]['validation_contract']=dict(o[target]['validation_contract'],seed_base=0)
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_old031_owner_rejected(self):
  m,o=fixture();o['owner']['schema']='deltalog.diagnostic-owned-host/v031'
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_missing_request_or_false_request_refuses(self):
  for mutate in('missing','false'):
   m,o=fixture();row=o['domain']['rows'][0]
   if mutate=='missing':row['per_request'].pop()
   else:row['per_request'][0]['request_pass']=False
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_bad_units_and_nan_refuse(self):
  for k,v in(('state_error',.00303),('output_error',float('nan')),('state_error',True)):
   m,o=fixture();o['domain']['rows'][0]['per_request'][0][k]=v
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_old_BF16_point_failure_is_diagnostic_not_FP32_relaxation(self):
  m,o=fixture();o['domain']['rows'][0]['per_request'][0]['output_error']=.005208333
  self.assertTrue(self.run_fixture(m,o)['diagnostic_smoke_admitted'])
  o['domain']['rows'][0]['per_request'][0]['actual_precast']['peak']=.0030301
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_missing_actual_sidecars_controls_or_cast_refuses(self):
  for mutate in('missing','control','cast','l2'):
   m,o=fixture()
   if mutate=='missing':o['domain']['actual_sidecar_rows'].pop()
   elif mutate=='control':o['domain']['boundary_controls']=[]
   elif mutate=='cast':o['domain']['rows'][0]['per_request'][0]['cast_bitwise']=False
   else:o['domain']['rows'][0]['per_request'][0]['actual_precast']['relative_l2']=2**-12
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_retained_uncast_missing_or_nonfinite_refuses(self):
  for missing in(True,False):
   m,o=fixture();row=o['domain']['rows'][0]['per_request'][0]
   if missing:row.pop('uncast_CPU64_output_error')
   else:row['BF16_RNE_floor']=float('nan')
   with self.assertRaises((ValueError,KeyError)):self.run_fixture(m,o)
 def test_anchor_runtime_byte_slot_missing_refuses(self):
  for field in('runtime','anchor','bytes','transition'):
   m,o=fixture();row=o['domain']['rows'][0]
   if field=='runtime':row['runtime_operand_immutability_pass']=False
   elif field=='anchor':o['domain']['anchors']={'1':{}}
   elif field=='bytes':row['metrics']['prefill_aux_reset_bitwise']=False
   else:row['transition']['missing']=['initialstate']
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_old_strict_failure_not_relabelled(self):
  m,o=fixture();o['old']['pass_gate']=True
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_source_or_record_join_refuses(self):
  for kind in('template','records'):
   m,o=fixture()
   if kind=='template':o['source']['prepared_template']={'label':'different'}
   else:o['producer']['records']=o['producer']['records'][1:]
   with self.assertRaises(ValueError):self.run_fixture(m,o)
if __name__=='__main__':unittest.main()
