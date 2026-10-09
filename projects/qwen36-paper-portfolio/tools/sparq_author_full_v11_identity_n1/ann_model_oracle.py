"""Independent ONLINE diagnostic consumer of original full q/K/V tensors.
Executes byte-bound literal author's BF16 selector independently (outside ACL
capture) then independent CPU-FP64 final QK/softmax/full selected V-MV. No candidate
support/channel/projected-score/alpha or feedback enters this formal reference.
Success receipts retain every-head full-vector reductions and source/hash
bindings; they do NOT claim post-mortem raw full-K/V replay. First failure retains
complete original one-request K/V/query and actual stage/output tensors.
"""
import hashlib,importlib,os,secrets,sys
from pathlib import Path
import source_contract as c,long_independent_oracle as long_reference
MODULES=None
def numerical_modules():
 global MODULES
 if MODULES is None:
  before=list(sys.path);manifest=c.obj(dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA))
  try:
   sys.path.insert(0,str(c.KERNEL))
   modules={}
   for name in ("contract","literal_author","independent_oracle"):
    m=importlib.import_module(name)
    c.require(Path(m.__file__).resolve()==c.KERNEL/(name+".py") and c.sha(m.__file__)==manifest["files"][name+".py"],
     "exact canonical author independent-program imports; foreign cache rejected")
    modules[name]=m
   MODULES=modules
  finally:sys.path[:]=before
 return MODULES
def tensor_ref(t):
 raw=t.detach().cpu().contiguous().view(__import__("torch").uint8).numpy().tobytes()
 return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw),shape=list(t.shape),dtype=str(t.dtype),
  device=str(t.device),observed_complete_tensor=True)
def full_reductions(t,actual,expected):
 # Reductions traverse ALL256 dimensions for EACH of all6heads/allrequests.
 a=actual.detach().cpu().double();e=expected.detach().cpu().to(t.bfloat16).double()
 c.require(a.shape==e.shape and a.shape[-2:]==(6,256),"complete own raw q/K/V CPU-FP64 final output")
 rows=[]
 for av,ev in zip(a,e):
  rr=[]
  for ah,eh in zip(av,ev):
   rr.append(dict(actual_energy=float(ah.square().sum()),reference_energy=float(eh.square().sum()),
    dot=float((ah*eh).sum()),squared_error=float((ah-eh).square().sum()),
    full_dimensions=256,actual_hash=tensor_ref(ah),reference_hash=tensor_ref(eh)))
  rows.append(rr)
 return rows
def first_failure(t,directory,prefix,epoch,row,raw,error):
 # Success vectors are checked by independent ONLINE program, not retained
 # TB-scale full-history dumps. One first failing row is completely preserved.
 root=Path(directory);final=root/("ANN-FAILURE-e%d-%s-r%d.pt"%(epoch,prefix.replace(".","_"),row))
 c.require(root.is_absolute() and Path("/cache/cch") in root.parents and not final.exists(),"new actual first fault, no overwrite")
 payload={n:x.detach().cpu().clone() if isinstance(x,t.Tensor) else x for n,x in raw.items()}
 total=sum(x.numel()*x.element_size() for x in payload.values() if isinstance(x,t.Tensor))
 c.require(total<=256*1024**2,"complete first-row raw evidence <=256MiB; never truncate")
 tmp=final.with_name("."+final.name+".pending-"+secrets.token_hex(16))
 try:
  with tmp.open("xb") as out:t.save(payload,out);out.flush();os.fsync(out.fileno())
  os.link(tmp,final,follow_symlinks=False)
  fd=os.open(str(root),os.O_RDONLY|os.O_DIRECTORY)
  try:os.fsync(fd);tmp.unlink();os.fsync(fd)
  finally:os.close(fd)
 except BaseException:
  print("ANN_FIRST_FAULT_PUBLISH "+str(tmp),flush=True);raise
 c.write(final.with_suffix(".json"),dict(schema="sparq.author-ann-model-first-fault/v1",original_error=repr(error),
  original_complete_payload=c.bound(final,c.sha(final)),full_history_tensor_bytes=total,
  epoch=epoch,prefix=prefix,row=row,ready=False))
def check_layer(t,sample,native,frame,lengths,prefix,epoch,directory,core,geometry_proof):
 t.set_num_threads(1) # Diagnostic four rank workers each one CPU; never formal timing.
 from ann_fa_consumer import consume
 mods=numerical_modules();literal=mods["literal_author"];independent=mods["independent_oracle"];objects=literal.build(t)
 kc,vc,table=native;b=sample.batch
 c.require(len(frame)==len(lengths)==b and len({r["rid"] for r in frame})==b,"every actual request original frame")
 tables=table.detach().cpu().tolist();rows=[]
 for i,(request,n) in enumerate(zip(frame,lengths)):
  raw=dict(epoch=epoch,prefix=prefix,row=i,request=request,original_native_length=n,original_block_table=tables[i])
  try:
   c.require(type(n) is int and 0<n<=sample.owner.pages*128 and request["native_length"]==n,"actual complete full native length")
   ids=t.tensor(tables[i][:(n+127)//128],dtype=t.int64,device=kc.device)
   key=kc.index_select(0,ids).view(-1,256)[:n];value=vc.index_select(0,ids).view(-1,256)[:n]
   query=sample.q[i];actual=sample.output[i]
   raw.update(query=query,key=key,value=value,actual_output=actual,
    candidate_channels=sample.channels[i],candidate_support=sample.selected[i],
    candidate_score=sample.score[i],candidate_ranking=sample.ranking[i])
   # INDEPENDENT literal author receives only original q and original full cache.
   reference=literal.reference(t,objects,query[None],key[None],value[None],False,outside_capture=True)
   dims=reference["channels"][0].detach().cpu().long();chosen=reference["indices"][0].detach().cpu().long()
   fp64=independent.conditional(t,query,key,value,dims,chosen,False)
   raw.update(literal_output=reference["output"][0],reference_channels=dims,reference_support=chosen,
    FP64_output=fp64["output"],literal_projected_scores=reference["score_observation"][0])
   # Same source-bound strict stage equality as numeric v2: not relaxed here.
   # Independent domain comes from actual retained native table, not selector score.
   pages=len(tables[i]);proof=geometry_proof
   c.require(pages==sample.owner.pages and sample.score.shape[-1]==sample.ranking.shape[-1]==pages*128,
    "actual native table/full captured score owner geometry equality")
   legality=long_reference.source_legality(t,query,key,sample.channels[i],sample.selected[i],
    sample.score[i],sample.ranking[i],pages,proof,mods["contract"].topk_legal)
   own_witness=independent.literal_support_witness(t,reference,n)
   fp64_metric=independent.metric(t,actual[None],fp64["output"][None])
   literal_metric=independent.metric(t,actual[None],reference["output"])
   selected=sample.selected[i,:min(n,128)]
   sp=tables[i]
   tokens=selected.detach().cpu().tolist()
   block=t.tensor([sp[int(x)//128] for x in tokens],dtype=t.int64,device=kc.device)
   offsets=t.tensor([int(x)%128 for x in tokens],dtype=t.int64,device=kc.device)
   gathered_key=kc[block,offsets,0,:];gathered_value=vc[block,offsets,0,:]
   c.require(t.equal(sample.key[i].view(128,256)[:min(n,128)],gathered_key) and
    t.equal(sample.value[i].view(128,256)[:min(n,128)],gathered_value),"actual selected scratch bitwise matches original native KV")
   c.require(bool((sample.owner.key[16:17]==0).all().cpu()) and bool((sample.owner.value[16:17]==0).all().cpu()),
    "fixed extra guard row16 never becomes batch-view valid scratch")
   row=dict(request=request,original_length=n,literal_source_selector=own_witness,strict_candidate_source_stage=legality,
    independent_FP64_output=fp64_metric,independent_literal_BF16_output=literal_metric,
    final_output_dtype="torch.bfloat16",compensation_dtype="torch.float32",literal_BF16_hard_gate=False,
    literal_deviation_status="within-original-hard-thresholds" if literal_metric["passed"] else "outside-original-hard-thresholds-diagnostic-only",
    FP64_full_vector_reductions=full_reductions(t,actual[None],fp64["output"][None])[0],
    literal_full_vector_reductions=full_reductions(t,actual[None],reference["output"])[0],
    complete_original_inputs={k:tensor_ref(x) for k,x in (("q",query),("K",key),("V",value))},
    literal_channels=dims.tolist(),literal_support=chosen.tolist(),
    candidate_channels=sample.channels[i].detach().cpu().tolist(),candidate_support=selected.detach().cpu().tolist(),
    original_native_selected_KV_bitwise=True,mean_configuration=False,meanON_coverage_claimed=False,
    reference_selected_from_own_full_original_qKV=True,candidate_data_used_by_reference=False,
    FP64_reselect_formal=False,all_dimensions=256,all_heads=6,online_independent_consumer=True,
    postmortem_full_qKV_replay_claimed=False)
   # Independent receipt consumer re-derives every unchanged metric from
   # complete per-head reductions. It never calls candidate/workspace code.
   consume(dict(schema="sparq.actual-model-author-ann-FP32-FA/v2",batch=1,prefix=prefix,epoch=epoch,
    frame=[request],rows=[row],mean_configuration=False,source_ANN=dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA),
    complete_online_full_qKV_literal_FP64=True,postmortem_full_qKV_replay=False))
   rows.append(row)
  except BaseException as error:
   try:first_failure(t,directory,prefix,epoch,i,raw,error)
   except BaseException as secondary:
    print("ANN_ORACLE_ORIGINAL_FIRST_ERROR "+repr(error)+"; raw retention secondary="+repr(secondary),flush=True)
   raise
 out=dict(schema="sparq.actual-model-author-ann-FP32-FA/v2",batch=b,prefix=prefix,epoch=epoch,frame=frame,rows=rows,
  mean_configuration=False,source_ANN=dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA),
  complete_online_full_qKV_literal_FP64=True,postmortem_full_qKV_replay=False,
  observer_literal_never_captured=True,model_ready=False)
 consume(out);return out
