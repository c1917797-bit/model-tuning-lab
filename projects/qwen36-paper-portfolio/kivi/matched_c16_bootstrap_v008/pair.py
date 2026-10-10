"""Pure pair comparison after source-qualified arm consumers and original terminals."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import screen_contract as c
def consume(dense,candidate):
 c.need(dense["schema"]==candidate["schema"]=="kivi.c16-fixed1024-arm-consumed/v1"
  and dense["arm"]=="dense"and candidate["arm"]=="candidate"and dense["source"]==candidate["source"],
  "same source actual dense then candidate")
 for row in(dense,candidate):
  c.need(row["actual_source_cleanup_resource_checked"]is True and row["model_ready"]is
   row["performance_accepted"]is row["full1024_numerically_verified"]is row["run_authority"]is False,
   "fixed C16 screen, not task accuracy")
  c.read(row["original_result"]);c.read(row["original_terminal"]);c.read(row["prerequisite"])
 d=c.read(dense["recipe"]);k=c.read(candidate["recipe"])
 c.need(d["cache_bytes"]==k["cache_bytes"]==c.COMMON["kv_cache_memory_bytes"]
  and d["screen_output_counts"]==k["screen_output_counts"]==[2,2]+[1024]*40
  and d["container_id"]!=k["container_id"],"distinct actual same6GiB runs")
 c.need(c.read(d["firstdecode_prerequisite_ref"])["consumed"]==
  c.read(k["firstdecode_prerequisite_ref"])["consumed"],"same genuine numerical prerequisite")
 import screen_whole as whole
 c.need(whole.utc(dense["stopped_inspect"]["State"]["FinishedAt"])<=
  whole.utc(candidate["stopped_inspect"]["State"]["StartedAt"]),"strict serial arm lease order")
 c.need(dense["same_actual_config"]["actual_scalar_policy"]==
  candidate["same_actual_config"]["actual_scalar_policy"],"identical actual common scalar engine policy")
 for row,recipe in((dense,d),(candidate,k)):
  result=c.read(row["original_result"])
  cpu=c.read(result["cpu"]["report"]);n1=c.read(result["npu"]["canary"])
  c.need(cpu["native_argv"]==n1["native_argv"],"same actual CPU/N1 native arguments")
  expected=c.native_argv(int(cpu["native_argv"][cpu["native_argv"].index("--port")+1]),
   "kivi_firstdecode_bootstrap.FirstDecodeWorker")
  # The frozen native builder's option order is fixed and compared as complete option mappings.
  def options(argv):
   result={};i=0
   while i<len(argv):
    key=argv[i];c.need(key.startswith("--")and key not in result,"unique native flags")
    if i+1<len(argv)and not argv[i+1].startswith("--"):result[key]=argv[i+1];i+=2
    else:result[key]=True;i+=1
   return result
  c.need(options(cpu["native_argv"])==options(expected),"whole common parameter mapping")
  row["native_options"]=options(cpu["native_argv"])
 c.need(dense["native_options"]==candidate["native_options"],"one exact common parameter set")
 return dict(schema="kivi.c16-fixed1024-pair/v1",source=dense["source"],protocol=c.PROTOCOL,
  dense=dense["original_result"],candidate=candidate["original_result"],
  dense_metrics=dense["metrics"],candidate_metrics=candidate["metrics"],**c.pair(dense["metrics"],candidate["metrics"]))
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256")
 for name in("dense","candidate"):
  p.add_argument("--"+name,type=Path);p.add_argument("--"+name+"-sha256")
  p.add_argument("--"+name+"-terminal",type=Path);p.add_argument("--"+name+"-terminal-sha256")
  p.add_argument("--"+name+"-operation");p.add_argument("--"+name+"-peer")
 p.add_argument("--output",type=Path);a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 import screen_whole as w,transport
 source=c.ref(Path(__file__).resolve().parent/"SOURCE_MANIFEST.json")
 c.need(source["sha256"]==a.source_manifest_sha256,"exact pair source")
 for row in c.read(source)["files"]:c.need(c.ref(row["path"])==row,"whole pair source")
 values=[]
 for name in("dense","candidate"):
  rr=c.ref(getattr(a,name));c.need(rr["sha256"]==getattr(a,name+"_sha256"),"whole actual consumed arm")
  tr=c.ref(getattr(a,name+"_terminal"))
  c.need(tr["sha256"]==getattr(a,name+"_terminal_sha256"),"original independent arm consumer terminal")
  rec=w.original(c.read(tr),getattr(a,name+"_peer"),getattr(a,name+"_operation"))
  command=[rec["command"],*rec["args"]]
  c.need(command[:5]==["/usr/bin/python3","-I","-B",str(Path(__file__).resolve().parent/"screen_whole.py"),"--execute"]
   and rec["cwd"]in(None,w.ROOT)and 0<rec["durationMs"]<=150000,"actual bounded source-qualified arm consumer")
  expected_flags=["--source-manifest-sha256","--arguments","--arguments-sha256","--output"]
  c.need(command[5::2]==expected_flags and len(command)==13 and command[6]==source["sha256"]
   and Path(command[8]).is_absolute()and command[12]==rr["path"],"whole original arm consumer argv")
  argsref=c.ref(command[8]);c.need(argsref["sha256"]==command[10],"exact original arm operation inputs")
  args=c.read(argsref);value=c.read(rr)
  c.need(value["source"]==source and value["arm"]==name
   and value["original_result"]==c.ref(args["result"])and value["original_terminal"]==c.ref(args["terminal"]),
   "consumer output bound to exact actual arm originals")
  refs=[]
  for line in rec["stdout"].splitlines():
   try:v=json.loads(line)
   except(ValueError,TypeError):continue
   if type(v)is dict and set(v)=={"path","bytes","sha256"}:refs.append(v)
  c.need(refs==[rr],"one original arm consumer output marker")
  values.append(value)
 result=consume(*values);c.need(a.output is not None and not a.output.exists(),"exclusive pair output")
 print(json.dumps(transport.publish(a.output,result)));return 0
if __name__=="__main__":raise SystemExit(main())
