"""Pure fixed001dense/003candidate reader. No result normalization or device operations."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
DENSE={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-b1-cost129-bootstrap-v1-001/SOURCE_MANIFEST.json","bytes":148006,"sha256":"56aa4844756055266ea7e05b6a2b862e4eac3be9f449cc3ae1d16d5c855bc0b6"}
CANDIDATE={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-b1-cost129-bootstrap-v1-003/SOURCE_MANIFEST.json","bytes":161966,"sha256":"806ff538b0d4cf196c818067fb30bb7fdce57697ba1296fcf5321fece79cd68c"}
DENSE_READER={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-cost129-owner-reader-v1-002/SOURCE_MANIFEST.json","bytes":78174,"sha256":"783ed6edeb26e55ff0b8706b15346c43b91bf8a2040058b60df9ea2f4aad8c7e"}
HERE=Path(__file__).resolve().parent
c=None
def need(v,why):
 if not v:raise ValueError(why)
def bytes_of(ref,resolver=None):
 p=Path(ref["path"])if resolver is None else Path(resolver(ref))
 need(p.is_absolute()and p.resolve()==p and not p.is_symlink()and p.is_file(),"ordinary exact source")
 a=p.stat();wire=p.read_bytes();z=p.stat()
 need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)
  and len(wire)==ref["bytes"]and hashlib.sha256(wire).hexdigest()==ref["sha256"],"whole exact source bytes")
 return wire
def qualify(resolver=None):
 old=json.loads(bytes_of(DENSE,resolver));new=json.loads(bytes_of(CANDIDATE,resolver))
 a={Path(r["path"]).name:r for r in old["files"]};b={Path(r["path"]).name:r for r in new["files"]}
 need(len(a)==54 and len(b)==55 and set(b)==set(a)|{"test_protocol.py"},"exact two own-file sets")
 changed=[]
 for name,row in a.items():
  x=bytes_of(row,resolver);y=bytes_of(b[name],resolver)
  if x!=y:changed.append(name)
 need(set(changed)=={"runtime_owner.py","software_check.py","screen_whole.py"},"only three fixed source deltas")
 x=bytes_of(a["runtime_owner.py"],resolver).decode();y=bytes_of(b["runtime_owner.py"],resolver).decode()
 needle='and recipe["algorithm_arm"]=="candidate" and recipe["screen_output_counts"]==[2,2,1024],'
 need(x.count(needle)==1 and y==x.replace(needle,needle.replace("1024","129")).replace(
  '"exact three sequential full32768 owners: two decode warmups then fixed1024")',
  '"exact three sequential full32768 owners: two decode warmups then cost129")'),"only candidate protocol literal/error repair")
 x=bytes_of(a["screen_whole.py"],resolver).decode();y=bytes_of(b["screen_whole.py"],resolver).decode()
 need(x.count('OWNER="kivi-b1-cost129-v2"')==1 and y==x.replace('OWNER="kivi-b1-cost129-v2"','OWNER="kivi-b1-matched1024-v2"'),
  "only consumer OWNER source-literal repair")
 need(old["budgets"]==new["budgets"]and old["clock"]==new["clock"],"unchanged all resource and absolute deadline")
 olddeps={r["path"]:r for r in old["dependencies"]};newdeps={r["path"]:r for r in new["dependencies"]}
 need(all(newdeps.get(k)==v for k,v in olddeps.items()),"all old dependencies retained")
 for k,v in old["runtime_roles"].items():
  w=new["runtime_roles"][k];need((v["bytes"],v["sha256"])==(w["bytes"],w["sha256"]),"all actual runtime roles byte-identical")
 return dict(dense_source=DENSE,candidate_source=CANDIDATE,changed_files=sorted(changed),
  all_other_51_own_files_byte_identical=True,mathematics_monitor_sync_capacity_budget_unchanged=True,
  dense_candidate_source_identities_preserved=True,dense_recapture=False,performance_permission=False)
def module(row,name):
 need(name not in sys.modules,"no ambient consumer substitution")
 wire=bytes_of(row);spec=importlib.util.spec_from_file_location(name,row["path"]);m=importlib.util.module_from_spec(spec)
 sys.modules[name]=m
 try:exec(compile(wire,row["path"],"exec"),m.__dict__)
 except BaseException:del sys.modules[name];raise
 return m
def source(expected):
 row=dict(path=str(HERE/"SOURCE_MANIFEST.json"),bytes=(HERE/"SOURCE_MANIFEST.json").stat().st_size,
  sha256=hashlib.sha256((HERE/"SOURCE_MANIFEST.json").read_bytes()).hexdigest())
 need(row["sha256"]==expected,"exact dual-source reader manifest")
 m=json.loads(bytes_of(row));need(m["dense"]==DENSE and m["candidate"]==CANDIDATE and m["dense_reader"]==DENSE_READER,"exact fixed predecessors")
 for r in m["files"]+m["dependencies"]:bytes_of(r)
 return row
def configure():
 global c
 m=json.loads(bytes_of(CANDIDATE));own={Path(r["path"]).name:r for r in m["files"]}
 need(not(set(Path(n).stem for n in own)&set(sys.modules)),"fresh actual candidate consumer namespace")
 sys.path.insert(0,str(Path(CANDIDATE["path"]).parent))
 c=module(own["screen_contract.py"],"screen_contract")
 w=module(own["screen_whole.py"],"screen_whole")
 return w
def consume(dense,candidate):
 c.need(dense["schema"]==candidate["schema"]=="kivi.b1-cost129-arm-consumed/v1"
  and dense["arm"]=="dense"and candidate["arm"]=="candidate"and dense["source"]==DENSE and candidate["source"]==CANDIDATE,
  "exact001 dense then protocol-repaired003 candidate")
 for row in(dense,candidate):
  c.need(row["actual_source_cleanup_resource_checked"]is True and row["model_ready"]is
   row["performance_accepted"]is row["full1024_numerically_verified"]is row["run_authority"]is False,
   "preliminary B1 screening only")
  c.read(row["original_result"]);c.read(row["original_terminal"]);c.read(row["prerequisite"])
 d=c.read(dense["recipe"]);k=c.read(candidate["recipe"])
 c.need(d["cache_bytes"]==k["cache_bytes"]==c.COMMON["kv_cache_memory_bytes"]
  and d["screen_output_counts"]==k["screen_output_counts"]==[2,2,129]
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
 return dict(schema="kivi.b1-cost129-dual-source-pair/v1",dense_source=dense["source"],candidate_source=candidate["source"],protocol=c.PROTOCOL,
  dense=dense["original_result"],candidate=candidate["original_result"],
  dense_metrics=dense["metrics"],candidate_metrics=candidate["metrics"],**c.pair(dense["metrics"],candidate["metrics"]))
def arm_value(name,a,w):
 rr=c.ref(getattr(a,name));need(rr["sha256"]==getattr(a,name+"_sha256"),"exact consumed arm output")
 tr=c.ref(getattr(a,name+"_terminal"));need(tr["sha256"]==getattr(a,name+"_terminal_sha256"),"actual arm reader terminal")
 rec=w.original(c.read(tr),getattr(a,name+"_peer"),getattr(a,name+"_operation"))
 command=[rec["command"],*rec["args"]]
 entry=(str(Path(DENSE_READER["path"]).parent/"arm.py")if name=="dense"else str(Path(CANDIDATE["path"]).parent/"screen_whole.py"))
 mf=DENSE_READER if name=="dense"else CANDIDATE
 need(command[:5]==["/usr/bin/python3","-I","-B",entry,"--execute"]
  and rec["cwd"]in(None,w.ROOT)and 0<rec["durationMs"]<=150000,"actual bounded exact arm reader")
 need(len(command)==13 and command[5::2]==["--source-manifest-sha256","--arguments","--arguments-sha256","--output"]
  and command[6]==mf["sha256"]and Path(command[8]).is_absolute()and command[12]==rr["path"],"complete fixed arm reader argv")
 ar=c.ref(command[8]);need(ar["sha256"]==command[10],"original operation arguments")
 args=c.read(ar);value=c.read(rr)
 need(value["source"]==(DENSE if name=="dense"else CANDIDATE)and value["arm"]==name
  and value["original_result"]==c.ref(args["result"])and value["original_terminal"]==c.ref(args["terminal"]),"exact arm originals/source")
 if name=="dense":
  m=json.loads(bytes_of(DENSE_READER));r=next(r for r in m["files"]if Path(r["path"]).name=="cost_owner_adapter.py")
  reader=module(r,"_cost003_dense_reader_identity");reader.require_identity(value,DENSE_READER)
 else:need("reader_adaptation"not in value,"new candidate uses its own corrected source directly")
 markers=[]
 for line in rec["stdout"].splitlines():
  try:v=json.loads(line)
  except(ValueError,TypeError):continue
  if type(v)is dict and set(v)=={"path","bytes","sha256"}:markers.append(v)
 need(markers==[rr],"one exact original reader output marker")
 return value
def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
 for name in("dense","candidate"):
  for suffix in("","-sha256","-terminal","-terminal-sha256","-operation","-peer"):p.add_argument("--"+name+suffix)
 p.add_argument("--output",type=Path);a=p.parse_args(argv)
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return 0
 own=source(a.source_manifest_sha256);proof=qualify();w=configure()
 value=consume(arm_value("dense",a,w),arm_value("candidate",a,w))
 value["source_equivalence"]=proof;value["reader_source"]=own
 need(a.output is not None and not a.output.exists(),"exclusive two-source output")
 source(a.source_manifest_sha256)
 import transport
 print(json.dumps(transport.publish(a.output,value)));return 0
if __name__=="__main__":raise SystemExit(main())
