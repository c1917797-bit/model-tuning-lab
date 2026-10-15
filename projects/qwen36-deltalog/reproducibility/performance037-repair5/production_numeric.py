"""MAIN-owned NPU finite-domain/health policy comparison on saved031 raw.
No model performance, no controller. Valid tests first; invalid test last.
"""
import argparse,importlib,importlib.util,json,math,os,sys,time
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from qwen36_deltalog_screen import admission as A
from qwen36_deltalog_screen import contract as C
import finite_numeric as F
FIELDS=('base','k_log','u_log','lambda_log','decay','length')

def module(ref,name):
 A.need(A.ref(ref['path'])==ref,'exact independent oracle source');s=importlib.util.spec_from_file_location(name,ref['path']);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 sr=json.loads(a.source_ref);m=A.source(sr);plan=A.obj(m['validation_inputs_ref']);A.need(plan['schema']=='deltalog.production-validation-inputs/v033','frozen real031 readset')
 producer=A.obj(plan['producer_ref']);A.need(producer['source']==plan['source031_ref'] and producer['primary']is None and producer['steps']in(16,160)and producer['NPU']is True,'actual completed source031 producer')
 A.need(plan['diagnostic_primitives_ref']['sha256']=='1b9a2e53ce137f319ca5939be6e21fa293735edd363cdc37f7b438626e985470'and A.ref(plan['diagnostic_primitives_ref']['path'])==plan['diagnostic_primitives_ref'],'exact original023 diagnostic materialization')
 A.need(plan['oracle_ref']['sha256']=='cd395a05dbfcb21f1104d617afb1fab6f80374016585e9096ca24d85c2cae97a','unchanged independent scalar oracle')
 sys.path.insert(0,str(Path(plan['diagnostic_primitives_ref']['path']).parent.parent));D=importlib.import_module('qwen36_deltalog_service.primitives')
 A.need(str(Path(D.__file__).resolve())==str(Path(plan['diagnostic_primitives_ref']['path']).resolve()),'actual old source, no shadow')
 from qwen36_deltalog_screen import primitives as L,health
 import torch,torch_npu
 torch.set_num_threads(1);torch.npu.set_device(0);R=module(plan['oracle_ref'],'independent035_oracle')
 A.need((torch.tensor([1.,2.],device='npu:0')+3).cpu().tolist()==[4.,5.],'actual NPU canary')
 direct=A.ref(P/'dependencies/direct_round013.py');A.need(direct['sha256']==F.DIRECT_SHA,'exact independent013 direct-RNE source');DR=module(direct,'independent035_direct_round')
 A.need(A.ref(m['library_ref']['path'])==m['library_ref']and m['library_ref']['sha256']==C.LIBRARY_SHA,'same original productionB010 DSO')
 torch.ops.load_library(m['library_ref']['path']);op=getattr(torch.ops,C.NAMESPACE).decode
 A.need(str(op.default._schema)==m['operator_schema']and torch._C._dispatch_has_kernel_for_dispatch_key(C.NAMESPACE+'::decode','PrivateUse1'),'real originalB010 namespace/schema/NPU dispatch')
 mapped_library=[line for line in Path('/proc/self/maps').read_text().splitlines()if len(line.split(None,5))==6 and line.split(None,5)[5]==str(Path(m['library_ref']['path']).resolve())]
 A.need(mapped_library,'same original productionB010 DSO actually mapped in this numerical PID')
 def same(x,y):return x.dtype==y.dtype and x.shape==y.shape and torch.equal(x.contiguous().view(torch.uint8),y.contiguous().view(torch.uint8))
 def upload(st):return {n:st[n].npu().clone()for n in FIELDS}
 def apply(fn,st,ids):
  layer=SimpleNamespace(prefix='production033.numeric',kv_cache=[None,st['base']]);fn(torch,layer,st,ids,'finite-domain-equivalence');torch.npu.synchronize();return {n:x.cpu()for n,x in st.items()}
 records=[r for r in producer['records']if r['kind']=='mixed'];rows=[];started=time.monotonic();first=None
 for record in records:
  A.need(time.monotonic()-started<560,'numeric560 budget');A.need(A.ref(record['raw']['path'])==record['raw'],'raw immutable exact Ref')
  raw=torch.load(Path(record['raw']['path']),map_location='cpu',weights_only=False);st={n:raw['state'][n]for n in FIELDS};first=first or (st,raw['ids'][:-1])
  cap,inputs,slots=F.capture(torch,raw,record['batch']);decode_state=upload(cap['before']);npu_inputs={n:inputs[n].npu().contiguous()for n in('query','key','value','g','beta','actual_seq_lengths','ssm_state_indices')}
  result=op(npu_inputs['query'],npu_inputs['key'],npu_inputs['value'],npu_inputs['g'],npu_inputs['beta'],decode_state['base'],decode_state['k_log'],decode_state['u_log'],decode_state['lambda_log'],decode_state['decay'],decode_state['length'],npu_inputs['actual_seq_lengths'],npu_inputs['ssm_state_indices'])
  health.observe(torch,result);torch.npu.synchronize();decoded={n:x.cpu()for n,x in decode_state.items()};actual=result.cpu()
  A.need(same(actual,cap['output']),'same input/DSO must reproduce actual saved035 BF16 output')
  for n in FIELDS:
   for slot in range(st['base'].shape[0]):
    expected=st[n][slot]if slot in slots else cap['before'][n][slot]
    A.need(same(decoded[n][slot],expected),'same saved active bytes/inactive guard '+n)
  A.need(all(same(npu_inputs[n].cpu(),inputs[n])for n in npu_inputs),'decode inputs/metadata immutable')
  independent=F.reference(torch,R,DR,cap['before'],decoded,inputs,actual,slots)
  ids=raw['ids'][:-1].npu();before=upload(st);after=upload(st)
  x=apply(D._flush_slots,before,ids);y=apply(L._flush_slots,after,ids)
  A.need(all(same(x[n],y[n])for n in FIELDS),'finite diagnostic/production bytes unchanged')
  worst=0.
  for slot in raw['ids'][:-1].tolist():
   expected=R.restore(torch,st,slot);actual=y['base'][slot].double();err=float((actual-expected).norm()/max(float(expected.norm()),1e-30));A.need(math.isfinite(err)and err<=R.STATE_LIMIT,'unchanged independent FP32 restore gate');worst=max(worst,err)
  rows.append(dict(batch=record['batch'],step=record['step'],raw=record['raw'],bitwise=True,independent_state_error=worst,decode=dict(saved_output_bitwise=True,active_state_bitwise=True,inactive_guard_bitwise=True,input_bitwise=True,requests=independent,health_observed=True)))
 for batch in(1,16):A.need([r['step']for r in rows if r['batch']==batch]==list(range(producer['steps'])),'both ordered actual multistep batches')
 st,selected=first;dead={n:v.clone()for n,v in st.items()};slot=int(selected[0]);dead['length'][slot].zero_();dead['decay'][slot].zero_()
 for name in('k_log','u_log','lambda_log'):dead[name][slot].fill_(float('nan'))
 ids=torch.tensor([slot],dtype=torch.int32,device='npu:0');x=apply(D._flush_slots,upload(dead),ids);y=apply(L._flush_slots,upload(dead),ids)
 A.need(all(same(x[n],y[n])for n in FIELDS),'dead NaN payload remains unchanged and masked')
 valid=health.snapshot(torch,outside_timing=True);A.need(valid['all_finite'],'all valid/dead/multistep health observations')
 bad={n:v.clone()for n,v in dead.items()};bad['length'][slot,:,0]=1;bad['lambda_log'][slot,:,0]=0;bad['k_log'][slot,:,0].fill_(.01);bad['u_log'][slot,:,0].fill_(float('nan'))
 diagnostic_rejected=False
 try:apply(D._flush_slots,upload(bad),ids)
 except RuntimeError as error:
  A.need('non-finite'in str(error),'only real invalid-live gate is expected');diagnostic_rejected=True
 apply(L._flush_slots,upload(bad),ids);invalid=health.snapshot(torch,outside_timing=True)
 A.need(diagnostic_rejected and not invalid['all_finite'],'invalid live permanently rejects whole production experiment')
 # A fresh exact-source helper isolates this synthetic output negative from
 # the already sticky failed live-flush flag; no experiment flag is cleared.
 negative_health=module(A.ref(P/'qwen36_deltalog_screen/health.py'),'isolated_output_negative_health')
 negative_health.observe(torch,torch.ones((1,12,128),device='npu:0',dtype=torch.bfloat16));negative_before=negative_health.snapshot(torch,outside_timing=True)
 bad_output=torch.full((1,12,128),float('nan'),device='npu:0',dtype=torch.bfloat16);negative_health.observe(torch,bad_output);negative_health.observe(torch,torch.ones_like(bad_output));decode_invalid=negative_health.snapshot(torch,outside_timing=True)
 A.need(negative_before['all_finite']and not decode_invalid['all_finite'],'independent nonfinite output control flips same exact-source production health and cannot recover')
 output=Path(a.output);A.need(output.is_absolute()and output.parent.is_dir()and not output.exists(),'new numeric output')
 result=dict(schema='deltalog.production-finite-domain-validation/v037-repair2',source=sr,inputs=m['validation_inputs_ref'],validation_contract=F.CONTRACT,library=m['library_ref'],mapped_library=mapped_library,operator_schema=str(op.default._schema),pid=os.getpid(),proc_stat=Path('/proc/self/stat').read_text(),cgroup=Path('/proc/self/cgroup').read_text(),NPU=True,rows=rows,steps_checked=len(rows),batches=[1,16],finite_domain_equal=True,decode_direct_RNE_pass=True,decode_health_negative_synthetic_output=True,decode_invalid_health=decode_invalid,invalid_live_whole_arm_rejected=True,dead_nan_pass=True,valid_health=valid,invalid_health=invalid,qualification=False,elapsed=time.monotonic()-started)
 with output.open('x',encoding='utf8')as f:json.dump(result,f,sort_keys=True,allow_nan=False)
 return 0
if __name__=='__main__':raise SystemExit(main())
