"""Saved 3x3 raw only: fixed A/G inverse cells and signed error decomposition."""
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,msg):
 if not v:raise ValueError(msg)
def ref(p):
 p=Path(p);before=p.stat();h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 after=p.stat();need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),'stable read');return dict(path=p.as_posix(),bytes=after.st_size,sha256=h.hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'},'Ref3');p=Path(r['path']);need(p.is_absolute()and p.is_file()and all(not q.is_symlink()for q in(p,*p.parents))and ref(p)==r,'exact ordinary immutable input');return p
def obj(r):return json.loads(checked(r).read_bytes())
def load(r,name):
 s=importlib.util.spec_from_file_location(name,checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def readset(m):
 need(m['schema']=='mxr.fixed-actual-A-G-CPU-source/v120-analysis4'and m['default_enabled']is False,'exact new diagnostic source')
 cm=obj(m['counterfactual_source_ref']);C=load(cm['files']['counterfactual.py'],'_A4_original_A3');gm,G,model,stage,prior,refs=C.readset(cm)
 a3=obj(m['actual_A3_report_ref']);owner=obj(m['actual_A3_owner_ref']);own=obj(m['actual_A3_source_ref'])
 need(owner['source']==m['actual_A3_source_ref']and owner['primary']is None and owner['secondary']==[]and owner['resource_release_verified']is True and owner['Devices']==[]and owner['NPU']is False,'actual released A3 CPU predecessor')
 need(a3['schema']=='mxr.actual-A-G-independent-CPU-counterfactual/v120-analysis3'and a3['source']==m['counterfactual_source_ref']and a3['actual_stage_ref']==m['actual_stage_ref']==cm['actual_stage_ref']and a3['qualification']is False and a3['old_failures_preserved']is True and[a['case']for a in a3['cases']]==gm['cases'],'actual A3 report/source/cases, not future PASS')
 need(own['counterfactual_source_ref']==m['counterfactual_source_ref'],'A3 owner input source join')
 refs +=[m['counterfactual_source_ref'],m['actual_A3_report_ref'],m['actual_A3_owner_ref'],m['actual_A3_source_ref'],m['owner_module_ref'],*m['files'].values()]
 for r in refs:checked(r)
 return cm,C,gm,G,model,stage,a3,refs
def bits_equal(torch,a,b):return a.dtype==b.dtype and a.shape==b.shape and torch.equal(a.contiguous().view(torch.uint8),b.contiguous().view(torch.uint8))
def vector_terms(torch,actual,operational,canonical):
 for v in(actual,operational,canonical):need(v.shape==canonical.shape and bool(torch.isfinite(v).all()),'finite same shape vector diagnostic')
 actual,operational,canonical=[v.double()for v in(actual,operational,canonical)];a=actual-operational;b=operational-canonical;total=actual-canonical;den=float(canonical.norm());na=float(a.norm());nb=float(b.norm());dot=float((a*b).sum())
 return dict(denominator='same canonical state Frobenius norm',denominator_norm=den,actual_minus_operational_norm=na,operational_minus_canonical_norm=nb,total_norm=float(total.norm()),actual_minus_operational_relative=na/den if den else None,operational_minus_canonical_relative=nb/den if den else None,total_relative=float(total.norm())/den if den else None,dot=dot,cosine=dot/(na*nb)if na and nb else None,cross_term=2*dot,reconstruction_max_abs=float((total-a-b).abs().max()),not_additive_error_budget=True)
def pair_first(torch,arms):
 names=('saved_candidate','native','cpu64_cast');out={}
 for i,a in enumerate(names):
  for b in names[i+1:]:
   out[a+'__'+b]={}
   for name in('B','W','U','Hentry','Vnew'):
    x,y=arms[a][name],arms[b][name]
    if name=='Hentry':parts=[(x.reshape(1,12,32,128,128)[0,:,j],y.reshape(1,12,32,128,128)[0,:,j])for j in range(32)]
    elif name=='Vnew':parts=[(x.reshape(1,12,2048,128)[0,:,j*64:(j+1)*64],y.reshape(1,12,2048,128)[0,:,j*64:(j+1)*64])for j in range(32)]
    else:parts=[(x[:,j*64:(j+1)*64],y[:,j*64:(j+1)*64])for j in range(32)]
    out[a+'__'+b][name]=next((j for j,(v,w)in enumerate(parts)if not bits_equal(torch,v,w)),None)
 return out
def run(torch,m):
 cm,C,gm,G,model,stage,a3,_=readset(m);H=C.load(cm['files']['reference_inputs.py'],'_A4_independent_original_hook');R=load(m['files']['direct_rne.py'],'_A4_independent_direct_RNE');results=[]
 for case,item,old in zip(gm['cases'],stage['result']['cases'],a3['cases']):
  saved=G.frame(torch,model,case);x=G.validate_frame(torch,saved);arms={r['arm']:torch.load(checked(r['raw']),map_location='cpu',weights_only=True)for r in item['result']['rows']};c=arms['saved_candidate']
  C.validate_operands(torch,x,c['A'],c['G']);need(bits_equal(torch,c['A'],saved['solve']['A'])and bits_equal(torch,c['B'],saved['solve']['output'])and bits_equal(torch,c['output'],saved['output'])and bits_equal(torch,c['state'],saved['final_state']),'actual saved candidate A/B/output/state bitwise anchor')
  need(all(bits_equal(torch,v['A'],c['A'])and bits_equal(torch,v['G'],c['G'])for v in arms.values()),'immutable shared actual A/G')
  baseline=H.evaluate(torch,x);proof=old['counterfactual']['baseline_identity'];need(C.fp(torch,baseline['output'])==proof['output_refingerprint']and C.fp(torch,baseline['state'])==proof['state_refingerprint'],'recomputed canonical baseline exact actual A3 fingerprints');operational=H.evaluate(torch,x,actual_A=c['A'],actual_G=c['G']);first=pair_first(torch,arms);chunks=sorted({v['B']for v in first.values()if v['B']is not None})or[0];rows=[]
  for j in chunks:
   z=slice(j*64,(j+1)*64);A=c['A'][0,z].permute(1,0,2).double().contiguous();eye=torch.eye(64,dtype=torch.float64).expand(12,64,64);inverse=torch.linalg.solve_triangular(eye+A,eye,upper=False,unitriangular=True);direct=R.round_bf16(torch,inverse);cast=inverse.to(torch.bfloat16)
   rows.append(dict(chunk=j,independent_inverse_residual_max_abs=float(((eye+A)@inverse-eye).abs().max()),torchcast_vs_direct_RNE_cells=int((cast.view(torch.int16)!=direct.view(torch.int16)).sum()),arms={name:dict(B_equals_direct_RNE=bits_equal(torch,v['B'][0,z].permute(1,0,2),direct),B_vs_direct_RNE_cells=int((v['B'][0,z].permute(1,0,2).contiguous().view(torch.int16)!=direct.view(torch.int16)).sum()),B_vs_direct_RNE_max_abs=float((v['B'][0,z].permute(1,0,2).double()-direct.double()).abs().max()))for name,v in arms.items()}))
  results.append(dict(case=case,actual_raw_refs=item['result']['rows'],same_actual_A_G=True,saved_candidate_anchor_bitwise=True,canonical_A3_anchor_bitwise=True,actual_anchors={name:{key:C.fp(torch,value[key])for key in('A','G','B','output','state')}for name,value in arms.items()},first_difference_by_pair=first,selected_chunks=rows,state_vectors={name:vector_terms(torch,v['state'],operational['state'],baseline['state'])for name,v in arms.items()},positive_g_and_safe_exp=old['counterfactual']['positive_g_and_safe_exp'],old_actual_registered_metrics=old['counterfactual']['variants'],baseline_not_claimed_instruction_exact=True,hidden_FP32_Hend_unavailable=True))
 return dict(schema='mxr.fixed-actual-A-G-B-RNE-vector-analysis/v120-analysis4',actual_stage_ref=m['actual_stage_ref'],actual_A3_report_ref=m['actual_A3_report_ref'],cases=results,qualification=False,model=False,performance=False,task=False,NPU=False,old_failures_preserved=True,no_X3_selected=True)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-audit',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not(a.execute or a.source_audit):print('disabled');return 0
 sr=json.loads(a.source_ref);m=obj(sr);need(m['root']==str(P)and m['files']['reader.py']==ref(__file__),'actual reader source/root');refs=readset(m)[-1]
 if a.source_audit:print(json.dumps(dict(source=sr,readset=refs,NPU=False)));return 0
 need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'actual no-device CPU');need(a.output.is_absolute()and a.output.parent.is_dir()and not a.output.exists(),'fresh report')
 import torch
 torch.set_num_threads(1);v=run(torch,m);v['source']=sr;b=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode();need(len(b)<=m['budgets']['output_bytes'],'full report2MiB, never truncate')
 with a.output.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return 0
if __name__=='__main__':raise SystemExit(main())
