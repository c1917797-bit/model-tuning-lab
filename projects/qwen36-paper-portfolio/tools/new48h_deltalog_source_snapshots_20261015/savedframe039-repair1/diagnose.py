"""One actual saved035 frame; independent CPU arithmetic, no new gate."""
import math,struct,decimal
def need(v,m):
 if not v:raise ValueError(m)
def bf16_value(code):return struct.unpack('>f',struct.pack('>I',(code&65535)<<16))[0]
def cell(value,code):
 neighbors=[-bf16_value(1),bf16_value(code),bf16_value(1)]if code in(0,0x8000)else sorted(bf16_value(c)for c in(code-1,code,code+1))
 need(all(math.isfinite(v)for v in neighbors),'finite normal neighboring BF16 cells')
 low=(neighbors[0]+neighbors[1])/2;high=(neighbors[1]+neighbors[2])/2
 return dict(bits_hex='%04x'%code,value=bf16_value(code),neighbor_low=neighbors[0],neighbor_high=neighbors[2],midpoint_low=low,midpoint_high=high,truth_minus_low=value-low,high_minus_truth=high-value,truth_within_closed_cell=low<=value<=high)
def metric(T,a,b):return float((a.double()-b.double()).abs().max()/max(float(b.double().abs().max()),1e-30))
def mp_column(before,inputs,slot,row,head,column,precision):
 """Independent Decimal single-column recurrence from exact input binaries."""
 with decimal.localcontext()as ctx:
  ctx.prec=precision
  f=lambda value:decimal.Decimal.from_float(float(value))
  decay=f(before['decay'][slot,head,0]);length=int(before['length'][slot,head,0]);kh=head//3
  state=[f(before['base'][slot,head,column,k])*decay.exp()for k in range(128)]
  for entry in range(length):
   coefficient=(decay-f(before['lambda_log'][slot,head,entry])).exp();u=f(before['u_log'][slot,head,entry,column])
   for k in range(128):state[k]+=coefficient*u*f(before['k_log'][slot,kh,entry,k])
  gd=f(inputs['g'][row,head]).exp();state=[x*gd for x in state];key=[f(inputs['key'][row,kh,k])for k in range(128)]
  pred=sum((state[k]*key[k]for k in range(128)),decimal.Decimal(0));update=f(inputs['beta'][row,head])*(f(inputs['value'][row,head,column])-pred)
  output=sum(((state[k]+key[k]*update)*f(inputs['query'][row,kh,k])for k in range(128)),decimal.Decimal(0))*f(inputs['scale'])
  return output
def run(T,C,m,out):
 R=C.load(m['files']['oracle.py'],'_actual035_independent_scalar');D=C.load(m['files']['direct_round.py'],'_actual013_integer_RNE')
 raw=T.load(C.checked(m['selected_raw_ref']),map_location='cpu',weights_only=False)
 need(raw['kind']=='mixed'and raw['step']==80 and len(raw['ids'])==17 and len(raw['captures']['decode'])==1,'fixed first failure B16step80')
 cap=raw['captures']['decode'][0];i=cap['inputs'];ids=i['ssm_state_indices'].tolist();need(ids==raw['ids'][:-1].tolist()and i['actual_seq_lengths'].tolist()==[0]+[1]*16,'actual metadata/native individual sequence ABI')
 j=10;s=ids[j];initial=R.restore(T,cap['before'],s);expected,truth=R.advance(T,initial,i,j);rounded=D.round_bf16(T,truth);candidate=cap['output'][j];native=raw['native_output'][j]
 need(truth.dtype==T.float64 and candidate.dtype==native.dtype==T.bfloat16 and candidate.shape==native.shape==truth.shape==(12,128),'actual BF16/independentCPU64 shapes')
 need(bool(T.isfinite(initial).all()and T.isfinite(truth).all()and T.isfinite(candidate).all()and T.isfinite(native).all()),'finite local operands')
 after=R.restore(T,raw['state'],s);q=i['query'][j].double().repeat_interleave(3,dim=0)*float(i['scale'])
 restored64=(after*q[:,None,:]).sum(-1)
 restored32=(after.float()*q.float()[:,None,:]).sum(-1)
 # Separate direct CPU32 recurrence, not native/precast reproduction.
 k=i['key'][j].float().repeat_interleave(3,dim=0);v=i['value'][j].float();g=i['g'][j].float();beta=i['beta'][j].float()
 decay32=initial.float()*T.exp(g)[:,None,None];prediction=(decay32*k[:,None,:]).sum(-1)
 next32=decay32+((v-prediction)*beta[:,None])[:,:,None]*k[:,None,:];direct32=(next32*q.float()[:,None,:]).sum(-1)
 dif=(candidate.double()-rounded.double()).abs();uncast=(candidate.double()-truth).abs();peer=(candidate.double()-native.double()).abs();indices=set()
 for delta in(dif,uncast,peer):
  for index in delta.flatten().argsort(descending=True)[:8].tolist():indices.add(int(index))
 for index in T.nonzero(dif.flatten(),as_tuple=False).flatten().tolist():indices.add(int(index))
 cells=[]
 for index in sorted(indices):
  coord=(index//128,index%128);value=float(truth[coord]);cb=int(candidate[coord].view(T.int16).item())&65535;nb=int(native[coord].view(T.int16).item())&65535;rb=int(rounded[coord].view(T.int16).item())&65535
  c=cell(value,cb);n=cell(value,nb);r=cell(value,rb);midpoints={c['midpoint_low'],c['midpoint_high'],n['midpoint_low'],n['midpoint_high']}
  cells.append(dict(coord=list(coord),truth_CPU64=value,truth_sign=math.copysign(1.,value),candidate=c,native=n,direct_RNE=r,candidate_minus_native=float(candidate[coord])-float(native[coord]),candidate_RNE_bit_distance=abs(cb-rb),CPU64_truth_as_FP32=float(truth[coord].float()),CPU64_truth_as_FP32_is_midpoint=float(truth[coord].float())in midpoints,after_restored_CPU64_dot=float(restored64[coord]),after_restored_CPU32_dot=float(restored32[coord]),CPU32_direct_recurrence_dot=float(direct32[coord]),FP32_diagnostic_is_actual_NPU_precast=False))
 dominant=int(dif.flatten().argmax());report=dict(schema='deltalog035.step80-readout-diagnostic/v039',raw=m['selected_raw_ref'],original_failed_owner=m['original_failed_owner_ref'],request=j,slot=s,step=80,batch=16,old_output_limit=.00303,old_state_limit=7.92e-7,candidate_vs_direct_RNE=metric(T,candidate,rounded),native_vs_direct_RNE=metric(T,native,rounded),candidate_native_peer=metric(T,candidate,native),candidate_vs_unrounded_CPU64=metric(T,candidate,truth),RNE_floor=metric(T,rounded,truth),candidate_state_relative_l2=float((after-expected).norm()/max(float(expected.norm()),1e-30)),native_state_vs_candidate_before_local_reference=float((raw['native_state'][s].double()-expected).norm()/max(float(expected.norm()),1e-30)),dominant_RNE_gap_coord=[dominant//128,dominant%128],candidate_diff_RNE_cells=int(T.count_nonzero(dif)),native_diff_RNE_cells=int(T.count_nonzero(native.double()-rounded.double())),length_before=cap['before']['length'][s,:,0].tolist(),length_after=raw['state']['length'][s,:,0].tolist(),cells=cells,scope='independent local one-step CPU64 from candidate-before represented state, not separate native-before or full trajectory',actual_NPU_FP32_precast_available=False,qualification=False,old_failed160_unchanged=True)
 head,column=dominant//128,dominant%128;mp80=mp_column(cap['before'],i,s,j,head,column,80);mp100=mp_column(cap['before'],i,s,j,head,column,100)
 dominant_cell=next(c for c in cells if c['coord']==[head,column]);midpoints=sorted({dominant_cell[name][key]for name in('candidate','native','direct_RNE')for key in('midpoint_low','midpoint_high')})
 with decimal.localcontext()as ctx:
  ctx.prec=110;cpu64=decimal.Decimal.from_float(float(truth[head,column]));report['dominant_independent_MP']=dict(precision80=str(mp80),precision100=str(mp100),agreement_abs=str(abs(mp100-mp80)),CPU64_minus_MP100=str(cpu64-mp100),midpoint_margins=[dict(midpoint=point,MP80_minus_midpoint=str(mp80-decimal.Decimal.from_float(point)),MP100_minus_midpoint=str(mp100-decimal.Decimal.from_float(point)),CPU64_minus_midpoint=str(cpu64-decimal.Decimal.from_float(point)))for point in midpoints],scope='independent high-precision natural-exp recurrence on exact stored binary operands, not CANN Exp accuracy theorem or actual NPU precast')
 rr=out/'DIAGNOSIS.json';C.write(rr,report);return C.ref(rr)
