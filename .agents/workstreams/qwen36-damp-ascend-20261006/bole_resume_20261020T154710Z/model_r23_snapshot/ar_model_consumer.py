"""Independent CPU validation of all64 native-AR FA controls per rank."""
from sourceio import need
def bits(t,a,b):
 return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def consume(t,raw,m):
 anchors={x['layer']:x for x in raw['initial_FA_pages']};rows=[]
 for path in raw['native']:
  prior={}
  for step_index,step in enumerate(path['steps']):
   need(step['node']==(0 if step_index==0 else path['child']),'actual AR token chronology')
   for layer in range(3,64,4):
    cap=step['context']['captures'][layer];a=anchors[layer]
    pk=t.stack([a['key'][pos//128,pos%128,0]for pos in range(131)]).unsqueeze(1)
    pv=t.stack([a['value'][pos//128,pos%128,0]for pos in range(131)]).unsqueeze(1)
    ak=cap['after_key'];av=cap['after_value']
    need(ak.shape==av.shape==(132+step_index,1,256)and bits(t,ak[:131],pk)and bits(t,av[:131],pv),'actual source-joined AR cache prefix/length')
    need(bits(t,ak[-1:],cap['key'].reshape(1,1,256))and bits(t,av[-1:],cap['value'].reshape(1,1,256)),'actual source-joined final AR projected key/value')
    if step_index:need(bits(t,ak[:-1],prior[layer][0])and bits(t,av[:-1],prior[layer][1]),'actual root to child AR history')
    else:prior[layer]=(ak.clone(),av.clone())
    q=cap['query'].reshape(1,1,6,256).permute(0,2,1,3).contiguous()
    k=ak.permute(1,0,2).unsqueeze(0).contiguous();v=av.permute(1,0,2).unsqueeze(0).contiguous()
    record=cap['ar_fp16_boundary']
    need(record['source']==m['files']['ar_fp16_boundary.py']and record['qualification']==m['native_ar_boundary_repair']['evidence']and record['completed']is True and
     record['input_dtype']=='torch.float16'and record['output_dtype']=='torch.bfloat16'and record['kernel_kind']=='dense/BNSD/unmasked/ip0',
     'actual per-frame AR intervention receipt')
    for name,x in(('query',q),('key',k),('value',v)):
     cv=x.to(t.float16);need(bool(t.isfinite(cv).all()),'independent finite AR conversion')
     delta=(cv.double()-x.double()).abs()
     stats=dict(changed=int((delta!=0).sum()),elements=delta.numel(),peak_abs=float(delta.max()))
     need(record['cast'][name]==stats,'independent original AR conversion ledger')
    metrics=[];output=cap['output']
    need(output.shape==q.shape and output.dtype==t.bfloat16 and bool(t.isfinite(output).all()),'actual native AR output BF16')
    for dtype in(t.float64,t.float32):
     truth=[]
     for head in range(6):
      logits=k[0,0].to(dtype).mv(q[0,head,0].to(dtype))*(256**-.5)
      p=(logits-logits.max()).exp();p/=p.sum();truth.append(v[0,0].to(dtype).T.mv(p))
     truth=t.stack(truth).reshape(1,6,1,256);error=(output.double()-truth.double()).abs()
     metrics.append(dict(pointwise_pass=bool((error<=.001+.01*truth.double().abs()).all()),peak_abs=float(error.max())))
    rows.append(dict(path=path['child'],node=step['node'],layer=layer,double=metrics[0],float=metrics[1]))
 need(len(rows)==64,'all16 FA xfour native AR forwards')
 return dict(schema='bole.native-ar-full-model-independent-fa/v1',rows=rows,passed=all(r['double']['pointwise_pass']and r['float']['pointwise_pass']for r in rows),
  original_pointwise_bounds_unchanged=True,whole_model_qualified=False)
