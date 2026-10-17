"""Minimal023 environment overlay on exact017 entry, no new Controller."""
import importlib.util,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-service-empirical-owned-v1-017')
def need(v,m):
 if not v:raise ValueError(m)
def obj(r):
 import hashlib
 p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and set(r)=={'path','bytes','sha256'}and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact immutable Ref');return json.loads(b)
def current(sr):
 m=obj(sr);need(m['schema']=='deltalog.service023-owned-overlay/v025'and m['root']==str(HERE)and m['default_enabled']is False,'actual new overlay identity')
 need(m['window']==dict(start=1792134133,cutoff=1792220533),'fixed authority window')
 for r in m['files'].values():obj_file(r)
 return m
def obj_file(r):
 import hashlib
 p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and not p.is_symlink()and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'source Ref');return p
def model_gate(m):
 need(m.get('admission_mode')=='actual052-split-scale-diagnostic-only'and m.get('short_model_diagnostic_scope',{}).get('schema')=='deltalog.actual16-to-nine-decode-model-diagnostic/v101-repair7','only independently preregistered16-to-nine-decode diagnostic route')
 if m.get('admission_mode')=='actual052-split-scale-diagnostic-only':
  import domain_qualification as D
  return D.consume(m)
 # The future exact024 qualification reader must come from MAIN's reviewed
 # bridge packet. No template/bool/event count substitutes for that API.
 api=m.get('bridge024_qualification_api_ref');owner=m.get('bridge024_owner_ref')
 need(api is not None and owner is not None,'actual024 bridge gate/source still missing; no weight load')
 need(m.get('prepared_only')is False,'actual completed binding, not template')
 source=obj(m['bridge024_source_ref'])
 need(source['files']['qualification.py']==api,'source-bound actual024 API')
 p=obj_file(api);sys.path.insert(0,str(p.parent));s=importlib.util.spec_from_file_location('_dl025_actual024_gate',p);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
 result=g.consume(owner)
 need(result['source']==m['bridge024_source_ref']and result['library']==m['library_ref']and result['actual_NPU']is True and result['independent_pass']is True and result['dead_zero_partial_live_pass']is True and result['mixed_B1_B16_pass']is True and result['slot_reuse_pass']is True and result['model_ready']is False,'actual numeric bridge/lifecycle, not a sample or eventcount')
 return result
def transitive_refs(m):
 """Exact lightweight reader closure, not full historical raw mounts."""
 refs=[m['plugin_source'],m['composite_source_ref'],m['composite_cpu_owner_ref'],m['bridge024_source_ref']]
 plugin=obj(m['plugin_source']);composite=obj(m['composite_source_ref']);bridge=obj(m['bridge024_source_ref'])
 refs.extend(plugin['files'].values());refs.extend(composite['files'].values());refs.extend(bridge['files'].values())
 owner=obj(m['composite_cpu_owner_ref']);refs.append(owner['result']);stage=obj(owner['result']);refs.append(stage['certificate'])
 cert=obj(stage['certificate']);refs.extend([cert['component_source'],plugin['production_build_ref'],plugin['library_ref']])
 if m.get('admission_mode')=='actual052-split-scale-diagnostic-only':
  import domain_qualification as D
  refs.extend(D.closure(m))
 else:refs.extend([m['bridge024_owner_ref'],obj(m['bridge024_owner_ref'])['independent_consumer']])
 return refs
def environment(E,o,sr,base,source,output,run,*,stage='model'):
 m=current(sr);e=o.environment_original(base,source,output,run)
 need(stage in('parser','model'),'explicit parser-vs-weightload phase')
 if stage=='model':model_gate(m)
 e.update(MST_MXR_CAPTURE_ENABLE='0',MST_MXR_SOLVE_ENABLE='0',MXR_DIAG16_GDN_SHADOW_ENABLE='0',MXR_OBSERVERLESS_ENABLE='0',MXR_ONCE_CORRECTNESS_ENABLE='0',QWEN36_DELTALOG_ENABLE='0',QWEN36_DELTALOG_MIXED_ENABLE='0',QWEN36_DELTALOG_FRESH_ENABLE='0',QWEN36_DELTALOG_SERVICE003_ENABLE='0',QWEN36_DELTALOG_SERVICE023_ENABLE='1',QWEN36_DELTALOG_SERVICE023_MODE='diagnostic-bridge-only',QWEN36_DELTALOG_SERVICE023_SOURCE_REF=json.dumps(m['plugin_source']),QWEN36_DELTALOG_SERVICE023_COMPOSITE_SOURCE_REF=json.dumps(m['composite_source_ref']),QWEN36_DELTALOG_SERVICE023_AUDIT=str(output),QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE='1',QWEN36_DELTALOG_TRACE025_ENABLE='1',QWEN36_DELTALOG_TRACE025_SOURCE_REF=json.dumps(sr))
 # Trace025 explicitly registers023 once and then observes its final forward.
 # Listing both service023 and trace025 would double-install the same provider.
 e['VLLM_PLUGINS']='ascend,mxr_native_worker_receipt,deltalog_service025_trace'
 e['QWEN36_DELTALOG_TENSOR026_ENABLE']='0'
 e['QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE']='0'
 e['QWEN36_DELTALOG_SERVICE023_ENABLE']='0'
 e['DL101R12_NATIVE_OBSERVATION_ENABLE']='1'
 e['DL101R12_SOURCE_REF']=json.dumps(sr)
 e['PYTHONPATH']=str(HERE)+':'+str(Path(m['plugin_source']['path']).parent)+':'+str(E.WORKER)+':'+e.get('PYTHONPATH','')
 return e
def configure(E):
 E.current=current
 E.environment=lambda o,sr,*a:environment(E,o,sr,*a)
 return E
