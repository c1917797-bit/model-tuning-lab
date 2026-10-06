"""CPU-only split runner contracts; no source-lock or NPU PASS is issued."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path

IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
LIBRARY_SHA="0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b"
BUILD_SHA="25db2cee4f6e6020e476b2c92e15fa8321655bd22e371e35c4d27b0db16dd0d4"
META_SHA="2765f4bbcbf1d935e260b4d6cfa3b5401257aaf125fca0ae4c149193566dc727"
CGROUP_BYTES=8*1024**3
BATCH_DEVICE={1:5,16:6}
REPO_PINS={
 "tools/native_oracle_probe.py": "caa65dd94506edbd68a5600e9f813d93711ba162a8a2fc0565e7e00ede4414dd",
 "plugin/kvbuffer_parallel/contract.py": "db673ba157e951c7e93031a215a32d17e6a0def5fdc3a5c601030f867b8b7e38",
 "plugin/kvbuffer_parallel/patch.py": "71be0c99af19d66bc5f44ebb983b748cd56e2e776d567b0b4df0789ca0d89e2d",
 "operator/CMakeLists.txt": "a46e98794744a2fe76c62d77d0cbf7936f8f87a0f7ff01db5c03e7337def064c",
 "operator/op_extension/ops.h": "d5e0e1ccb511e107a9d1421eed1430af8735b95ed67809f41d84eafd8522930f",
 "operator/op_extension/qwen36_gdn_kvbuffer_parallel_torch.cpp": "13aba192a2fb7d869c2b4f065a31b26e584e123a110001476c326699b837553e",
 "operator/op_extension/register.cpp": "78cf3f62b312ca230d2a0cee199dce845bf5879608a5bb6d7ea0d66d48275481",
 "operator/op_kernel/qwen36_gdn_kvbuffer_parallel.h": "8fde339a17c32d853de9d05bdfb69dd2e6ab4e023f1de8c3dc7abc9c7e153674",
 "operator/op_kernel/qwen36_gdn_kvbuffer_parallel_kernel.asc": "b18b4ba12de7334f80616353511983963f30438ecf4d190c3e89e0eaee13f610",
 "operator/op_kernel/qwen36_gdn_kvbuffer_parallel_tiling.h": "db531136e309b4d886e7a728f0cb177ffd505a8a71b724be8fc87fc1e83337fd"
}
NATIVE_PINS={
 "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py":"d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
 "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py":"21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3",
 "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py":"885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py":"94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"}
def require(ok,reason):
 if not ok:raise ValueError(reason)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def protocol(batch,physical):
 require(type(batch) is int and type(physical) is int and BATCH_DEVICE.get(batch)==physical,
  "only physical5 B1 or physical6 B16")
 return dict(batch=batch,physical_device=physical,logical_device=0,slots=batch+3,
  eager_trials=1,graph_trials=3,steps_per_case=160,feedback=True,
  output_limit=.00303,complete_and_per_head_l2_limit=2e-6,
  graph_active_schedule=[0,1,3,7,12,15,16,16] if batch==16 else [1],
  reset_steps=[64,112],required_flushes=True,retry="none",scope="kernel-only-not-model-E2E-or-task-accuracy")
def validate_identity(obj,batch,physical,driver_sources):
 p=protocol(batch,physical)
 require(obj.get("schema")=="kvbp.split-launch-identity/v1" and obj.get("image_id")==IMAGE,"MAIN identity/image")
 require(obj.get("physical_devices")==[physical] and obj.get("logical_to_physical")=={"0":physical} and
  obj.get("fresh_idle_verified") is True and obj.get("nonprivileged") is True and
  obj.get("source_canary_passed") is True,"fresh single-device/mapping/canary")
 require(obj.get("memory_cgroup_bytes")==CGROUP_BYTES and obj.get("protocol")==p,"8GiB cgroup/protocol")
 require(obj.get("library_sha256")==LIBRARY_SHA and obj.get("build_receipt_sha256")==BUILD_SHA and
  obj.get("meta_receipt_sha256")==META_SHA and obj.get("repo_sources")==REPO_PINS and
  obj.get("native_sources")==NATIVE_PINS and obj.get("driver_sources")==driver_sources,"complete immutable sources")
 require(type(obj.get("evidence")) is dict and obj["evidence"],"MAIN independent evidence refs")
 now=datetime.now(timezone.utc);t=datetime.fromisoformat(obj["preflight_utc"].replace("Z","+00:00"))
 require(t.tzinfo is not None and 0<=(now-t).total_seconds()<=600,"stale/invalid preflight")
 return p
def cgroup_limit():
 for path in (Path("/sys/fs/cgroup/memory.max"),Path("/sys/fs/cgroup/memory/memory.limit_in_bytes")):
  if path.is_file():
   text=path.read_text().strip()
   require(text.isdigit() and int(text)==CGROUP_BYTES,"actual cgroup memory is not8GiB")
   return dict(path=str(path),bytes=int(text))
 raise ValueError("actual container cgroup memory limit unavailable")
def receipts(build,meta,library,project):
 require(sha(build)==BUILD_SHA and sha(meta)==META_SHA and sha(library)==LIBRARY_SHA,"existing receipt/artifact drift")
 b=json.loads(Path(build).read_text());m=json.loads(Path(meta).read_text())
 expected={k.removeprefix("operator/"):v for k,v in REPO_PINS.items() if k.startswith("operator/")}
 require(b["sources"]==expected and b["status"]=="compiled_no_device" and b["npu_executed"] is False and
  b["image_id"]==IMAGE and b["library_sha256"]==LIBRARY_SHA and all(c["exit_code"]==0 for c in b["commands"]),
  "actual compiler receipt binding")
 require(m["status"]=="pass" and m["npu_executed"] is False and m["build_receipt_sha256"]==BUILD_SHA and
  m["library_sha256"]==LIBRARY_SHA and [v["T"] for v in m["meta"]]==[1,16],"actual load/Meta receipt")
 actual={n:sha(Path(project)/n) for n in REPO_PINS};require(actual==REPO_PINS,"frozen gate/operator/plugin drift")
 return dict(build_receipt_sha256=BUILD_SHA,meta_receipt_sha256=META_SHA,library_sha256=LIBRARY_SHA,
  repo_sources=actual,meta_is_not_npu_proof=True)
