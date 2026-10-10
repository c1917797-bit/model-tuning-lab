"""Foreground collect16, only metadata seals while model lease lives. No CPU oracle."""
import argparse,json,time,importlib.util,sys
from pathlib import Path
def run(l,m,source,recipe_ref,output,port):
 recipe=l.obj(recipe_ref);root=Path(recipe["raw_root"]);diag=Path(recipe["diagnostic_root"])
 l.need(recipe["source_ref"]==source,"same actual mixed recipe")
 mods={k:l.module("_mixed_client_"+k,m["runtime_roles"][k]) for k in
  ("client_stage","input_lifecycle","transport","capture_receipt","resource_ledger")}
 mods["geometry"]=l.geometry_modules(m)[1]
 rank_ref,rank=l.module("_mixed_client_ownership",l.own(m,"ownership.py")).await_ref(recipe["rank_bindings_path"],l.obj)
 ids=rank["rank_bindings"]
 # Actual geometry before first HTTP: no fixture capacity and no silent raw budget truncation.
 owners=[];events=[];geometries=[]
 for r in range(4):
  ident=ids[str(r)]
  path=diag/("r%d-p%d-s%d-PACKED-QWEN-r%d-INSTALL-OWNER.json"%(r,ident["pid"],ident["start_ticks"],r))
  end=time.monotonic()+120
  while not path.exists():
   l.need(time.monotonic()<end and time.time()<recipe["capture_deadline_epoch"],"bounded real install owner")
   time.sleep(.1)
  owner=l.obj(l.ref(path));capacity=l.obj(owner["capacity_receipt_ref"])
  events.append(capacity["event_ref"]);geometries.append(owner["field_geometry_refs"]);owners.append(l.ref(path))
 g=mods["resource_ledger"].from_layouts(events,geometries,fields_module=mods["geometry"],document=l.obj)
 ledger=mods["resource_ledger"].ledger(g)
 l.need(ledger["retained_payload_and_declared_additional_bytes"]<=160*1024**3,"full actual raw budget before collection")
 lr=l.publish(root/"ACTUAL-GEOMETRY-RESOURCE-LEDGER.json",dict(ledger=ledger,owners=owners,actual=True))
 seals=[]
 for stage in range(16):
  remaining=recipe["capture_deadline_epoch"]-time.time()
  l.need(remaining>0,"fixed capture deadline")
  mods["client_stage"].collect(stage,recipe["capture_plan_ref"],life=mods["input_lifecycle"],
   transport=mods["transport"],root=root,diagnostic_root=diag,identities=ids,port=port,
   deadline=time.monotonic()+remaining)
  cr=l.ref(root/("STAGE-%02d-HTTP-REPORT.json"%stage))
  sealed=mods["capture_receipt"].seal(cr,plan_ref=recipe["capture_plan_ref"],identities=ids,
   document=l.obj,publish=lambda label,value:l.publish(root/(label+".json"),value))
  l.publish(Path(recipe["capture_ref_paths"][stage]),sealed);seals.append(sealed)
 finals=[]
 for rank in range(4):
  p=diag/("RANK-%d-FINAL-INDEX.json"%rank)
  while not p.exists():
   l.need(time.time()<recipe["capture_deadline_epoch"],"actual64 native retirements before fixed cap");time.sleep(.1)
  ref=l.obj(l.ref(p));value=l.obj(ref)
  l.need(value["schema"]=="kivi.actual-mixed-all-stages-index/v2" and value["rank"]==rank
   and value["identity"]==ids[str(rank)] and len(value["stage_refs"])==16
   and value["cpu_numeric_during_lease"]is False,"actual all64 native completion, not HTTP DONE")
  finals.append(ref)
 return l.publish(output,dict(schema="kivi.actual-mixed-all16-client/v2",status="ALL16_RAW_AND_NATIVE_FINAL_OBSERVED",
  source_ref=source,recipe_ref=recipe_ref,capture_receipt_refs=seals,rank_final_refs=finals,
  rank_identities=ids,actual_resource_ledger=lr,cpu_numeric_during_lease=False,
  retained_all_raw=True,model_ready=False,performance_ready=False,run_authority=False))
def main():
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--recipe-ref-json",type=Path)
 p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8250);a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False)));return
 spec=importlib.util.spec_from_file_location("_mixed_client_loader",Path(__file__).parent/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 m,source=l.source(a.source_manifest_sha256)
 run(l,m,source,json.loads(a.recipe_ref_json.read_bytes()),a.output,a.port)
if __name__=="__main__":main()
