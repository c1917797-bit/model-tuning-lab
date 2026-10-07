"""Original terminal/report/source/owned-process/retention consumer, stdlib only."""
import json,re
from datetime import datetime
from pathlib import Path
from contract import *
def terminal_record(envelope,expected_peer):
 require(envelope.get("targetPeerId")==expected_peer and envelope.get("routeDecision") in ("peer_direct","upstream_local_peer"),"actual original intended peer route")
 records=[]
 if isinstance(envelope.get("result"),dict):
  r=envelope["result"]
  if isinstance(r.get("record"),dict):records.append(r["record"])
  if isinstance(r.get("operation"),dict) and isinstance(r["operation"].get("result"),dict) and isinstance(r["operation"]["result"].get("record"),dict):records.append(r["operation"]["result"]["record"])
 if isinstance(envelope.get("operation"),dict):
  r=envelope["operation"]
  if isinstance(r.get("result"),dict) and isinstance(r["result"].get("record"),dict):records.append(r["result"]["record"])
 require(records and all(v==records[0] for v in records),"one original terminal record identity")
 r=records[0]
 require(r.get("state")=="completed" and r.get("exitCode")==0 and r.get("timedOut") is False and r.get("cancelled") is False,"actual completed original zero exit, no timeout/cancel")
 return r
def producer_marker(text):
 rows=[line for line in text.splitlines() if line.startswith("MAIN_FLASHINFER_NATIVE_STATE_V3_REPORT ")]
 require(len(rows)==1,"one actual producer marker, not old successful terminal")
 return json.loads(rows[0].split(" ",1)[1])
def consume(a,source,files):
 require(all((a.launch_proof,a.launch_proof_sha256,a.terminal,a.terminal_sha256,
    a.execution_authority,a.execution_authority_sha256,a.report,a.report_sha256,a.expected_peer)),"all original actual receipt Refs and expected peer required")
 tr=bound(a.terminal,a.terminal_sha256);envelope=load_ref(tr);record=terminal_record(envelope,a.expected_peer)
 ar=bound(a.execution_authority,a.execution_authority_sha256);authority=load_ref(ar)
 lr=bound(a.launch_proof,a.launch_proof_sha256);launch=load_ref(lr)
 rr=bound(a.report,a.report_sha256);report=load_ref(rr)
 require(authority.get("schema")=="flashinfer.native-state-host-result/v3" and
   authority.get("container_id")==launch["container_id"] and authority.get("source_manifest")==source and
   authority.get("source_launch_proof")==lr and authority.get("producer_report")==rr,"original host authority closure")
 requested=[record["command"],*record["args"]]
 from host import host_argv
 output=Path(authority["output_dir"])
 host_args=__import__("argparse").Namespace(source_manifest=Path(source["path"]),source_manifest_sha256=source["sha256"],output_dir=output)
 expected_host=host_argv(host_args)
 require(requested==expected_host==authority.get("actual_host_argv")==authority.get("expected_host_argv"),"exact frozen actual MAIN CLI/current source/new output; no substring or wrapper")
 require(authority.get("status")=="kernel_numerics_checked" and authority.get("numerical_component_checked") is True and authority.get("primary_error") is None and authority.get("secondary_errors")==[] and
   authority.get("sources_before")==authority.get("sources_after")==files and authority.get("dependencies")==DEPENDENCIES and
   authority.get("host_script_sha256")==files["host.py"] and authority.get("entry_script_sha256")==files["main.py"],"full actual host result/controller/source and primary-secondary closure")
 host_marker_rows=[l for l in record["stdout"].splitlines() if l.startswith("MAIN_FLASHINFER_NATIVE_STATE_V3_HOST ")]
 require(len(host_marker_rows)==1,"one original actual host terminal marker")
 host_marker=json.loads(host_marker_rows[0].split(" ",1)[1])
 require(host_marker["result"]==ar and host_marker["status"]==authority["status"] and host_marker["source_manifest"]==source and
   host_marker["host_script_sha256"]==files["host.py"] and host_marker["entry_script_sha256"]==files["main.py"],"original terminal marker binds exact immutable host result bytes")
 require(authority["actual_host_process"]["argv"]==requested and authority["actual_host_process"]["pid"]>1 and
   authority["actual_host_process"]["cmdline_sha256"]==__import__("hashlib").sha256(("\0".join(requested)+"\0").encode()).hexdigest(),"actual host process exact cmdline identity")
 require(report["source_manifest"]==source and report["sources_before"]==files and report["sources_after"]==files and
    report["script_sha256"]==files["main.py"] and report["launch_proof"]==lr and report["launch_identity"]==launch,"this actual producer/source/proof")
 validate_launch(launch,source,files,report["actual_container_process"]["argv"],launch_ref=lr,now=datetime.fromisoformat(report["started_utc"]))
 child=None
 require("numerical_child" in authority,"actual owned numerical child mandatory")
 if "numerical_child" in authority:
  child=load_ref(authority["numerical_child"])
  require(child.get("exit_code")==0 and child.get("child_termination_observed") is True and
     child.get("expected_image_python_argv")==report["actual_container_process"]["argv"],"actual numerical child original termination/argv")
  marker_text=Path(bound(child["stdout_ref"]["path"],child["stdout_ref"]["sha256"])["path"]).read_text()
  child_argv=child["requested_argv"]
 else:
  marker_text=record["stdout"];child_argv=requested
 expected_child=["/usr/bin/docker","exec",launch["container_id"],"/bin/bash","-c",
    'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"kvbp-diagnostic",
    *report["actual_container_process"]["argv"]]
 if child_argv[:3]==["/usr/bin/prlimit","--as=unlimited","--"]:child_argv=child_argv[3:]
 require(child_argv==expected_child and child["actual_host_argv"]==["/usr/bin/prlimit","--as=unlimited","--",*expected_child],"complete actual CID/environment/Python/source/flags/output child CLI and Docker-only AS wrapper")
 marker=producer_marker(marker_text)
 require(marker["status"]=="passed" and marker["report"]["sha256"]==rr["sha256"] and marker["source_manifest"]==source and
   marker["producer_script_sha256"]==files["main.py"] and marker["launch_proof"]==lr,"actual stdout -> immutable report bytes/source")
 inspected=load_ref(launch["evidence"]["inspect"])
 if "stdout" in inspected:inspected=json.loads(inspected["stdout"])
 x=inspected[0]
 ms=[m for m in x["Mounts"] if m["Destination"]=="/flashinfer-results"]
 require(len(ms)==1 and ms[0]["Type"]=="bind" and ms[0]["RW"] is True,"actual owned output bind")
 host_root=Path(ms[0]["Source"]);image_root=Path("/flashinfer-results")
 require(host_root==output and rr["path"]==str(output/"gate/report.json") and lr["path"]==str(output/"launch.json") and ar["path"]==str(output/"RESULT.json"),"full original new unique output leaf closure")
 def translate(r):
  p=Path(r["path"]);require(image_root in p.parents and ".." not in p.parts,"original producer case ABI/report image path")
  host=host_root/p.relative_to(image_root)
  require(host.resolve()==host and host.is_file() and not host.is_symlink(),"exact mapped original owned output file")
  return bound(host,r["sha256"])
 require(translate(marker["report"])==rr,"actual new output leaf mapping")
 abi=load_ref(translate(report["actual_native_abi"]))
 require(abi["source_manifest"]==source and abi["sources"]==files and abi["launch_proof"]==lr and
    abi["actual_exports"]==report["actual_exports"] and abi["actually_mapped_libraries"]==report["actually_mapped_libraries"],"original actual loaded ABI/library receipt")
 full=validate_cases(report,read_case=lambda r:load_ref(translate(r)))
 process=report["actual_container_process"];proofs=authority.get("actual_npu_python_process_proofs")
 require(type(proofs) is list and proofs,"actual numerical NPU Python PID proofs mandatory, not canary")
 identities=set()
 for p in proofs:
  require(p["physical"]==6 and p["chip"]==0 and launch["container_id"] in p["cgroup"] and
    p["argv"]==process["argv"] and p["cmdline_sha256"]==process["cmdline_sha256"] and
    p["namespace_pids"][-1]==process["pid"] and p["stage"]=="matrix" and "--execute" in p["argv"] and
    p.get("borrowed_from_canary") is False,"actual distinct numerical process identity")
  require(p["start_ticks"]==int(process["stat"][process["stat"].rfind(")")+2:].split()[19]),"actual kernel start_ticks")
  for key in ("smi","complete_observation"):load_ref(p[key])
  identities.add((p["pid"],p["start_ticks"]))
 require([{k:v for k,v in p.items() if k!="borrowed_from_canary"} for p in proofs]==child["physical_pid_proofs"],"original numerical child -> actual hardware proof list linkage")
 require(len(identities)==1 and not identities & {(p["pid"],p["start_ticks"]) for p in authority["canary_process_proofs"]},"actual numerical identity remains exact and distinct from canary")
 before=load_ref(authority["protected_before"]);after=load_ref(authority["protected_after"])
 require(before["processes"]==after["processes"] and set(before["processes"])=={"0","1","2","3"},"actual protected0..3 PID/start/cgroup/hash unchanged")
 stopped=load_ref(authority["stopped_owned_inspect"])
 if "stdout" in stopped:stopped=json.loads(stopped["stdout"])
 require(len(stopped)==1 and stopped[0]["Id"]==launch["container_id"] and stopped[0]["Image"]==IMAGE and
    stopped[0]["Config"]["Labels"]==x["Config"]["Labels"] and stopped[0]["HostConfig"]==x["HostConfig"] and
    stopped[0]["Mounts"]==x["Mounts"] and not stopped[0]["State"]["Running"] and stopped[0]["State"]["Pid"]==0 and
    not stopped[0]["State"].get("OOMKilled",False) and not stopped[0].get("ExecIDs"),"full exact owned stopped-retained inspect, no rm")
 cleanup=load_ref(authority["cleanup"])
 require(cleanup.get("container")==launch["container_id"] and cleanup.get("stopped") is True and cleanup.get("retained") is True and
    cleanup.get("deleted") is False and cleanup.get("errors")==[] and cleanup.get("primary_error") is None,"actual exact release and original/secondary cleanup closure")
 return {"schema":"flashinfer.actual-native-state-component-authority/v3","numerical_component_checked":True,"MAIN_original_operation_authority_verified":True,
   "changing_feedback_steps":full["changing_feedback_steps"],"original_terminal":tr,"execution_authority":ar,
   "actual_report":rr,"actual_native_abi":translate(report["actual_native_abi"]),"source_manifest":source,
   "source_files":files,"ready":False,"serving_ready":False,"model_lifecycle_verified":False,
   "native_scheduler_or_tiling_benefit_verified":False,"matched1024_e2e_verified":False,"final2048_task_verified":False}
