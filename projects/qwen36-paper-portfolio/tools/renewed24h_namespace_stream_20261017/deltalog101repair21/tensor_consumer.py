"""Independent CPU64 recurrence across real selected-layer model requests."""
import hashlib,importlib.util,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
DIRECT_SHA='60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d'
VALIDATION_CONTRACT=dict(schema='deltalog.actual-FP32-precast-per-request-empirical-model/v045',precast_peak=.00303,precast_relative_L2=2**-13,output_limit=.00303,state_limit=7.92e-7,per_request_worst=True,direct_round_sha256=DIRECT_SHA,uncast_metrics_diagnostic_only=True,BF16_point_metrics_diagnostic_only=True,scope='selected-model-native-prefill-boundary-nine-independent-decodes',model_inputs_unchanged=True,production_unchanged_split_scale051=True)
def need(v,s):
 if not v:raise ValueError(s)
def module():
 p=P/'dependencies/numeric_oracle.py';s=importlib.util.spec_from_file_location('_dl026_independent_scalar',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v

def direct_module():
 p=P/'dependencies/direct_round013.py';b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==DIRECT_SHA,'exact independent013 integer direct-RNE source')
 s=importlib.util.spec_from_file_location('_model036r1_direct_integer_RNE',p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v

def readout(torch,actual,expected):
 need(actual.shape==expected.shape==(12,128)and actual.dtype==torch.bfloat16 and expected.dtype==torch.float64,'actual BF16(12,128) and independent CPU64; no broadcast/cast acceptance')
 D=direct_module();error,diagnostic=D.peer_error(torch,actual,expected)
 return dict(output_error=error,uncast_CPU64_output_error=diagnostic['uncast_peak'],independent_CPU64_BF16_floor=diagnostic['rounding_floor_peak'],direct_RNE_diagnostic=diagnostic)
def metric(torch,a,b):
 a=a.double();b=b.double();return dict(state_relative_l2=float((a-b).norm()/max(float(b.norm()),1e-30)),output_normalized_max=float((a-b).abs().max()/max(float(b.abs().max()),1e-30)))
def normalize(torch,x):
 y=x.float();return(y*torch.rsqrt((y*y).sum(-1,keepdim=True)+1e-6)).to(x.dtype)

def actual_sidecar(torch,R,raw,expected,slot):
 import precast as P,sidecar_audit as A
 s=raw['sidecar_record'];A.audit(torch,R,P,s,numeric=False)
 b=s['before'];a=s['after'];ids=b[12].flatten().tolist()
 need(ids==[slot]and b[11].flatten().tolist()==[0,1],'actual full-arena selected slot and native sequence ABI')
 for index,name in enumerate(('query','key','value','g','beta')):need(P.bits(torch,b[index],raw['inputs'][name]),'actual sidecar input join '+name)
 for index,name in enumerate(('base','k_log','u_log','lambda_log','decay','length'),5):
  need(0<=slot<b[index].shape[0]and P.bits(torch,b[index][slot:slot+1],raw['before'][name])and P.bits(torch,a[index][slot:slot+1],raw['after'][name]),'actual arena-to-compact state join '+name)
  need(P.bits(torch,b[index][:slot],a[index][:slot])and P.bits(torch,b[index][slot+1:],a[index][slot+1:]),'all unselected arena bytes unchanged '+name)
 need(s['sidecar_guards_before'].shape==s['sidecar_guards_after'].shape==(256,)and s['sidecar_guards_before'].dtype==torch.float32 and bool((s['sidecar_guards_before']==13.).all()),'actual015 redzone seed and extent')
 need(P.bits(torch,s['production_output'],raw['output']),'actual selected model return and sidecar output bytes')
 n=int(b[10][slot,0,0])
 if n<7:need(P.bits(torch,b[5][slot],a[5][slot]),'append keeps actual base bytes including signed zeros')
 for index,start in((8,7),(9,1),(10,1)):
  need(P.bits(torch,b[index][slot,:,start:],a[index][slot,:,start:]),'actual selected metadata padding byte unchanged')
 y=s['actual_precast_FP32'];need(y.shape==(1,12,128)and y.dtype==torch.float32,'actual015 FP32 readout exact shape')
 pred=P.evaluate(torch,y,raw['output'],expected.unsqueeze(0))
 return pred
def prefill(torch,R,raw,previous):
 need(raw['actual_NPU']is True and len(raw['chunks'])==1 and len(raw['actual_ids'])==1,'real B1 one native prefill')
 cap=raw['chunks'][0];i=cap['inputs'];q,k,v,g,beta=[i[n]for n in('q','k','v','g','beta')];T=q.shape[1]
 need(q.shape==(1,T,4,128)and v.shape==(1,T,12,128)and i['cu_seqlens'].flatten().tolist()==[0,T]and i['use_qk_l2norm_in_kernel']is True,'real unpadded request inputs')
 need(i.get('scale')in(None,128**-.5),'actual native scale domain')
 init=i.get('initial_state')
 if raw['has_initial']==[False]:
  state=torch.zeros((12,128,128),dtype=torch.float64)
  need(init is None or bool((init==0).all()),'real fresh native prefill receives zero state')
 else:
  need(raw['has_initial']==[True]and previous is not None,'cannot use candidate-derived initial state as independent reference')
  state=previous.clone();need(init is not None and metric(torch,init[0].transpose(-1,-2),state)['state_relative_l2']<=R.STATE_LIMIT,'independent continuation state')
 q,k=normalize(torch,q),normalize(torch,k);outputs=[]
 for t in range(T):
  state,out=R.advance(torch,state,dict(query=q[0,t:t+1],key=k[0,t:t+1],value=v[0,t:t+1],g=g[0,t:t+1],beta=beta[0,t:t+1]),0);outputs.append(out)
 expected=torch.stack(outputs);actual=cap['output'].reshape(T,12,128)
 output_error=metric(torch,actual,expected)['output_normalized_max'];state_error=metric(torch,R.restore(torch,raw['after'],0),state)['state_relative_l2']
 need(torch.equal(raw['core_output'].reshape(-1,12,128)[:T],actual),'actual returned model core equals native chunk output')
 need(torch.equal(raw['after']['base'][0],cap['final_state'][0].transpose(-1,-2)),'actual arena checkpoint equals native chunk state')
 need(all(bool((raw['after'][n]==0).all())for n in('k_log','u_log','lambda_log','decay','length')),'real prefill/reset clears all deferred auxiliary state')
 # Actual native chunk has additional BF16 work-state/intermediate boundaries.
 # Unrounded FP64 is diagnostic here, NOT the recurrent FP32 acceptance domain.
 boundary=raw['after']['base'][0].double().clone()
 return boundary,dict(output_error=output_error,state_error=state_error,old_unrounded_threshold_pass=output_error<=R.OUTPUT_LIMIT and state_error<=R.STATE_LIMIT,passed=True,gate_scope='unchanged-native-boundary-copy/reset-only',native_prefill_numerically_qualified=False,CPU64_unrounded_diagnostic_only=True,tokens=T,actual_core_bitwise=True)
def decode(torch,R,raw,previous,expected_slot):
 need(previous is not None and raw['actual_NPU']is True and len(raw['actual_ids'])==1,'independent request state from real prefill')
 need(type(expected_slot)is int and expected_slot>=0 and raw['actual_ids']==[expected_slot]and type(raw['actual_ids'][0])is int,'actual prefill slot to compact0 decode join; no inferred slot')
 need(type(raw['scale'])in(int,float)and math.isclose(raw['scale'],128**-.5,rel_tol=0,abs_tol=1e-12),'fixed source scale128**-.5; not candidate-derived oracle scale')
 specifications=(('query',torch.bfloat16,(1,4,128)),('key',torch.bfloat16,(1,4,128)),('value',torch.bfloat16,(1,12,128)),('g',torch.float32,(1,12)),('beta',torch.bfloat16,(1,12)))
 need(set(raw['inputs'])=={n for n,_,_ in specifications}and all(t.device.type=='cpu'and t.dtype==dtype and t.shape==shape and bool(torch.isfinite(t).all())for n,dtype,shape in specifications for t in[raw['inputs'][n]]),'fixed source BF16/FP32 Hq4/Hv12/D128 input/finite contract')
 need(raw['output'].shape==(1,12,128)and raw['output'].dtype==torch.bfloat16,'actual BF16 output batch1 exact shape')
 need(raw['native_output'].shape==(1,12,128)and raw['native_output'].dtype==torch.bfloat16 and raw['native_after'].shape==(1,12,128,128)and bool(torch.isfinite(raw['native_output']).all()and torch.isfinite(raw['native_after']).all()),'actual native-peer shape/BF16/live finite before numeric max')
 before=R.restore(torch,raw['before'],0);before_error=metric(torch,before,previous)['state_relative_l2']
 need(bool(torch.isfinite(before).all()and torch.isfinite(previous).all()),'active restored-before and independent trajectory state finite; dead payload is not scanned')
 state,expected=R.advance(torch,previous,raw['inputs'],0,scale=128**-.5)
 state_error=metric(torch,R.restore(torch,raw['after'],0),state)['state_relative_l2'];rounded=readout(torch,raw['output'][0],expected);output_error=rounded['output_error']
 inv=R.invariant(torch,raw['before'],raw['after'],[0])
 need(all(inv.values()),'original append/length state invariants')
 need(raw['pointer_before']==raw['pointer_after']and all(torch.equal(v,raw['input_after'][n])for n,v in raw['inputs'].items()),'real source inputs/pointers unmutated')
 for n in('length','decay'):need(torch.equal(raw['before'][n][:,:,1:],raw['after'][n][:,:,1:]),'metadata padding unchanged')
 need(torch.equal(raw['before']['lambda_log'][:,:,7:],raw['after']['lambda_log'][:,:,7:]),'lambda padding unchanged')
 n=int(raw['before']['length'][0,0,0]);a=int(raw['after']['length'][0,0,0])
 native_state_error=metric(torch,R.restore(torch,raw['after'],0),raw['native_after'][0])['state_relative_l2'];native_output_error=metric(torch,raw['output'],raw['native_output'])['output_normalized_max']
 need(all(math.isfinite(x)and x>=0 for x in(state_error,before_error,native_state_error,native_output_error,output_error)),'all independent/before/native/output metrics finite before threshold max')
 pred=actual_sidecar(torch,R,raw,expected,expected_slot)
 return state,dict(**rounded,state_error=state_error,before_state_error=before_error,native_state_error=native_state_error,native_output_error=native_output_error,old_BF16_point_pass=max(output_error,native_output_error)<=R.OUTPUT_LIMIT,BF16_point_metrics_diagnostic_only=True,actual_precast=pred,passed=max(state_error,before_error,native_state_error)<=R.STATE_LIMIT and pred['passed'],length_before=n,length_after=a,invariants=inv)
def consume(audit,sr,trajectory,assigned_ids,output):
 import torch
 import raw_codec
 raw_codec.install(torch)
 torch.set_num_threads(1);R=module();roots=sorted((Path(audit)/'tensor026').glob('worker-*'));need(len(roots)==4,'actual four tensor workers')
 sb=Path(sr['path']).read_bytes();need(len(sb)==sr['bytes']and hashlib.sha256(sb).hexdigest()==sr['sha256'],'actual model source Ref');manifest=json.loads(sb)
 references={};records=[];selections=[];seen={};slots={};reused=False;primary=None
 try:
  for root in roots:
   selection=json.loads((root/'SELECTION.json').read_bytes());need(selection['source']==sr and len(selection['all48'])==48 and len(selection['selected'])==3,'same source actual layer selection')
   selections.append(selection);rank=selection['rank'];states={};request_slots={}
   for line in(root/'ROWS.jsonl').read_text().splitlines():
    row=json.loads(line);need(row['source']==sr and row['rank']==rank and row['pid']==selection['pid']and row['prefix']in selection['selected']and row['engine_request_id']in assigned_ids,'actual selected prefix/request/rank')
    need(any(t['rank']==rank and t['pid']==row['pid']and t['epoch']==row['epoch']and t['request_ids']==[row['engine_request_id']]for t in trajectory),'exact actual metadata/PID step join')
    r=row['raw'];b=Path(r['path']).read_bytes();need(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'immutable complete raw')
    raw=torch.load(Path(r['path']),map_location='cpu',weights_only=False);key=(row['prefix'],row['engine_request_id']);before=states.get(key)
    if row['kind']=='prefill':
     current,metrics=prefill(torch,R,raw,before);actual_slot=raw['actual_ids'][0];need(type(actual_slot)is int and actual_slot>=0,'actual prefill metadata slot');request_slots[key]=actual_slot;slot=(rank,row['prefix'],actual_slot);reused|=slot in slots and slots[slot]!=row['engine_request_id'];slots[slot]=row['engine_request_id']
    else:
     sc=raw['actual_sidecar045'];sp=Path(sc['path']);sbytes=sp.read_bytes();need(sp.parent==root and len(sbytes)==sc['bytes']and hashlib.sha256(sbytes).hexdigest()==sc['sha256'],'same owned worker immutable sidecar Ref')
     raw['sidecar_record']=torch.load(sp,map_location='cpu',weights_only=False);ss=raw['sidecar_record']
     need(ss['model_identity']=={k:row[k]for k in('source','prefix','layer_idx','pid','rank','epoch','engine_request_id')}and ss['production_library']==manifest['library_ref']and ss['debug_library']==manifest['debug_library'],'actual source/epoch/request/prefix and exact production/debug library join')
     current,metrics=decode(torch,R,raw,before,request_slots[key]);metrics['actual_sidecar_ref']=sc
    states[key]=current;seen.setdefault((rank,*key),[]).append((row['kind'],metrics));records.append(dict(identity=row,independent=metrics))
    need(metrics['passed'],'original per-request CPU64 tensor gate failed')
  need({s['rank']for s in selections}=={0,1,2,3},'four distinct actual ranks')
  need(all(s['selected']==selections[0]['selected']for s in selections),'same first/middle/last real GDN prefixes')
  for rank in range(4):
   for prefix in selections[0]['selected']:
    for request_id in assigned_ids:
     rows=seen[(rank,prefix,request_id)];need([x[0]for x in rows]==['prefill']+['decode']*9,'real prefill+9 decode checkpoints')
     need([x[1]['length_before']for x in rows[1:]]==list(range(8))+[0]and [x[1]['length_after']for x in rows[1:]]==list(range(1,8))+[0,1],'actual append0..6 merge7 and next append')
 except BaseException as e:primary=repr(e)
 result=dict(schema='deltalog.selected-model-tensor-diagnostic/v026',source=sr,validation_contract=VALIDATION_CONTRACT,records=records,selections=selections,primary=primary,modified_decode_arithmetic_pass=primary is None,tensor_arithmetic_pass=False,native_prefill_CPU64_diagnostic_only=True,actual_second_request_slot_reuse_observed=bool(reused),full48_tensor_qualified=False,model_numeric_qualified=False,performance_ready=False,graph=False,PDC=False,diagnostic_D2H=True)
 with Path(output).open('x')as f:json.dump(result,f,sort_keys=True);f.write('\n')
 return result
