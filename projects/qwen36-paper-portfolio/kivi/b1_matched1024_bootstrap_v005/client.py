"""Shared B1 fixed1024 HTTP transport; actual all4 native drain between owners."""
import argparse,importlib.util,json,sys,time
from pathlib import Path
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--recipe-ref-json",type=Path)
 p.add_argument("--output",type=Path);p.add_argument("--port",type=int,default=8250);a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,model_ready=False)));return 0
 here=Path(__file__).resolve().parent;sys.path.insert(0,str(here))
 spec=importlib.util.spec_from_file_location("_kivi_screen_client_loader",here/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 m,source=l.source(a.source_manifest_sha256)
 import screen_contract as c,screen_gate,screen_evidence as e,transport
 return run(l,m,source,json.loads(a.recipe_ref_json.read_bytes()),a.output,a.port)

def run(l,m,source,rr,output,port):
 import screen_contract as c,screen_gate,screen_evidence as e,transport
 recipe=l.obj(rr)
 c.need(recipe["source_ref"]==source,"same source actual common client")
 screen_gate.worker_check(recipe,l.obj,source);plan,rows=e.expected(recipe,l.obj)
 protocol=l.obj(recipe["actual_input_protocol_ref"])
 c.need(protocol["source_ref"]==source and protocol["plan_ref"]==recipe["declared_ingress_plan_ref"]
  and protocol["protocol"]==c.PROTOCOL and protocol["requests"]==
  [dict(row,payload=c.payload(c.prompt(),row["outputs"]))for row in rows],"actual original input producer protocol")
 bindings=l.module("_kivi_screen_client_bindings",m["runtime_roles"]["bindings"])
 oracle=l.module("_kivi_screen_client_oracle",m["runtime_roles"]["assignment_oracle"])
 owners=l.obj(l.ref(recipe["rank_bindings_path"]));rank_ids=owners["rank_bindings"]
 def wait(paths):
  until=time.monotonic()+120
  while not all(p.is_file()for p in paths):
   c.need(time.monotonic()<until and time.time()<c.CUTOFF,"actual native finish bounded; no dummy request")
   time.sleep(.1)
 def retired(row,response_ref):
  actual=next(v for v in plan["rows"]if v["header_request_id"]==row["header_id"])
  rid=actual["declared_passed_id"]
  paths=[e.retirement_path(recipe,rank_ids[str(rank)],rank,rid)for rank in range(4)]
  wait(paths);refs=[l.ref(path)for path in paths]
  for rank,ref in enumerate(refs):e.retirement(ref,recipe,rank_ids[str(rank)],rank,rid,l.obj)
  return refs
 report=transport.run(output.parent/"http",port,recipe["run_id"],retired)
 paths=[Path(recipe["diagnostic_root"])/("RANK-%d-FINAL-INDEX.json"%rank)for rank in range(4)]
 wait(paths);finals=[l.obj(l.ref(path))for path in paths]
 value=dict(schema="kivi.b1-fixed1024-client/v1",status="FIXED1024_HTTP_NATIVE_FINISHED",
  source_ref=source,recipe_ref=rr,algorithm_arm=recipe["algorithm_arm"],
  input_protocol_ref=recipe["actual_input_protocol_ref"],http_report_ref=report,
  metrics=l.obj(report)["metrics"],rank_bundle_refs=finals,model_ready=False,performance_ready=False,run_authority=False)
 e.client(value,recipe,rr,l.obj,bindings,oracle,m["runtime_roles"]["installer"]["sha256"])
 print(json.dumps(l.publish(output,value)));return 0
if __name__=="__main__":raise SystemExit(main())
