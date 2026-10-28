"""Official offline parse successor: manager metadata only, no compute devices."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time,traceback,socket
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r43_renewal_policy as policy
from host_audits.r41_profile_trace import inventory,audit_tree
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path,value):
 data=(json.dumps(value,sort_keys=True)+"\n").encode()
 with Path(path).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
 return hashlib.sha256(data).hexdigest()
def run(plan_path):
 plan=json.loads(Path(plan_path).read_bytes())
 if plan["helper_sha256"]!=sha(__file__):raise ValueError("offline helper bytes drift")
 cp=W/plan["contract"];c=json.loads(cp.read_bytes())
 if sha(cp)!=plan["contract_sha256"]:raise ValueError("actual contract drift")
 policy.check(c,root=W,require_new_root=False)
 policy.require_budget(c)
 import formal_r15_tp4 as base
 before=base.snapshot()
 if before["processes"]or before["foreign"]:raise RuntimeError("physical0-3 not idle for metadata-only parse")
 for port in [c["port"]]+list(range(c["hccl_ports"][0],c["hccl_ports"][1]+1)):
  with socket.socket()as sock:sock.bind(("0.0.0.0",port))
 if not Path("/dev/davinci_manager").is_char_device():raise RuntimeError("manager control missing")
 for probe in plan["manager_export_evidence"]:
  if sha(probe["path"])!=probe["sha256"]:raise ValueError("manager counterfactual evidence drift")
 proof=Path(plan["release_proof"]["path"])
 if sha(proof)!=plan["release_proof"]["sha256"]:raise ValueError("original capture/release proof drift")
 release=json.loads(proof.read_bytes())
 if not release.get("valid_release_only")or not release.get("exact_owned_container_absent"):raise ValueError("exact released capture required")
 source=Path(c["raw_root"])/"profiles";files,total=inventory(source)
 hashes={str(p.relative_to(source)):sha(p)for p in files}
 if hashes!=release["raw_profile_sha256"]:raise ValueError("immutable capture input drift")
 output=Path(plan["analysis_root"])
 if output.parent!=policy.RAW_PARENT or output.is_symlink()or output.exists():raise ValueError("new dedicated offline root required")
 st=os.statvfs(output.parent)
 if st.f_bavail*st.f_frsize<8*1024**3:raise RuntimeError("offline parse workspace headroom required")
 output.mkdir()
 save(output/"input-manifest.json",{"source":str(source),"files":hashes,"total_bytes":total,"plan_sha256":sha(plan_path),"helper_sha256":sha(__file__)})
 shutil.copytree(source,output/"profiles")
 if any(sha(output/"profiles"/n)!=h for n,h in hashes.items()):raise ValueError("copied bytes differ")
 script=("import pathlib,inspect,hashlib,json,multiprocessing;import torch_npu.profiler.profiler as p;"
  "assert hashlib.sha256(pathlib.Path(inspect.getsourcefile(p)).read_bytes()).hexdigest()=="+repr(plan["official_profiler_sha256"])+";"
  "assert not multiprocessing.current_process().daemon;"
  "paths=sorted(pathlib.Path('/scratch/profiles').glob('*_ascend_pt'));assert len(paths)==4;"
  "print(json.dumps({'daemon':False,'ranks':len(paths),'max_process_number':2}),flush=True);"
  "[(print('PARSE_BEGIN '+str(x),flush=True),p.analyse(str(x),max_process_number=2,export_type=['text']),print('PARSE_END '+str(x),flush=True))for x in paths]")
 cmd=["docker","run","--rm","--network","none","--cpuset-cpus","112-119","--memory","8g","--pids-limit","256",
  "--name",plan["container_name"],"--label","model-tuning-lab.task=hypic-independent-20261013",
  "--device","/dev/davinci_manager","-v","/usr/local/Ascend/driver:/usr/local/Ascend/driver:ro","-v",str(output)+":/scratch:rw",c["image"],"python3","-B","-c",script]
 save(output/"launch.json",{"argv":cmd,"no_physical_npu_devices":True,"manager_metadata_control_only":True,"only_profile_copy_rw":True,"original_capture_readonly_by_omission":True})
 result={"schema":"hypic-r43-offline-manager-parse-result/v1","source":str(source),"analysis_root":str(output),"helper_sha256":sha(__file__),"plan_sha256":sha(plan_path),"no_npu_allocation":True,"four_rank_trace_valid":False,"full_goal_complete":False}
 with(output/"parser.stdout").open("xb")as out,(output/"parser.stderr").open("xb")as err:
  try:
   proc=subprocess.Popen(cmd,stdout=out,stderr=err)
   for _ in range(100):
    probe=subprocess.run(["docker","inspect",plan["container_name"]],text=True,capture_output=True)
    if probe.returncode==0:
     item=json.loads(probe.stdout)[0]
     if item["Image"]!=c["image"]or item["HostConfig"]["Privileged"]or [x["PathOnHost"]for x in item["HostConfig"]["Devices"]]!=["/dev/davinci_manager"]:raise RuntimeError("parser actual device scope mismatch")
     result["actual_container"]={"id":item["Id"],"devices":item["HostConfig"]["Devices"],"network":item["HostConfig"]["NetworkMode"],"privileged":False}
     break
    if proc.poll()is not None:break
    time.sleep(.2)
   proc.wait(timeout=900);result["exit_code"]=proc.returncode
   if "actual_container"not in result:raise RuntimeError("parser live device mapping proof missing")
   if proc.returncode:raise RuntimeError("official offline parser container failed")
  except Exception as failure:
   inspect=subprocess.run(["docker","inspect",plan["container_name"]],text=True,capture_output=True)
   if inspect.returncode==0:
    item=json.loads(inspect.stdout)[0]
    if(item["Config"]["Labels"].get("model-tuning-lab.task")!="hypic-independent-20261013"or item["Image"]!=c["image"]or [x["PathOnHost"]for x in item["HostConfig"]["Devices"]]!=["/dev/davinci_manager"]):
     raise RuntimeError("exact CPU parser cleanup identity mismatch")
    subprocess.run(["docker","stop","--time","10",item["Id"]],check=True)
   result["failure"]={"type":type(failure).__name__,"message":str(failure)}
   result["original_capture_unchanged"]=all(sha(source/n)==h for n,h in hashes.items())
   save(output/"result.json",result);raise
 try:
  if any(sha(source/n)!=h for n,h in hashes.items()):raise ValueError("original capture mutated")
  workers={int(k):int(v)for k,v in release["graph"]["workers"].items()}
  result["profiler"]=audit_tree(output/"profiles",workers)
  result["four_rank_trace_valid"]=True
 except Exception as e:result["failure"]={"type":type(e).__name__,"message":str(e)}
 after=base.snapshot()
 result["physical0_3_after"]=after["processes"];result["foreign_after"]=after["foreign"]
 result["original_capture_unchanged"]=all(sha(source/n)==h for n,h in hashes.items())
 result["parser_stdout_sha256"]=sha(output/"parser.stdout");result["parser_stderr_sha256"]=sha(output/"parser.stderr")
 digest=save(output/"result.json",result)
 print(json.dumps({"path":str(output/"result.json"),"sha256":digest,"four_rank_trace_valid":result["four_rank_trace_valid"],"failure":result.get("failure"),"original_capture_unchanged":result["original_capture_unchanged"]}))
 if not result["four_rank_trace_valid"]:raise SystemExit(1)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--plan",required=True);a=p.parse_args();run(a.plan)
