"""Source-only bind of actual saved R3 producer; no NPU restart or old PASS."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import host as H,raw_closure043 as R
ROOT='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog043r3-sidecar-cpu-recovery-new48h-v1-001-repair3'
CPU_FAILURE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-dl043r3-savedraw-cpu-new48h-MAIN-20261015-001-repair2/RESULT.json',bytes=1189,sha256='9c078651e3c29ccbf72d171b68e107adf64ca9fa01dd52ff20689b2ca815085a')
OLD_STRICT=dict(path=str(Path(CPU_FAILURE['path']).parent/'native/result/ORIGINAL_INDEPENDENT.json'),bytes=3639,sha256='f8fe4b5f639f4fc67893fe57c6d0efaa5cee7f8dbc1dc3080e83dff0411558e0')
OLD=Path('/opt/host/vnf/austinov/deltalog-mixed-precast-new48h-043-repair3/run-numeric16-MAIN-20261015-001')
PRODUCER=dict(path=str(OLD/'numeric/result/RESULT.json'),bytes=55236,sha256='1612b5aa68a87517972971bec368d1a0659c25d69594d458209ddcaa82f2d894')
FROZEN={
 'RESULT.json':(1257,'43351493fcaec43dbdf5d2df08b257f953262e8fbdc4497d3aeca780b7e29f5a'),
 'numeric/cleanup-verdict.json':(246,'8b486b914a2e3ae6eaa8172a3932b355c225f9b1e6d94c3dae0f4cea395b6a44'),
 'numeric/result/STAGE_RESULT.json':(1082,'4aa05e18c89b3f41eefd9d48e7c87398c3499d6be20b13f729ece0c41cba3f20'),
 'protected-ownership-1792095231740436080.json':(34060,'3774f30ad6a6763c294e3d4eac4c07866d8286d730e8a2d3508b3302da3a167a'),
 'numeric/ACTUAL_OWNER.json':(2818,'5a87f4d887e8ba22d4e6b8535d0934044d92cdf736b4914cf82ac7aa20b32480'),
 'numeric/cleanup-before-inspect.json':(32661,'789511a3820fa4cbed507a5dc8def37e997217b38c19b86f8e551ff0e0fdd82f'),
 'numeric/cleanup-after-inspect.json':(32661,'a694db9a0981b66936f0c92b83a2930d7751edc4a7ccb147045c2a95c03f3f81')}
def actual(name):
 size,sha=FROZEN[name];r=dict(path=str(OLD/name),bytes=size,sha256=sha);H.validate_ref_streamed(r);return r
RUNTIME_IDENTITIES={
 'module_file':dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py',bytes=16312,sha256='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'),
 'metadata_source':dict(path='/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py',bytes=40595,sha256='42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16')}
def runtime_identity(r,path):
 if len(path)<6 or path[:2]!=('captures','prefill')or type(path[2])is not int or path[3]!='native_call'or path[4]not in('before','after'):return False
 suffix=path[5:]
 key='module_file'if suffix==('module_file',)else'metadata_source'if suffix==('controls','metadata_source')else None
 if key is None:return False
 H.need(r==RUNTIME_IDENTITIES[key],'exact schema-bound original guest runtime source identity')
 return True
def validate_runtime_identities(identities,producer):
 mixed={r['raw']['path']:r['raw']for r in producer['records']if r['kind']=='mixed'}
 H.need(len(mixed)==32,'actual16 both batches unique mixed raws')
 expected={('captures','prefill',0,'native_call',phase,*suffix)for phase in('before','after')for suffix in(('module_file',),('controls','metadata_source'))}
 observed={p:set()for p in mixed}
 for item in identities:
  raw=item['raw_ref'];path=tuple(item['record_json_path'])
  H.need(raw['path']in mixed and raw==mixed[raw['path']]and runtime_identity(item['identity'],path),'row-specific source/identity path join')
  H.need(path not in observed[raw['path']],'no duplicate raw identity field')
  observed[raw['path']].add(path)
 H.need(all(paths==expected for paths in observed.values()),'each actual mixed raw has exact before/after chunk and builder identities')
 return True
def metadata_closure(refs,add,parent):
 identities=[]
 def walk(v,path=()):
  if type(v)is dict:
   if set(v)=={'path','bytes','sha256'}:
    if runtime_identity(v,path):identities.append(dict(record_json_path=list(path),identity=v))
    else:add(v)
   else:
    for k,x in v.items():walk(x,path+(k,))
  elif type(v)is list:
   for k,x in enumerate(v):walk(x,path+(k,))
 done=set()
 while True:
  pending=[r for r in refs.values()if r['path']not in done and Path(r['path']).suffix=='.pt'and Path(r['path']).parent==parent]
  if not pending:return identities
  for r in pending:
   done.add(r['path']);start=len(identities);walk(R.metadata(r,H.validate_ref_streamed))
   for item in identities[start:]:item['raw_ref']=r
   for blob in R.closure(r,H.validate_ref_streamed):add(blob)
def bind(template_ref):
 H.need(str(P)==ROOT,'actual MAIN-reviewed deployment root')
 template=H.obj(template_ref);H.need(template_ref['path']==str(P/'SOURCE_TEMPLATE.json')and template['root']==ROOT and template['prepared_only']is True,'exact reviewed recovery template')
 for r in template['files'].values():H.validate_ref_streamed(r)
 prod=H.obj(PRODUCER);sr=prod['source'];m=H.obj(sr)
 H.need(m['root']=='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-mixed-precast-new48h-v1-043-repair3','actual original R3 source')
 H.need(prod['primary']is None and prod['steps']==16 and len(prod['records'])==40 and len(prod['actual_sidecar_records'])==57 and prod['NPU']is True,'actual complete original16 producer; not a plan')
 failed=actual('RESULT.json');cleanup=actual('numeric/cleanup-verdict.json');stage=actual('numeric/result/STAGE_RESULT.json');v=H.obj(stage)
 H.need(v['actual_result']==PRODUCER and v['producer_exit']==0 and v['observation_complete']is True,'actual stopped producer stage')
 refs={}
 def add(r):H.validate_ref_streamed(r);H.need(r['path']not in refs or refs[r['path']]==r,'unique immutable Ref');refs[r['path']]=r
 for r in[sr,PRODUCER,failed,cleanup,stage,*m['files'].values()]:add(r)
 evidence=dict(verdict=actual('protected-ownership-1792095231740436080.json'),arm=actual('numeric/ACTUAL_OWNER.json'),before=actual('numeric/cleanup-before-inspect.json'),after=actual('numeric/cleanup-after-inspect.json'))
 for r in evidence.values():add(r)
 cf=H.obj(CPU_FAILURE);strict=H.obj(OLD_STRICT)
 H.need(cf['schema']=='deltalog.fresh-bridge-owned-host/v5'and cf['primary']is not None and cf['result']is None and cf['stopped_retained']is True and cf['NPU']is False,'actual0928 CPU failure preserved, never success')
 H.need(strict['schema']=='deltalog.fresh-bridge-consumption/v5'and strict['source']==sr and strict['producer']==PRODUCER and strict['pass_gate']is False,'actual old strict FAIL preserved')
 add(CPU_FAILURE);add(OLD_STRICT)
 child_path=Path(CPU_FAILURE['path']).parent/'native/result/CHILD-02-domain_entry.json'
 child_failure=H.ref(child_path);add(child_failure)
 import provenance
 provenance.validate(H.obj(failed),prod,v,H.obj(cleanup),*[H.obj(evidence[k])for k in('verdict','arm','before','after')],sr,PRODUCER)
 raws=[r['raw']for r in prod['records']]+prod['actual_sidecar_records']
 # Extra initial anchors and source/original CPU Meta refs are walked from the
 # actual report/source recursively; only typed Ref3 objects are treated as refs.
 def walk(v):
  if type(v)is dict:
   if set(v)=={'path','bytes','sha256'}:add(v)
   else:
    for x in v.values():walk(x)
  elif type(v)is list:
   for x in v:walk(x)
 walk(prod);walk(m)
 runtime_identities=metadata_closure(refs,add,OLD/'numeric/result')
 validate_runtime_identities(runtime_identities,prod)
 own=template['files'];add(template_ref)
 result=dict(m,root=ROOT,files=own,original_source_ref=sr,original_producer_ref=PRODUCER,original_failed_owner_ref=failed,original_CPU_failure_ref=CPU_FAILURE,original_strict_failure_ref=OLD_STRICT,original_domain_child_failure_ref=child_failure,original_cleanup_ref=cleanup,original_stage_ref=stage,original_exit_evidence=evidence,recovery_refs=list(refs.values()),guest_runtime_identity_evidence=runtime_identities,recovery_scope='CPU-only57 original sidecar predicates; old NPU host and0928 CPU failures retained',default_enabled=False,model_ready=False,performance_ready=False)
 H.write(P/'SOURCE_MANIFEST.json',result);print(json.dumps(H.ref(P/'SOURCE_MANIFEST.json')))
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--template-ref',required=True);a=p.parse_args()
 if not a.execute:print('disabled');return
 bind(json.loads(a.template_ref))
if __name__=='__main__':main()
