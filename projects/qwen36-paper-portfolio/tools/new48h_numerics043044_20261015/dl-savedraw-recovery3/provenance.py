"""Saved natural-exit provenance; never converts the failed host owner to PASS."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import terminal_fence as F
CID='79ed1080aeaa9e28ea35b889d446758278005e245b1e31709bf09ac8c3a8ee35'
def inspect_record(r):
 F.need(r['exit_code']==0,'actual successful readonly inspect')
 values=json.loads(r['stdout']);F.need(type(values)is list and len(values)==1,'one actual original CID inspect')
 return values[0]
def validate(failed,producer,stage,cleanup,verdict,arm,before,after,sr,pr):
 F.need(failed['schema']=='deltalog.diagnostic-owned-host/v035'and failed['target_source']==sr and failed['primary']=="ValueError(\"owned protected0-3 boundary or incomplete proof: ['protected ownership observation incomplete']\")"and failed['bridge_primitive_gate_pass']is False and failed['stopped_retained']is True,'preserve exact original host observer FAIL')
 F.need(producer['source']==sr and producer['primary']is None and producer['steps']==16 and len(producer['records'])==40 and producer['NPU']is True and stage['actual_result']==pr and stage['producer_exit']==0 and stage['observation_complete']is True,'actual complete original NPU producer, not a new NPU run')
 F.need(cleanup['resource_release_verified']is cleanup['stopped']is cleanup['retained']is True and cleanup['errors']==[]and cleanup['secondary_guard_cleanup']==[]and cleanup['unresolved_active_cid']is None,'original actual release/secondary preserved')
 F.need(arm['pid']==1362378 and arm['start_ticks']==21233724 and CID in arm['cgroup'],'actual original ARM PID/start/cgroup')
 original=json.loads(verdict['exact_owned_inspect']['stdout'])[0]
 F.empty_top_exit([({},verdict)],arm,original,CID)
 a,b=inspect_record(before),inspect_record(after);F.state(a,CID);F.state(b,CID)
 F.need(a['State']==b['State']and a['HostConfig']['Devices']==b['HostConfig']['Devices']and a['Image']==b['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1','same immutable CID terminal/image/mapping')
 devices={(d['PathOnHost'],d['PathInContainer'])for d in a['HostConfig']['Devices']}
 F.need(devices=={('/dev/davinci5','/dev/davinci0'),*((p,p)for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc'))},'actual original scoped5, no0-3 device')
 return dict(schema='deltalog.saved043R3-natural-exit-provenance/v1',old_host_failure_unchanged=True,original_NPU=True,NPU_reexecuted=False,natural_exit_verified=True,original_secondary=failed['secondary'],original_numerical_qualified=False)
