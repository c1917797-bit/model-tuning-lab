"""Independent WHOLE four-shard authority+every original step consumer.
No candidate/oracle math executed here; frozen independent row predicates
recheck each real128*160 result. A shard can never grant whole component PASS.
"""
import argparse,hashlib,json,re
from pathlib import Path
import shard_contract as sc
def load(ref):
 return json.loads(sc.read_ref(ref))
def header_union(parts,plan):
 sc.need(type(parts) is list and len(parts)==4,"exactly four whole shard reports, not fragments")
 seen=set();ids=set();steps=0
 for report in parts:
  sid=report["shard_id"];sc.need(sid not in ids,"duplicate shard identity");ids.add(sid)
  part=sc.check_headers(report,plan,sid)
  keys={sc.coordinate(r) for r in part["assigned_cases"]}
  sc.need(not seen & keys,"disjoint global coordinate ownership")
  seen.update(keys);steps+=report["completed_steps"]
 sc.need(ids==set(range(4)) and seen==set(sc.coordinates()) and steps==20480,"EXACT whole128/20480; no old partial salvage")
 return dict(cases=128,changing_feedback_steps=20480,shards=4)
def marker(text,name):
 lines=[v for v in text.splitlines() if v.startswith(name+" ")]
 sc.need(len(lines)==1,"one actual original terminal marker")
 return json.loads(lines[0].split(" ",1)[1])
def inspect(ref,c):
 raw=c.load(ref);rows=json.loads(raw["stdout"])
 sc.need(type(rows) is list and len(rows)==1,"single exact original Docker inspect")
 return rows[0]
def process_proofs(rows,child,report,cid,physical,canary_rows,c):
 sc.need(type(rows) is list and rows,"actual distinct numerical NPU process proof, not canary or CPU")
 argv=report["actual_container_process"]["argv"];proc=report["actual_container_process"]
 original=[{k:v for k,v in row.items() if k!="borrowed_from_canary"} for row in rows]
 sc.need(original==child["physical_pid_proofs"],"actual child/hardware proof list byte-field linkage")
 ids=set()
 for row in rows:
  sc.need(row["physical"]==physical and row["chip"]==0 and row["stage"]=="matrix" and cid in row["cgroup"] and
   row["argv"]==argv and row["namespace_pids"][-1]==proc["pid"] and row["cmdline_sha256"]==proc["cmdline_sha256"] and
   row.get("borrowed_from_canary") is False,"actual same-source original this numerical Python on this card")
  sc.need(row["start_ticks"]==int(proc["stat"][proc["stat"].rfind(")")+2:].split()[19]),"actual start_ticks from namespace /proc")
  raw=c.load(row["smi"]);ob=c.load(row["complete_observation"]);c.load(row["raw_observation"])
  sc.need(ob["smi"]==row["smi"] and ob["npu_smi"]==raw["stdout"],"whole original SMI/observation binds this actual PID")
  sc.need((physical,0,row["pid"]) in __import__("host").H.frozen().legacy().process_rows(raw["stdout"]),"actual original hardware process row")
  ids.add((row["pid"],row["start_ticks"]))
 sc.need(len(ids)==1 and not ids & {(p["pid"],p["start_ticks"]) for p in canary_rows},"not borrowed canary/other shard identity")
 return ids
def validate_cleanup(ref,stopped_ref,cid,owned_before,c):
 cr=c.load(ref);x=inspect(stopped_ref,c)
 sc.need(cr["container"]==cid and cr["stopped"] is True and cr["retained"] is True and cr["deleted"] is False and
  cr["errors"]==[] and cr["primary_error"] is None and cr["after_inspect"]==stopped_ref,"actual complete exact own stop-retain")
 sc.need(x["Id"]==cid and x["Image"]==c.IMAGE and x["HostConfig"]==owned_before["HostConfig"] and
  x["Config"]["Labels"]==owned_before["Config"]["Labels"] and x["Mounts"]==owned_before["Mounts"] and
  x["State"]["Running"] is False and x["State"]["Pid"]==0 and x["State"]["OOMKilled"] is False and
  not x.get("ExecIDs"),"full original stopped-inspect identity/source/isolation/resources")
 stop=c.load(cr["stop_receipt"])
 sc.need(stop["requested_argv"]==["/usr/bin/docker","stop","--time","15",cid] and stop["exit_code"]==0,
  "actual precise owned stop, no rm/global stop")
 raw=c.load(cr["release_smi"])
 physical=int(next(d["PathOnHost"][len("/dev/davinci"):] for d in owned_before["HostConfig"]["Devices"] if re.fullmatch("/dev/davinci[4-7]",d["PathOnHost"])))
 __import__("host").H.frozen().idle_one(raw["stdout"],physical)
 return x
def consume(own_ref,result_ref,terminal_ref,peer):
 own,m=sc.own_identity(own_ref["path"],own_ref["sha256"]);c,source,files=sc.native();nh=__import__("host")
 authority=c.load(result_ref);root=Path(authority["output_dir"])
 sc.need(root.is_absolute() and Path("/cache/cch") in root.parents and root.resolve()==root and
  result_ref["path"]==str(root/"RESULT.json"),"exact original new whole output root")
 sc.need(authority["schema"]=="sparq.disjoint4-host-result/v1" and authority["status"]=="complete-disjoint-numerics" and
  authority["packet_source"]==own and authority["native_source"]==source and
  authority["native_sources_before"]==authority["native_sources_after"]==files and
  authority["packet_files"]==m["files"] and authority["host_script_sha256"]==m["files"]["shard_host.py"] and
  authority["primary_error"] is None and authority["secondary_errors"]==[] and authority["partial_cases_used"]==0 and
  authority["numerical_component_checked"] is True and authority["ready"] is False and
  authority["model_executed"] is False and authority["matched1024_e2e_verified"] is False and
  authority["final2048_task_verified"] is False,"complete NEW4 numerical authority only, not model/performance")
 sc.need(authority["execution_clock"]==sc.own_clock(m) and authority["phase_seconds"]==5400 and
  authority["cleanup_seconds"]==90 and authority["common_deadline_monotonic"]-authority["common_created_monotonic"]==5400 and
  0<=authority["phase_elapsed_seconds"]<=5400,"same original whole5400 including joint90cleanup, no reset")
 from original_terminal import original_terminal
 terminal=original_terminal(c.load(terminal_ref),peer);record=terminal["record"]
 actual=[record["command"],*record["args"]]
 sc.need(actual==authority["actual_host_argv"]==authority["expected_host_argv"],"whole original host argv, not reconstructed legacy PASS")
 from shard_host import host_argv,previous_admission
 prior=authority["predecessor"]
 aa=argparse.Namespace(source_manifest=Path(own["path"]),source_manifest_sha256=own["sha256"],
  predecessor_result=Path(prior["result"]["path"]),predecessor_result_sha256=prior["result"]["sha256"],
  predecessor_terminal=Path(prior["whole_terminal"]["path"]),predecessor_terminal_sha256=prior["whole_terminal"]["sha256"],output=root)
 sc.need(host_argv(aa)==actual and previous_admission(prior["result"],prior["whole_terminal"],c)==prior,"full MAIN CLI + original timeout release prerequisite")
 mk=marker(record["stdout"],"MAIN_SPARQ_DISJOINT_HOST")
 sc.need(mk==dict(result=result_ref,status=authority["status"],packet_source=own),"whole actual terminal binds RESULT+source")
 hp=authority["actual_host_process"]
 sc.need(hp["argv"]==actual and hp["pid"]>1 and hp["cmdline_sha256"]==hashlib.sha256(("\0".join(actual)+"\0").encode()).hexdigest(),"actual host PID/argv/hash")
 plan=c.load(authority["allocation"]);sc.validate_allocation(plan)
 sc.need(authority["allocation"]["path"]==str(root/"ALLOCATION.json") and
  authority["allocation"]["sha256"]==sc.digest(plan),"exact allocated immutable canonical bytes")
 sc.need(len(authority["parts"])==len(authority["cleanup_records"])==4,"all four real host child/cleanup chains")
 cpu=authority["cpu_fields"];cpu_out=root/"cpu-preflight"
 sc.need(cpu["cpu_host_output_root"]==str(cpu_out) and cpu["native_no_device_abi"]["path"]==str(cpu_out/"ABI.json") and
  cpu["packet_cpu"]["path"]==str(cpu_out/"PACKET_CPU.json"),"only original actual CPU output roots")
 from preflight import validate_abi
 abi=validate_abi(c.load(cpu["native_no_device_abi"]),source,files)
 c.validate_cpu_phase(cpu,cpu["cpu_container_id"],source,files)
 c.validate_cpu_abi_child(cpu["cpu_container_id"],cpu_out,source,c.load(cpu["native_no_device_child"]),abi)
 pr=c.load(cpu["packet_cpu"]);pc=c.load(cpu["packet_cpu_child"])
 pa=[c.PY,"-B",str(sc.ROOT/"shard_numeric.py"),"--cpu-audit-only","--source-manifest",own["path"],"--source-manifest-sha256",own["sha256"]]
 sc.need(pr["status"]=="software-checked" and pr["packet_source"]==own and pr["native_source"]==source and
  pr["native_files"]==files and pr["argv"]==pa and pr["tests"]==m["software_test_count"] and
  pr["device_nodes"]==[] and pr["npu_executed"] is False and
  pc["exit_code"]==0 and pc["requested_argv"]==c.docker_argv(cpu["cpu_container_id"],pa),"real actual Devices[] source/software child")
 sc.need(nh.translate(marker(pc["stdout"],"MAIN_SPARQ_DISJOINT_CPU")["report"],cpu_out)==cpu["packet_cpu"],"packet CPU original stdout binds bytes")
 reports=[];all_cids=[cpu["cpu_container_id"]];all_proofs=[];seen=set();identities=set()
 cleanup={r["shard_id"]:r for r in authority["cleanup_records"]}
 sc.need(set(cleanup)==set(range(4)),"exact one original cleanup per shard")
 for part in authority["parts"]:
  sid=part["shard_id"];sc.need(sid not in seen and sid in range(4),"each original part exactly once");seen.add(sid)
  assigned=sc.assigned(plan,sid);out=root/("shard-%d-physical%d"%(sid,assigned["physical"]));cid=part["container_id"]
  sc.need(part["physical"]==assigned["physical"] and part["output"]==str(out) and cid not in all_cids,"exact shard output/card/distinct owned CID")
  all_cids.append(cid);ref=part["producer_report"];report=c.load(ref);reports.append(report)
  sc.check_headers(report,plan,sid)
  sc.need(ref["path"]==str(out/"gate/REPORT.json") and report["packet_source"]==own and
   report["source_manifest"]==source and report["sources_before"]==report["sources_after"]==files and
   report["script_sha256"]==m["files"]["shard_numeric.py"] and report["device_proof"]==part["source_device_proof"] and
   report["native_no_device_abi"]==cpu["native_no_device_abi"] and report["aggregate_execution_clock"]==authority["execution_clock"] and
   report["npu_executed"] is True and report["ready"] is False and report["model_executed"] is False,
   "actual shard producer/own math/clock/proof scope")
  argv=sc.shard_argv(Path("/sparq-results/gate"),part["source_device_proof"],authority["allocation"],own,sid)
  from shard_proof import validate_proof
  proof=validate_proof(part["source_device_proof"]["path"],part["source_device_proof"]["sha256"],source,files,argv,now_ns=report["started_ns"])
  owned=c.load(part["owned"])
  sc.need(part["owned"]["path"]==str(out/"OWNED.json") and owned["source"]==source and owned["packet_files"]==m["files"] and
   owned["packet_source"]==own and owned["physical"]==assigned["physical"] and owned["shard_id"]==sid and
   c.load(part["actual_guest_cpu"])==proof["actual_guest_cpu"],"actual complete source-bound owned/CPU receipts")
  from shard_host import inspect_card
  inspect_card(proof["container_inspect"],owned,nh)
  sc.need(proof["packet_source"]==own and proof["common_created_monotonic"]==authority["common_created_monotonic"] and
   proof["common_deadline_monotonic"]==authority["common_deadline_monotonic"] and
   all(proof[k]==cpu[k] for k in cpu),"original single CPU + joint lease + actual per-card proof")
  sc.need(report["started_ns"]/10**9+report["elapsed_seconds"]<=authority["execution_clock"]["repair_cutoff_epoch"],"actual shard completes by unchanged authorized repair cutoff")
  child=c.load(part["numerical_child"]);sc.need(child["exit_code"]==0 and child["child_termination_observed"] is True and
   child["primary_error"] is None and child["expected_image_python_argv"]==argv and report["actual_container_process"]["argv"]==argv and
   child["requested_argv"]==c.docker_argv(cid,argv) and
   child["actual_host_argv"]==["/usr/bin/prlimit","--as=unlimited","--",*c.docker_argv(cid,argv)],"full this owned CID/producer/source/newoutput argv")
  so=Path(c.bound(child["stdout_ref"]["path"],child["stdout_ref"]["sha256"])["path"]).read_text()
  sc.need(nh.translate(marker(so,"MAIN_SPARQ_DISJOINT_REPORT")["report"],out)==ref,"actual original shard stdout REPORT bytes")
  c.bound(child["stderr_ref"]["path"],child["stderr_ref"]["sha256"])
  canary=c.load(part["canary"]);cc=c.load(part["canary_child"])
  sc.need(cc["exit_code"]==0 and cc["child_termination_observed"] and cc["physical_pid_proofs"]==part["canary_process_proofs"] and
   canary["pid"]==cc["physical_pid_proofs"][-1]["namespace_pids"][-1] and
   canary["source_manifest"]==source and canary["script_sha256"]==files["host.py"] and
   all(p["physical"]==assigned["physical"] and p["stage"]=="canary" and cid in p["cgroup"] for p in cc["physical_pid_proofs"]),
   "each actual canary/source/physical PID, not other shard")
  ids=process_proofs(part["actual_npu_python_process_proofs"],child,report,cid,assigned["physical"],part["canary_process_proofs"],c)
  sc.need(not identities&ids,"four distinct actual process identities");identities.update(ids)
  all_proofs.extend(part["actual_npu_python_process_proofs"]+part["canary_process_proofs"])
  from shard_rows import validate_case_set
  checked=validate_case_set(report,out/"gate",{sc.coordinate(r) for r in assigned["assigned_cases"]})
  sc.need(checked==part["report_completeness"] and checked["numerical_component_checked"] is False,"shard receipt not labelled128 PASS")
  cl=cleanup[sid];sc.need(cl["container_id"]==cid,"exact cleanup CID assignment")
  validate_cleanup(cl["cleanup"],cl["stopped_owned_inspect"],cid,proof["container_inspect"],c)
 coverage=header_union(reports,plan)
 release=c.load(authority["release"]);raw=c.load(release["smi"]);sc.need(release["all_cards"]==list(sc.CARDS) and release["no_owned_compute"] is True,"whole real final release")
 for card in sc.CARDS:nh.H.frozen().idle_one(raw["stdout"],card)
 boundary=release["protected_boundary"]
 sc.need(nh.protected_boundary(boundary["baseline"],boundary["observed"],all_cids,[hp["pid"]])==boundary,"owned never protected0..3; external churn not immutable-population requirement")
 for p in all_proofs:
  ob=c.load(p["complete_observation"]);b=ob["protected_boundary"];sr=c.load(ob["smi"])
  sc.need(ob["npu_smi"]==sr["stdout"] and b["baseline"]==boundary["baseline"] and
   nh.protected_boundary(b["baseline"],b["observed"],all_cids,[hp["pid"]])==b,
   "all original actual observations protected identity/source boundaries")
  sc.need(sorted((v["physical"],v["chip"],v["pid"]) for v in b["observed"])==
   sorted(v for v in nh.H.frozen().legacy().process_rows(sr["stdout"]) if v[0] in (0,1,2,3)),"raw SMI matches each protected observation")
 return dict(schema=sc.AGG_SCHEMA,status="complete-numerical-component",**coverage,
  MAIN_original_operation_authority_verified=True,numerical_component_checked=True,packet_source=own,native_source=source,
  original_terminal=terminal_ref,operation_id=terminal["operation_id"],result=result_ref,execution_clock=authority["execution_clock"],
  original0227_status="timeout-not-promoted",original_ba508_status="FAILED-not-promoted",partial_cases_used=0,
  ready=False,model_executed=False,matched1024_e2e_verified=False,final2048_task_verified=False)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--consume",action="store_true")
 for name in ("source-manifest","result","original-terminal","output"):p.add_argument("--"+name,type=Path)
 for name in ("source-manifest","result","original-terminal"):p.add_argument("--"+name+"-sha256")
 p.add_argument("--peer",default="lgw_a6109c51076a4a2c9d2674ca5a8704a0");a=p.parse_args()
 if not a.consume:
  print(json.dumps(dict(status="disabled",ready=False,numerical_component_checked=False)));return
 ref=lambda name:dict(path=str(getattr(a,name.replace("-","_"))),sha256=getattr(a,name.replace("-","_")+"_sha256"))
 result=consume(ref("source-manifest"),ref("result"),ref("original-terminal"),a.peer)
 sc.need(a.output is not None and a.output.is_absolute() and not a.output.exists(),"one new exclusive consumer output")
 out=sc.publication(a.output,result);print(json.dumps(dict(report=out,**result)))
if __name__=="__main__":main()
