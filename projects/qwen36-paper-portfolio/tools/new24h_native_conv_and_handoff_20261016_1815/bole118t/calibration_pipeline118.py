"""Twelve actual native calls with pre-fault capture; independent CPU consumer."""
import importlib,time
from pathlib import Path
def run(t,C,m,out,deadline):
 import registration118,device_receipt_conv118 as R,calibrate_conv118 as K,kernel_contract118 as S
 abi_ref,abi=R.join(C,template=m['observed_template_ref'],device_owner_ref=m['observed_device_owner_ref'],consumer_owner_ref=m['observed_consumer_owner_ref'])
 C.need(abi_ref==m['observed_device_abi_ref'],'actual pinned device ABI')
 proof=S.verify(C);reg=registration118.actual(t,C,arm_verified=True)
 C.need(reg['actual_extension_ref']==abi['registration']['actual_extension_ref']and [x['ref']for x in reg['actual_opapi_mappings']]==[x['ref']for x in abi['registration']['actual_opapi_mappings']],'same actual native extension and opapi bytes')
 gdn=importlib.import_module('vllm_ascend.ops.gdn');C.need(C.ref(gdn.__file__)==abi['gdn_ref'],'same actual native GDN callsite')
 op=R.overload(t,abi);records=[];before_records=[]
 def store(i,row,*,before=False):
  C.need(time.time()<deadline,'original guest deadline');row=dict(row,source=m['_actual_source'],actual_device_abi_ref=abi_ref,index=i)
  p=out/(('before-'if before else'frame-')+('%02d.pt'%i));C.need(not p.exists(),'exclusive raw');t.save(row,p)
  C.need(sum(x.stat().st_size for x in out.iterdir()if x.is_file())<=64*2**20,'raw64MiB no truncation');(before_records if before else records).append(C.ref(p))
 K.execute(t,op,abi['actual_schema_family']['']['schema'],device=t.device('npu:0'),save=lambda i,r:store(i,r),save_before=lambda i,r:store(i,r,before=True))
 return dict(schema='bole.actual-native-conv-capture/v118t',source=m['_actual_source'],actual_device_abi_ref=abi_ref,registration=reg,kernel_source=proof,records=records,before_records=before_records,NPU=True,operator_executed=True,qualified=False,model_ready=False)
def consume(t,C,m,sr,outer):
 import calibrate_conv118 as K
 C.need(outer['schema']=='bole.tree-stage/v118t'and outer['source']==sr and outer['primary']is None and outer['NPU']is True,'actual complete calibration outer')
 capture=C.obj(outer['result']);C.need(capture['schema']=='bole.actual-native-conv-capture/v118t'and capture['source']==sr and capture['actual_device_abi_ref']==m['observed_device_abi_ref']and capture['operator_executed']is True and len(capture['records'])==len(capture['before_records'])==12,'actual exact12 calls not schema-only')
 rows=[]
 for i,(r,b)in enumerate(zip(capture['records'],capture['before_records'])):
  after=t.load(C.checked(r),map_location='cpu',weights_only=True);before=t.load(C.checked(b),map_location='cpu',weights_only=True)
  C.need(after['source']==before['source']==sr and after['index']==before['index']==i and before['output']is None,'pre-call and post-call source/index join')
  C.need(after['actual_device_abi_ref']==before['actual_device_abi_ref']==capture['actual_device_abi_ref'],'each actual frame ABI provenance')
  for name in('inputs','weight','bias','indices','before'):
   a,z=after[name],before[name];C.need((a is None and z is None)or(a is not None and z is not None and a.dtype==z.dtype and a.shape==z.shape and t.equal(a.contiguous().view(t.uint8),z.contiguous().view(t.uint8))),'actual prefault input bytes '+name)
  C.need(after['inputs'].shape==(after['batch'],2560),'real local GDN convolution channel count');rows.append(after)
 result=K.consume(t,rows,require_native_metadata=True)
 return dict(result,schema='bole.native-conv-independent/v118t',source=sr,actual_capture=outer['result'],actual_device_abi_ref=m['observed_device_abi_ref'],records=capture['records'],before_records=capture['before_records'],native_SD_chronology_pass=result['pass_gate'],qualified=False,model_ready=False,BOLE_model_ready=False)
