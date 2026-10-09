"""Real Devices[] CPU arithmetic preflight, never native/graph/model admission."""
from pathlib import Path
from contract import PROTOCOL,read_ref,require,sha,write_new
from ann_workspace import ANNWorkspace,substrate
from literal_author import build,reference
from independent_oracle import source_legality,author_feedback,metric
def validate(report):
 require(report["protocol"]==PROTOCOL and report["source_sha256"]==sha(Path(__file__).resolve()) and
  report["torch_npu_initialized_after"] is False and report["torch_threads"]==1 and report["npu_executed"] is False,
  "this-source true no-device author arithmetic smoke")
 read_ref(report["raw_before"])
 rows=report["cases"]
 require(len(rows)==4 and {(r["batch"],r["reallocation"]) for r in rows}=={(b,c) for b in (1,2) for c in (False,True)} and
  all(r["source_stage_checked"] is True and r["native_input_untouched"] is True and r["guards"] is True and
   r["candidate_data_used_by_formal_reference"] is False and r["FP64_reselect_formal"] is False and
   r["reference_selector"]=="own BF16 literal author q/rq independent" and r["literal_outside_capture"] is True and r["literal_output_metric"]["finite"] is True and r["author_literal_output_hard_gate"] is False and
   r["literal_output_deviation_complete_every_head"] is True and r["original_BF16_dual_gate_status"]=="FAILED-not-promoted" and
   r["conditional_fp64_metric"]["passed"] is True for r in rows),
  "all actual four CPU-BF16 source stages/full FP64 cases for NEW FP32 compensation, not kernel permission")
 return report

def observed_tensor(tensor):
 """Diagnostic-only complete CPU values; nonfinite raw values stay explicit.
 This serializer never replaces operands, changes a result or grants acceptance.
 """
 import math
 def value(x):
  if isinstance(x,list):return [value(v) for v in x]
  if type(x) is float and not math.isfinite(x):
   return "NaN" if math.isnan(x) else "+Infinity" if x>0 else "-Infinity"
  return x
 return {"dtype":str(tensor.dtype),"device":str(tensor.device),"shape":list(tensor.shape),
  "stride":list(tensor.stride()),"contiguous":bool(tensor.is_contiguous()),
  "values":value(tensor.detach().cpu().tolist())}
def publish_validate(report,output_root,host_alias):
 """Retain all four actual cases BEFORE the original validation predicate.
 Atomic exclusive publication and actual host alias bytes are mandatory.
 A validation failure leaves the complete observation and first exception intact.
 """
 report=dict(report)
 observation={"schema":"sparq.author-ann-CPU-fourcase-before-validation/v1",
  "stage":"before_original_validate","report":report,"validation_attempted":False,
  "validation_passed":False,"native_numeric_ready":False,"model_ready":False,"npu_executed":False}
 result=write_new(Path(output_root)/"ANN_CPU_CASES_BEFORE_VALIDATE.json",observation)
 alias={"path":str(Path(host_alias)/"ANN_CPU_CASES_BEFORE_VALIDATE.json"),"sha256":result["sha256"]}
 read_ref(alias)
 report["raw_before_validate"]=alias
 return validate(report)

def smoke(torch,torch_npu,output,host_alias):
 output_root=Path(output) # Retain the original path before workspace output shadows this local.
 torch.set_num_threads(1);objects=build(torch);cases=[]
 before=write_new(Path(output)/"ANN_CPU_RAW_BEFORE.json",{"protocol":PROTOCOL,"stage":"before_arithmetic_assertions",
  "source_sha256":sha(Path(__file__).resolve()),"torch_npu_initialized":torch_npu.npu.is_initialized(),
  "device":"cpu","native_ATB_writer_executed":False,"numerical_component_checked":False})
 raw={"path":str(Path(host_alias)/"ANN_CPU_RAW_BEFORE.json"),"sha256":before["sha256"]}
 read_ref(raw)
 for batch in (1,2):
  workspace=ANNWorkspace("cpu",batch,18)
  rows=[[18*i+j for j in range(18)] for i in range(batch)];lengths=[129,257][:batch]
  workspace.rows.copy_(torch.tensor(rows,dtype=torch.int64));workspace.lengths.copy_(torch.tensor(lengths,dtype=torch.int32))
  q=((torch.arange(batch*6*256).view(batch,6,256)%17-8)/64).to(torch.bfloat16)
  k=((torch.arange((batch*18+1)*128*256).view(batch*18+1,128,1,256)%19-9)/64).to(torch.bfloat16)
  v=(1+(torch.arange(k.numel()).view_as(k)%31)/2048).to(torch.bfloat16)
  kbefore=k.clone();vbefore=v.clone()
  means=[]
  for row,n in zip(rows,lengths):
   ids=torch.tensor(row[:(n+127)//128]);value=v.index_select(0,ids).view(-1,256)[:n]
   means.append(value.float().sum(0)/n)
  mean=torch.stack(means)
  for correction in (False,True):
   output,selected,alpha,channels=workspace.run(q,k,v,mean,reallocation=correction)
   formal=author_feedback(torch,objects,q,k,v,rows,lengths,correction)
   for i,(row,n) in enumerate(zip(rows,lengths)):
    ids=torch.tensor(row[:(n+127)//128]);key=k.index_select(0,ids).view(-1,256)[:n];value=v.index_select(0,ids).view(-1,256)[:n]
    source_legality(torch,q[i],key,channels[i],selected[i],workspace.score[i],workspace.ranking[i],workspace.capacity)

   cases.append({"batch":batch,"reallocation":correction,"source_stage_checked":True,
    "literal_outside_capture":True,"native_input_untouched":bool(torch.equal(k,kbefore) and torch.equal(v,vbefore)),
    "guards":workspace.guards(),"candidate_data_used_by_formal_reference":False,"FP64_reselect_formal":False,
    "reference_selector":"own BF16 literal author q/rq independent","literal_selector_witnesses":formal["selector_witnesses"],"literal_output_metric":metric(torch,output,formal["literal_output"]),
    "conditional_fp64_metric":metric(torch,output,formal["output"]),
    "actual_outputs":{"candidate":observed_tensor(output),"literal_BF16":observed_tensor(formal["literal_output"]),
     "independent_CPU_FP64":observed_tensor(formal["output"])},
    "actual_selection":{"candidate_channels":observed_tensor(channels),"candidate_support":observed_tensor(selected),
     "candidate_alpha":observed_tensor(alpha),
     "literal_channels":[observed_tensor(x) for x in formal["channels"]],
     "literal_support":[observed_tensor(x) for x in formal["supports"]]},
    "raw_observation_is_not_acceptance":True,
    "finite_precision_variant":"FP32 alpha/softmax/V-MV/mean compensation; one BF16 output",
    "author_literal_output_hard_gate":False,"literal_output_deviation_complete_every_head":True,
    "original_BF16_dual_gate_status":"FAILED-not-promoted"})
 return publish_validate({"protocol":PROTOCOL,"source_sha256":sha(Path(__file__).resolve()),"cases":cases,"raw_before":raw,
  "torch_npu_initialized_after":torch_npu.npu.is_initialized(),"torch_threads":torch.get_num_threads(),"npu_executed":False},output_root,host_alias)
