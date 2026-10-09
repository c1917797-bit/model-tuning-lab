"""Two explicit source seams; not numerical/model/performance authority.
Actual assignment tap -> immutable per-request map; CPU static -> admitted N1.
Formal records one mapping per request, never tensor/per-token observations.
"""
import hashlib,json,os,sys,traceback
from pathlib import Path
import source_contract as c
IDROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/recurrent/vllm023-completion-identity-oracle-v1-user72h-20261009")
ORACLE_SHA="f288191487869fe752fea8713742bff2e6245c30d9ed790243b8868520f0e333"
CAPTURE_SHA="1cfb4c995917c5d89868102e6bd8b4c6d68fe1f59881186be6e7831ff0ccaec5"
ASSIGN_SHA="c5673988c0f7cfec268220e3f044e718702c015a4f236c020937cfd40a793f15"
PROFILE=dict(endpoint="/v1/completions",prompt_count=1,n=1,beam_search=False,streaming_input=False)
_INSTALLED=False
def oracle():return c.module(IDROOT/"oracle.py",ORACLE_SHA,"_sparq_actual_assigned_identity_oracle")
def flag():
 c.require(os.environ.get("VLLM_DISABLE_REQUEST_ID_RANDOMIZATION")=="1","both arms explicit same randomization OFF")
 from vllm import envs
 c.require(envs.VLLM_DISABLE_REQUEST_ID_RANDOMIZATION is True,"actual installed env flag agrees")
 c.bound("/vllm-workspace/vllm/vllm/v1/engine/input_processor.py",ASSIGN_SHA)
 return dict(disable_request_id_randomization=True,environment_value="1",processor_source_sha256=ASSIGN_SHA)
def raw_process():
 pid=os.getpid();root=Path("/proc")/str(pid);stat=(root/"stat").read_text();tail=stat[stat.rfind(")")+2:].split()
 c.require(len(tail)>=20,"complete actual process stat")
 argv=(root/"cmdline").read_bytes()
 return dict(pid=pid,start_ticks=int(tail[19]),cgroup=(root/"cgroup").read_text(),stat=stat,
  argv=argv.decode().rstrip("\0").split("\0"),cmdline_sha256=hashlib.sha256(argv).hexdigest())
def identity_root(service_root):
 root=Path(service_root)/"identity"
 c.require(root.is_absolute() and root.resolve()==root and Path("/cache/cch") in root.parents and root.is_dir() and
  not root.is_symlink(),"exact owned identity journal separate from formal per-layer trace")
 return root
def assignment_path(service_root,passed):
 c.require(type(passed) is str and passed and len(passed)<512,"bounded actual passed ID")
 return identity_root(service_root)/("assigned-"+hashlib.sha256(passed.encode()).hexdigest()+".json")
def install_frontend():
 global _INSTALLED
 c.require(not _INSTALLED,"one assignment tap in each actual frontend/worker process")
 from vllm.v1.engine.input_processor import InputProcessor
 actual_flag=flag()
 capture=c.module(IDROOT/"capture.py",CAPTURE_SHA,"_sparq_actual_assigned_capture")
 root=identity_root(os.environ["QWEN36_SPARQ_MODEL_SERVICE_ROOT"])
 source=c.bound(os.environ["QWEN36_SPARQ_STOCK_FULL_SOURCE"],os.environ["QWEN36_SPARQ_STOCK_FULL_SOURCE_SHA"])
 frontend=c.write(root/("frontend-%d.json"%os.getpid()),dict(schema="sparq.actual-assignment-frontend/v1",
  source=source,process=raw_process(),flag=actual_flag,assignment_source_sha256=ASSIGN_SHA))
 def emit(kind,event):
  c.require(kind=="assignment","only real processor assignment event")
  c.require(event["disable_request_id_randomization"] is True,"runtime event does not silently change common flag")
  value=dict(schema="sparq.actual-assignment-record/v1",source=source,frontend=frontend,
   profile=PROFILE,event=event)
  c.write(assignment_path(root.parent,event["before_request_id"]),value)
 capture.install_assignment(InputProcessor,emit)
 _INSTALLED=True
 return frontend
def mapping(server_id,service_root):
 # This expression is only the official *passed* ID / immutable file locator.
 # Actual worker ID below is obtained from the post-call assignment event.
 o=oracle();passed=server_id+"-0"
 path=assignment_path(service_root,passed);ref=c.bound(path,c.sha(path));record=c.obj(ref)
 c.require(record["schema"]=="sparq.actual-assignment-record/v1" and record["profile"]==PROFILE,"actual assignment record/schema")
 external,assigned=o.validate_assignment(server_id,PROFILE,record["event"])
 c.require(record["event"]["disable_request_id_randomization"] is True and external==passed,
  "actual callback confirms common OFF; no inferred suffix or configuration-only proof")
 front=c.obj(record["frontend"]);p=front["process"]
 c.require(front["schema"]=="sparq.actual-assignment-frontend/v1" and front["source"]==record["source"] and
  record["event"]["identity"]=={k:p[k] for k in ("pid","start_ticks","cgroup")} and
  front["flag"]==dict(disable_request_id_randomization=True,environment_value="1",processor_source_sha256=ASSIGN_SHA),
  "actual same frontend PID/start/cgroup and source-bound flag")
 return dict(actual_server_response_id=server_id,passed_request_id=external,actual_engine_request_id=assigned,
  assignment_ref=ref,assignment_frontend_ref=record["frontend"])
def verify_row(row,service_root):
 actual=mapping(row["actual_server_response_id"],service_root)
 c.require(all(row[k]==v for k,v in actual.items()),"row assigned ID must equal actual callback, not SSE guess")
 arm=c.obj(c.bound(Path(service_root)/"ARM.json",c.sha(Path(service_root)/"ARM.json")))
 rec=c.obj(actual["assignment_ref"]);front=c.obj(actual["assignment_frontend_ref"]);ident=c.obj(arm["identity"])
 c.require(rec["source"]==front["source"]==arm["source"] and ident["container_id"] in front["process"]["cgroup"],
  "assignment belongs to the source-bound exact owned arm/CID, not external or stale frontend")
 return actual["actual_engine_request_id"]
def validate_worker_flag(value):
 c.require(value==dict(disable_request_id_randomization=True,environment_value="1",processor_source_sha256=ASSIGN_SHA),
  "each actual worker must observe same source-bound common flag")
 return True
def static_probe(probe,source,files):
 c.require(probe["status"]=="source-static-checked" and probe["source"]==source and probe["files"]==files and
  probe["runtime_framework_imported"] is False and probe["device_query_called_by_probe"] is False and
  probe["runner_import_pending_admitted_N1"] is True and probe["actual_device_nodes"]==[] and probe["actual_device_fds"]==[] and
  probe["installed_runtime_sources"]==c.RUNTIME_PINS,"actual Devices[] static closure; no pretend runner import")
 return True
def n1_dependency_gate(source,files,identity,service_root):
 ident=c.obj(identity);cid=ident["container_id"];inspect=c.obj(ident["actual_owned_inspect"])
 rows=json.loads(inspect["stdout"]);c.require(inspect["exit_code"]==0 and len(rows)==1 and rows[0]["Id"]==cid,
  "actual admitted exact owned inspect before hardware import")
 want={"/dev/davinci%d"%p:"/dev/davinci%d"%r for r,p in enumerate((4,5,6,7))}
 want.update({"/dev/"+n:"/dev/"+n for n in ("davinci_manager","devmm_svm","hisi_hdc")})
 actual={d["PathOnHost"]:d["PathInContainer"] for d in rows[0]["HostConfig"].get("Devices",[])}
 c.require(actual==want and rows[0]["Image"]=="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
  "N1 requires exact already admitted physical4..7 guest0..3 mapping, never CPU hardware bypass")
 report=dict(schema="sparq.admitted-N1-runtime-dependencies/v1",status="failed",source=source,files=files,
  identity=identity,container_id=cid,process=raw_process(),installed_runtime_sources=c.RUNTIME_PINS,
  imports=[],first_exception=None,model_allocation_not_started=True,model_numeric_authorized=False)
 try:
  import vllm_ascend.ops
  import torch,torch_npu
  import vllm_ascend.attention.attention_v1 as attention
  import vllm_ascend.worker.model_runner_v1 as runner
  import vllm_ascend.compilation.acl_graph as acl
  import gdn_source
  c.runtime_sources(attention,runner,acl);modules=gdn_source.runtime()
  report["imports"]=["vllm_ascend.ops","torch","torch_npu",attention.__name__,runner.__name__,acl.__name__,*[m.__name__ for m in modules.values()]]
  for owner,name in ((runner.NPUModelRunner,"_model_forward"),(attention.AscendAttentionBackendImpl,"update_graph_params"),(acl.ACLGraphWrapper,"__call__")):
   c.require(callable(getattr(owner,name)),"real N1 receiver ABI "+name)
  import long_workspace,no_pa_full,long_independent_oracle,gdn_stream,numpy
  c.bound(long_independent_oracle.__file__,files["long_independent_oracle.py"])
  c.bound(gdn_stream.__file__,files["gdn_stream.py"])
  report["original_post_order"]=no_pa_full.original_post_order(no_pa_full.verified_sources()["model_runner_v1.py"])
  inherited=long_workspace.numeric_source()
  report["author_workspace_source"]=c.bound(c.KERNEL/"ann_workspace.py",long_workspace.WORKSPACE_SHA)
  report["inherited_run_unchanged"]=inherited.ANNWorkspace.run.__module__==inherited.__name__
  c.require(report["inherited_run_unchanged"] is True,"real inherited ANN run retained before model allocation")
  report["long_reference_protocol"]=long_independent_oracle.PROTOCOL
  report["long_reference_arithmetic_not_executed"]=True
  report["mean_configuration"]=False
  from common import COMMON
  report["common"]=COMMON;report["torch"]=torch.__version__;report["torch_npu"]=torch_npu.__version__
  report["common_identity_flag"]=flag()
  report["status"]="runtime-dependencies-checked"
 except BaseException as error:
  report.update(first_exception=repr(error),traceback=traceback.format_exc())
  c.write(Path(service_root)/"N1_DEPENDENCIES.json",report);raise
 return c.write(Path(service_root)/"N1_DEPENDENCIES.json",report)
def consume_n1(ref,source,files,identity,service_root):
 c.require(Path(ref["path"])==Path(service_root)/"N1_DEPENDENCIES.json","own actual N1 Ref, no old CPU substitute")
 x=c.obj(ref);ident=c.obj(identity)
 c.require(x["schema"]=="sparq.admitted-N1-runtime-dependencies/v1" and x["status"]=="runtime-dependencies-checked" and
  x["source"]==source and x["files"]==files and x["identity"]==identity and x["container_id"]==ident["container_id"] and
  x["container_id"] in x["process"]["cgroup"] and x["first_exception"] is None and
  x["installed_runtime_sources"]==c.RUNTIME_PINS and x["model_allocation_not_started"] is True and
  x["original_post_order"]==["original_run_model","original_POST_update"] and x["inherited_run_unchanged"] is True and
  x["long_reference_protocol"]=="sparq.long-native-per-request-FP32-SUM0/v1" and x["mean_configuration"] is False,
  "actual source/owned N1 hardware dependency closure before model construction; no fake HAL/arch")
 validate_worker_flag(x["common_identity_flag"]);return x
