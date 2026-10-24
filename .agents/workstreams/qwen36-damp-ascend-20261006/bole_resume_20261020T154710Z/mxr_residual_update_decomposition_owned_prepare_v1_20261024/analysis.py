"""Three actual tile residual/update decomposition; no inverse or GDN/state recompute."""
import hashlib,json,os,sys,types
from pathlib import Path
DIRECT={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-two-residual-model-new24h-v1-098-repair5/direct_round.py","bytes":3378,"sha256":"60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d"}
SCHEMA='mxr.actual-three-tile-residual-update-decomposition/v1'
FALSE=('qualification','performance','task_accuracy','prefill_state_causation_proven','canonical_changed','thresholds_changed','new_NPU_execution')
def need(v,s):
    if not v:raise ValueError(s)
def checked(r):
    p=Path(r['path']);a=p.stat();h=hashlib.sha256()
    need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'exact ordinary Ref3')
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and z.st_size==r['bytes']and h.hexdigest()==r['sha256'],'stable complete pinned bytes');return p
def load(r,name):
    m=types.ModuleType(name);m.__file__=r['path'];exec(compile(checked(r).read_bytes(),r['path'],'exec'),m.__dict__);return m
def digest(torch,t):
    t=t.detach().cpu().contiguous()
    need(bool(torch.isfinite(t).all()),'finite full actual tensor')
    raw=t.view(torch.uint8).numpy().tobytes()
    return dict(shape=list(t.shape),dtype=str(t.dtype),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

CONSUMED={"path":"/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-THREE_TILE_ROUNDING_NPU_20261024_V6/physical6/numeric/CONSUMED.json","bytes":5024,"sha256":"5c7c8d3acc2ba5268d834041316b87626841e31831089462f0a37677d62aa8ab"}
RAW_REFS=[{"bytes":129545,"path":"/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-THREE_TILE_ROUNDING_NPU_20261024_V6/physical6/numeric/actual-native/saved_candidate-c00-precast.pt","sha256":"3c61bd5a2b4d87d97e082e08d5fc5d99a4e603a519fb11f314e0120662a600a3"},{"bytes":129545,"path":"/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-THREE_TILE_ROUNDING_NPU_20261024_V6/physical6/numeric/actual-native/saved_candidate-c03-precast.pt","sha256":"bb64d3bd04198687fd793609a74863f7e86b72ad54e7b63213eb14b362eb0fff"},{"bytes":129545,"path":"/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-THREE_TILE_ROUNDING_NPU_20261024_V6/physical6/numeric/actual-native/saved_candidate-c19-precast.pt","sha256":"1c1427e201c7eb25e8e76ed282ced673cebb3282aa142d9a736fa5f01e9ec288"}]
NPU_SOURCE={"bytes":320810,"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_three_tile_rounding_prepare_v6_20261024/prepared-source/SOURCE_MANIFEST.json","sha256":"0fa2ab01e188b4efe4b90b60de865c456f6ef4e9d3194d57a5426722f6d88d6f"}
VARIANT={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-two-residual-new24h-v1-097-repair1/two_residual097.py","bytes":7165,"sha256":"58b68fe106356d5fc608ac09a29728fb45a0aba07e970deabfbb2f87ae63aceb"}
TILES=((0,0),(3,2),(19,5))
KEYS={'A32','X0','X1','X2','R1','R2','B','native_B','cpu64_sameA_B'}
ROUTES=('actual_X2_B','Xa_via_FP32_B','Xa_direct_RNE_B','Xb_via_FP32_B','Xb_direct_RNE_B')
def validate_labels(raw,c,h):
    need(type(raw)is dict and raw.get('schema')=='mxr.actual-three-tile-rounding-raw/v1'and raw.get('arm')=='saved_candidate'and raw.get('variant')=='precast','exact actual producer schema/arm/variant')
    need(type(raw.get('chunk'))is int and type(raw.get('head'))is int and(raw['chunk'],raw['head'])==(c,h)and raw['source']==NPU_SOURCE and raw['variant_ref']==VARIANT and raw['full_saved_B_bitwise']is True and raw['qualification']is False and raw['native_precast']=='unknown','actual source/tile labels and bitwise witness')
def counts(rows):
    total={k:sum(r['sameA_B_mismatches'][k]for r in rows)for k in ROUTES}
    decision='CONSIDER_BOUNDED_COMPENSATED_RESIDUAL_DIAGNOSTIC'if total['Xb_direct_RNE_B']<min(total['actual_X2_B'],total['Xa_direct_RNE_B'])else'NO_THREE_TILE_EVIDENCE_TO_PREFER_COMPENSATED_RESIDUAL'
    return dict(total_sameA_B_mismatches=total,next_action=decision)
def verify_report(r,plan):
    need(r['schema']==SCHEMA and r['input_plan']==plan and r['consumed_ref']==CONSUMED and r['raw_refs']==RAW_REFS and r['direct_reference']==DIRECT and r['diagnostic_complete']is True,'exact actual inputs/source/schema')
    need(all(r[k]is False for k in FALSE)and r['inverse_recomputed']is False and r['native_precast']=='unknown','no solve/state/causation/qualification or oracle change')
    need([(x['chunk'],x['head'])for x in r['rows']]==list(TILES),'complete actual three tiles')
    expected=[(0,0,55,49),(3,2,52,42),(3,2,59,50),(19,5,44,15),(19,5,52,20)]
    need([(x['chunk'],x['head'],*x['index'])for x in r['five_coordinates']]==expected,'all five consumed coordinates, no replacement')
    for row,rr in zip(r['rows'],RAW_REFS):
        need(row['raw']==rr and row['actual_B_bitwise_anchor']is True and row['sameA_B_bitwise_anchor']is True,'real original B anchors')
        need(set(row['sameA_B_mismatches'])==set(ROUTES)and all(type(n)is int and 0<=n<=4096 for n in row['sameA_B_mismatches'].values()),'full4096 route counts')
        need(set(row['errors'])=={'residual_formation','update_bmm_add_rounding','residual_formation_propagated','combined_to_Xb'},'two distinct formation/update errors')
        for e in row['errors'].values():need(set(e)=={'max_abs','frobenius','rmse'}and all(type(v)in(int,float)and __import__('math').isfinite(v)and v>=0 for v in e.values()),'finite complete error metrics')
        need(set(row['digests'])=={'A32','X1','R2','X2','Rideal_FP64','Xa_FP64','Xb_FP64','native_B','sameA_B',*ROUTES},'full tensor digest coverage')
        for k,d in row['digests'].items():
            dtype='torch.bfloat16'if k in(*ROUTES,'native_B','sameA_B')else'torch.float64'if k.endswith('FP64')else'torch.float32'
            size=8192 if dtype=='torch.bfloat16'else 32768 if dtype=='torch.float64'else 16384
            need(d['shape']==[64,64]and d['dtype']==dtype and d['bytes']==size and len(d['sha256'])==64 and all(c in '0123456789abcdef'for c in d['sha256']),'typed full tile digest')
    need(r['summary']==counts(r['rows']),'independent exact non-waiver decision')
    for c in r['five_coordinates']:
        need(set(c['cast_bits'])=={*ROUTES,'native_B','sameA_B'}and all(type(v)is int and 0<=v<65536 for v in c['cast_bits'].values()),'all real coordinate cast classes')
        need(set(c['sameA_match'])==set(ROUTES)and all(c['sameA_match'][k]==(c['cast_bits'][k]==c['cast_bits']['sameA_B'])for k in ROUTES),'coordinate classification rederived')
        need(set(c['FP64_values_hex'])=={'Xa','Xb','Rstored','Rideal','actual_X2'}and all(__import__('math').isfinite(float.fromhex(v))for v in c['FP64_values_hex'].values()),'all finite coordinate FP64 operands')
    return r
def analyze(torch,plan):
    C=load(plan['continuous_source'],'_decomposition_actual_fixed_source');need(C.FIXED==plan['fixed_inputs'],'unchanged real case')
    donor=C.load(C.FIXED['donor'],'_decomposition_real_frame',{'need','fp','equal','validate_frame'})
    codec=C.load(C.FIXED['codec'],'_decomposition_raw_codec')
    checked(C.FIXED['case']['raw_sidecar']);saved=codec.read(torch,checked(C.FIXED['case']['raw']));x=donor.validate_frame(torch,saved)
    need(x['cu_seqlens'].tolist()==[0,2048],'complete source input')
    cast=torch.load(checked(C.FIXED['arms'][2]),map_location='cpu',weights_only=True)
    wanted={k:donor.fp(torch,x[k])for k in('q','k','v','g','beta','initial_state','cu_seqlens')}
    need(cast['arm']=='cpu64_cast'and cast['inputs_after']==wanted and donor.equal(torch,cast['A'],saved['solve']['A']),'same actual A/input CPU64 stored anchor')
    observed=json.loads(checked(CONSUMED).read_bytes())
    need(observed['schema']=='mxr.native2048-three-tile-rounding-independent/v1'and observed['diagnostic_complete']is True and observed['qualification']is observed['performance']is observed['thresholds_changed']is False and [z['raw']for z in observed['rows']]==RAW_REFS,'exact prior actual independent consumption')
    D=load(DIRECT,'_decomposition_integer_RNE');rows=[];coords=[]
    def error(a,b):
        z=a-b;need(bool(torch.isfinite(z).all()),'finite error operands')
        return dict(max_abs=float(z.abs().max()),frobenius=float(torch.linalg.vector_norm(z)),rmse=float(z.square().mean().sqrt()))
    def bits(t):return [int(v)&65535 for v in t.view(torch.int16).reshape(-1).tolist()]
    for (c,h),rr,old in zip(TILES,RAW_REFS,observed['rows']):
        raw=torch.load(checked(rr),map_location='cpu',weights_only=True);validate_labels(raw,c,h)
        need(raw['case']==plan['fixed_inputs']['case']and set(raw['tensors'])==KEYS,'same case/complete actual nine tensor ABI')
        t=raw['tensors']
        for n,v in t.items():
            dtype=torch.bfloat16 if n in('B','native_B','cpu64_sameA_B')else torch.float32
            need(v.device.type=='cpu'and v.dtype==dtype and tuple(v.shape)==(64,64)and v.is_contiguous()and v.storage_offset()==0 and v.untyped_storage().nbytes()==v.numel()*v.element_size()and bool(torch.isfinite(v).all()),'actual compact finite tile')
        sl=(0,slice(c*64,(c+1)*64),h)
        need(digest(torch,t['A32'])==digest(torch,saved['solve']['A'][sl])and digest(torch,t['B'])==digest(torch,saved['solve']['output'][sl])and digest(torch,t['cpu64_sameA_B'])==digest(torch,cast['B'][sl]),'full A/B/sameA saved byte anchors before decomposition')
        need(raw['full_geometry']['T']==2048 and raw['full_geometry']['chunks']==32 and raw['full_geometry']['A']==raw['full_geometry']['A_after']==donor.fp(torch,saved['solve']['A']),'actual full native2K geometry, not tile-only input')
        M=torch.eye(64,dtype=torch.float64)+t['A32'].double();X1=t['X1'].double();Rstored=t['R2'].double()
        Rideal=torch.eye(64,dtype=torch.float64)-M@X1
        Xa=X1+X1@Rstored
        Xb=X1+X1@Rideal
        routes=dict(actual_X2_B=t['X2'].to(torch.bfloat16),Xa_via_FP32_B=Xa.float().to(torch.bfloat16),Xa_direct_RNE_B=D.round_bf16(torch,Xa),Xb_via_FP32_B=Xb.float().to(torch.bfloat16),Xb_direct_RNE_B=D.round_bf16(torch,Xb))
        need(digest(torch,routes['actual_X2_B'])==digest(torch,t['B']),'actual X2 FP32-to-BF16 complete saved B anchor')
        target=bits(t['cpu64_sameA_B']);routebits={k:bits(v)for k,v in routes.items()}
        row=dict(chunk=c,head=h,raw=rr,actual_B_bitwise_anchor=True,sameA_B_bitwise_anchor=True,
            sameA_B_mismatches={k:sum(a!=b for a,b in zip(v,target))for k,v in routebits.items()},
            errors=dict(residual_formation=error(Rstored,Rideal),update_bmm_add_rounding=error(t['X2'].double(),Xa),residual_formation_propagated=error(Xa,Xb),combined_to_Xb=error(t['X2'].double(),Xb)),
            digests={k:digest(torch,v)for k,v in dict(A32=t['A32'],X1=t['X1'],R2=t['R2'],X2=t['X2'],Rideal_FP64=Rideal,Xa_FP64=Xa,Xb_FP64=Xb,native_B=t['native_B'],sameA_B=t['cpu64_sameA_B'],**routes).items()})
        rows.append(row);native=bits(t['native_B'])
        for z in old['classification']:
            i,j=z['index'];idx=i*64+j
            need(z['actual_B_bits']==routebits['actual_X2_B'][idx]and z['native_B_bits']==native[idx]and z['same_A_CPU64_B_bits']==target[idx],'selected five original classifications independently rejoined')
            cb={k:v[idx]for k,v in routebits.items()};cb.update(native_B=native[idx],sameA_B=target[idx])
            coords.append(dict(chunk=c,head=h,index=[i,j],cast_bits=cb,sameA_match={k:cb[k]==target[idx]for k in ROUTES},
                FP64_values_hex={k:float(v[i,j]).hex()for k,v in dict(Xa=Xa,Xb=Xb,Rstored=Rstored,Rideal=Rideal,actual_X2=t['X2'].double()).items()}))
    result=dict(schema=SCHEMA,input_plan=plan,consumed_ref=CONSUMED,raw_refs=RAW_REFS,direct_reference=DIRECT,rows=rows,five_coordinates=coords,summary=counts(rows),diagnostic_complete=True,inverse_recomputed=False,native_precast='unknown',**{k:False for k in FALSE})
    verify_report(result,plan);return result
