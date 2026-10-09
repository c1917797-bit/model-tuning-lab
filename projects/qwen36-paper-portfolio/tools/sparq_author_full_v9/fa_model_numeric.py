"""Independent full-row BF16 PA-output consumer. Stdlib only, no candidate calls.
This validates every query/head/dimension of actual selected scratch, NOT support
math or dense task equivalence. Missing writer provenance/64-layer coverage cannot
be promoted to model permission.
"""
import math,struct,sys
from pathlib import Path
import evidence as c
HEADS=6;DIM=256;BUDGET=128;RMS=.005;COS=.99998
def shape(row,want,dtype):
 c.require(row.get("shape")==list(want) and row.get("dtype")==dtype and row.get("byte_order")=="little"
  and row.get("native_format")==2,"exact actual BF16/layout/shape metadata")
def binary(ref,limit):
 c.require(set(ref)>={"path","sha256","size_bytes","shape","dtype","byte_order","native_format"},
  "complete actual binary Ref plus typed shape")
 p=Path(c.bound(ref["path"],ref["sha256"])["path"])
 c.require(p.stat().st_size==ref["size_bytes"] and 0<ref["size_bytes"]<=limit,"bounded exact binary size")
 return p.read_bytes()
def bf16(ref,shape_):
 shape(ref,shape_,"torch.bfloat16");raw=binary(ref,math.prod(shape_)*2)
 c.require(len(raw)==math.prod(shape_)*2,"entire BF16 payload, no sampling/truncation")
 return [struct.unpack("<f",struct.pack("<I",v[0]<<16))[0] for v in struct.iter_unpack("<H",raw)]
def integer(ref,shape_):
 shape(ref,shape_,"torch.int64");raw=binary(ref,math.prod(shape_)*8)
 c.require(len(raw)==math.prod(shape_)*8,"entire int64 payload")
 return [v[0] for v in struct.iter_unpack("<q",raw)]
def bfloat_round(v):
 c.require(math.isfinite(v),"finite independent FP64 oracle")
 bits=struct.unpack("<I",struct.pack("<f",v))[0]
 bits=((bits+0x7fff+((bits>>16)&1))>>16)&0xffff
 out=struct.unpack("<f",struct.pack("<I",bits<<16))[0]
 c.require(math.isfinite(out),"finite BF16-rounded FP64 oracle");return out
def one_head(q,k,v,count,actual):
 """Independent CPU-FP64 formula, lazy Torch CPU only, never candidate calls.
 Uses actual BF16 inputs converted separately to FP64 including V. CPU dot/
 softmax/MV are independent of selector/bmm/native NPU PA implementation.
 """
 c.require(len(q)==len(actual)==DIM and len(k)==len(v)==BUDGET*DIM and 0<count<=BUDGET,"entire independent selected-PA domain")
 import torch
 qt=torch.tensor(q,dtype=torch.float64,device="cpu")
 kt=torch.tensor(k,dtype=torch.float64,device="cpu").reshape(BUDGET,DIM)[:count]
 vt=torch.tensor(v,dtype=torch.float64,device="cpu").reshape(BUDGET,DIM)[:count]
 c.require(qt.dtype==kt.dtype==vt.dtype==torch.float64 and qt.device.type==kt.device.type==vt.device.type=="cpu",
  "independent CPU-FP64 query/K/V; no FP32 V regression")
 logits=torch.mv(kt,qt)/math.sqrt(DIM)
 weights=torch.softmax(logits,dim=0)
 expected=torch.mv(vt.T,weights).to(torch.bfloat16).double()
 out=torch.tensor(actual,dtype=torch.float64,device="cpu")
 c.require(bool(torch.isfinite(logits).all()) and bool(torch.isfinite(expected).all()) and bool(torch.isfinite(out).all()),
  "same original full finite reference metric")
 ee=float(torch.sum(expected*expected));aa=float(torch.sum(out*out))
 c.require(ee>0 and aa>0,"original nonzero-reference cosine domain")
 rms=math.sqrt(float(torch.sum((out-expected)**2))/ee)
 cosine=float(torch.sum(out*expected))/math.sqrt(aa*ee)
 return dict(relative_rms=rms,cosine=cosine,passed=rms<=RMS and cosine>=COS,
  dimensions=DIM,selected_tokens=count,reference="independent-CPU-FP64-MV-softmax-V-MV; actual-Torch-BF16-round")
def consume(observation):
 x=observation;batch=x["batch"];arm=x["arm"];frame=x["frame"]
 c.require(type(batch) is int and batch in range(1,17) and arm=="candidate" and
  type(frame) is list and len(frame)==batch and x.get("q_before_PA") is True and
  x.get("output_after_PA") is True and x.get("guards") is True and
  x.get("observation_graph") is True and x.get("formal_graph") is False,
  "actual current candidate diagnostic PA observation, not timing graph")
 c.require(len({r["rid"] for r in frame})==batch and all(type(r["generation"]) is int and r["generation"]>0
  and type(r["native_length"]) is int and r["native_length"]>0 and r["scheduled"]==1 for r in frame),
  "real request/generation/one-token native length frame")
 refs=x["snapshot_refs"];c.require(set(refs)=={"q","output","key","value","selected","alpha","channels"},
  "complete actual candidate q/output/selected scratch/metadata Ref set")
 q=bf16(refs["q"],(batch,HEADS,DIM));out=bf16(refs["output"],(batch,HEADS,DIM))
 key=bf16(refs["key"],(batch+1,BUDGET,1,DIM));val=bf16(refs["value"],(batch+1,BUDGET,1,DIM))
 ids=integer(refs["selected"],(batch,BUDGET));channels=integer(refs["channels"],(batch,32))
 # All alpha values are retained/hashed; alpha is NOT used by model mean-OFF.
 shape(refs["alpha"],(batch,HEADS),"torch.float32")
 alpha_raw=binary(refs["alpha"],batch*HEADS*4)
 c.require(len(alpha_raw)==batch*HEADS*4 and all(math.isfinite(v[0]) for v in struct.iter_unpack("<f",alpha_raw)),
  "actual complete finite probability-GQA-sum alpha; no extra epsilon gate")
 gather=x.get("original_native_selected_gather")
 if gather is not None:
  c.require(gather["capture"] is False and len(gather["rows"])==batch,"actual outside-capture complete original native gather")
  native=[];native_raw=[]
  for name in ("key","value"):
   ref=gather[name];raw=binary(dict(ref,shape=[batch,BUDGET,1,DIM],dtype="torch.bfloat16",byte_order="little",native_format=2),batch*BUDGET*DIM*2)
   native_raw.append(raw)
   native.append([struct.unpack("<f",struct.pack("<I",v[0]<<16))[0] for v in struct.iter_unpack("<H",raw)])
 result=[]
 for b,request in enumerate(frame):
  n=request["native_length"];count=min(n,BUDGET);chosen=ids[b*BUDGET:b*BUDGET+count]
  c.require(chosen==sorted(set(chosen)) and all(0<=t<n for t in chosen) and n-1 in chosen,
   "exact ordered valid selected-token PA domain and forced recent token")
  dims=channels[b*32:(b+1)*32];c.require(len(set(dims))==32 and all(0<=d<DIM for d in dims),
   "entire actual channel-ID domain")
  nk=key[b*BUDGET*DIM:(b+1)*BUDGET*DIM];nv=val[b*BUDGET*DIM:(b+1)*BUDGET*DIM]
  if gather is not None:
   row=gather["rows"][b];mapping=row["mapping"]
   c.require(row["rid"]==request["rid"] and row["generation"]==request["generation"] and row["full_native_length"]==n and
    [r["token"] for r in mapping]==chosen and all(r["offset"]==r["token"]%128 and
     r["block"]==row["block_table"][r["token"]//128] for r in mapping),"actual complete original native token mapping")
   for name,reference in zip(("key","value"),native_raw):
    actual=binary(refs[name],(batch+1)*BUDGET*DIM*2)
    lo=b*BUDGET*DIM*2;hi=lo+count*DIM*2
    c.require(actual[lo:hi]==reference[lo:hi],
     "selected scratch K/V bitwise differ from actual original native cache writer domain")
  heads=[]
  for h in range(HEADS):
   lo=(b*HEADS+h)*DIM;heads.append(one_head(q[lo:lo+DIM],nk,nv,count,out[lo:lo+DIM]))
  result.append(dict(request=request,selected=chosen,channels=dims,heads=heads))
 return dict(schema="sparq.actual-model-conditional-FA/v1",batch=batch,prefix=x["prefix"],epoch=x["epoch"],
  arm=arm,reference_independent_scalar=True,all_query_rows=True,all_six_heads=True,all_256_dimensions=True,
  reallocation=False,support_selection_not_proven_by_this_consumer=True,
  native_component_full_support_authority_still_required=True,rows=result,
  passed=all(h["passed"] for r in result for h in r["heads"]),model_ready=False)

def main():
 import argparse,json
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument("--execute",action="store_true");parser.add_argument("--observation")
 parser.add_argument("--observation-sha256");parser.add_argument("--output",type=Path)
 args=parser.parse_args()
 if not args.execute:
  print(json.dumps(dict(status="disabled",model_ready=False,npu_executed=False)));return
 c.require(args.observation and args.observation_sha256 and args.output,"explicit actual observation/newoutput")
 raw=c.obj(c.bound(args.observation,args.observation_sha256))
 c.require(raw.get("schema")=="sparq.actual-full-model-observation/v3" and raw.get("kind")=="actual-full-PA-snapshot"
  and raw.get("rank") in range(4),"whole source-bound actual FULL layer observation")
 result=consume(raw["value"])
 result.update(observation=dict(path=args.observation,sha256=args.observation_sha256),rank=raw["rank"],
  source=raw["source"],kernel_authority=raw["kernel_authority"],conditional_FA_only=True,model_ready=False,ready=False)
 ref=c.write(args.output,result);print(json.dumps(dict(result=ref,status="conditional-output-checked" if result["passed"] else "failed",model_ready=False)))
 if not result["passed"]:raise ValueError("actual conditional PA output failed unchanged numeric threshold")
if __name__=="__main__":main()
