"""SHA-bound source/full-CLI/terminal marker contracts, stdlib only.
This numeric packet alone has no host process/cleanup/model authority.
"""
import hashlib,json,os,re,sys
from pathlib import Path
from sparq_token_v4.core import require
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PY="/usr/local/python3.12.13/bin/python3"
OWNER="sparq-token-v6"
BATCHES="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16"
MODES=(("eager",0),("graph",0),("graph",1),("graph",2))
ROOT=Path(__file__).resolve().parent
CUT="2026-10-09T11:17:31+00:00"
DEPENDENCIES={
 "/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4/host_run.py": "4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20",
 "/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py": "ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86",
 "/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py": "86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc"
}
OWN=("README.md","READY.md","consume_numeric.py","numeric_gate.py","preflight.py","sparq_token_v4/__init__.py",
 "sparq_token_v4/core.py","sparq_token_v4/oracle.py","sparq_token_v4/proof.py","test_contract.py","receipt.py","host.py","model_bridge.py","sitecustomize.py","original_terminal.py","original_operation_get_ma0e85.json","original_operation_get_ma0e7f_not_found.json","test_abi.py","original_v4_failed_ABI.json","original_v4_failed_child.json","test_launch_linkage.py")
def sha(path):
 p=Path(path);require(p.is_absolute() and p.is_file() and not p.is_symlink(),"exact absolute ordinary evidence")
 h=hashlib.sha256()
 with p.open("rb") as r:
  for b in iter(lambda:r.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def bound(path,digest):
 p=Path(path);require(p.is_absolute() and ".." not in p.parts and re.fullmatch("[a-f0-9]{64}",digest or ""),"exact absolute SHA Ref")
 require(sha(p)==digest,"actual bytes changed");return {"path":str(p),"sha256":digest}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def write_new(p,v):
 with Path(p).open("xb") as stream:stream.write(canonical(v)+b"\n");stream.flush();os.fsync(stream.fileno())
 return bound(p,sha(p))
def load(r):
 bound(r["path"],r["sha256"]);return json.loads(Path(r["path"]).read_bytes())
MODEL_SOURCES={"attention_v1":{"runtime_ref":{"path":"/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py","sha256":"80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"},"captured_source_ref":{"path":"/cache/cch/flashinfer-native-abi-v1-20261007-1716-001/source_snapshots/attention_v1.py","sha256":"80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"}},"model_runner_v1":{"runtime_ref":{"path":"/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py","sha256":"94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"},"captured_source_ref":{"path":"/cache/cch/flashinfer-native-abi-v1-20261007-1716-001/source_snapshots/model_runner_v1.py","sha256":"94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"}}}
def source_identity(root,path,digest,context="host"):
 require(context in ("host","runtime") and path==root/"SOURCE_MANIFEST.json","exact current source manifest/context")
 sr=bound(path,digest);m=load(sr)
 require(m["schema"]=="sparq.token-preparation/v6" and m["ready"] is False and m["source_count"]==27 and
   set(m["files"])==set(OWN),"full21 own +1 native +3 generic +2 actual model-source closure")
 for name,s in m["files"].items():bound(root/name,s)
 require(m.get("dependencies")==DEPENDENCIES,"fixed generic host source closure")
 for path,d in DEPENDENCIES.items():bound(path,d)
 pair=m["native_device_operator"];require(pair["runtime_ref"]["sha256"]==pair["captured_source_ref"]["sha256"]=="de6a8547df3ff92bf8666e475be56840005cccb3272452c2d6cac4c3f1ddff47","same actual native/captured source")
 r=pair["runtime_ref"] if context=="runtime" else pair["captured_source_ref"];bound(r["path"],r["sha256"])
 require(m.get("model_sources")==MODEL_SOURCES,"actual deployed model seam source pins, never public tag guesses")
 for pair in MODEL_SOURCES.values():
  r=pair["runtime_ref"] if context=="runtime" else pair["captured_source_ref"];bound(r["path"],r["sha256"])
 return sr,m["files"]
def abi_image_argv(root,source,host_output_root):
 root=Path(root);out=Path(host_output_root)
 require(root.is_absolute() and ".." not in root.parts and source["path"]==str(root/"SOURCE_MANIFEST.json") and
  re.fullmatch("[a-f0-9]{64}",source["sha256"] or "") and out.is_absolute() and ".." not in out.parts and
  Path("/cache/cch") in out.parents,"one exact source-bound CPU ABI root/output Ref")
 return [PY,"-B",str(root/"preflight.py"),"--execute","--source-manifest",source["path"],
  "--source-manifest-sha256",source["sha256"],"--output","/sparq-results/ABI.json","--host-output-root",str(out)]
def validate_cpu_abi_child(cid,host_output_root,source,child,abi):
 expected=abi_image_argv(Path(source["path"]).parent,source,host_output_root)
 command=docker_argv(cid,expected)
 require(abi["actual_argv"]==expected and abi["actual_observations"]["actual_argv"]==expected and
  child["requested_argv"]==command and child["argv"]==["/usr/bin/prlimit","--as=unlimited","--",*command] and
  child["exit_code"]==0,"actual complete CPU ABI argv/source/output/owned CID; no missing/duplicate/reordered flags")
 require(abi["original_observations"]["path"]==str(Path(host_output_root)/"ABI_OBSERVATIONS.json"),
  "actual original observer must belong to exact owned CPU output root")
 return expected
def image_argv(root,output,proof,source):
 return [PY,"-B",str(root/"numeric_gate.py"),"--execute","--output",str(output),
  "--device-proof",proof["path"],"--device-proof-sha256",proof["sha256"],
  "--source-manifest",source["path"],"--source-manifest-sha256",source["sha256"],"--batches",BATCHES,"--steps","160"]
def docker_argv(cid,argv):
 require(re.fullmatch("[a-f0-9]{64}",cid or ""),"complete exact owned CID")
 return ["/usr/bin/docker","exec",cid,"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"kvbp-diagnostic",*argv]
def marker(text):
 rows=[r for r in text.splitlines() if r.startswith("MAIN_SPARQ_TOKEN_V5_REPORT ")]
 require(len(rows)==1,"one actual original producer marker")
 return json.loads(rows[0].split(" ",1)[1])
def check_terminal(r,expected,report_ref,source,files,proof):
 require([r["command"],*r["args"]]==expected,"exact full original foreground CLI/CID/script/refs/batches/steps/newoutput; no substring")
 m=marker(r["stdout"])
 require(m["report"]==report_ref and m["status"]=="passed" and m["source_manifest"]==source and
   m["script_sha256"]==files["numeric_gate.py"] and m["device_proof"]==proof,"actual stdout -> immutable report/source/proof bytes")
 return m
def host_marker(text):
 rows=[r for r in text.splitlines() if r.startswith("MAIN_SPARQ_TOKEN_V5_HOST ")]
 require(len(rows)==1,"one original actual host terminal marker")
 return json.loads(rows[0].split(" ",1)[1])

def validate_matrix(report,root):
 from numeric_gate import LIMITS
 from sparq_token_v4.core import HEADS
 import math
 require(report.get("schema")=="sparq.token-numeric/v4" and report.get("status")=="passed" and report.get("limits")==LIMITS,
  "actual complete original SparQ kernel report")
 output=Path("/sparq-results/gate")
 require(root.is_absolute() and root.is_dir() and root.resolve()==root,"exact owned numerical gate root")
 require(not (root/"FAILURE.json").exists() and not list(root.glob("failure-*.pt")) and not list(root.glob("raw-failure-*.json")) and
  "secondary_source_error" not in report,"first numerical failure never relabelled")
 def translated(r):
  p=Path(r["path"]);require(output in p.parents and ".." not in p.parts,"actual immutable original image-owned case/step path")
  hp=root/p.relative_to(output);require(hp.resolve()==hp and hp.is_file() and not hp.is_symlink(),"actual owned case/step mapping")
  return bound(hp,r["sha256"])
 keys=set();count=0
 for header in report["cases"]:
  b,m,c,t=header["batch"],header["mode"],header["reallocation"],header["trial"];key=(b,m,c,t)
  require(type(b) is int and b in range(1,17) and type(c) is bool and (m,t) in MODES and key not in keys,"unique exact128-case coordinates");keys.add(key)
  case=load(translated(header["actual_case_ref"]));require(all(case[k]==header[k] for k in ("batch","mode","reallocation","trial")),"actual immutable case coordinates")
  require(case["status"]=="passed" and case["steps"]==160 and case["service_ready"] is False and case["model_graph_supported"] is False and
    case["worst_relative_rms"]<=.005 and case["minimum_cosine"]>=.99998 and case["actual_mean_bytes"]==18*(256*4+8)+128*(4+8) and
    case["mean_payload_bytes"]==18*(256*4+8) and case["actual_workspace_bytes"]>0 and len(case["actual_step_refs"])==160,"original complete guarded case")
  for s,sr in enumerate(case["actual_step_refs"]):
   row=load(translated(sr));require((row["batch"],row["mode"],row["reallocation"],row["trial"],row["step"])==(b,m,c,t,s),"all160 actual ordered steps")
   require(all(row[k] is True for k in ("finite","full_native_cache_bitwise","selected_scratch_guard","input_untouched","mean_request_lease_checked","support_independent","pointer_identity","workspace_mean_guards","all_topology_immutable","reference_feedback_independent","oracle_cpu_fp64","per_head_metric","native_cache_input_outer_guards")),"complete original per-step full guards/slot/oracle checks")
   require(row.get("support_independent_query")=="candidate-feedback-q" and row.get("dense_attention_equivalence_claimed") is False and
    type(row.get("reference_feedback_support_equal")) is bool and type(row.get("cross_feedback_support_divergence")) is list and
    len(row["cross_feedback_support_divergence"])==b and all(type(v) is bool for v in row["cross_feedback_support_divergence"]) and
    row["reference_feedback_support_equal"]==(not any(row["cross_feedback_support_divergence"])),
    "actual approximate-support divergence classification; q/rq feedback never shared")
   for name,lo,hi in (("relative_rms",0,.005),("cosine",.99998,1.000001)):
    values=row[name];require(len(values)==b and all(len(v)==HEADS for v in values) and
      all(type(v) in (int,float) and math.isfinite(v) and lo<=v<=hi for heads in values for v in heads),"actual EVERY request/head gate; no mean")
   count+=1
 require(keys=={(b,m,c,t) for b in range(1,17) for m,t in MODES for c in (False,True)} and count==20480,"full128cases/20480 numerical steps; no shard PASS")
 return {"cases":128,"changing_feedback_steps":count,"numerical_component_checked":True,
  "ready":False,"service_ready":False,"model_executed":False,"matched1024_e2e_verified":False,"final2048_task_verified":False}

def inspect_row(ref):
 rows=load(ref)
 if "stdout" in rows:rows=json.loads(rows["stdout"])
 require(type(rows) is list and len(rows)==1,"one complete original exact CID inspect")
 return rows[0]
def validate_cpu_phase(e,cid,source,files):
 require(re.fullmatch("[a-f0-9]{64}",cid or ""),"actual complete independent CPU-only CID")
 owned=load(e["cpu_only_owned"]);live=inspect_row(e["cpu_only_inspect"]);stopped=inspect_row(e["cpu_stopped_inspect"])
 require(owned.get("cid")==cid and owned.get("mode")=="cpu" and owned.get("source")==source and
   owned.get("host_sha256")==files["host.py"],"actual own source-bound CPU-only role")
 from host import validate_inspect
 validate_inspect(live,owned);validate_inspect(stopped,owned)
 require(not (live["HostConfig"].get("Devices") or []) and live["State"]["Running"] is True and live["State"]["Pid"]>0,
  "original actual CPU-only inspected live guest: no device nodes/remaps")
 require(not stopped["State"]["Running"] and stopped["State"]["Pid"]==0 and not stopped.get("ExecIDs") and
  not stopped["State"].get("OOMKilled",False),"actual CPU-only stopped-retained process/no OOM")
 cleanup=load(e["cpu_only_cleanup"])
 require(cleanup["container"]==cid and cleanup["stopped"] is True and cleanup["retained"] is True and cleanup["deleted"] is False and
  cleanup["errors"]==[] and cleanup["primary_error"] is None and cleanup["after_inspect"]==e["cpu_stopped_inspect"],
  "original CPU-only exact own stop-retain/primary-secondary closure")
 stop=load(cleanup["stop_receipt"])
 require(stop["requested_argv"]==["/usr/bin/docker","stop","--time","15",cid] and stop["exit_code"]==0,
  "original precise CPU-only stop terminal, no rm/global stops")
 return live,stopped
