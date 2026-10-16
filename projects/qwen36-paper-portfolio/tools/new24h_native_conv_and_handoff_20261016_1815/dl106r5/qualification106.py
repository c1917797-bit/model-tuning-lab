"""Source-bound real component + real model/lifecycle -> bounded execution."""
import hashlib,importlib.util,json,math,time,types
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODEL_TEMPLATE={'path': '/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-real-worker-new24h-v1-101-repair5/SOURCE_TEMPLATE.json', 'bytes': 205705, 'sha256': 'd657d8e9140f765d402b0619fd9d9589c8ed0479b9c860a1cf5400710b510a8d'}
START,CUT=1792134133,1792220533
def need(v,s):
 if not v:raise ValueError(s)
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'exact Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary actual source')
 h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):size+=len(b);h.update(b)
 need((size,h.hexdigest())==(r['bytes'],r['sha256']),'exact immutable byte identity');return p
obj_file=checked
def obj(r):return json.loads(checked(r).read_bytes())
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(r,n):
 s=importlib.util.spec_from_file_location(n,checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def source(sr):
 m=obj(sr);need(m['schema']=='deltalog.production-source/v106'and m['root']==str(ROOT)and m['prepared_only']is False and m['default_enabled']is False,'bound actual106 source, not prepared template')
 need(m['window']==dict(start=START,cutoff=CUT)and START<=time.time()<CUT,'actual fixed24h authority')
 for r in m['files'].values():checked(r)
 checked(m['authority_ref']);return m
def model_gate(m):
 msr=m['model_source_ref'];model=obj(msr);t=obj(MODEL_TEMPLATE)
 need(model['prepared_template']==MODEL_TEMPLATE and model['prepared_only']is False and model['files']==t['files']and model['root']==t['root'],'actual reviewed101 bound whole source')
 need(model['library_ref']==m['library_ref']and model['bridge024_source_ref']==m['component_source_ref']and model['bridge024_owner_ref']==m['component_owner_ref'],'same051 library/component model provenance')
 for r in model['files'].values():checked(r)
 ps=obj(model['plugin_source']);pt=obj(model['plugin_template_ref']);need(ps['prepared_template']==model['plugin_template_ref']and ps['files']==pt['files']and ps['prepared_only']is False,'exact real101 runtime files')
 qr=model['split_qualification_api_ref'];need(qr==ps['files']['qwen36_deltalog_service/split_qualification.py'],'source-bound101 typed088 reader')
 Q=load(qr,'_106_actual101_component');component=Q.admit(types.SimpleNamespace(need=need,obj=obj,obj_file=checked),model)
 need(component['schema']=='deltalog.eager-component-to-model-diagnostic/v101'and component['diagnostic_smoke_admitted']is True and component['source']==m['component_source_ref']and component['owner']==m['component_owner_ref'],'actual independent088 full160, not template')
 owner=obj(m['model_owner_ref']);need(owner['schema']=='deltalog.actual-owned-dispatch-smoke/v025'and owner['source']==msr and owner['component_owner']==m['component_owner_ref'],'actual101 owned model source join')
 need(owner['primary']is None and owner['secondary']==[]and owner['all_created_containers_release_verified']is True and owner['status']=='actual-DL-smoke-only','real successful model and all releases')
 need(len(owner['owned_containers'])>=3 and all(v['exact_owned_release_verified']is True for v in owner['owned_containers']if v['cid']),'all actual model/CPU containers released')
 cr=owner['independent_smoke_consumer'];c=obj(cr)
 need(c['schema']=='deltalog.model-selected-tensor-independent-consumption/v026'and c['source']==msr and c['actual_loaded_workers']==owner['actual_loaded_workers']and c['actual_client']==owner['client'],'actual independent model joins')
 need(c['smoke_dispatch_and_response_pass']is True and c['selected_modified_decode_pass']is True and c['actual_slot_reuse_observed']is True,'real model numeric + second request slotreuse')
 need([r['prompt_tokens']for r in c['responses']]==[2048,2048]and all(r['output_tokens']==10 and r['finish']=='length'for r in c['responses']),'both real2K and9decode trajectories')
 dp=c['dispatch'];need(dp['dispatch_trajectory_pass']is True and dp['capacity7_merge_reachable']is True and {r['rank']for r in dp['rows']}=={0,1,2,3}and all(r['all48']is True and len(r['requests'])==2 and all(v['prefill']is True and v['decode']>=9 for v in r['requests'].values())for r in dp['rows']),'all4x48 original dispatch')
 assigned=c['actual_assignments'];ids={r['engine_id']for r in assigned};need(len(assigned)==len(ids)==2,'two actual assigned request identities')
 retired=c['actual_retirement'];need(len(retired)==2 and {r['engine_id']for r in retired}==ids and all(r['all4_actual_retirement_pass']is True and r['error']is None for r in retired),'both requests all4 real worker retirement, not inferred IDs')
 tr=c['selected_tensor_ref'];tensor=obj(tr);TC=load(model['files']['tensor_consumer.py'],'_106_actual101_tensor_contract')
 need(tensor['schema']=='deltalog.selected-model-tensor-diagnostic/v026'and tensor['source']==msr and tensor['primary']is None and tensor['modified_decode_arithmetic_pass']is True and tensor['validation_contract']==TC.VALIDATION_CONTRACT==c['validation_contract'],'unchanged actual independent tensor math/thresholds')
 need(tensor['actual_second_request_slot_reuse_observed']is True and len(tensor['selections'])==4 and {v['rank']for v in tensor['selections']}=={0,1,2,3},'actual selected all4 layer instances')
 selected=tensor['selections'][0]['selected'];need(len(selected)==3 and all(v['selected']==selected and len(v['all48'])==48 for v in tensor['selections']),'same first/middle/last actual48 prefixes')
 rows=tensor['records'];need(len(rows)==240 and all(v['independent']['passed']is True for v in rows),'all4x3x2x(prefill+9decode) original numeric rows')
 for rank in range(4):
  for prefix in selected:
   for rid in ids:
    rs=[v for v in rows if v['identity']['rank']==rank and v['identity']['prefix']==prefix and v['identity']['engine_request_id']==rid]
    need([v['identity']['kind']for v in rs]==['prefill']+['decode']*9,'exact original layer/request chronology')
    need([v['independent']['length_before']for v in rs[1:]]==list(range(8))+[0]and [v['independent']['length_after']for v in rs[1:]]==list(range(1,8))+[0,1],'actual merge and nextappend')
 return dict(model_source=msr,model_owner=m['model_owner_ref'],model_consumer=cr,model_tensor=tr,component=component,assigned_ids=sorted(ids),model_library=model['library_ref'])
def consume(sr):
 m=source(sr);proof=model_gate(m)
 return dict(schema='deltalog.production-execution-qualification/v106',source=sr,execution_admitted=True,production_library=m['library_ref'],component_source=m['component_source_ref'],component_owner=m['component_owner_ref'],model_source=m['model_source_ref'],model_owner=m['model_owner_ref'],model_consumer=proof['model_consumer'],model_tensor=proof['model_tensor'],proof=proof,actual_scope=dict(prefill_tokens=[2048],max_sequences=1,decode_tokens_per_sequence=1,TP=4,PCP=1,Hq=4,Hv=12,D=128,dtype='torch.bfloat16',graph=False,async_scheduling=False,prefix_caching=False,PDC=False),iteration_scope='component160 covers all append/merge phases; actual model9decodes+2requests; longer screen must retain terminal sticky-health and actual dispatch counts; not measured performance proof',observer_free=True,graph_qualified=False,performance_measured=False,task_scores_measured=False)
def qualify(qref,sr):
 q=obj(qref);need(q==consume(sr),'actual published qualification exactly recomputed; no future Boolean');return q
def readset(sr):
 m=source(sr);model=obj(m['model_source_ref']);o=obj(m['model_owner_ref']);c=obj(o['independent_smoke_consumer']);ps=obj(model['plugin_source'])
 refs=[sr,m['authority_ref'],MODEL_TEMPLATE,m['model_source_ref'],m['model_owner_ref'],o['independent_smoke_consumer'],o['actual_loaded_workers'],o['client'],c['selected_tensor_ref'],model['plugin_source'],model['plugin_template_ref'],*m['files'].values(),*model['files'].values(),*ps['files'].values()]
 # Source-bound101 qualification closure is explicit; never broad/cache mount.
 co=obj(model['bridge024_owner_ref']);p=obj(co['result']);r=obj(co['independent_consumer']);cpu=obj(model['component_cpu_owner_ref'])
 refs += [model['bridge024_source_ref'],model['bridge024_owner_ref'],model['reviewed_domain_template_ref'],model['component_cpu_owner_ref'],model['production_build_ref'],model['split_kernel_source_ref'],model['library_ref'],model['debug_library'],co['result'],co['independent_consumer'],p['plan'],cpu['result'],r['original_strict_consumer'],r['domain_consumer'],*r['initial_anchor_refs'].values()]
 refs+=list(obj(model['bridge024_source_ref'])['files'].values())
 out={json.dumps(v,sort_keys=True):v for v in refs};[checked(v)for v in out.values()];return list(out.values())
def environment(sr,qref,receipt_root,enabled):
 if not enabled:return dict(QWEN36_DELTALOG_PRODUCTION106_ENABLE='0')
 qualify(qref,sr)
 return dict(QWEN36_DELTALOG_PRODUCTION106_ENABLE='1',QWEN36_DELTALOG_PRODUCTION106_MODE='production-bounded',QWEN36_DELTALOG_PRODUCTION106_SOURCE_REF=json.dumps(sr),QWEN36_DELTALOG_PRODUCTION106_QUALIFICATION_REF=json.dumps(qref),QWEN36_DELTALOG_PRODUCTION106_RECEIPT_ROOT=str(receipt_root),QWEN36_DELTALOG_CPU_MIRROR018_REV2_ENABLE='1',VLLM_PLUGINS='ascend,mxr_native_worker_receipt,deltalog_production106',QWEN36_DELTALOG_SERVICE023_ENABLE='0',QWEN36_DELTALOG_TRACE025_ENABLE='',QWEN36_DELTALOG_TENSOR026_ENABLE='')
