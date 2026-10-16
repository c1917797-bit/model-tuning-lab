"""Source-only mechanical manifest/commands serializer; no experiment dispatch."""
import base64,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-native-prefill-counterfactual-new24h-v1-079'
def data(v):return(json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def ref(p,b):return dict(path=p,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
 import guest_core as G
 names=['guest_core.py','test_guest079.py','early_vendor.py','native_bootstrap.py','device_dispatch.py','ACTUAL_VENDOR_CONFIG_PROOF.json','HANDOFF.md','seal079.py']
 files={n:(P/n).read_bytes()for n in names}
 for n,b in files.items():
  if b'\r'in b or not b.endswith(b'\n'):raise ValueError('full LF source '+n)
 m=dict(schema='deltalog.native-prefill-counterfactual-source/v079',root=ROOT,default_enabled=False,source_only=True,READY=False,qualified=False,NPU_executed=False,authority_ref=G.AUTHORITY,retained_source=G.SOURCE,retained_failed_producer=G.PRODUCER,cann_helper_ref=G.CANN,files={n:ref(ROOT+'/'+n,b)for n,b in files.items()},resource_contract=dict(physical=None,logical=0,guest_GiB=8,host_GiB=.5,reserve_GiB=8,whole_seconds=900,guest_seconds=600,cleanup_seconds=90,ARM_seconds=30,raw_cap_bytes=G.RAW_CAP,whole_output_bytes=2**30),selection=dict(batch=1,steps=[89,90],prefill_slot=1,decode_slot=0,initial_state_C='exact current captured initial N,H,K,V',initial_state_N='previous native slot1 transposed N,H,K,V',other_operands='same captured candidate postconv operands, not historical native-baseline operands'),calls=['SC-repeat0','SN-repeat0','SC-repeat1','SN-repeat1','SC-common-control0','SC-common-control1'],actual_gmH_observation=True,source_to_binary_identity_proved=False,local_software_controls=dict(passed=7,NPU=False,sameimage=False))
 raw=data(m);(P/'SOURCE_MANIFEST.json').write_bytes(raw);sr=ref(ROOT+'/SOURCE_MANIFEST.json',raw)
 plan=dict(schema='deltalog.native-prefill-counterfactual-plan/v079',source=sr,retained_source=G.SOURCE,producer=G.PRODUCER,physical=None,logical=0,qualification=False)
 pb=data(plan);(P/'PLAN_TEMPLATE.json').write_bytes(pb)
 commands=dict(schema='deltalog.native-prefill-counterfactual-commands/v079',source=sr,default_enabled=False,NPU_executed=False,sourceaudit=['/usr/local/python3.12.13/bin/python3','-I','-B',ROOT+'/guest_core.py','--source-audit','--source-ref',json.dumps(sr,separators=(',',':'))],guest=['/usr/local/python3.12.13/bin/python3','-I','-B',ROOT+'/guest_core.py','--execute','--source-ref',json.dumps(sr,separators=(',',':')),'--plan-ref','ACTUAL_MAIN_SOURCEBOUND_SINGLETON_PLAN_REF3','--output','ACTUAL_OWNED_LEAF/numeric/result'],must_run_only_in_MAIN_existing_owned_singleton=True,must_prepend_vendor_before_Python='/vllm-workspace/vllm-ascend/vllm_ascend/_cann_ops_custom/vendors/custom_transformer',pending=['same-image source/CANN/native import checks','actual MAIN-owned host binding and exact physical/PID/ARM proof','actual six-call NPU counterfactual and independent result reopen'],qualified=False)
 cb=data(commands);(P/'COMMANDS.json').write_bytes(cb);files.update({'SOURCE_MANIFEST.json':raw,'PLAN_TEMPLATE.json':pb,'COMMANDS.json':cb})
 bundle=dict(schema='deltalog079.source-only-byteexact/v1',root=ROOT,READY=False,NPU=False,files=[dict(relative=n,**ref(ROOT+'/'+n,b),base64=base64.b64encode(b).decode())for n,b in sorted(files.items())]);db=data(bundle);(P/'BYTE_EXACT_DELIVERY.json').write_bytes(db)
 print(json.dumps(dict(source=sr,delivery=ref(str(P/'BYTE_EXACT_DELIVERY.json'),db),files=len(files),NPU=False,READY=False)))
if __name__=='__main__':main()
