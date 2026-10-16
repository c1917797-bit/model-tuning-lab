"""Devices[] actual three-arm tensor chain attribution; no threshold change."""
import argparse,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import guest_core as G
def metric(torch,a,b):
 G.need(a.shape==b.shape and bool(torch.isfinite(a).all()and torch.isfinite(b).all()),'finite same-shape API comparison')
 d=a.double()-b.double();return dict(relative_l2=float(d.norm()/max(float(b.double().norm()),1e-30)),max_abs=float(d.abs().max()),changed_bytes=int((a.contiguous().view(torch.uint8)!=b.contiguous().view(torch.uint8)).sum())if a.dtype==b.dtype else None,bitwise=G.equal(torch,a,b))
def consume_case(torch,m,stage,saved):
 G.need(stage['schema']=='mxr.prefill-three-arm-stage/v084'and stage['primary']is None and stage['NPU']is True and stage['qualified']is False and stage['raw']==G.RAW and stage['authority']==G.AUTHORITY,'actual complete diagnostic stage')
 value=stage['result'];G.need(value['candidate_anchor_bitwise']is True and value['same_actual_A_G']is True and value['raw_bytes']<=G.RAW_CAP,'actual stage anchor/fullraw bound')
 G.need([r['arm']for r in value['rows']]==list(G.ARMS),'exact three arms in candidate-first order')
 rows={r['arm']:torch.load(G.checked(r['raw']),map_location='cpu',weights_only=True)for r in value['rows']}
 G.need(sum(r['raw']['bytes']for r in value['rows'])==value['raw_bytes'],'exact complete fullraw byte ledger')
 x=G.validate_frame(torch,saved);candidate=rows['saved_candidate']
 actual=candidate['actual_X2'];passed=G.obj(m['actual037_prerequisite']);identity=actual['solver_identity']
 G.need(actual['variant_ref']==m['variant_ref']and actual['trace']is None and identity['source']==passed['source']and identity['build']==passed['build']and identity['library']==passed['library']and identity['symbol']=='call_mxr_y16_compensated','actual original037 plus exact097R1 X2, not B injection under candidate label')
 G.need(G.equal(torch,candidate['output'],saved['output'])and G.equal(torch,candidate['state'],saved['final_state'])and G.equal(torch,candidate['B'],saved['solve']['output']),'independent saved candidate bitwise anchor')
 O=G.load(m['original_metrics'],'_084_consumer_original_inverse');inverse,residual=O.fp64_reference(torch,saved['solve']['A'],x['cu_seqlens'].tolist())
 G.need(G.equal(torch,rows['cpu64_cast']['B'],inverse.to(torch.bfloat16)),'independent CPU64 inverse from actual savedA cast, not reconstructedA')
 for name,row in rows.items():
  G.need(row['arm']==name and G.equal(torch,row['A'],saved['solve']['A'])and G.equal(torch,row['G'],candidate['G']),'same actual A/G and arm identity')
  G.need(row['inputs_after']=={n:G.fp(torch,x[n])for n in('q','k','v','g','beta','initial_state','cu_seqlens')},'whole immutable actual operands')
  G.need(G.equal(torch,row['state'],row['Hend_final']),'actual returned state joins official Hfinal')
  for key in('G','A','B','W','U','Hentry','Vnew','output','state'):G.need(bool(torch.isfinite(row[key]).all()),'finite actual API '+key)
 pairs={}
 for left,right in(('saved_candidate','native'),('saved_candidate','cpu64_cast'),('native','cpu64_cast')):
  a,b=rows[left],rows[right];trace=[]
  for chunk in range(32):
   z=slice(chunk*64,(chunk+1)*64);cells={}
   for key in('G','A','B','W','U','output'):cells[key]=metric(torch,a[key][:,z],b[key][:,z])
   # Native H storage offsets are head-major/chunk-major within head, as the
   # pinned GDNFwdHKernel hOffset proves; preserve actual API shape in raw.
   cells['Hentry']=metric(torch,a['Hentry'].reshape(1,12,32,128,128)[:,:,chunk],b['Hentry'].reshape(1,12,32,128,128)[:,:,chunk])
   cells['Vnew']=metric(torch,a['Vnew'].reshape(1,12,2048,128)[:,:,z],b['Vnew'].reshape(1,12,2048,128)[:,:,z])
   trace.append(dict(chunk=chunk,start=chunk*64,metrics=cells))
  first={key:next((t['chunk']for t in trace if not t['metrics'][key]['bitwise']),None)for key in trace[0]['metrics']}
  pairs[left+'_vs_'+right]=dict(first_differing_chunk=first,chunks=trace,final_state=metric(torch,a['state'],b['state']))
 boundary=G.load(m['original_working_oracle'],'_120_unchanged_working_oracle');working=boundary.evaluate(torch,x)
 registered={name:dict(output=O.metrics(torch,row['output'],working['output']),state=O.metrics(torch,row['state'],working['state']))for name,row in rows.items()}
 return dict(registered_working=registered,schema='mxr.prefill-three-arm-independent/v084',rows=value['rows'],candidate_anchor_bitwise=True,source=stage['source'],actual_A_only=True,CPU64_inverse_residual=residual,pairs=pairs,intermediate_Hend_FP32_API_available=False,qualification=False,old_failures_unchanged=True,performance=False,task=False)

def consume(torch,m,stage,saved=None):
 G.need(stage['schema']=='mxr.prefill-three-arm-stage/v084'and stage['source']is not None and stage['primary']is None and stage['NPU']is True,'actual complete120 stage')
 cases=stage['result']['cases'];G.need([c['case_id']for c in cases]==[c['case_id']for c in m['cases']]and stage['result']['raw_bytes']==sum(c['result']['raw_bytes']for c in cases),'complete source-bound case cardinality/raw ledger')
 model,_,_,_=G.readset(m);reports=[]
 for case,result in zip(m['cases'],cases):
  G.need(result['raw']==case['raw'],'actual case/raw order');G.CASE=case;G.RAW=case['raw'];raw=G.frame(torch,model,case)
  # This adapter invokes the exact original084 full tensor attribution predicate
  # per case. Only the enclosing multi-frame transport is new.
  inner=dict(stage,raw=case['raw'],result=result['result']);report=consume_case(torch,m,inner,raw)
  reports.append(dict(case=case,attribution=report))
 return dict(schema='mxr.r5-prefill-counterfactual-independent/v120',source=stage['source'],cases=reports,candidate_anchor_bitwise=True,qualification=False,performance=False,task=False,old_R5_FAIL_preserved=True,CPU64_cast_is_operational_not_exact_nearest=True)

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 G.need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'actual Devices[] independent consumer')
 sr=json.loads(a.source_ref);m=G.obj(sr);stage=G.obj(json.loads(a.stage_ref));G.need(stage['source']==sr,'same exact current source')
 model,_,_,_=G.readset(m)
 import torch
 torch.set_num_threads(1);report=consume(torch,m,stage)
 G.need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'exclusive new CPU report');G.write(a.output,report);return 0
if __name__=='__main__':raise SystemExit(main())
