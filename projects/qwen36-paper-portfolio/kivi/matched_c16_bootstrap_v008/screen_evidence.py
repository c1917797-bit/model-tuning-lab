"""Independent HTTP/actual ingress and native-finish boundary replay. No tensor claims."""
import json
from pathlib import Path
import screen_contract as c
import transport
def expected(recipe,read):
 plan=read(recipe["declared_ingress_plan_ref"]);rows=c.rows(recipe["run_id"])
 c.need(len(plan["rows"])==42 and recipe["screen_output_counts"]==[2,2]+[1024]*40,"exact42 fixed protocol owners")
 for actual,want in zip(plan["rows"],rows):
  c.need(actual["header_request_id"]==want["header_id"]and actual["body_request_id"]is None
   and actual["declared_server_id"]=="cmpl-"+want["header_id"]
   and actual["declared_passed_id"]==actual["declared_server_id"]+"-0"
   and read(actual["prompt_token_ids_ref"])==c.prompt(want["prompt_index"]),"original declared full prompt/header protocol")
 return plan,rows
def retirement_path(recipe,ident,rank,rid):
 prefix="r%d-p%d-s%d"%(rank,ident["pid"],ident["start_ticks"])
 return Path(recipe["diagnostic_root"])/(prefix+"-PACKED-QWEN-r%d-RETIRE-%s.json"%(rank,rid))
def retirement(ref,recipe,ident,rank,rid,read):
 row=read(ref)
 c.need(row["schema"]=="kivi.actual-packed-qwen-retire/v1"and row["rank"]==rank and row["identity"]==ident
  and row["request_id"]==rid and row["actual_native_finished"]is True and row["model_ready"]is False,
  "actual all4 native retirement, not HTTP completion")
 c.need(Path(ref["path"])==retirement_path(recipe,ident,rank,rid),"exact actual rank-owned native finish path")
 return row
def rank_bundle(ref,recipe,recipe_ref,rank,ident,read,bindings,oracle,installer_sha):
 value=read(ref);plan,rows=expected(recipe,read);ids=[r["declared_passed_id"]for r in plan["rows"]]
 c.need(value["rank"]==rank and value["identity"]==ident and value["finished"]==sorted(ids)
  and value["complete_per_token_journal"]is value["numeric_verified"]is value["model_ready"]is value["run_authority"]is False,
  "actual all42 finished boundary bundle, not per-token/numerical evidence")
 if recipe["algorithm_arm"]=="candidate":
  c.need(value["schema"]=="kivi.c16-timing-native-final/v1","actual candidate timing bundle")
  owner=read(value["owner_ref"]);final=read(value["final_ref"]);event=read(value["event_ref"])
  c.need(final["schema"]=="kivi.actual-packed-qwen-installer-final/v1"
   and final["owner_ref"]==value["owner_ref"]and final["event_ref"]==value["event_ref"]
   and final["rank"]==rank and final["identity"]==ident and final["finished"]==sorted(ids)
   and final["source_sha256"]==installer_sha and final["diagnostic"]is False
   and final["timing_model_prerequisite_external"]is True
   and final["allocation_replaced"]is final["graph_checked"]is final["model_ready"]is final["run_authority"]is False,
   "actual original Book.close/all16 restore with observation OFF")
  c.need(event["rank"]==rank and event["identity"]==ident and len(event["layers"])==64,
   "whole actual native layout retained")
 else:
  c.need(value["schema"]=="kivi.c16-dense-native-final/v1"and value["source_ref"]==recipe["source_ref"]
   and value["recipe_ref"]==recipe_ref and value["original_update_restored"]is True
   and value["runner_source_sha256"]==bindings.NPU_SHA,"original native OFF update restored")
  owners=read(c.ref(recipe["rank_bindings_path"]))
  owner=dict(container_id=recipe["container_id"],rank_bindings=owners["rank_bindings"],
   declared_ingress_plan_ref=recipe["declared_ingress_plan_ref"],
   actual_frontend_binding_ref=c.ref(recipe["frontend_binding_path"]),
   actual_rank_bindings_ref=c.ref(recipe["rank_bindings_path"]),declared_passed_request_ids=ids,
   prompt_lengths={rid:32768 for rid in ids})
 verifier=bindings.Verifier(oracle);seen=set();retired=[];ingress=[];updates=[];epochs={}
 for rr in value["boundary_refs"]:
  row=read(rr);schema=row["schema"]
  if schema=="kivi.actual-native-ingress/v1":
   seen.update(verifier([rr],owner,rank,ident,seen));ingress.append(row["req_id"])
  elif schema=="kivi.actual-packed-qwen-retire/v1":
   rid=row["request_id"];retirement(rr,recipe,ident,rank,rid,read)
   c.need(rid in seen and rid not in retired,"actual unique ingress before retire")
   if recipe["algorithm_arm"]=="candidate":
    slot,epoch=row["slot"],row["epoch"]
    c.need(type(slot)is int and 0<=slot<16 and type(epoch)is int and epoch==epochs.get(slot,0)+1,
     "actual disjoint slot0..15 lifecycle; epoch increments only after preceding owner retired")
    epochs[slot]=epoch
   retired.append(rid)
  elif schema=="kivi.actual-packed-qwen-update/v1":
   c.need(recipe["algorithm_arm"]=="candidate"and row["rank"]==rank and row["identity"]==ident
    and row["runner_source_sha256"]==bindings.NPU_SHA,"original candidate lifecycle boundary")
   for r in row["finished_req_ids"]:
    c.need(r in seen and r not in row["requests_after"]and r not in row["batch_after"],
     "actual native update confirms request/batch removal")
   updates.append(row)
  else:raise ValueError("raw/per-token/failure schema forbidden in timing boundary bundle")
 c.need(len(ingress)==len(retired)==42 and set(ingress)==set(retired)==seen==set(ids)
  and ingress[:2]==retired[:2]==ids[:2],"all42 actual owners; measured completion order is native, not declaration order")
 if recipe["algorithm_arm"]=="candidate":
  finished=[r for row in updates for r in row["finished_req_ids"]]
  c.need(len(finished)==42 and set(finished)==set(ids)
   and all(len(row["batch_after"])<=16 and len(set(row["batch_after"]))==len(row["batch_after"])for row in updates),
   "all42 native finished updates and actual max16 batch; no exact batch grouping guessed")
  c.need(any(epoch>1 for epoch in epochs.values()),"actual slots recycled across42 owners")
 return dict(rank=rank,bundle_ref=ref,finished=retired,actual_ingress_checked=True,numeric_verified=False)
def client(value,recipe,recipe_ref,read,bindings,oracle,installer_sha):
 c.need(value["schema"]=="kivi.c16-fixed1024-client/v1"and value["status"]=="FIXED1024_HTTP_NATIVE_FINISHED"
  and value["source_ref"]==recipe["source_ref"]and value["recipe_ref"]==recipe_ref
  and value["algorithm_arm"]==recipe["algorithm_arm"]and value["input_protocol_ref"]==recipe["actual_input_protocol_ref"]
  and value["model_ready"]is value["performance_ready"]is value["run_authority"]is False,
  "exact actual arm/client/source without borrowed performance permission")
 plan,rows=expected(recipe,read);report=read(value["http_report_ref"]);root=Path(value["http_report_ref"]["path"]).parent
 c.need(report["schema"]=="kivi.c16-fixed1024-http/v1"and report["protocol"]==c.PROTOCOL and len(report["rows"])==42,
  "40 measured1024 and two full prompt warmups")
 owners=read(c.ref(recipe["rank_bindings_path"]));ids=owners["rank_bindings"]
 for i,(record,want)in enumerate(zip(report["rows"],rows)):
  c.need(record["plan"]==want,"exact HTTP order")
  transport.replay(read(record["response"]),want,root)
  c.need(len(record["native_retirement_refs"])==4,"all4 retirement refs after each HTTP request")
  for rank,rr in enumerate(record["native_retirement_refs"]):
   retirement(rr,recipe,ids[str(rank)],rank,plan["rows"][i]["declared_passed_id"],read)
 c.need(report["metrics"]==value["metrics"]==c.metrics([read(row["response"])for row in report["rows"][2:]]),"original full E2E metrics")
 c.need(len(value["rank_bundle_refs"])==4,"complete actual rank finals")
 finals=[rank_bundle(rr,recipe,recipe_ref,rank,ids[str(rank)],read,bindings,oracle,installer_sha)
  for rank,rr in enumerate(value["rank_bundle_refs"])]
 return dict(metrics=report["metrics"],rank_boundaries=finals,whole_http_replayed=True,
  native_finished_replayed=True,full1024_numerical_verified=False,performance_accepted=False)
