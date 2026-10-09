"""Independent full matrix receipt consumer for NEW author arithmetic only.
Source/whole terminal/CID/process/no-device/cleanup authority remains mandatory
in consume_numeric; no synthetic row or kernel fragment creates that authority.
"""
import json,math
from pathlib import Path
from contract import PROTOCOL,COMMIT,LIMITS,require,sha
def read_step(ref,root):
 p=Path(ref["path"]);guest=Path("/sparq-results/gate")
 require(guest in p.parents and ".." not in p.parts,"original image-owned complete case/step path")
 target=root/p.relative_to(guest)
 require(target.resolve()==target and target.is_file() and not target.is_symlink() and sha(target)==ref["sha256"],"actual original immutable case/step bytes")
 return json.loads(target.read_bytes())
def metrics(value,b):
 require(value.get("passed") is True and value.get("finite") is True,"actual independent every-head output finite/PASS")
 for key,lo,hi in (("relative_rms",0,.005),("cosine",.99998,1.000001)):
  rows=value[key];require(len(rows)==b and all(len(v)==6 for v in rows) and
   all(type(x) in (int,float) and math.isfinite(x) and lo<=x<=hi for v in rows for x in v),"original EVERY request/head .005/.99998, no averaging")
def topk_witness(value,k):
 require(value["selected_count"]==k and value["epsilon"]==0 and value["stable_token_ID_required"] is False,"author exact cutoff/ties, not old stable-ID contract")
 chosen=value["tied_selected"];excluded=value["tied_excluded"]
 require(type(chosen) is list and type(excluded) is list and len(chosen)==len(set(chosen)) and len(excluded)==len(set(excluded)) and
  not set(chosen)&set(excluded) and all(type(x) is int and x>=0 for x in chosen+excluded),"actual exact tie identities")
 cutoff=value["exact_cutoff"];require(type(cutoff) in (int,float) and math.isfinite(cutoff) or cutoff=="forced-positive-infinity","only explicit forced +Inf rank sentinel")
def validate_rank_layout(layout,n):
 require(type(n) is int and 0<n<=2304 and layout["protocol"]=="per-request-FP32-SUM0-fixed-capacity/v1" and
  type(layout["capacity"]) is int and layout["capacity"]==2304 and
  layout["live_length"]==n and layout["current_sentinel"]==n-1 and
  layout["own_inputs"] is True and layout["candidate_rank_or_score_used"] is False and
  layout["cropped_reduction_diagnostic_only"] is True and
  type(layout["cropped_vs_registered_difference_tokens"]) is list and
  len(layout["cropped_vs_registered_difference_tokens"])==len(set(layout["cropped_vs_registered_difference_tokens"])) and
  all(type(x) is int and 0<=x<n for x in layout["cropped_vs_registered_difference_tokens"]),
  "NEW registered fixed-capacity request-wise rank witness; old cropped gate not promoted")
 return layout
def validate_case_set(report,root,expected):
 from receipt import validate_cutoff_fields
 validate_cutoff_fields(report)
 require(report.get("schema")=="sparq.author-ann-disjoint-numeric/v1" and report.get("status")=="shard_passed" and
  report.get("limits")==LIMITS and report.get("precision_contract")==PROTOCOL and
  report.get("original_ba508_numeric_status")=="failed-not-promoted" and
  report.get("original011_numeric_status")=="failed-not-promoted","NEW author report only; old011 or observation not promoted")
 root=Path(root);require(root.is_absolute() and root.resolve()==root and root.is_dir(),"exact actual original new matrix root")
 require(not (root/"FAILURE.json").exists() and not list(root.glob("failure-*.pt")) and not list(root.glob("raw-failure-*.json")) and
  "secondary_source_error" not in report,"original first fault permanently invalidates this run")
 keys=set();steps=0
 for header in report["cases"]:
  b,m,c,t=(header[k] for k in ("batch","mode","reallocation","trial"));key=(b,m,c,t)
  require(type(b) is int and b in range(1,17) and type(c) is bool and (m,t) in (("eager",0),("graph",0),("graph",1),("graph",2)) and
   key not in keys,"unique full original128 coordinates");keys.add(key)
  case=read_step(header["actual_case_ref"],root)
  require(all(case[k]==header[k] for k in ("batch","mode","reallocation","trial")) and
   case["status"]=="passed" and case["steps"]==160 and len(case["actual_step_refs"])==160 and
   case["service_ready"] is False and case["model_graph_supported"] is False and
   case["worst_relative_rms"]<=.005 and case["minimum_cosine"]>=.99998 and
   case["actual_mean_bytes"]==18*(256*4+8)+128*(4+8) and case["mean_payload_bytes"]==18*(256*4+8) and
   case["actual_workspace_bytes"]>0,"complete original guarded case, not model permission")
  slots=list(range(b));live={s:2048-3*s for s in slots};generations={s:1 for s in slots+[16,17]}
  for index,ref in enumerate(case["actual_step_refs"]):
   row=read_step(ref,root)
   require((row["batch"],row["mode"],row["reallocation"],row["trial"],row["step"])==(b,m,c,t,index),"every160 ordered immutable steps")
   if index%11==0:slots=slots[1:]+slots[:1]
   if index==80:live[slots[0]]=1;generations[slots[0]]+=1
   lengths=[live[s]+1 for s in slots]
   require(row["actual_current_lengths"]==lengths and row["actual_slot_order"]==slots and
    row["actual_slot_generations"]=={str(s):g for s,g in generations.items()},"actual whole changing topology, shortened step80 ABA-safe reuse")
   for name in ("finite","full_native_cache_bitwise","selected_scratch_guard","input_untouched","mean_request_lease_checked","support_independent",
    "pointer_identity","workspace_mean_guards","all_topology_immutable","reference_feedback_independent","oracle_cpu_fp64","per_head_metric",
    "native_cache_input_outer_guards","static_tails_zero","selected_native_KV_exact","author_literal_outside_capture","literal_reference_never_captured"):
    require(row[name] is True,"actual complete original guard/oracle: "+name)
   require(row["precision_contract"]==PROTOCOL and row["author_commit"]==COMMIT and
    row["original011_status"]=="FAILED-not-promoted" and row["nonzero_score_tolerance"] is False and
    row["CPU32_stable_ID_required"] is False and row["native_PA_executed"] is False and
    row["dense_attention_equivalence_claimed"] is False and row["support_independent_query"]=="candidate-feedback-q" and
    row["graph_capture_scope"]=="actual native writer + mean append + registered FP32-compensation ANN only",
    "explicit NEW source arithmetic scope; no old PA/direct-reference capture claim")
   require(len(row["cross_feedback_support_divergence"])==b and all(type(x) is bool for x in row["cross_feedback_support_divergence"]) and
    row["reference_feedback_support_equal"]==(not any(row["cross_feedback_support_divergence"])),"independent reference feedback never shared")
   metrics({"passed":True,"finite":row["finite"],"relative_rms":row["relative_rms"],"cosine":row["cosine"]},b)
   metrics(row["author_conditional_fp64_metric"],b)
   diagnostic=row["author_literal_output_metric"]
   require(row["author_literal_output_hard_gate"] is False and row["literal_output_deviation_complete_every_head"] is True and
    row["original_BF16_dual_gate_status"]=="FAILED-not-promoted" and
    row["finite_precision_variant"]=="FP32 alpha/softmax/V-MV/mean compensation; one BF16 output" and
    diagnostic["finite"] is True and type(diagnostic["passed"]) is bool,"explicit new registered FP32 adaptation, not literal BF16 parity")
   for field in ("relative_rms","cosine"):
    require(len(diagnostic[field])==b and all(len(x)==6 for x in diagnostic[field]) and
     all(type(v) in (int,float) and math.isfinite(v) for x in diagnostic[field] for v in x),
     "every actual head complete literal deviation, no unsampled or suppressed comparison")
   calculated=all(v<=.005 for x in diagnostic["relative_rms"] for v in x) and all(v>=.99998 for x in diagnostic["cosine"] for v in x)
   require(diagnostic["passed"]==calculated,"actual complete literal diagnostic classification retained")
   require(row["FP64_reselect_formal"] is False and row["candidate_data_used_by_formal_reference"] is False and
    row["full_original_qKV_FP64_recomputed"] is True and row["literal_selector_observation_restored"] is True and
    row["reference_selector"]=="own BF16 literal author q/rq independent","own literal selector + own original q/K/V FP64, diagnostic reselect never gates")
   for name in ("author_reference_q_selector_witness","author_reference_rq_selector_witness"):
    require(len(row[name])==b,"every own q/rq literal selector witness")
    for n,w in zip(lengths,row[name]):
     topk_witness(w["support_contract"],min(n,128))
     require(w["literal_source_same_invocation"] is True and w["outside_capture"] is True and w["selector_feedback_never_shared"] is True and
      w["candidate_selected_channels_score_alpha_used"] is False and w["fp64_reselect_formal"] is False and
      w["score_observation_used_only_for_legality"] is True,"exact own invocation trace, never candidate operand substitution")
   require(len(row["author_legal_topk"])==b,"every request strict author stage witness")
   for n,w in zip(lengths,row["author_legal_topk"]):
    topk_witness(w["channel_contract"],32);topk_witness(w["support_contract"],min(n,128))
    require(w["nonzero_score_tolerance"] is False and w["CPU32_stable_ID_spec"] is False and
     w["reference"]=="independent original-dtype per-head NPU operators","actual independent source-stage oracle")
    validate_rank_layout(w["rank_layout"],n)
   for s in slots:live[s]+=1
   steps+=1
 require(type(expected) is set and expected and expected<={(b,m,c,t) for b in range(1,17) for m,t in (("eager",0),("graph",0),("graph",1),("graph",2)) for c in (False,True)},"exact registered assigned coordinates")
 require(keys==expected and steps==160*len(expected),"complete declared shard only; never original128 PASS")
 return {"cases":len(expected),"changing_feedback_steps":steps,"precision_contract":PROTOCOL,"author_commit":COMMIT,
  "numerical_component_checked":False,"shard_receipts_checked":True,"author_literal_output_hard_gate":False,
  "original_BF16_dual_gate_status":"FAILED-not-promoted","original011_status":"FAILED-not-promoted","ready":False,"service_ready":False,
  "model_executed":False,"matched1024_e2e_verified":False,"final2048_task_verified":False}
