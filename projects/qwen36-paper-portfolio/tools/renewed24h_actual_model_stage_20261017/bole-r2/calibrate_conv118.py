"""Admitted-NPU component function only; never selects/initializes a device."""
def execute(t,op,actual_schema,*,device,channels=2560,width=4,save=None,save_before=None):
    if str(getattr(op,'_schema',None))!=actual_schema:raise ValueError('observed dispatcher ABI required')
    if device.type!='npu':raise ValueError('MAIN admitted NPU only')
    if channels!=2560 or width!=4:raise ValueError('preregistered GDN 4/12 D128 local projection geometry')
    # SD oldest-to-newest chronology. Deliberately distinct time/channel values.
    rows=[]
    for b in (1,16):
        slots=2*b+3
        cache=(t.arange(slots*(width-1)*channels,dtype=t.float32).reshape(slots,width-1,channels)%29-14).div(64).bfloat16().to(device)
        ids=t.tensor([2*r+1 for r in range(b)],dtype=t.int32,device=device)
        w=((t.arange(channels*width,dtype=t.float32).reshape(channels,width)%11)-5).div(32).bfloat16().to(device)
        bias=None
        for activation in (False,True):
            active_cache=cache.clone()
            for step in range(3):
                x=((t.arange(b*channels,dtype=t.float32).reshape(b,channels)+7*step)%23-11).div(64).bfloat16().to(device)
                before=active_cache.clone();out=t.full_like(x,float('nan'));seq=t.arange(b+1,dtype=t.int32,device=device)
                invariant_before=[None if v is None else v.cpu().clone()for v in(x,w,bias,seq,ids)]
                if save_before is not None:save_before(len(rows),dict(batch=b,step=step,activation=activation,inputs=x.cpu(),weight=w.cpu(),bias=None,indices=ids.cpu(),before=before.cpu(),output=None))
                returned=op(out,x,w.transpose(0,1),conv_state=active_cache,bias_opt=bias,query_start_loc_opt=seq,cache_indices_opt=ids,initial_state_mode_opt=None,num_accepted_tokens_opt=None,activation_mode=int(activation),pad_slot_id=-1,run_mode=1)
                # Save BEFORE assertions; independent consumer must run on CPU.
                row=dict(batch=b,step=step,activation=activation,inputs=x.cpu(),weight=w.cpu(),bias=None,indices=ids.cpu(),before=before.cpu(),after=active_cache.cpu(),output=out.cpu(),returned=returned.cpu(),returned_alias_output=returned.data_ptr()==out.data_ptr(),invariant_before=invariant_before,invariant_after=[None if v is None else v.cpu().clone()for v in(x,w,bias,seq,ids)])
                if save is not None:save(len(rows),row)
                rows.append(row)
    return rows

def consume(t,rows,*,require_native_metadata=False):
    if len(rows)!=12:raise ValueError('B1/B16 activation0/1 three-step complete capture')
    expected_order=[(b,s,a)for b in(1,16)for a in(False,True)for s in range(3)]
    if [(r['batch'],r['step'],r['activation'])for r in rows]!=expected_order:raise ValueError('exact12 chronology matrix, no duplicate/omitted steps')
    results=[];previous={}
    for r in rows:
        b,step,act=r['batch'],r['step'],r['activation'];before=r['before'];after=r['after'];ids=r['indices'].long();key=(b,act)
        if before.dtype!=t.bfloat16 or after.dtype!=t.bfloat16 or r['inputs'].dtype!=t.bfloat16 or r['weight'].dtype!=t.bfloat16 or r['output'].dtype!=t.bfloat16:raise ValueError('actual model BF16 cache/input/weight/output only')
        if before.ndim!=3 or before.shape!=after.shape or before.shape[0]!=2*b+3 or before.shape[1]!=3:raise ValueError('exact SD whole cache geometry')
        c=before.shape[2]
        if r['inputs'].shape!=(b,c)or r['weight'].shape!=(c,4)or r['output'].shape!=(b,c)or(r['bias']is not None and r['bias'].shape!=(c,)):raise ValueError('exact no-broadcast tensor ABI')
        if r['indices'].dtype!=t.int32 or r['indices'].tolist()!=[2*j+1 for j in range(b)]:raise ValueError('real selected odd slots, no request/slot permutation')
        if not all(bool(t.isfinite(v).all())for v in(before,after,r['inputs'],r['weight'],r['bias'],r['output'])if v is not None):raise ValueError('finite diagnostic fixture and actual outputs')
        if require_native_metadata:
            bits=lambda a,b:(a is None and b is None)or(a is not None and b is not None and a.dtype==b.dtype and a.shape==b.shape and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8)))
            if len(r['invariant_before'])!=5 or len(r['invariant_after'])!=5 or not all(bits(a,b)for a,b in zip(r['invariant_before'],r['invariant_after'])):raise ValueError('native modified input/weight/bias/sequence/slot')
            if not bits(r['returned'],r['output']):raise ValueError('native return versus actual output buffer bytes')
        if step and not t.equal(before.view(t.uint8),previous[key].view(t.uint8)):raise ValueError('actual native multistep continuity')
        history=t.cat((before.index_select(0,ids).double(),r['inputs'].double().unsqueeze(1)),dim=1)
        truth=(history*r['weight'].double().T.unsqueeze(0)).sum(1)
        if r['bias']is not None:truth=truth+r['bias'].double()
        if act:truth=truth/(1+(-truth).exp())
        expected=before.clone();expected.index_copy_(0,ids,history[:,1:].to(before.dtype))
        state=t.equal(expected.view(t.uint8),after.view(t.uint8))
        error=(r['output'].double()-truth).abs();bound=.001+.01*truth.abs()
        good=bool(t.isfinite(r['output']).all()and(error<=bound).all())
        results.append(dict(batch=b,step=step,activation=act,state_bitwise=state,output_within_preregistered_bf16_bound=good,max_abs=float(error.max())))
        previous[key]=after
    return dict(schema='bole.native-conv-chronology-diagnostic/v118',rows=results,pass_gate=all(x['state_bitwise']and x['output_within_preregistered_bf16_bound']for x in results),model_ready=False)
