"""Complete raw once-candidate GDN CPU reference, unchanged original metrics."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
ORIGINAL={'path':'/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-capture-20261013-001/consume_capture.py','bytes':10097,'sha256':'7c31e87b409ef095e5789a2bc1b71a987a69dc237789c125ad749a69fecec6c3'}
def need(v,s):
 if not v:raise ValueError(s)
def checked(r):
 p=Path(r['path']);need(type(r['bytes'])is int and 0<r['bytes']<=768*1024**2 and p.stat().st_size==r['bytes'],'bounded full raw Ref3');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'full raw source SHA');return b
def module(r,n):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);exec(compile(checked(r),r['path'],'exec'),m.__dict__);return m
def fingerprint(torch,t):
 b=t.contiguous().view(torch.uint8).numpy().tobytes();return dict(dtype=str(t.dtype),shape=list(t.shape),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def consume(worker,source,output,run_id):
 m=json.loads(checked(source));need(m['schema']=='mxr.diag16.full-gdn-frame-bridge-source/v1','new source, not061')
 from admission047 import consume as admit
 admit(m['new_prerequisites'])
 oracle=module(ORIGINAL,'_actual_original_FP64metrics')
 ref=module(m['files']['independent_block_reference.py'],'_independent_GDN_recurrence')
 boundary=module(m['files']['boundary_oracle.py'],'_047_independent_working_storage')
 import torch
 torch.set_num_threads(1)
 codec=module(m['files']['lossless_raw.py'],'_independent_shared_raw011')
 notes=[json.loads(p.read_text())for p in sorted(worker.glob('frame-*/FRAME.json'))]
 need(notes and len(notes)==48,'declared short48 or full longshape representative')
 binding_consumer=module(m['files']['binding_consumer.py'],'_long012_actual_target_binding_consumer')
 binding_consumer.consume(worker,source,notes,run_id,m['files']['worker.py'])
 first_install=json.loads((worker/'FIRST_CORE_INSTALL.json').read_bytes())
 need(first_install['schema']=='mxr.actual-first-core-install/v067'and first_install['source']==source and first_install['run_id']==run_id and first_install['before_first_actual_core']is True and first_install['actual_worker_install']is True and first_install['registry_registration_is_not_worker']is True,'actual first-core install receipt, not registry registration')
 native=first_install['official_operator'];need(native['qualified_name']=='_C_ascend::npu_recurrent_gated_delta_rule'and native['OpOverloadPacket']is True and native['schemas']and native['before_actual_first_core']is True,'official operator before actual model dispatch')
 associations=[json.loads(p.read_bytes())for p in worker.glob('core-binding-*.json')]
 need(any(a['prefix']==first_install['first_prefix']and a['instance_id']==first_install['first_instance_id']for a in associations),'actual first instance joins real48 bindings')
 runtime=json.loads((worker/'RUNTIME.json').read_bytes());need(runtime['source']==source and runtime['plugin_source']==m['plugin_source']and runtime['run_id']==run_id and runtime['mode']=='correctness'and first_install['pid']==runtime['pid'],'actual current runtime identity')
 rows=[]
 for n in notes:
  need(n['pid']==runtime['pid']and n['run_id']==run_id and n['source']==source and n['plugin_source']==m['plugin_source']and n['candidate_delta']==1 and n['graph']is False,'actual004 candidate once, not fallback/shadow')
  raw=n['raw'];checked(raw);payload=codec.read(torch,raw['path'])
  need(set(payload)=={'inputs','inputs_after','normalized_inputs','normalized_inputs_after','output','final_state','solve','FP32_policy','block044'},'complete actual once-pipeline payload')
  x=payload['inputs'];need(set(x)==set(payload['inputs_after']),'same actual input keys')
  for k,v in x.items():
   if torch.is_tensor(v):need(fingerprint(torch,v)==payload['inputs_after'][k],'unchanged entire input byte fingerprint '+k)
  nx=payload['normalized_inputs'];need(nx['already_normalized']is True,'actual post-native-normalizer boundary, no guessed epsilon')
  for k,v in nx.items():
   if torch.is_tensor(v):need(fingerprint(torch,v)==payload['normalized_inputs_after'][k],'whole normalized boundary unchanged '+k)
  expected,final=ref.recurrence(torch,nx);om=oracle.metrics(torch,payload['output'],expected);sm=oracle.metrics(torch,payload['final_state'],final)
  canonical=boundary.evaluate(torch,nx);workout=oracle.metrics(torch,payload['output'],canonical['output']);workstate=oracle.metrics(torch,payload['final_state'],canonical['state'])
  need(payload['FP32_policy']['allow_hf32']is False and payload['FP32_policy']['common_to_all_arms']is True,'registered commonHF32off')
  proof=payload['block044'];need(proof['source']==m['plugin_source']and proof['boundaries']==nx['cu_seqlens'].tolist()and proof['pool_bytes']==512*1024**2 and proof['pool_entries']==2,'actual044 source/geometry/pool')
  sv=payload['solve'];need(fingerprint(torch,sv['A'])==sv['A_after']and fingerprint(torch,sv['cu'])==sv['cu_after'],'whole solve original input immutability')
  e,res=oracle.fp64_reference(torch,sv['A'],sv['cu'].tolist());am=oracle.metrics(torch,sv['output'],e)
  T=x['q'].shape[1];cu=x['cu_seqlens'].tolist()
  need(T==2048 and cu==[0,2048],'exact short129 single request; no long qualification')
  physical_note=Path(raw['path']).parent/'PHYSICAL.json';physical_ref=json.loads(physical_note.read_bytes());checked(physical_ref);physical=torch.load(physical_ref['path'],map_location='cpu',weights_only=True)
  need(fingerprint(torch,physical['returned'].transpose(-1,-2).contiguous().to(physical['physical_after'].dtype))==fingerprint(torch,physical['physical_after']),'bitwise actual prefill returned state written to physical slots')
  for j,flag in enumerate(physical['prefill_has_initial_state'].tolist()):
   if not flag:need(torch.count_nonzero(x['initial_state'][j]).item()==0,'actual new/reused request initial state cleared')
  rows.append(dict(prefix=n['prefix'],stage=n['stage'],tokens=T,output=om,state=sm,solve=am,physical_state_ref=physical_ref,physical_indices=physical['indices'].tolist(),pass_gate=workout['pass']and workstate['pass']and am['pass'],working_output=workout,working_state=workstate,original_ideal_gate_pass=om['pass']and sm['pass']and am['pass'],reference_contract='mxr.independent-canonical-working-storage/v043',raw=raw))
 need(len(rows)==48 and len({r['prefix']for r in rows})==48 and {r['tokens']for r in rows}=={2048},'complete distinct48 short129')
 decode=[];groups={}
 from decode_coverage072 import check as decode_coverage
 decode_coverage([json.loads(p.read_bytes())for p in worker.glob('decode-*.json')],[r['prefix']for r in rows])
 for note in sorted(worker.glob('decode-*.json')):
  n=json.loads(note.read_bytes());need(n['source']==source and n['plugin_source']==m['plugin_source']and n['pid']==runtime['pid']and n['run_id']==run_id,'actual decode source/PID/run')
  checked(n['raw']);d=codec.read(torch,n['raw']['path']);lens=d['actual_seq_lengths'].tolist();cu=[0]
  need(lens[0]==0 and all(z>0 for z in lens[1:]),'actual builder per-sequence lengths')
  for length in lens[1:]:cu.append(cu[-1]+length)
  x=dict(q=d['query'].unsqueeze(0),k=d['key'].unsqueeze(0),v=d['value'].unsqueeze(0),g=d['g'].unsqueeze(0),beta=d['beta'].unsqueeze(0),scale=d['scale'],cu_seqlens=torch.tensor(cu),initial_state=d['initial_state'].transpose(-1,-2).contiguous(),already_normalized=True)
  e,s=ref.recurrence(torch,x);om=oracle.metrics(torch,d['output'].unsqueeze(0),e);sm=oracle.metrics(torch,d['final_state'].transpose(-1,-2).contiguous(),s)
  key=(n['prefill_tokens'],n['prefix']);groups.setdefault(key,[]).append((n,d))
  decode.append(dict(prefix=n['prefix'],prefill_tokens=n['prefill_tokens'],step=n['step'],output=om,state=sm,pass_gate=om['pass']and sm['pass'],raw=n['raw']))
 need(len(groups)==48 and len(decode)==432,'all48 both lengths, two actual native decode steps each')
 for key,values in groups.items():
  values.sort(key=lambda z:z[0]['step']);need([z[0]['step']for z in values]==list(range(9)),'exact two sequential decode steps')
  first=values[0][1];row=next(z for z in rows if(z['tokens'],z['prefix'])==key)
  physical=torch.load(row['physical_state_ref']['path'],map_location='cpu',weights_only=True)
  before={int(slot):v for slot,v in zip(physical['indices'].flatten().tolist(),physical['physical_after'])}
  for slot,v in zip(first['ssm_state_indices'].flatten().tolist(),first['initial_state']):need(int(slot)in before and fingerprint(torch,v)==fingerprint(torch,before[int(slot)]),'actual2K prefill→firstdecode same physical slot bytes')
  for(_,previous),(_,current)in zip(values,values[1:]):
   before={int(slot):v for slot,v in zip(previous['ssm_state_indices'].flatten().tolist(),previous['final_state'])}
   need(set(current['ssm_state_indices'].flatten().tolist())==set(before),'same actual slot across9decode')
   for slot,v in zip(current['ssm_state_indices'].flatten().tolist(),current['initial_state']):need(int(slot)in before and fingerprint(torch,v)==fingerprint(torch,before[int(slot)]),'actual successive9decode bitwise slot/state continuity')
 reused=False
 passed=all(r['pass_gate']for r in rows+decode)
 value=dict(reference_contract='mxr.independent-canonical-working-storage/v043',actual044_component=m['plugin_source'],bootstrap_short043_is_not044_numeric=True,original_ideal_metrics_retained=True,schema='mxr.observerless-once-GDN-independent/v1',plugin_source_ref=m['plugin_source'],capture_source=source,run_id=run_id,pid=runtime['pid'],worker_root=str(worker),lengths=sorted({r['tokens']for r in rows}),layer_prefixes=sorted({r['prefix']for r in rows}),gdn_frame_gate_pass=passed,model_logits_qualified=False,rows=rows,decode_rows=decode,pass_stage=passed,full_GDN=True,multistep_state=passed,decode_slot_continuity_pass=passed,inference_metadata_lifecycle_pass=False,actual_slot_reuse=reused,independent_conv_oracle=False,graph_candidate=False,performance_ready=False,task_ready=False,qualification_not_yet_promotable=True)
 need(output.is_absolute()and not output.exists(),'new independent result directory')
 output.mkdir();output=output/'BRIDGE_RESULT.json'
 with output.open('x')as f:json.dump(value,f,sort_keys=True);f.write('\n')
 return 0 if value['pass_stage']else 3
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--worker-root',type=Path);p.add_argument('--source-ref');p.add_argument('--prerequisite-ref');p.add_argument('--run-id');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 need(a.prerequisite_ref and a.run_id and a.source_ref,'explicit actual039/source/run')
 module(dict(path=str(P/'prerequisite.py'),bytes=(P/'prerequisite.py').stat().st_size,sha256=hashlib.sha256((P/'prerequisite.py').read_bytes()).hexdigest()),'_once_prerequisite').gate(json.loads(a.prerequisite_ref))
 return consume(a.worker_root,json.loads(a.source_ref),a.output,a.run_id)
if __name__=='__main__':raise SystemExit(main())
