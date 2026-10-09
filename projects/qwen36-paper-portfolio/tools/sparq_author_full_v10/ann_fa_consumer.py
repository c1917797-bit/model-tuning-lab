"""Independent whole FA receipt consumer of complete ONLINE vector reductions.
No Torch import, candidate, selector rerun, borrowed support or hidden epsilon.
This validates original .005/.99998 on EVERY request/head/dimension; it does not
invent a postmortem full-K/V replay nor active GDN dense equivalence.
"""
import math,re
import source_contract as c,long_independent_oracle as long_reference
RMS=.005;COS=.99998
def reductions(values,metric):
 c.require(type(values) is list and len(values)==6 and metric["passed"] is True and metric["finite"] is True,
  "actual complete six-head independent output result")
 for i,row in enumerate(values):
  c.require(row["full_dimensions"]==256 and all(type(row[k]) in (float,int) and math.isfinite(row[k]) for k in
   ("actual_energy","reference_energy","dot","squared_error")),"complete finite whole256dim reduction")
  aa,ee,dot,err=[row[k] for k in ("actual_energy","reference_energy","dot","squared_error")]
  c.require(aa>0 and ee>0 and err>=0,"original nonzero-reference output metric domain, no epsilon")
  rms=math.sqrt(err/ee);cos=dot/math.sqrt(aa*ee)
  c.require(rms<=RMS and cos>=COS and metric["relative_rms"][0][i]<=RMS and metric["cosine"][0][i]>=COS,
   "unchanged every-head output threshold; no averaging or sampled dimensions")
  for name in ("actual_hash","reference_hash"):
   r=row[name];c.require(r["shape"]==[256] and r["dtype"]=="torch.float64" and r["size_bytes"]==2048 and
    re.fullmatch("[a-f0-9]{64}",r["sha256"]) and r["observed_complete_tensor"] is True,"complete vector hash, not guessed golden")
 return True
def literal_diagnostic(values,metric,status):
 """Full literal deviations retained, recomputed; never a hard parity gate."""
 c.require(type(values) is list and len(values)==6 and metric["finite"] is True and
  type(metric["passed"]) is bool and len(metric["relative_rms"])==len(metric["cosine"])==1 and
  len(metric["relative_rms"][0])==len(metric["cosine"][0])==6,"complete literal all-six-head diagnostics")
 accepted=[]
 for i,row in enumerate(values):
  c.require(row["full_dimensions"]==256 and all(type(row[k]) in (float,int) and math.isfinite(row[k]) for k in
   ("actual_energy","reference_energy","dot","squared_error")),"literal whole256 finite reductions, not sampled")
  aa,ee,dot,err=[row[k] for k in ("actual_energy","reference_energy","dot","squared_error")]
  c.require(aa>0 and ee>0 and err>=0,"original literal metric domain unchanged; no epsilon")
  rms=math.sqrt(err/ee);cos=dot/math.sqrt(aa*ee)
  mr,mc=metric["relative_rms"][0][i],metric["cosine"][0][i]
  c.require(all(type(v) in (float,int) and math.isfinite(v) for v in (mr,mc)) and mr>=0 and
   (rms<=RMS and cos>=COS)==(mr<=RMS and mc>=COS),
   "literal serializer threshold classification agrees with independent full reductions; no cross-program bitwise float spec")
  for name in ("actual_hash","reference_hash"):
   r=row[name];c.require(r["shape"]==[256] and r["dtype"]=="torch.float64" and r["size_bytes"]==2048 and
    re.fullmatch("[a-f0-9]{64}",r["sha256"]) and r["observed_complete_tensor"] is True,"complete literal vector hash")
  accepted.append(rms<=RMS and cos>=COS)
 c.require(metric["passed"]==all(accepted) and status==("within-original-hard-thresholds" if all(accepted) else
  "outside-original-hard-thresholds-diagnostic-only"),"literal deviations never silently omitted or called parity")
 return dict(complete=True,hard_gate=False,within_original_thresholds=all(accepted))
def witness(w,k):
 c.require(w["selected_count"]==k and w["epsilon"]==0 and w["stable_token_ID_required"] is False,
  "author arbitrary exact tie only; stable low-ID never invented")
 c.require(type(w["tied_selected"]) is list and type(w["tied_excluded"]) is list and
  len(set(w["tied_selected"]))==len(w["tied_selected"]) and
  not set(w["tied_selected"])&set(w["tied_excluded"]),"actual disjoint exact tie IDs")
def consume(x):
 b=x["batch"]
 c.require(x["schema"]=="sparq.actual-model-author-ann-FP32-FA/v2" and type(b) is int and b in range(1,17) and
  len(x["rows"])==len(x["frame"])==b and x["mean_configuration"] is False and
  x["complete_online_full_qKV_literal_FP64"] is True and x["postmortem_full_qKV_replay"] is False and
  x["source_ANN"]==dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA),
  "every actual author meanOFF row and honest independent-online scope")
 for row,req in zip(x["rows"],x["frame"]):
  n=row["original_length"];k=min(n,128)
  c.require(row["request"]==req and req["native_length"]==n and type(n) is int and n>0 and
   row["all_heads"]==6 and row["all_dimensions"]==256 and row["mean_configuration"] is False and
   row["meanON_coverage_claimed"] is False and row["reference_selected_from_own_full_original_qKV"] is True and
   row["candidate_data_used_by_reference"] is False and row["FP64_reselect_formal"] is False and
   row["online_independent_consumer"] is True and row["postmortem_full_qKV_replay_claimed"] is False and
   row["original_native_selected_KV_bitwise"] is True,"no borrowed candidate reference or meanON substitution")
  c.require(len(row["literal_channels"])==32 and len(set(row["literal_channels"]))==32 and
   len(row["literal_support"])==k and len(set(row["literal_support"]))==k and n-1 in row["literal_support"] and
   all(type(i) is int and 0<=i<n for i in row["literal_support"]),"literal independent full-domain support")
  c.require(len(row["candidate_support"])==k and len(set(row["candidate_support"]))==k and
   n-1 in row["candidate_support"] and all(0<=i<n for i in row["candidate_support"]),"candidate valid author rank-order support, NOT sorted token ID")
  for name,shape,size in (("q",[6,256],6*256*2),("K",[n,256],n*256*2),("V",[n,256],n*256*2)):
   r=row["complete_original_inputs"][name];c.require(r["shape"]==shape and r["size_bytes"]==size and
    r["dtype"]=="torch.bfloat16" and r["observed_complete_tensor"] is True and
    re.fullmatch("[a-f0-9]{64}",r["sha256"]),"complete original q/K/V identities, no selected-cache self-golden")
  leg=row["strict_candidate_source_stage"]
  witness(leg["channel_contract"],32);witness(leg["support_contract"],k)
  long_reference.consume_domain(leg["rank_layout"],n)
  c.require(leg["nonzero_score_tolerance"] is False and leg["CPU32_stable_ID_spec"] is False,
   "native v2 exact stage comparison unchanged")
  own=row["literal_source_selector"];witness(own["support_contract"],k)
  c.require(own["literal_source_same_invocation"] is True and own["outside_capture"] is True and
   own["candidate_selected_channels_score_alpha_used"] is False,"independent byte-bound source selector outside original ACL")
  reductions(row["FP64_full_vector_reductions"],row["independent_FP64_output"])
  literal_diagnostic(row["literal_full_vector_reductions"],row["independent_literal_BF16_output"],row["literal_deviation_status"])
  c.require(row["final_output_dtype"]=="torch.bfloat16" and row["compensation_dtype"]=="torch.float32" and
   row["literal_BF16_hard_gate"] is False,"registered FP32 compensation is not literal BF16 output equivalence")
 return dict(batch=b,prefix=x["prefix"],epoch=x["epoch"],passed=True,mean_configuration=False,
  reference="independent own literal BF16 full-domain selector + own original q/K/V CPU-FP64 output",
  all_rows=True,all_six_heads=True,all_256_dimensions=True,literal_complete_diagnostic=True,literal_hard_gate=False,compensation_dtype="torch.float32",postmortem_full_qKV_replay=False,model_ready=False)
