"""Supplemental audit of immutable capture plus genuine official parsed copy."""
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
if str(W)not in sys.path:sys.path.insert(0,str(W))
from host_audits import r43_profile_audit as retained
from host_audits import r43_renewal_policy as policy
from host_audits.r41_profile_trace import audit_tree,inventory,sha
def bound_file(row):
 path=Path(row["path"])
 if path.is_symlink()or sha(path)!=row["sha256"]:raise ValueError("supplemental provenance file differs")
 return path
def audit(plan_path):
 plan_path=Path(plan_path).resolve();plan=json.loads(plan_path.read_bytes())
 if sha(__file__)!=plan["auditor_sha256"]:raise ValueError("supplemental auditor source drift")
 cp=bound_file(plan["contract"]);c=json.loads(cp.read_bytes())
 if cp.parent!=W or Path.cwd().resolve()!=W:raise ValueError("owning workstream required")
 policy.check(c,root=W,require_new_root=False)
 offline_path=bound_file(plan["offline_plan"]);offline=json.loads(offline_path.read_bytes())
 result_path=bound_file(plan["offline_result"]);result=json.loads(result_path.read_bytes())
 if sha(W/offline["helper"])!=offline["helper_sha256"]or result["helper_sha256"]!=offline["helper_sha256"]:raise ValueError("parser source differs")
 if result["plan_sha256"]!=sha(offline_path)or offline["contract"]!=cp.name or offline["contract_sha256"]!=sha(cp):raise ValueError("parser contract linkage differs")
 parsed=Path(offline["analysis_root"]);source=Path(c["raw_root"])/"profiles"
 if result_path!=parsed/"result.json"or parsed.parent!=policy.RAW_PARENT or parsed.is_symlink():raise ValueError("new parsed copy identity required")
 if not result.get("four_rank_trace_valid")or not result.get("original_capture_unchanged")or result.get("exit_code")!=0:raise ValueError("parser did not actually complete")
 launch=json.loads((parsed/"launch.json").read_bytes());argv=launch["argv"]
 devices=[argv[i+1]for i,x in enumerate(argv)if x=="--device"]
 if devices!=["/dev/davinci_manager"]or "--privileged"in argv or c["image"]not in argv:raise ValueError("manager-only same-image parser required")
 actual=result["actual_container"]
 if actual["privileged"]or actual["network"]!="none"or[x["PathOnHost"]for x in actual["devices"]]!=devices:raise ValueError("actual parser device mapping differs")
 q=subprocess.run(["docker","inspect",actual["id"]],text=True,capture_output=True)
 if q.returncode!=1 or"No such object"not in q.stderr:raise ValueError("exact CPU parser not released")
 manifest=json.loads((parsed/"input-manifest.json").read_bytes())
 proof_path=bound_file(offline["release_proof"]);release=json.loads(proof_path.read_bytes())
 expected=release["raw_profile_sha256"]
 if manifest["files"]!=expected or manifest["plan_sha256"]!=sha(offline_path):raise ValueError("original392 input linkage differs")
 original_files,_=inventory(source)
 if {str(p.relative_to(source)):sha(p)for p in original_files}!=expected:raise ValueError("original capture changed")
 if any(sha(parsed/"profiles"/n)!=h for n,h in expected.items()):raise ValueError("copied original file changed")
 for name in ("stdout","stderr"):
  path=parsed/("parser."+name)
  if sha(path)!=result["parser_"+name+"_sha256"]:raise ValueError("parser log differs")
  text=path.read_text()
  if any(marker in text.lower()for marker in ("[error]","traceback (most recent","segfault","failed to generate trace_view","cannexportparser failed")):raise ValueError("official parser failure")
 log=(parsed/"parser.stdout").read_text()
 if log.count("PARSE_BEGIN ")!=4 or log.count("PARSE_END ")!=4:raise ValueError("four completed actual official parses required")
 workers={int(k):int(v)for k,v in release["graph"]["workers"].items()}
 original_tree=retained.retained.audit_tree
 calls=[]
 def verified_copy(requested,actual_workers):
  if Path(requested)!=source or {int(k):int(v)for k,v in actual_workers.items()}!=workers:raise ValueError("one exact capture/worker mapping required")
  calls.append(str(requested))
  return audit_tree(parsed/"profiles",workers)
 retained.retained.audit_tree=verified_copy
 try:report=retained.audit(cp,live_release=True)
 finally:retained.retained.audit_tree=original_tree
 if calls!=[str(source)]:raise ValueError("original trace gate not actually reached once")
 if not report["profiler"]["four_rank_trace_valid"]or not report.get("live_release_verified"):raise ValueError("genuine original full audit required")
 report["r43_offline_supplemental"]={"schema":"hypic-r43-offline-supplemental/v1","plan":str(plan_path),"plan_sha256":sha(plan_path),"auditor_sha256":sha(__file__),"offline_plan_sha256":sha(offline_path),"offline_result_sha256":sha(result_path),"original_files":len(expected),"original_raw_sha256":expected,"parsed_root":str(parsed),"parsed_file_sha256":{str(p.relative_to(parsed/"profiles")):sha(p)for p in inventory(parsed/"profiles")[0]},"old_strict_audit_failure_preserved":True,"all_original_guards_rerun":True,"no_new_inference":True}
 report["scope"]="Supplemental forensic diagnostic only. All original source/math/warm/40request/physical/isolation/exact-release checks rerun; unchanged canonical four-rank CPU+NPU trace gate reads only source-hash-verified official offline copy. Original failed audit remains failed. No service gain/quality/full reproduction acceptance."
 report["full_goal_complete"]=False;report["new_performance_acceptance"]=False
 return report
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--plan",required=True);p.add_argument("--output",required=True);a=p.parse_args()
 report=audit(a.plan);data=(json.dumps(report,sort_keys=True)+"\n").encode()
 with Path(a.output).open("xb")as f:f.write(data);f.flush();os.fsync(f.fileno())
 print(json.dumps({"output":a.output,"sha256":hashlib.sha256(data).hexdigest(),"four_rank_trace_valid":report["profiler"]["four_rank_trace_valid"],"live_release_verified":report["live_release_verified"],"new_performance_acceptance":False}))
