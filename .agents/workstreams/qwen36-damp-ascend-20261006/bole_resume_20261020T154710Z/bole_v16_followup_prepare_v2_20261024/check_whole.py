"""Full remote source reconstruction only; no binding, authority or NPU."""
import os,resource,sys,importlib.util,json,hashlib
from pathlib import Path
os.sched_setaffinity(0,{145})
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(144,144))
W=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
S=W/'bole_v16_followup_prepare_v2_20261024'
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def compare(b,old):
 for key in ('resources','input_resource_profile32k','fastpath_numeric_qualification','runtime_joint_capture_ledger','native_speculative_config','service_experiment','performance_client_contract'):
  assert (key in b['manifest'])==(key in old['manifest']),key
  if key in old['manifest']:assert b['manifest'][key]==old['manifest'][key],key
 assert b['manifest']['fa_lossless_capture']==dict(old['manifest']['fa_lossless_capture'],raw_cap=b['manifest']['input_resource_profile32k']['per_rank_disk_cap'])
 for n in ('fastpath_numeric_consumer.py','independent_model.py','oracle112.py','g2_numeric.py','short_state_digest.py','transaction.py'):
  if n in old['files']:assert b['files'][n]==old['files'][n],n
 for n,raw in b['files'].items():
  if n.endswith('.py'):compile(raw,n,'exec')
 assert b['files']['disk_ledger.py']==(W/'bole_profile_disk_ledger_v16_prepare_20261024/disk_ledger.py').read_bytes()
 assert b['files']['adapt_disk_ledger.py']==(W/'bole_profile_disk_ledger_v16_prepare_20261024/adapt_disk_ledger.py').read_bytes()
R=load(S/'related_qualification.py','_actual_v16_related')
O=load(W/'bole_related160_v14_output_scan_prepare_20261024/related_qualification.py','_old_related14')
for mode in ('rawON','rawOFF'):
 b=R.render(base_root=S/('review-related-'+mode));R.inverse(b)
 old=O.render(base_root=S/('old-review-related-'+mode));O.inverse(old)
 compare(b,old)
 print(json.dumps(dict(role='related160',mode=mode,files=len(b['files']),whole_inverse=True,actual_source_math_unchanged=True,timefit=False,NPU=False)),flush=True)
F=load(S/'formal_runtime.py','_actual_v16_formal')
O=load(W/'bole_formal_v15_arm_geometry_prepare_20261024/formal_runtime.py','_old_formal15')
for arm in ('native_ar','bole'):
 b=F.render(S/('review-formal-'+arm),arm=arm);F.inverse(b)
 old=O.render(S/('old-review-formal-'+arm),arm=arm);O.inverse(old)
 compare(b,old)
 assert b['files']['conv_resource_layout.py']==old['files']['conv_resource_layout.py']
 assert b['manifest']['input_resource_profile32k']['conv_slot_bytes']==56320
 print(json.dumps(dict(role='formal1024',arm=arm,files=len(b['files']),whole_inverse=True,actual_source_math_unchanged=True,original_v15_geometry=True,NPU=False)),flush=True)
for p in sorted(S.iterdir()):
 if p.is_file():
  raw=p.read_bytes()
  assert raw.endswith(b'\n')and not raw.endswith(b'\n\n')and all(x==x.rstrip()for x in raw.splitlines())
  print(json.dumps(dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
