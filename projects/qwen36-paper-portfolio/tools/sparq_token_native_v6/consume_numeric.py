"""Standalone numerical component consumer; full host/model authority stays pending."""
import argparse,json,math
from pathlib import Path
from sparq_token_v4.core import require,HEADS
from sparq_token_v4.proof import validate_proof
from receipt import IMAGE,sha,bound,load,source_identity,MODES,image_argv,docker_argv,check_terminal,write_new
from numeric_gate import LIMITS
def terminal(path,digest,peer,container,expected=None,report_ref=None,source=None,files=None,proof_ref=None):
 require(sha(Path(path))==digest,"original terminal bytes changed")
 original=json.loads(Path(path).read_bytes())
 from original_terminal import original_terminal
 parsed=original_terminal(original,peer);r=parsed["record"]
 require(all((expected,report_ref,source,files,proof_ref)) and container in expected,"mandatory actual full CLI/source/report/proof Refs")
 check_terminal(r,expected,report_ref,source,files,proof_ref)
 return {"operation":parsed["operation_id"],"original_terminal_shape":parsed["origin_shape"],"receipt_sha256":digest,"container":container}
def consume(root,terminal_path,terminal_sha,proof_path,peer,source,files,host_result,host_result_sha):
 from receipt import host_marker,validate_matrix,validate_cpu_phase,canonical
 from host import host_argv,translate
 from preflight import validate_abi
 authority_ref=bound(host_result,host_result_sha);authority=load(authority_ref)
 report_ref=authority["producer_report"];report=load(report_ref)
 require(Path(report_ref["path"])==root/"REPORT.json","original host -> exact numerical gate report")
 proof_ref=bound(proof_path,report["device_proof"]["sha256"]);proof=validate_proof(proof_path,proof_ref["sha256"],source,files,
  report["actual_container_process"]["argv"],now_ns=report["started_ns"])
 x=proof["container_inspect"];output=Path(authority["output_dir"]);require(root==output/"gate" and output.resolve()==output,"original new host/gate leaf")
 require(authority["schema"]=="sparq.token-host-result/v4" and authority["status"]=="kernel_numerics_checked" and
  authority["source_manifest"]==source and authority["sources_before"]==authority["sources_after"]==files and
  authority["dependencies"]==__import__("receipt").DEPENDENCIES and authority["source_device_proof"]==proof_ref and
  authority["primary_error"] is None and authority["secondary_errors"]==[] and
  authority["host_script_sha256"]==files["host.py"] and authority["entry_script_sha256"]==files["numeric_gate.py"] and
  authority["numerical_component_checked"] is True,"actual complete original host source/primary-secondary authority")
 require(authority["common_deadline_monotonic"]-authority["common_created_monotonic"]==5400 and
  authority["phase_elapsed_seconds"]<=5400,"single whole5400s lease, no CPU/NPU reset")
 original_ref=bound(terminal_path,terminal_sha)
 from original_terminal import original_terminal
 parsed=original_terminal(load(original_ref),peer);record=parsed["record"]
 requested=[record["command"],*record["args"]]
 args=argparse.Namespace(source_manifest=Path(source["path"]),source_manifest_sha256=source["sha256"],output_dir=output)
 require(requested==host_argv(args)==authority["actual_host_argv"]==authority["expected_host_argv"],"actual whole host argv/source/new output")
 mk=host_marker(record["stdout"]);require(mk["result"]==authority_ref and mk["status"]==authority["status"] and
  mk["source_manifest"]==source and mk["host_script_sha256"]==files["host.py"] and mk["entry_script_sha256"]==files["numeric_gate.py"],
  "original actual host stdout binds immutable RESULT bytes")
 hp=authority["actual_host_process"];require(hp["argv"]==requested and hp["pid"]>1 and
  hp["cmdline_sha256"]==__import__("hashlib").sha256(("\0".join(requested)+"\0").encode()).hexdigest(),"actual host argv/PID/hash")
 require(report["schema"]=="sparq.token-numeric/v4" and report["status"]=="passed" and report["source_manifest"]==source and
  report["sources_before"]==report["sources_after"]==files and report["script_sha256"]==files["numeric_gate.py"] and
  report["npu_executed"] is True and report["service_ready"] is False and report["model_executed"] is False,
  "actual original producer scope/source/matrix")
 image_argv_expected=image_argv(Path(__file__).parent,Path("/sparq-results/gate"),proof_ref,source)
 require(report["actual_container_process"]["argv"]==image_argv_expected,"exact image Python CLI, no substring/source drift")
 child=load(authority["numerical_child"])
 require(child["exit_code"]==0 and child["child_termination_observed"] is True and
  child["expected_image_python_argv"]==image_argv_expected,"actual numerical child terminated original identity")
 expected_child=docker_argv(proof["container_id"],image_argv_expected)
 require(child["requested_argv"]==expected_child and child["actual_host_argv"]==["/usr/bin/prlimit","--as=unlimited","--",*expected_child],
  "original exact CID/environment/Python/source/newoutput/flags and Docker-only AS child argv")
 stdout=Path(bound(child["stdout_ref"]["path"],child["stdout_ref"]["sha256"])["path"]).read_text()
 marker=__import__("receipt").marker(stdout)
 require(translate(marker["report"],output)==report_ref and marker["status"]=="passed" and marker["source_manifest"]==source and
  marker["script_sha256"]==files["numeric_gate.py"] and marker["device_proof"]==proof_ref,"actual child marker binds report bytes")
 ndref=proof["native_no_device_abi"];nd=validate_abi(load(ndref),source,files)
 require(authority["native_no_device_abi"]==ndref==report["native_no_device_abi"] and
  report["preinit_actual_exports"]==nd["actual_exports"] and authority["native_no_device_child"]==proof["native_no_device_child"] and
  ndref["path"]==str(output/"cpu-preflight/ABI.json"),"original actual no-device -> source/proof/native producer/authority linkage")
 require(authority["cpu_container_id"]==proof["cpu_container_id"] and
  all(authority[k]==proof[k] for k in ("cpu_only_inspect","cpu_only_cleanup","cpu_stopped_inspect")),"actual CPU-only CID/cleanup linkage")
 validate_cpu_phase(proof,proof["cpu_container_id"],source,files)
 ndchild=load(authority["native_no_device_child"]);rows=[l for l in ndchild["stdout"].splitlines() if l.startswith("MAIN_SPARQ_TOKEN_V5_NO_DEVICE ")]
 require(len(rows)==1 and translate(json.loads(rows[0].split(" ",1)[1])["actual_abi"],output/"cpu-preflight")==ndref,
  "original actual CPU-only child stdout binds immutable ABI bytes")
 from receipt import validate_cpu_abi_child
 require(proof["cpu_host_output_root"]==str(output/"cpu-preflight"),"original complete authority CPU output root")
 validate_cpu_abi_child(proof["cpu_container_id"],output/"cpu-preflight",source,ndchild,nd)
 canary=load(proof["canary"]);canary_child=load(proof["canary_child"])
 require(canary["script_sha256"]==files["host.py"] and canary_child["exit_code"]==0 and
  canary_child["child_termination_observed"] is True and canary_child["physical_pid_proofs"] and
  all(p["physical"]==6 and p["stage"]=="canary" and p["namespace_pids"][-1]==canary["pid"] and proof["container_id"] in p["cgroup"]
   for p in canary_child["physical_pid_proofs"]),"actual distinct this-source canary original process")
 full=validate_matrix(report,root)
 process=report["actual_container_process"];proofs=authority.get("actual_npu_python_process_proofs")
 require(type(proofs) is list and proofs,"actual numerical NPU Python PID proofs mandatory, not canary")
 identities=set()
 for p in proofs:
  require(p["physical"]==6 and p["chip"]==0 and proof["container_id"] in p["cgroup"] and
    p["argv"]==process["argv"] and p["cmdline_sha256"]==process["cmdline_sha256"] and
    p["namespace_pids"][-1]==process["pid"] and p["stage"]=="matrix" and "--execute" in p["argv"] and
    p.get("borrowed_from_canary") is False,"actual distinct numerical process identity")
  require(p["start_ticks"]==int(process["stat"][process["stat"].rfind(")")+2:].split()[19]),"actual kernel start_ticks")
  for key in ("smi","complete_observation"):load(p[key])
  identities.add((p["pid"],p["start_ticks"]))
 require([{k:v for k,v in p.items() if k!="borrowed_from_canary"} for p in proofs]==child["physical_pid_proofs"],"original numerical child -> actual hardware proof list linkage")
 require(len(identities)==1 and not identities & {(p["pid"],p["start_ticks"]) for p in authority["canary_process_proofs"]},"actual numerical identity remains exact and distinct from canary")
 before=load(authority["protected_before"]);after=load(authority["protected_after"])
 require(before["processes"]==after["processes"] and set(before["processes"])=={"0","1","2","3"},"actual protected0..3 PID/start/cgroup/hash unchanged")
 stopped=load(authority["stopped_owned_inspect"])
 if "stdout" in stopped:stopped=json.loads(stopped["stdout"])
 require(len(stopped)==1 and stopped[0]["Id"]==proof["container_id"] and stopped[0]["Image"]==IMAGE and
    stopped[0]["Config"]["Labels"]==x["Config"]["Labels"] and stopped[0]["HostConfig"]==x["HostConfig"] and
    stopped[0]["Mounts"]==x["Mounts"] and not stopped[0]["State"]["Running"] and stopped[0]["State"]["Pid"]==0 and
    not stopped[0]["State"].get("OOMKilled",False) and not stopped[0].get("ExecIDs"),"full exact owned stopped-retained inspect, no rm")
 cleanup=load(authority["cleanup"])
 require(cleanup.get("container")==proof["container_id"] and cleanup.get("stopped") is True and cleanup.get("retained") is True and
    cleanup.get("deleted") is False and cleanup.get("errors")==[] and cleanup.get("primary_error") is None,"actual exact release and original/secondary cleanup closure")
 return {"schema":"sparq.complete-token-component/v4","component_report_checked":True,
  "MAIN_original_operation_authority_verified":True,"actual_numerical_steps":full["changing_feedback_steps"],"cases":128,
  "original_terminal":original_ref,"original_operation_id":parsed["operation_id"],"original_terminal_shape":parsed["origin_shape"],
  "original_record_origin":parsed["record_origin"],"actual_report":report_ref,"host_result":authority_ref,"native_no_device_abi":ndref,
  "source_manifest":source,"source_files":files,"ready":False,"service_ready":False,"model_executed":False,
  "physical_NPU_process_authority_verified":True,"owned_stop_retention_verified":True,
  "mixed_prefill_decode_model_scheduler_verified":False,"performance_evaluated":False,"accuracy_evaluated":False,
  "matched1024_e2e_verified":False,"final2048_task_verified":False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 for key in ("shard","terminal","proof","source-manifest","output"):p.add_argument("--"+key,type=Path)
 p.add_argument("--host-result",type=Path);p.add_argument("--host-result-sha256")
 p.add_argument("--terminal-sha256");p.add_argument("--source-manifest-sha256");p.add_argument("--expected-peer")
 a=p.parse_args()
 if not a.execute:print(json.dumps({"status":"disabled","ready":False,"npu_executed":False}));return
 require(all((a.shard,a.terminal,a.terminal_sha256,a.proof,a.source_manifest,a.source_manifest_sha256,a.expected_peer,a.output,a.host_result,a.host_result_sha256)) and not a.output.exists(),"all original actual explicit Refs/new result required")
 source,files=source_identity(Path(__file__).resolve().parent,a.source_manifest,a.source_manifest_sha256)
 result=consume(a.shard,a.terminal,a.terminal_sha256,a.proof,a.expected_peer,source,files,a.host_result,a.host_result_sha256);write_new(a.output,result)
 print(json.dumps(result),flush=True)
if __name__=="__main__":main()
