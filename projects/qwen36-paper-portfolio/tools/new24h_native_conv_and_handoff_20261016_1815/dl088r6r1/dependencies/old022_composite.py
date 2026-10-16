"""Source-aware composite evidence reader. Missing actual guard evidence rejects."""
import hashlib,importlib.util,json,math,time
from pathlib import Path
MISSING=('sidecar_redzones','pointers_before','pointers_after','debug_pointers_before','debug_pointers_after')
REGRESSION_ALLOWED_FALSE={'regression_redzones_present','regression_pointers_present'}
B010='298749129c8586ecea56cb6076c435631b6fbef4b4e7757636ff87a4ec09abf7'
LEGACY017='1c47fcfd510da06d5b0c5ceacf21601163604c5c1a64e98759096a230cd4f478'
TEMPLATE016='70059cbc540b9faf0ee40b0bf29f23232712022d9e44dfd51c8676598f5c2915'
AUTHORITY='71211e77fc870a8c94a7f80424925e38e1e092b9374d3a6a1066960ea74fbf99'
OLD_PRIMARY="independent consumer ValueError('actual GE child failed; preserved logs/raw')"
REGRESSION_CHECKS={'shape_dtype','inactive','append_base','length_padding','decay_padding','lambda_padding','original_before','original_after','debug_after','inputs',*REGRESSION_ALLOWED_FALSE}
COMMON_CHECKS={'shape_dtype','inactive','append_base','length_padding','decay_padding','lambda_padding','debug_shape_dtype','debug_inactive','debug_append_base','debug_length_padding','debug_decay_padding','debug_lambda_padding','continuity','debug_before','debug_after','inputs','sequence','guards','pointers'}
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and r['bytes']>0,'exact positive Ref3')
 p=Path(r['path']);need(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'absolute ordinary artifact');b=p.read_bytes()
 need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'immutable whole bytes');return b
class Reader:
 def __init__(self):self.refs=[]
 def bytes(self,r):
  b=checked(r);self.refs.append(r);return b
 def __call__(self,r):return json.loads(self.bytes(r))
def strict019(audit):
 need(audit['schema']=='deltalog.raw-bitwise-audit/v019'and audit['complete']is True and audit['expected']==325 and audit['strict_pass']is False and audit['NPU']is False and audit['qualification']is False,'honest actual019 strictFALSE')
 expected=[(p,b,i)for p,b,n in(('smoke',16,4),('full',1,160),('full',16,160))for i in range(n)]
 need([(r['phase'],r['batch'],r['step'])for r in audit['records']]==expected,'all324 exact ordered strict coverage')
 for r in audit['records']:
  need(r['passed']is True and COMMON_CHECKS<=set(r['checks'])and all(v is True for v in r['checks'].values()),'any324 false/missing check rejects')
  if r['step']==0:need(r['checks'].get('initial_recipe')is True,'initial recipe required')
 rg=audit['regression'];need(rg['passed']is False and rg['missing']==list(MISSING),'only five exact unrecorded137 fields')
 failed={k for k,v in rg['checks'].items()if v is not True}
 need(set(rg['checks'])==REGRESSION_CHECKS and failed==REGRESSION_ALLOWED_FALSE and all(type(v)is bool for v in rg['checks'].values()),'no other regression false/missing tolerated')
 return rg
def terminal(v,source,stage,*,cpu,physical=None):
 need(v['source']==v['target_source']==source and v['stage']==stage and v['primary']is None and v['secondary']==[] and v['stopped_retained']is True and v['resource_admitted']is True and v['NPU']is(not cpu) and v['physical']==([]if cpu else physical) and v['authority']['sha256']==AUTHORITY,'actual terminal/release/source/device scope')
def exact_meta_chain(read,m16,cpu_owner_ref):
 cpu=read(cpu_owner_ref);terminal(cpu,m16,'cpu',cpu=True)
 need(cpu['schema']=='deltalog.lifecycle-actual-owned-host/v007','actual016 CPU owner')
 cp=read(cpu['result']);need(cp['schema']=='deltalog.lifecycle-CPU-preflight/v007'and cp['source']==m16 and cp['pass_gate']is True and cp['NPU']is False and cp['CPU_FP64_oracle_tests_passed']is True,'actual016 CPU/Meta')
 dm=read(cp['debug_meta_ref']);need(dm['source']==m16 and dm['pass_gate']is True and dm['NPU']is False,'actualsame-source debugMeta')
 return cpu,cp,dm
def allowed_old_failure(v,policy):
 # Exact observed failure is frozen only after actual error evidence is supplied.
 expected=policy.get('original002_exact_primary')
 need(expected==OLD_PRIMARY and policy.get('original002_error_evidence_ref')is not None,'actual precise failure policy still missing; failclosed')
 need(v['schema']=='deltalog.lifecycle-actual-owned-host/v007'and v['primary']==expected and v['secondary']==[]and v['stopped_retained']is True and v['resource_admitted']is True and v['NPU']is True and v['physical']==[5]and v['stage']=='numeric'and v['independent_consumer']is None and v['lifecycle_gate_pass']is False and v['authority']['sha256']==AUTHORITY,'only exact old consumer mount failure, never arbitrary primary')
def cause(error,policy):
 # A successful docker-logs read is NOT a successful consumer.
 need(error['exit_code']==0 and error['stdout']==''and error['requested_argv']==['/usr/bin/docker','logs','--timestamps','--tail','10000','740729aa8fb73bae65ea09c5c738eeb6a3041e63bd9a4afadaf121d11240877f'],'exact original consumer container logs')
 lines=error['stderr'].splitlines();last=lines[-1].split(' ',1)[-1]
 expected="FileNotFoundError: [Errno 2] No such file or directory: '"+policy['original_cpu_stage_ref']['path']+"'"
 need(last==expected and any('consumer.py' in x and 'line 51' in x for x in lines)and any("cpu_ref=C.obj(v['plan'])['cpu_preflight']"in x for x in lines),'only exact post-NPU consumer missing Meta mount traceback')
def samebytes(torch,a,b):
 return a.dtype==b.dtype and a.shape==b.shape and torch.equal(a.contiguous().view(torch.uint8),b.contiguous().view(torch.uint8))
def join_raw(torch,read,old_ref,new_ref,origin_ref):
 # Reopen both producer raws; do not trust a JSON 'joined' assertion.
 import io
 old=torch.load(io.BytesIO(read.bytes(old_ref)),map_location='cpu',weights_only=True);new=torch.load(io.BytesIO(read.bytes(new_ref)),map_location='cpu',weights_only=True);origin=torch.load(io.BytesIO(read.bytes(origin_ref)),map_location='cpu',weights_only=True)
 need(old['original_raw']==new['original_raw']==origin_ref and origin['event']['step']==137,'same original137 raw lineage')
 def tensor(r):return torch.load(io.BytesIO(read.bytes(r)),map_location='cpu',weights_only=True)
 for name in ('candidate_output','debug_output','actual_precast_FP32'):
  need(samebytes(torch,old[name],new[name]),'same016-020 actual output/precast bytes '+name)
 need(samebytes(torch,new['candidate_output'],origin['candidate_output']),'same original013 output bytes')
 for group in ('before','after','debug_after'):
  need(set(old[group])==set(new[group]),'same state inventory')
  for k in old[group]:need(samebytes(torch,tensor(old[group][k]),tensor(new[group][k])),'same016-020 fullstate bytes '+group+'/'+k)
 for group in ('before','after'):
  for k in origin[group]:need(samebytes(torch,tensor(new[group][k]),tensor(origin[group][k])),'sameoriginal fullstate bytes')
 need(set(old['inputs_after'])==set(new['inputs_after'])==set(origin['inputs']),'complete actual inputs')
 for k,v in origin['inputs'].items():need(samebytes(torch,old['inputs_after'][k],v)and samebytes(torch,new['inputs_after'][k],v),'sameoriginal input bytes')
 need(samebytes(torch,new['sequence_after'],origin['sequence']),'actual original sequence')
 return dict(actual_tensor_join=True,original_raw=origin_ref,old_guardless_raw=old_ref,new_guarded_raw=new_ref,model_qualified=False)
def release(read,policy):
 for role,cid in(('numeric','921fdb86da5bc17e9459ee75b3a1979ece5d7ed199953ce6c0143b8aa9b25f68'),('native','740729aa8fb73bae65ea09c5c738eeb6a3041e63bd9a4afadaf121d11240877f')):
  v=read(policy['original002_release'][role]);need(v==dict(cid=cid,errors=[],resource_release_verified=True,retained=True,rm_authorized=False,secondary_guard_cleanup=[],stopped=True,unresolved_active_cid=None),'actual original release, no error ignored')
def build_chain(read,m):
 for r in [*m['files'].values(),m['prepared_template'],m['kernel_source_ref'],m['debug_library'],m['debug_kernel_source_ref'],*m['libraries'].values()]:read.bytes(r)
 b=read(m['build_ref']);db=read(m['debug_build_ref'])
 need(b['schema']=='deltalog-key-projection-actual-build/v010'and b['primary']is None and b['source_manifest']==m['kernel_source_ref']and{x['arm']:x['library']for x in b['artifacts']}==m['libraries'],'actual production build/source/library')
 need(db['schema']=='deltalog-readout-sidecar-actual-build/v015'and db['primary']is None and db['source_manifest']==m['debug_kernel_source_ref']and len(db['artifacts'])==1 and db['artifacts'][0]['arm']=='readout_sidecar_v015'and db['artifacts'][0]['library']==m['debug_library'],'actual sidecar build/source/library')
 need(m['debug_kernel_source_ref']['sha256']==m['expected015_kernel_source']['sha256']and m['debug_kernel_source_ref']['bytes']==m['expected015_kernel_source']['bytes'],'reviewed exact015 source')
def consume_policy(policy,read,torch):
 # 'policy' is to be frozen with actual019/020 terminal refs; unknowns reject.
 for k in ('owner019','owner020','original002_owner','CPU016_owner','error_evidence','legacy017_admission'):
  need(policy.get(k)is not None,'missing actual evidence '+k)
 old=read(policy['original002_owner']);allowed_old_failure(old,policy);error=read(policy['error_evidence'])
 need(policy['error_evidence']==policy['original002_error_evidence_ref'],'exact observed cause artifact');cause(error,policy);release(read,policy)
 own19=read(policy['owner019']);s19=own19['source'];terminal(own19,s19,'cpu',cpu=True)
 need(own19['schema']=='deltalog.readout-diagnostic-owned-host/v005'and own19['diagnostic_complete']is True,'actual019 CPU owner')
 st19=read(own19['result']);need(st19['schema']=='deltalog.raw-bitwise-audit-CPU/v019'and st19['source']==s19 and st19['NPU']is False and st19['pass_gate']is True and st19['audit_complete']is True and st19['strict_pass']is False and st19['original016_numerical_pass']is True and st19['old002_failure_unchanged']is True,'actual019 stage, never pretend strictPASS')
 m19=read(s19);s16=m19['actual016_source_ref'];m16=read(s16)
 need(s19==policy['source019']and own19['result']==policy['stage019']and old['source']==policy['source016']and st19['audit']==policy['audit019']and st19['original016_independent_consumer']==policy['numeric019'],'reviewed actual019/016 exact identities')
 need(m16['prepared_template']['sha256']==TEMPLATE016 and old['source']==old['target_source']==s16 and old['result']==m19['actual_stage_ref'],'exact old016 source/stage, no donor PASS')
 need(m16['libraries']['key_projection']['sha256']==B010,'actual production B010')
 template16=read(m16['prepared_template']);need(m16==dict(template16,prepared_template=m16['prepared_template'],debug_build_ref=m16['debug_build_ref'],debug_kernel_source_ref=m16['debug_kernel_source_ref'],debug_library=m16['debug_library']),'only original016 binder fields differ');build_chain(read,m16)
 stage=read(m19['actual_stage_ref']);producer=read(stage['actual_result']);need(stage['source']==producer['source']==s16 and stage['NPU']is True and stage['producer_exit']==0 and producer['primary']is None and producer['NPU']is True and m19['actual_producer_ref']==stage['actual_result'],'successful actual016 NPU stage and producer')
 audit=read(st19['audit']);rg=strict019(audit);need(audit['source']==s19 and audit['actual_producer']==stage['actual_result']and rg['raw']==producer['regression']['raw'],'same019 strict raw source')
 need([r['raw']for r in audit['records']]==[r['raw']for r in producer['rows']],'strict all324 same real raw frames')
 cv=read(st19['original016_independent_consumer']);need(cv['source']==s16 and cv['actual_result']==m19['actual_stage_ref']and cv['raw_producer']==stage['actual_result'],'same recovered numeric reader')
 # Reuse original017 exhaustive325 numerical predicate, not recreated thresholds.
 need(policy['legacy017_admission']['sha256']==LEGACY017,'reviewed existing exhaustive325 numerical predicate')
 spec=importlib.util.spec_from_file_location('_frozen017_numerical_evidence',policy['legacy017_admission']['path']);A=importlib.util.module_from_spec(spec);exec(compile(read.bytes(policy['legacy017_admission']),spec.origin,'exec'),A.__dict__);A.evidence(cv,m16['validation_contract'])
 cpu,cp,dm=exact_meta_chain(read,s16,policy['CPU016_owner'])
 need(cpu['result']==cv['actual_cpu_preflight_ref']==m19['original_cpu_preflight_ref']==policy['original_cpu_stage_ref']and cp['debug_meta_ref']==cv['actual_debug_meta_ref']==m19['original_debug_meta_ref']and cp['source']==dm['source']==s16,'CPU Meta chain exact')
 reg=cp['actual_new_library_registration'];need(len(reg)==1 and reg[0]['library']==m16['libraries']['key_projection']and reg[0]['Meta']is reg[0]['PrivateUse1']is True,'actual production Meta/registration');op_schema=reg[0]['schema']
 need(dm['schema']=='deltalog.actual-debug-Meta/v016'and dm['debug_build']==m16['debug_build_ref']and dm['library']==m16['debug_library']and dm['dtype']=='torch.bfloat16'and dm['shape']==[16,12,128],'exact actual sidecar Meta')
 expectedmap=[dict(arm='key_projection',library=m16['libraries']['key_projection'],schema=op_schema),dict(arm='debug',library=m16['debug_library'],schema=dm['actual_schema'])]
 need(producer['mapped']==expectedmap,'actual original016 mapped production/debug')
 own20=read(policy['owner020']);s20=own20['source'];terminal(own20,s20,'numeric',cpu=False,physical=policy['guard_physical'])
 need(own20['schema']=='deltalog.lifecycle-actual-owned-host/v007'and own20['lifecycle_gate_pass']is True,'actual020 terminal independent pass')
 m20=read(s20);need(s20==policy['guard_source']and m20['prepared_template']==policy['guard_template']and m20['actual016_source_ref']==s16 and m20['regression_only']is True,'actual reviewed guard source binding')
 t20=read(policy['guard_template']);need(m20==dict(t20,prepared_template=policy['guard_template'],actual016_source_ref=s16,debug_build_ref=m16['debug_build_ref'],debug_kernel_source_ref=m16['debug_kernel_source_ref'],debug_library=m16['debug_library']),'only reviewed guard binder fields differ');build_chain(read,m20)
 for k in ('libraries','kernel_source_ref','debug_library','debug_build_ref','debug_kernel_source_ref','regression_refs'):
  need(m20[k]==m16[k],'unchanged exact production/debug/math/raw binding '+k)
 stage20=read(own20['result']);prod20=read(stage20['actual_result']);c20=read(own20['independent_consumer'])
 need(stage20['schema']=='deltalog.lifecycle-actual-stage/v007'and stage20['source']==prod20['source']==c20['source']==s20 and stage20['NPU']is True and stage20['observation_complete']is True and stage20['producer_exit']==0 and prod20['primary']is None and prod20['scope']=='single-original137-guard-v020'and prod20['rows']==[] and prod20['mapped']==expectedmap and c20['schema']=='deltalog.independent-lifecycle-consumption/v007'and c20['scope']=='single-original137-guard-v020'and c20['actual_result']==own20['result']and c20['raw_producer']==stage20['actual_result']and c20['expected_records']==len(c20['records'])==1 and c20['pass_gate']is True and c20['observation_complete']is True and c20['NPU']is False,'exact actual guard single-frame consumer')
 r20=c20['records'][0]
 # No arbitrary true dictionaries: require every check emitted by reviewed020.
 required={'before_exact_original','after_exact_original','prod_debug_state_bytes','prod_debug_output_bytes','output_exact_original','inputs_exact','sequence_exact','inactive_bytes','metadata_padding_bytes','slot_guards','side_redzones','all_pointers_stable','pointer_tensor_binding','side_view_binding'}
 need(set(r20['checks'])==required and all(v is True for v in r20['checks'].values())and r20['passed']is True,'complete reviewed020 memory evidence')
 need(c20['raw']==prod20['regression']['raw']and prod20['regression']['passed']is True,'same actual guarded raw')
 q=r20['precast'];need(q['passed']is True and q['finite']is True and q['cast_bitwise']is True and q['per_request_worst']is True and len(q['requests'])==16 and [r['request_row']for r in q['requests']]==list(range(16))and all(r['passed']is True and type(r['peak'])in(int,float)and math.isfinite(r['peak'])and 0<=r['peak']<=.00303 and type(r['relative_l2'])in(int,float)and math.isfinite(r['relative_l2'])and 0<=r['relative_l2']<=2**-13 for r in q['requests'])and type(r20['state_relative_l2'])in(int,float)and math.isfinite(r20['state_relative_l2'])and 0<=r20['state_relative_l2']<=7.92e-7,'unchanged independent per-request FP32/CPU64 and state gates')
 joined=join_raw(torch,read,rg['raw'],c20['raw'],r20['original_raw'])
 return dict(schema='deltalog.composite-component-qualification/v022',old002_owner=policy['original002_owner'],owner019=policy['owner019'],owner020=policy['owner020'],component_source=s16,library=m16['libraries']['key_projection'],operator_schema=op_schema,strict324=True,original_numeric325=True,strict137_join=joined,strict325_composed=True,original019_strict_pass=False,old002_failure_unchanged=True,model_ready=False,performance_ready=False,task_ready=False,graph=False,PDC=False,readset=read.refs)
def consume(composite_source_ref):
 """Run once in existing controlled Devices[] CPU stage, not inside timed workers."""
 read=Reader();m=read(composite_source_ref)
 need(m['schema']=='deltalog.composite-source/v022'and m['default_enabled']is False and m['prepared_only']is False and m['root']==str(Path(__file__).resolve().parent),'actual immutable bound022 source')
 selfpath=Path(__file__).resolve();selfbytes=selfpath.read_bytes();need(m['files']['composite.py']==dict(path=str(selfpath),bytes=len(selfbytes),sha256=hashlib.sha256(selfbytes).hexdigest()),'actual loaded composite helper source')
 need(m['window']==dict(start=1791962297,cutoff=1792135097)and 1791962297<=time.time()<1792135097,'unchanged authority window')
 for r in m['files'].values():read.bytes(r)
 need(not list(Path('/dev').glob('davinci*')),'Devices[] only composite raw reader')
 import torch
 torch.set_num_threads(1)
 need('torch_npu'not in __import__('sys').modules,'no torch_npu in composite CPU consumer')
 result=consume_policy(m['policy'],read,torch);result['source']=composite_source_ref;return result
def admit_receipt(composite_source_ref,composite_cpu_owner_ref):
 """Untimed startup: verify actual released CPU receipt, never import Torch."""
 read=Reader();m=read(composite_source_ref)
 need(m['schema']=='deltalog.composite-source/v022'and m['default_enabled']is False and m['prepared_only']is False and m['root']==str(Path(__file__).resolve().parent),'frozen defaultOFF composite source')
 need(m['window']==dict(start=1791962297,cutoff=1792135097)and 1791962297<=time.time()<1792135097,'same immutable runtime window')
 selfpath=Path(__file__).resolve();selfbytes=selfpath.read_bytes();need(m['files']['composite.py']==dict(path=str(selfpath),bytes=len(selfbytes),sha256=hashlib.sha256(selfbytes).hexdigest()),'actual loaded composite helper source')
 for r in m['files'].values():read.bytes(r)
 p=m['policy'];owner=read(composite_cpu_owner_ref);terminal(owner,composite_source_ref,'cpu',cpu=True)
 need(owner['schema']=='deltalog.readout-diagnostic-owned-host/v005'and owner['diagnostic_complete']is True and owner['diagnostic_only']is True and owner['model_ready']is False,'actual released composite CPU owner')
 stage=read(owner['result']);need(stage['schema']=='deltalog.composite-CPU/v022'and stage['source']==composite_source_ref and stage['authority']==owner['authority']==m['authority_ref']and stage['NPU']is False and stage['pass_gate']is True and stage['model_ready']is False,'actual source-bound composite CPU stage')
 controls=stage['software_controls'];need(controls['source']==m['files']['test_composite.py']and type(controls['discovered'])is int and controls['discovered']>0 and controls['executed']==controls['discovered']and controls['passed']is True,'actual source-bound complete software controls')
 cert=read(stage['certificate'])
 need(cert['schema']=='deltalog.composite-component-qualification/v022'and cert['source']==composite_source_ref and cert['owner019']==p['owner019']and cert['owner020']==p['owner020']and cert['old002_owner']==p['original002_owner']and cert['component_source']==p['source016']and cert['library']==m['library_ref']and cert['operator_schema']==m['operator_schema'],'actual certificate lineage/library/schema')
 need(cert['strict324']is cert['original_numeric325']is cert['strict325_composed']is True and cert['original019_strict_pass']is False and cert['old002_failure_unchanged']is True and cert['strict137_join']['actual_tensor_join']is True,'composed actual gate, no original false upgraded')
 need(all(cert[k]is False for k in('model_ready','performance_ready','task_ready','graph','PDC')),'component scope only')
 for r in (p['owner019'],p['owner020'],p['original002_owner'],p['CPU016_owner'],p['source016'],p['audit019'],p['numeric019'],p['error_evidence']):need(r in cert['readset'],'certificate consumed exact original proof '+r['path'])
 need(cert['strict137_join']['old_guardless_raw']==p['old137_raw']and cert['strict137_join']['original_raw']==p['original137_raw'],'frozen same137 raw lineage')
 read.bytes(m['library_ref']);need(m['library_ref']['sha256']==B010,'same actual production B010')
 return dict(cert,certificate_ref=stage['certificate'],CPU_owner=composite_cpu_owner_ref,CPU_stage=owner['result'])
