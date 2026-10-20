"""Actual Ascend replay of all256 saved dense native-AR FA inputs."""
import argparse,hashlib,json,time,traceback
from pathlib import Path
def ref(p):
 p=Path(p);h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(2**20),b''):size+=len(b);h.update(b)
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def write(p,x):
 with p.open('x')as f:json.dump(x,f,sort_keys=True,allow_nan=False);f.write('\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--frames-ref');ap.add_argument('--output',type=Path);a=ap.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 fr=json.loads(a.frames_ref);assert ref(fr['path'])==fr
 import torch as t
 import torch_npu as n
 t.set_num_threads(4);assert t.npu.device_count()==1;t.npu.set_device(0);t.npu.matmul.allow_hf32=False
 frames=t.load(fr['path'],map_location='cpu',weights_only=False);assert len(frames)==256
 a.output.mkdir();rows=[];outputs=[];original_matches=0;errors=[];start=time.monotonic()
 variants=(('bf16-ip0',t.bfloat16,0),('bf16-ip2',t.bfloat16,2),('fp16-ip0',t.float16,0),('fp16-ip2',t.float16,2))
 with t.inference_mode():
  for frame_index,frame in enumerate(frames):
   q,k,v=(frame[x]for x in('query','key','value'))
   assert q.shape==(1,6,1,256)and k.shape==v.shape and k.shape[:2]==(1,1)and k.shape[2]in(132,133)and k.shape[3]==256
   assert q.dtype==k.dtype==v.dtype==t.bfloat16
   key=dict(frame=frame_index,**{x:frame[x]for x in('rank','path','node','layer')})
   for label,dtype,precise in variants:
    try:
     values=[x.to(device='npu:0',dtype=dtype)for x in(q,k,v)]
     assert all(bool(t.isfinite(x).all())for x in values)
     before=[x.clone()for x in values]
     out,aux=n.npu_fused_infer_attention_score(query=values[0],key=values[1],value=values[2],
      input_layout='BNSD',num_heads=6,num_key_value_heads=1,scale=256**-.5,
      actual_seq_lengths=[1],actual_seq_lengths_kv=[k.shape[2]],sparse_mode=0,
      pre_tokens=2147483647,next_tokens=2147483647,inner_precise=precise)
     assert out.shape==q.shape and out.dtype==dtype
     t.npu.synchronize()
     assert all(t.equal(x.contiguous().view(t.uint8),b.contiguous().view(t.uint8))for x,b in zip(values,before))
     actual=out.cpu().to(t.bfloat16);assert bool(t.isfinite(actual).all())
     metrics=[]
     for reference in(frame['reference64'],frame['reference32']):
      error=(actual.double()-reference.double()).abs()
      metrics.append(dict(pointwise_pass=bool((error<=.001+.01*reference.double().abs()).all()),peak_abs=float(error.max())))
     same=t.equal(actual.contiguous().view(t.uint8),frame['original'].contiguous().view(t.uint8))
     if label=='bf16-ip0':original_matches+=int(same)
     rows.append(dict(**key,variant=label,double=metrics[0],float=metrics[1],matches_saved_original=bool(same),kernel_error=None))
     outputs.append(dict(**key,variant=label,output=actual.clone()))
    except BaseException as error:
     item=dict(**key,variant=label,kernel_error=repr(error),traceback=traceback.format_exc())
     errors.append(item);rows.append(item)
  t.npu.synchronize()
 summary={label:dict(frames=sum(r['variant']==label for r in rows),
  failed=sum(r['variant']==label and(r['kernel_error']is not None or not(r['double']['pointwise_pass']and r['float']['pointwise_pass']))for r in rows))for label,_,_ in variants}
 with (a.output/'OUTPUTS.pt').open('xb')as f:t.save(outputs,f)
 result=dict(schema='bole.native-ar-fia-actual-savedinput-matrix/v1',
  source=ref(__file__),frames=fr,physical_npu=4,guest_npu=0,image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',
  torch_version=t.__version__,torch_npu_version=getattr(n,'__version__',None),
  actual_schema_family={key:str(value)for key,value in t.ops.npu.npu_fused_infer_attention_score._schemas.items()},
  original_bitwise_matches=original_matches,frame_count=256,summary=summary,rows=rows,errors=errors,
  outputs=ref(a.output/'OUTPUTS.pt'),elapsed=time.monotonic()-start,
  original_pointwise_limits_unchanged=True,model_ready=False,performance_ready=False,final_success=False)
 write(a.output/'RESULT.json',result)
 print(json.dumps(dict(original_bitwise_matches=original_matches,frame_count=256,summary=summary,errors=len(errors),elapsed=result['elapsed'])))
if __name__=='__main__':main()

