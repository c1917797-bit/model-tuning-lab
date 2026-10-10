"""Materialize the exact runtime source closure in an already deployed fresh source leaf.
No Docker, remote command, model import, device lease or source rewrite.
The mixed adapter is concrete; actual firstdecode consumer refs remain external.
"""
import argparse,hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
CORE_MF_SHA="75bc370029ad75e3302109d2124fe7e05c40e042a084b797f29634b060c8fca7"
BASE_MF_SHA="a5726b3ec27178f574962b02a745ffe20060ebd42bf2de3d4cffc0161df5a7e4"
CONFIG_ARCHIVES=[
 dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-model-firstdecode-bootstrap-v1-007/safety_host.py",
  bytes=21529,sha256="0c35d88c4ebe3bf98fde9c3f7f95d8658a7f4c1e577688afa7b0127974426a16"),
 dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/source-engine-config-660-20261010-001/scheduler.py",
  bytes=13052,sha256="36bdfcf50a8f30d9f1c0dbdd3630a0075234f5c9e1a77943a934c45329f25c86"),
 dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/source-engine-config-660-20261010-001/model.py",
  bytes=91921,sha256="cf5aeb9e16d6cac82426cf7e8d140741b35c503ae8b9e1fc9ba3dde53c585a62"),
 dict(path="/cache/cch/qwen36-paper-preparation-20261007/lowbit/source-engine-config-660-20261010-001/vllm.py",
  bytes=99611,sha256="ba062ec38d075937b73d953059cf1d0e1b96f1474990bc6d45ed45e20ba6a336")]
RUNTIME_ABI_ARCHIVES={"numeric":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-packed-three-kernel-numeric-v3-signed-20261010-001/numeric.py","bytes":19612,"sha256":"7853f967eb44f32da3de785111adcb23ff01fc7cbe95e50dfb78a2c6ff18979a"},"numeric_manifest":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-packed-three-kernel-numeric-v3-signed-20261010-001/SOURCE_MANIFEST.json","bytes":16678,"sha256":"d6a151a13bd3b665eab14f25f5c1c45b1b6ab3b3b470014305977132d7643914"},"helper":{"path":"/cache/cch/qwen36-paper-preparation-20261007/MAIN-deployed-api-source-660-20261010-001/triton_utils.py","bytes":2090,"sha256":"f94d81f163f0076e8243990dd687f7ec8d42ce1ed30d67eea3155bf1c3a073a4"}}
CORE_NAMES={"installer":"installer.py","book":"book.py","bindings":"bindings.py","worker":"worker.py","capture_schedule":"capture_schedule.py","stage_observer":"stage_observer.py","phase_sequence":"phase_sequence.py","mixed":"mixed.py","capture_receipt":"capture_receipt.py","resource_ledger":"resource_ledger.py","client_stage":"client_stage.py","input_plan":"input_plan.py","transport":"transport.py","stage_consumer":"consume_stage.py","original_writer":"consume_original_writer.py","stage_lifecycle":"consume_stage_lifecycle.py","matrix_consumer":"consume_matrix.py","offline_consume":"offline_consume.py","release_replay":"release_replay.py"}
CORE_PINS={"installer":"150b149762ce1b2cf43f29b13595ee66c7012382f180de9dce8463cb5a5b0ef9","book":"c0882fa2868fa0b7e784bd031da3053d75a210362f4c955a5c93a0158fc63fa9","bindings":"a72c8ea47f6f04f661a9b8e6c159e02eb7f743aa3fe94a27c212e7a6cd7e8761","worker":"bfd9cd5ef70be0bf6df07079aff25f6465aff24ee9359f20e434fff62552b943","capture_schedule":"9b6ad7d3eaad36a7c9efd7ea06b14dd58f048e6b20746f13da805b5f03e6a470","stage_observer":"89529921e404060e302b7c227fdf2a58dfffec83b444871e66fed464adc58d74","phase_sequence":"9b629cc2f46ec4b0592f9eab4a5f63b39c6a0c48e26a4634da118bc4879c3125","mixed":"8e55b113337e8881b96634cc7ef2304b46374b1f39fe048d682ddf0b2ad16ce6","capture_receipt":"8f5291975eee99fa286a58dd06162bbc3ed90f07381931f05b667d1e717c9511","resource_ledger":"7463d84a80d621c56b13710ee73955f4c974484becb84592d9f1624e0a3356e4","client_stage":"8f1af84b6388b353f7cb331856c3558ec23e2c7d074d2aad598e673f7ff5e67b","input_plan":"30024f8a182c1b3295f942c5e1d28582599a3d5ffc9a713aeda4459c2761a550","transport":"ba53f2774a5b43c257c4a6b9db9e56c37ebc44619d8ee55c0d599cb15b89580e","stage_consumer":"d3f6a9089287521fdb01a4114f814391cfbfc4f25500a103dad0599502aa7da4","original_writer":"af94eb7f88b643234b2562e4707e9d2e8fd476c851ecf882334c5cce64387c68","stage_lifecycle":"def3ba9590673f1559c5bfbbc19191716197742c61d24e0f8b1b8c57c8c322a0","matrix_consumer":"734fcd8e512c124a605716cdb13760e7dfdf08eb17af3af0dc93b5128ef1e68a","offline_consume":"b8bce06887d1a70f2cc5947ee048a3dae4be31cca111888e2f80bc3a60358f75","release_replay":"bacb98cb15e6cc8b4542e9153d2124a3cb73045735c44485970074b969485f37"}
SUCCESSOR_NAMES={"stage_observer":"stage_observer.py","installer":"installer.py","client_stage":"client_stage.py","capture_receipt":"capture_receipt.py","worker":"worker.py","resource_ledger":"resource_ledger.py","original_writer":"consume_original_writer.py","offline_consume":"offline_consume.py"}
SUCCESSOR_PINS={"stage_observer":"cd957ae3b6e2303a0890e00dd3be178e473a1488636d4cb141f15c6649d5189b","installer":"536131653087de8f2daab16a65c3d5ce863e4ff7d74a8cf0eabb03aec620cedc","client_stage":"3d570bd09afce0b4218e13d4f4ea788fcb9f1f98adce5deda7a62984ce7f6796","capture_receipt":"7048bfa09c5a8dcc156da3edf8fd9ace954cc10ebee7ff9ffa15ed74b128918d","worker":"51f9934e88f2b868fe32effd541e19cf65edaa882dad5f49900bc6120ba6dbd1","resource_ledger":"3776c130d9d5b4efdad35c64a2fe289d24fcdf87940288d08f9eaa5327c95dbc","original_writer":"26d680f232f8cd5a0afde9b21ccb64f4955428052352c93901a80f4bfc2150da","offline_consume":"a37b704c209bc97c9ac5631d4b402fc14eebf51ab79f3845d5627931ce6a7e17"}
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.resolve()==p and p.is_file()and not p.is_symlink(),"actual ordinary source")
 b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={"path","bytes","sha256"}and ref(r["path"])==r,"exact full3Ref")
 return r
def obj(r):checked(r);return json.loads(Path(r["path"]).read_bytes())
def build(prepared,base_ref,core_ref,core_root,external):
 p=obj(prepared);base=obj(base_ref);cm=obj(core_ref)
 need(base_ref["sha256"]==BASE_MF_SHA and core_ref["sha256"]==CORE_MF_SHA,"immutable reviewed ancestors; old failures retained")
 need(p["schema"]=="kivi.local-mixed-host-preparation/v1","exact frozen own preparation")
 files=[]
 for name,row in p["files"].items():
  r=ref(BASE/name);need(r["bytes"]==row["bytes"]and r["sha256"]==row["sha256"],"deployed own exact bytes "+name)
  files.append(r)
 roles=dict(base["runtime_roles"])
 dependencies=[base_ref,core_ref,prepared]+base["files"]+base["dependencies"]+CONFIG_ARCHIVES+list(RUNTIME_ABI_ARCHIVES.values())
 for role,name in CORE_NAMES.items():
  r=ref(Path(core_root)/name)
  old=next(q for q in cm["files"]if q["name"]==name)
  need(r["sha256"]==CORE_PINS[role]==old["sha256"]and r["bytes"]==old["bytes"],"frozen mixed002 exact runtime "+role)
  roles[role]=r;dependencies.append(r)
 own={Path(r["path"]).name:r for r in files}
 # Original mixed002 stays immutable; select explicit-budget provider and declared wire successors only.
 for role,name in SUCCESSOR_NAMES.items():
  need(own[name]["sha256"]==SUCCESSOR_PINS[role],"exact publication successor "+role)
  roles[role]=own[name]
 for role,name in {"output_scanner":"output_budget.py","peer_inspector":"peer_inspector.py",
  "input_lifecycle":"input_lifecycle.py","matched_prompts":"matched_prompts.py","release_core":"release_core.py",
  "native_config_adapter":"native_config_adapter.py","native_config_proof":"native_config_v008.py",
  "whole_cpu_consumer":"consume_whole_cpu.py","geometry":"explicit_geometry.py","explicit_geometry":"explicit_geometry.py",
  "explicit_provider":"explicit_provider.py"}.items():
  roles[role]=own[name]
 roles["geometry_helper"]=roles["writer_reader"]
 need(set(external)=={"firstdecode_consumer","firstdecode_producer_ref","firstdecode_raw_source","firstdecode_whole_source",
  "transitive_source_refs"},"only explicit configuration/predecessor sources; not unknown embedded pins")
 for name in("firstdecode_consumer",):
  roles[name]=checked(external[name])
 dependencies.extend(external["transitive_source_refs"])
 dependencies.extend([external["firstdecode_consumer"],external["firstdecode_producer_ref"],external["firstdecode_raw_source"],external["firstdecode_whole_source"]])
 # External source closure is inspected and compiled, including its precise
 # original core/official config dependencies. No authority from a supplied flag.
 unique={r["path"]:r for r in files}
 for r in dependencies:
  checked(r)
  need(r["path"]not in unique or unique[r["path"]]==r,"conflicting byte identity")
  unique[r["path"]]=r
 for r in roles.values():need(unique.get(r["path"])==r,"role missing mounted source "+r["path"])
 for r in unique.values():
  if r["path"].endswith(".py"):compile(Path(r["path"]).read_bytes(),r["path"],"exec")
 out=dict(base)
 out.update(schema="kivi.actual-mixed-capture-bootstrap-sources/v2",root=str(BASE),files=files,
  dependencies=[r for r in unique.values()if r not in files],runtime_roles=roles,
  portfolio_cutoff_epoch=1791788425,firstdecode_producer_ref=external["firstdecode_producer_ref"],
  firstdecode_raw_source=external["firstdecode_raw_source"],firstdecode_whole_source=external["firstdecode_whole_source"],
  prepared_packet_ref=prepared,reviewed_firstdecode_v018_ref=base_ref,frozen_mixed002_ref=core_ref,
  software_tests_declared=p["software_tests_declared"],default_enabled=False,
  runtime_abi_original_refs=RUNTIME_ABI_ARCHIVES,
  source_count=len(unique),own_file_count=len(files),dependency_count=len(unique)-len(files),
  budgets=dict(capture_seconds=5400,cpu_seconds=43200,cleanup_each_seconds=90,guest_NPU_bytes=64*1024**3,
   guest_CPU_bytes=8*1024**3,host_bytes=512*1024**2,workspace_bytes=160*1024**3,
   disk_reserve_bytes=int(8.5*1024**3),full_budget_fit_unmeasured=True),
  scope=dict(eager=True,total_cache_bytes=6*1024**3,max_num_seqs=16,HTTP_concurrency=16,
   fixed32768_input_only=True,preemption_supported=False,final40_request_performance_checked=False,stages=16,requests=64,FA_pairs=64,raw_frames=320,whole_output_rows=576,
   mixed=True,full_graph=False,GDN_content_numerically_checked=False,matched_performance=False),
  states=dict(source="PREPARED",same_image="UNRUN",firstdecode_actual="REQUIRED_EXTERNAL",
   mixed_capture="UNRUN",offline_CPU="UNRUN",whole_terminals="UNRUN"),
  model_ready=False,performance_ready=False,run_authority=False,whole_176=False)
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
 for n in("prepared","base","core","external"):
  p.add_argument("--"+n);p.add_argument("--"+n+"-sha256")
 p.add_argument("--core-root");a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,run_authority=False)));return
 refs={}
 for n in("prepared","base","core","external"):
  refs[n]=ref(getattr(a,n));need(refs[n]["sha256"]==getattr(a,n+"_sha256"),"exact input "+n)
 out=build(refs["prepared"],refs["base"],refs["core"],a.core_root,obj(refs["external"]))
 path=BASE/"SOURCE_MANIFEST.json";need(not path.exists(),"new source identity; never overwrite old MF")
 import os
 with path.open("xb")as f:
  data=(json.dumps(out,sort_keys=True,indent=2)+"\n").encode()
  need(f.write(data)==len(data),"whole manifest");f.flush();os.fsync(f.fileno())
 print(json.dumps(ref(path)),flush=True)
if __name__=="__main__":main()
