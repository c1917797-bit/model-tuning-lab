"""MAIN-owned guest worker entry. OFF unless --execute; no Docker or host admission.
ON diagnostics still requires the genuine complete author v2/v8 original consumer result.
Formal/performance/tasks are hard OFF until full64-layer model authority exists.
"""
import argparse,json,os,sys
from pathlib import Path
import common,source_contract as c
PY="/usr/local/python3.12.13/bin/python3"
MODEL=dict(path="/cache/cch/qwen36-paper-preparation-20261007/sparse/actual-input-inventory-v1-001/MAIN-original-checkpoint-fullhash-20261008-001/ACTUAL_MODEL_MANIFEST.json",
 sha256="11ac18fa31878609b6b56a9c9213d12729cdb466d14c587efcf6d261566a706c")
def server_argv(port):
 c.require(type(port) is int and 1024<port<65536,"MAIN isolated port")
 return [PY,"-m","vllm.entrypoints.openai.api_server","--model","/models/Qwen3.6-27B",
  "--served-model-name","qwen36-sparq-tp4","--tensor-parallel-size","4","--data-parallel-size","1","--dtype","bfloat16",
  "--seed","0","--max-model-len","40960","--max-num-batched-tokens","40960","--max-num-seqs","16",
  "--no-enable-prefix-caching","--mamba-cache-mode","none","--no-enable-chunked-prefill","--no-async-scheduling",
  "--disable-log-stats","--kv-cache-memory-bytes",str(10*1024**3),
  "--compilation-config",json.dumps(common.COMPILATION,separators=(",",":")),
  "--additional-config",json.dumps(common.ADDITIONAL,separators=(",",":")),
  "--host","127.0.0.1","--port",str(port)]
def model_inventory():
 x=c.obj(MODEL);c.require(x.get("host_model_root")=="/cache/efim/Qwen3.6-27B" and
  x.get("complete_file_count")==29 and x.get("weight_shard_count")==15 and
  x.get("total_bytes")==55586107940 and x.get("config_sha256")=="69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c",
  "actual original checkpoint identity, no model switching")
 root=Path("/models/Qwen3.6-27B");seen=set()
 for row in x["files"]:
  name=row["relative_path"];p=Path(name)
  c.require(not p.is_absolute() and ".." not in p.parts and name not in seen,"unique relative actual model inventory")
  seen.add(name);file=root/p
  c.require(file.is_file() and not file.is_symlink() and file.stat().st_size==row["size_bytes"],"actual read-only mounted model inventory")
 # This small inventory check does NOT replace MAIN's full29-file hash gate.
 return dict(ref=MODEL,file_count=29,full_rehash_performed=False,full_host_hash_gate_required=True)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument("--execute",action="store_true");p.add_argument("--arm",choices=("dense","candidate"))
 p.add_argument("--mode",choices=("diagnostic","formal"),default="diagnostic")
 p.add_argument("--source-manifest-sha256");p.add_argument("--numeric-authority");p.add_argument("--numeric-authority-sha256")
 p.add_argument("--output",type=Path);p.add_argument("--port",type=int)
 p.add_argument("--identity");p.add_argument("--identity-sha256");p.add_argument("--diagnostic");p.add_argument("--diagnostic-sha256")
 a=p.parse_args()
 if not a.execute:
  print(json.dumps(dict(status="disabled",model_executed=False,npu_executed=False,ready=False)));return
 c.require(a.mode=="diagnostic" or (a.diagnostic and a.diagnostic_sha256),"formal1024/final2048 require actual full64-layer model gate")
 c.require(a.arm and a.numeric_authority and a.numeric_authority_sha256 and a.source_manifest_sha256 and a.output and a.port,
  "explicit source/numeric authority/new owned output/arm/port")
 source,files=c.source(str(c.ROOT/"SOURCE_MANIFEST.json"),a.source_manifest_sha256)
 authority=c.actual_component(a.numeric_authority,a.numeric_authority_sha256) # BEFORE Torch/server/import/bootstrap.
 identity=c.obj(c.bound(a.identity,a.identity_sha256))
 c.require(identity["schema"]=="sparq.tp4-arm-identity/v1" and identity["source"]==source and identity["component"]==dict(path=a.numeric_authority,sha256=a.numeric_authority_sha256) and
  identity["mode"]==a.mode and identity["arm"]==a.arm and identity["port"]==a.port and
  a.output==Path(a.identity).parent/"service","exact host identity/owned output/arm/mode/port")
 # Only exact final argv SHA position is expanded. No optional SHA or union.
 expected=[PY,"-B",str(c.ROOT/"full_entry.py"),"--execute","--source-manifest-sha256",a.source_manifest_sha256,
  "--numeric-authority",a.numeric_authority,"--numeric-authority-sha256",a.numeric_authority_sha256,
  "--identity",a.identity,"--identity-sha256",a.identity_sha256,"--mode",a.mode,"--arm",a.arm,"--port",str(a.port),"--output",str(a.output)]
 if a.diagnostic:expected+=["--diagnostic",a.diagnostic,"--diagnostic-sha256",a.diagnostic_sha256]
 template=list(identity["image_argv_template"]);slot=template.index("--identity-sha256")+1
 c.require(template[slot]=="@ACTUAL_IDENTITY_SHA256@","only exact self-hash argv sentinel")
 template[slot]=a.identity_sha256;c.require(template==expected==[sys.executable,"-B",*sys.argv],"actual complete guest entry argv")
 diagnostic=None
 if a.mode=="formal":
  from consume_model import consume_authority
  diagnostic=consume_authority(c.bound(a.diagnostic,a.diagnostic_sha256),source,
   dict(path=a.numeric_authority,sha256=a.numeric_authority_sha256),replay=True)
 inventory=model_inventory();common.validate(common.COMMON,a.arm)
 root=a.output;c.require(root.is_absolute() and root.resolve()==root and Path("/cache/cch") in root.parents and
  not root.exists(),"new exact MAIN-owned writable guest output")
 root.mkdir();trace=root/"trace";trace.mkdir();(root/"identity").mkdir()
 from identity_bridge import n1_dependency_gate
 identity_ref=dict(path=a.identity,sha256=a.identity_sha256)
 n1=n1_dependency_gate(source,files,identity_ref,root) # Admitted N1 BEFORE model allocation.
 command=server_argv(a.port)
 from service_contract import DIAGNOSTIC_PROTOCOL,PROTOCOL
 env=dict(os.environ);oldpath=env.get("PYTHONPATH","")
 if diagnostic:
  env.update(QWEN36_SPARQ_FULL_MODEL_AUTHORITY=a.diagnostic,QWEN36_SPARQ_FULL_MODEL_AUTHORITY_SHA=a.diagnostic_sha256)
 env.update(QWEN36_SPARQ_STOCK_FULL_ENABLED="1",QWEN36_SPARQ_MODEL_ARM=a.arm,QWEN36_SPARQ_MODEL_MODE=a.mode,
  QWEN36_SPARQ_STOCK_FULL_SOURCE=source["path"],QWEN36_SPARQ_STOCK_FULL_SOURCE_SHA=source["sha256"],
  QWEN36_SPARQ_NUMERIC_AUTHORITY=a.numeric_authority,QWEN36_SPARQ_NUMERIC_AUTHORITY_SHA=a.numeric_authority_sha256,
  QWEN36_SPARQ_MODEL_TRACE_ROOT=str(trace),QWEN36_SPARQ_MODEL_SERVICE_ROOT=str(root),VLLM_WORKER_MULTIPROC_METHOD="spawn",
  PYTHONDONTWRITEBYTECODE="1",TORCH_DEVICE_BACKEND_AUTOLOAD="0",
  PYTHONPATH=str(c.ROOT)+":"+str(c.KERNEL)+(":"+oldpath if oldpath else ""))
 c.write(root/"ARM.json",dict(schema="sparq.author-ann-stock-full-arm/v1",execution_clock=c.execution_clock(),source=source,source_files=files,
  numeric_authority=dict(path=a.numeric_authority,sha256=a.numeric_authority_sha256),common=common.COMMON,
  arm=a.arm,mode=a.mode,command=command,pid=os.getpid(),model=inventory,port=a.port,identity=dict(path=a.identity,sha256=a.identity_sha256),
  protocol=DIAGNOSTIC_PROTOCOL if a.mode=="diagnostic" else PROTOCOL,refs=dict(source=source,component=dict(path=a.numeric_authority,sha256=a.numeric_authority_sha256),**{"model-manifest":MODEL}),
  author_algorithm=dict(protocol=c.AUTHOR_PROTOCOL,reallocate_to_mean_value=False,meanON_not_supported_by_service=True),
  observation_graph=a.mode=="diagnostic",formal_enabled=a.mode=="formal",host_resource_admission_not_provided_by_entry=True,
  full64_layer_numeric_verified=False,device_dependency=n1,ready=False))
 os.execve(PY,command,env) # Only MAIN's separately admitted physical4-7 TP4 guest may call ON.
if __name__=="__main__":main()
