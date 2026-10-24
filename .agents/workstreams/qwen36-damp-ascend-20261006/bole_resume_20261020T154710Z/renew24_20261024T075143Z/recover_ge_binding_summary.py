"""Recover already completed GE binding after MAIN summary construction failure; never rebind."""
import hashlib,json
from pathlib import Path
OUT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/renew24_20261024T075143Z")
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/good_enough_layer37_renew_v2_20261024/prepared-source")
def ref(p):
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
sr=ref(ROOT/'SOURCE_MANIFEST.json');m=json.loads((ROOT/'SOURCE_MANIFEST.json').read_bytes())
hr=m['files']['successor_bindings.py'];raw=Path(hr['path']).read_bytes()
assert len(raw)==hr['bytes'] and hashlib.sha256(raw).hexdigest()==hr['sha256']
ns={'__file__':hr['path'],'__name__':'_MAIN_recover_actual_GE_binding'}
exec(compile(raw,hr['path'],'exec'),ns)
ns['validate_source'](sr,m,ROOT,clock=True)
commands=ref(ROOT/'COMMANDS.json');a=json.loads(Path(m['authority_ref']['path']).read_bytes())
result=dict(schema='MAIN.GE-layer37-source-binding/v1',source=sr,commands=commands,authority_ref=m['authority_ref'],review_ref=a['MAIN_review_ref'],full64_source=True,original96_cases_retained=True,NPU=False,execution_not_started=True,previous_summary_failure='exec-00000000000014c6: duplicate NPU keyword after original bind had already completed',rebind_executed=False)
with (OUT/'GE_LAYER37_SOURCE_BIND_RECOVERY_RESULT.json').open('x')as f:json.dump(result,f,sort_keys=True);f.write('\n')
print(json.dumps(result,sort_keys=True))
