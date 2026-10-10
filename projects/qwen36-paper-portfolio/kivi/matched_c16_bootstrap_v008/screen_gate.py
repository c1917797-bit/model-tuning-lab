"""Exact full018 numerical prerequisite; isolated pure host replay, never a lease."""
import argparse,hashlib,json,sys,time
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def check_consumed(result,policy):
 need(result["status"]=="FIRSTDECODE_OWNED_RAW_AND_WHOLE_CONSUMED"
  and result["producer_source"]==policy.PRODUCER and result["firstdecode_integration_checked"]is True
  and result["FA_frames"]==64 and result["native_finished_all4_checked"]is True
  and result["original_prefill_tokens"]==32768 and result["actual_first_decode_length"]==32769
  and result["model_ready"]is result["performance_ready"]is result["run_authority"]is False,
  "genuine complete firstdecode raw/whole; not performance or a software receipt")
 return result
def worker_check(recipe,read,source):
 value=read(recipe["firstdecode_prerequisite_ref"])
 import screen_contract as policy
 need(value["schema"]=="kivi.screen.actual-firstdecode-prerequisite/v1"
  and value["source"]==source and value["successful"]is True
  and value["whole_source"]==policy.WHOLE and value["raw_source"]==policy.RAW
  and value["NPU"]is value["model_ready"]is value["performance_ready"]is value["run_authority"]is False,
  "actual source-qualified host replay before timing worker")
 check_consumed(value["consumed"],policy)
 import mixed_gate
 mixed_gate.check(value["mixed_consumed"],value["mixed_source"])
 need(recipe["algorithm_arm"]in("dense","candidate")and recipe["screen_output_counts"]==[2,2]+[1024]*40
  and recipe["cache_bytes"]==6*1024**3,"one exact same-budget C16 fixed40 protocol")
 return value
def host_replay(c,source,arguments,out,start):
 """One bounded existing-host read-only child; separate Python namespace."""
 h=c.module(c.H8,c.DEPS[str(c.H8)],"_sparq_tp4_frozen_host").frozen()
 output=out/"FIRSTDECODE_PREREQUISITE.json"
 argv=["/usr/bin/python3","-I","-B",str(c.BASE/"screen_gate.py"),"--execute",
  "--source-manifest-sha256",source["sha256"],"--arguments",arguments["path"],
  "--arguments-sha256",arguments["sha256"],"--output",str(output)]
 remaining=min(150,5400-(time.monotonic()-start)-90,c.CUTOFF-time.time()-90)
 need(remaining>0,"existing phase/cutoff fit before prerequisite replay")
 raw=h.run(argv,remaining)
 receipt=c.write(out/"FIRSTDECODE_PREREQUISITE_CHILD.json",dict(raw,requested_argv=argv))
 need(raw["exit_code"]==0,"actual independent raw/whole replay failed; retained "+str(receipt))
 ref=c.ref(output);value=c.obj(ref)
 need(value["source"]==source and value["arguments_ref"]==c.checked(arguments)
  and value["successful"]is True,"same original prerequisite inputs and source")
 import screen_contract as policy
 check_consumed(value["consumed"],policy)
 import mixed_gate
 mixed_gate.check(value["mixed_consumed"],value["mixed_source"])
 return ref
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--arguments");p.add_argument("--arguments-sha256")
 p.add_argument("--output",type=Path);a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 here=Path(__file__).resolve().parent;sys.path.insert(0,str(here))
 import screen_contract as policy
 import transport
 source=policy.ref(here/"SOURCE_MANIFEST.json")
 need(source["sha256"]==a.source_manifest_sha256,"exact current screen source")
 mf=policy.read(source)
 for row in mf["files"]:
  need(policy.ref(row["path"])==row,"all current screen source bytes before child")
 argsref=policy.ref(a.arguments);need(argsref["sha256"]==a.arguments_sha256,"original whole/raw consume arguments")
 need(a.output is not None and a.output.is_absolute()and not a.output.exists(),"exclusive exact prerequisite output")
 report=dict(schema="kivi.screen.actual-firstdecode-prerequisite/v1",source=source,
  arguments_ref=argsref,whole_source=policy.WHOLE,raw_source=policy.RAW,successful=False,primary=None,
  NPU=False,model_ready=False,performance_ready=False,run_authority=False)
 try:
  from screen_predecessor import replay
  inputs=policy.read(argsref)
  report["consumed"]=check_consumed(replay(inputs),policy)
  import mixed_gate
  report["mixed_source"]=inputs["mixed_source"]
  report["mixed_consumed"]=mixed_gate.replay(inputs,mf);report["successful"]=True
 except BaseException as error:
  import traceback
  report["primary"]=repr(error);report["traceback"]=traceback.format_exc()
 finally:print(json.dumps(transport.publish(a.output,report)),flush=True)
 return 0 if report["successful"]else 1
if __name__=="__main__":raise SystemExit(main())
