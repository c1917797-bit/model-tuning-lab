"""Strict source/actual complete-kernel authority. No Torch/Docker launch."""
from __future__ import annotations
import ast,hashlib,importlib.util,json,os,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
KERNEL=Path("/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6")
KERNEL_SHA="eb7ed908879c6bdea7fab670bcf83e570a7439045e2d8e5c4535c6a41611f528"
PINS={
 "/cache/cch/flashinfer-native-abi-v1-20261007-1716-001/source_snapshots/attention_v1.py": "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390",
 "/cache/cch/flashinfer-native-abi-v1-20261007-1716-001/source_snapshots/model_runner_v1.py": "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-aclgraph-input-source-v1-001/acl_graph.py": "27f3b838f223dec86113649625f65b158969a30ce0265271d6a3ce1403db2491",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-graph-and-engine-source-v1-001/torch_npu_graphs.py": "eb11cac181087766e8489cf3a1da0c0fa150933b7e74454dba4a47db6114164e",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-graph-and-engine-source-v1-001/torch_npu_streams.py": "241741b356db5006797dbec119007afb33b73b0e1753bfb06ab27c989c5bfac4",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-graph-and-engine-source-v1-001/torch_npu_init.py": "355df777433fd8c85670db75d8aacf7fa076332092470d59b6ba26202ed7fd2f",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-graph-and-engine-source-v1-001/llm_engine.py": "2900f6732a1e507f6ced6f75f05f1fcaf2cc2929df0f5066574e9077ad3fbde1",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-graph-and-engine-source-v1-001/arg_utils.py": "3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d",
 "/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/SOURCE_MANIFEST.json": "eb7ed908879c6bdea7fab670bcf83e570a7439045e2d8e5c4535c6a41611f528",
 "/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/sparq_token_v4/core.py": "c5ef88f12828597469f7f3ce32a78ca4b4bb31d66c38beba102420d11bb21393",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-framework-source-v2-001/ascend_attention_utils.py": "6a8c083d632cb745fb57b4bda522c44a2b967f44170be22aa0bc478145ba6dee",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-framework-source-v2-001/vllm_config_init.py": "3aec3c595391b38c5a46ab895c8f7d4041136be3bdf5eb8d0ae25b484d244875",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-framework-source-v2-001/gpu_model_runner.py": "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-dispatch-cache-source-v3-001/compilation.py": "301f785491044b4428aec617b8a98161ab7ffc424fc2bfb0f2ab26bed6ee6913",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-dispatch-cache-source-v3-001/cudagraph_dispatcher.py": "2ac6454dd72c9f54d159b5a2da0fdd60a4f841970eb32dbf54129e3c6a8d0bfd",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/sp4-public-bootstrap-source-v1-001/ascend_config.py": "8da61f88d8e5153fde5311ddc8de11cd8a361deb5f2efed5140640a5eeeb7c38",
 "/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_token_native_v6/model_bridge.py": "74400ac82b9f28ce4cbed21faf00f2201307eb43c31b76f8a2851e1eb97bffb9",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-graph-and-engine-source-v1-001/COPY_SOURCE_IDENTITY.json": "801da2ba3abbc67b43bc840ac58fbbef08677ab5671f18c8e3a89da80de1f9b8",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-aclgraph-input-source-v1-001/COPY_SOURCE_IDENTITY.json": "d3cefa47634e87bed353b8a9e41f9c5c5c2a6f7be4801ad56ae9ee5ecf2c260d",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-framework-source-v2-001/COPY_SOURCE_IDENTITY.json": "1cd0b12325a0ce8199eea6da5f1bc56d87031107bbdc0ae05afda57f882f3f75",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-dispatch-cache-source-v3-001/COPY_SOURCE_IDENTITY.json": "3bbf0e47d0de640720971138286d03ba5cd2e97fadd9755a1cef6add71aaed39",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/sp4-public-bootstrap-source-v1-001/COPY_SOURCE_IDENTITY.json": "ed0f5416245e30b3ab29dc0276680e4ecd1380de90f6125238a736500fe9d52e",
 "/cache/cch/qwen36-paper-preparation-20261007/sparse/actual-input-inventory-v1-001/MAIN-original-checkpoint-fullhash-20261008-001/ACTUAL_MODEL_MANIFEST.json": "11ac18fa31878609b6b56a9c9213d12729cdb466d14c587efcf6d261566a706c"
}
PINS.update({"/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/MANIFEST.json":"2287ff93333612616c3f552e9137693c4995ea27d206f82dac5a45009bf6c502","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/gdn.py":"d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/patch_qwen3_5.py":"21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/qwen_gdn_linear_attn.py":"885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/mamba_utils.py":"1d854c36fe1b32cfacd071393c05fc155f37190fe19afc5e6c02d5d0a2d561f3","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/mamba_abstract.py":"d7cba061c9d8c55b00e18bc7af515cfd28d875eee76c04fea7f6861f2d1c4e08","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-gdn-and-torchnpu-660-20261008-0854-002/gdn_attn_builder.py":"42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16"})
PINS.update({"/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-660-20261008-0937-001/api_server.py":"6d8df133280618a1afffa9d03e4655af011f2f94ced0f90c15f7fc8b0afc538f","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-generate-660-20261008-0942-001/api_router.py":"eed72cdc15a84b31e1e345133b217ded05d3f9e4ba15562af16a95b9bc7cbaa3","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-completion-660-20261008-0949-001/api_router.py":"9347872bbdd3f2488b35a9db59bdb85e4dd990a6559a2615145e8a1e5dd3239a","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-completion-660-20261008-0949-001/serving.py":"c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-protocol-660-20261008-1003-001/completion_protocol.py":"93c720549f2a9ef217d7c2a60710225c862032517520dd9ba693d4820f55365c","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-protocol-660-20261008-1003-001/engine_protocol.py":"2ca4ccb38beaff09bf3b31e8990ca036bd008b9e5caacbc20889b8f4d7dc2529","/cache/cch/qwen36-paper-preparation-20261007/sparse/source-openai-protocol-660-20261008-1003-001/engine_serving.py":"38b242a091b2b4502a58b7d9b8a274ac17611b383fecc30e9b714f5da9c8dc75"})
MODEL_GDN_PROTOCOL="sparq.GDN-all-row-live-byte-finite/v2"
AUTHOR_PROTOCOL="sparq.author-ann-original-dtype-selector/v4-FP32-compensation-fixed-capacity-per-request-SUM"
AUTHOR_PRIVATE=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-author-ann-native-v2-001")
PINS.update({"/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-author-ann-fp32-full-v3-current-pin-compat-v1-001/ACTUAL_CANONICAL_SOURCE_MANIFEST.json":"ba5086984dd058ecf2c0ce0b63b4756d635c86de750478c5e70c153ab4ae4b78","/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-author-ann-stock-full-v2-001/SOURCE_MANIFEST.json":"d98d15c3be1ac14e9205de47107ed24cd55a8bab1a3b7f6956f54b1d32b2fc98"})
PINS.update({
 str(AUTHOR_PRIVATE/"SOURCE_MANIFEST.json"):"1c7a710ab3fb9b625508c83bc3b1183f6e45cee44e63533266e6ad542557563d"})
PINS.update({"/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-official-ann-source-20261008-1040-001/ann_attention.py":"2b07afe06ff1dd6627f1a255be585c82a632f7bbdb7bf606f4ff2f8b260b6b74","/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-official-causal-source-20261008-1045-001/sparse_attention.py":"dc24fa18ca67b58dc0b28e8a18deb4728c7d7fdac020a61dd1238d24b5c0e4b1","/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-official-ann-source-20261008-1040-001/SOURCE_RESULT.json":"347852be4a9ef13bb928bc3882ab04d12c5ac7cd78587ee084f4d8f04e17e331","/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq-official-causal-source-20261008-1045-001/SOURCE_RESULT.json":"512ef331444a9cc561861edc08c7b9c169c8085d7369a223798e31651b14af27"})
PINS.update({"/cache/cch/qwen36-paper-preparation-20261007/MAIN-native-input-config-source-660-20261009-001/npu_input_batch.py":"a4dc08a9918f07797622f8d0915785e8c7b6899e0d10d92603e1dddec218acc3","/cache/cch/qwen36-paper-preparation-20261007/recurrent/h8-model-tp4-v2-cpu-ledger/source_blobs/ascend_block_table.py":"8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a"})
RUNTIME_PINS={
 "/vllm-workspace/vllm/vllm/engine/arg_utils.py": "3ade2488897d08b5c1fd4ddb815eb5743169907d59741a47867185caab7f250d",
 "/vllm-workspace/vllm/vllm/v1/engine/llm_engine.py": "2900f6732a1e507f6ced6f75f05f1fcaf2cc2929df0f5066574e9077ad3fbde1",
 "/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/npu/graphs.py": "eb11cac181087766e8489cf3a1da0c0fa150933b7e74454dba4a47db6114164e",
 "/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/npu/__init__.py": "355df777433fd8c85670db75d8aacf7fa076332092470d59b6ba26202ed7fd2f",
 "/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/npu/streams.py": "241741b356db5006797dbec119007afb33b73b0e1753bfb06ab27c989c5bfac4",
 "/vllm-workspace/vllm-ascend/vllm_ascend/compilation/acl_graph.py": "27f3b838f223dec86113649625f65b158969a30ce0265271d6a3ce1403db2491",
 "/vllm-workspace/vllm-ascend/vllm_ascend/attention/utils.py": "6a8c083d632cb745fb57b4bda522c44a2b967f44170be22aa0bc478145ba6dee",
 "/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py": "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
 "/vllm-workspace/vllm/vllm/config/__init__.py": "3aec3c595391b38c5a46ab895c8f7d4041136be3bdf5eb8d0ae25b484d244875",
 "/vllm-workspace/vllm/vllm/config/compilation.py": "301f785491044b4428aec617b8a98161ab7ffc424fc2bfb0f2ab26bed6ee6913",
 "/vllm-workspace/vllm/vllm/v1/cudagraph_dispatcher.py": "2ac6454dd72c9f54d159b5a2da0fdd60a4f841970eb32dbf54129e3c6a8d0bfd",
 "/vllm-workspace/vllm-ascend/vllm_ascend/ascend_config.py": "8da61f88d8e5153fde5311ddc8de11cd8a361deb5f2efed5140640a5eeeb7c38",
 "/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py": "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py": "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
}
RUNTIME_PINS.update({"/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py":"d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816","/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py":"21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3","/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py":"885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0","/vllm-workspace/vllm/vllm/v1/worker/mamba_utils.py":"1d854c36fe1b32cfacd071393c05fc155f37190fe19afc5e6c02d5d0a2d561f3","/vllm-workspace/vllm/vllm/model_executor/layers/mamba/abstract.py":"d7cba061c9d8c55b00e18bc7af515cfd28d875eee76c04fea7f6861f2d1c4e08","/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py":"42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16"})
RUNTIME_PINS.update({"/vllm-workspace/vllm/vllm/entrypoints/openai/api_server.py":"6d8df133280618a1afffa9d03e4655af011f2f94ced0f90c15f7fc8b0afc538f","/vllm-workspace/vllm/vllm/entrypoints/generate/api_router.py":"eed72cdc15a84b31e1e345133b217ded05d3f9e4ba15562af16a95b9bc7cbaa3","/vllm-workspace/vllm/vllm/entrypoints/openai/completion/api_router.py":"9347872bbdd3f2488b35a9db59bdb85e4dd990a6559a2615145e8a1e5dd3239a","/vllm-workspace/vllm/vllm/entrypoints/openai/completion/serving.py":"c67bff55fa29c5f89000c3afdc9c7c66305612b13a8a1d85976e5872cee086d7","/vllm-workspace/vllm/vllm/entrypoints/openai/completion/protocol.py":"93c720549f2a9ef217d7c2a60710225c862032517520dd9ba693d4820f55365c","/vllm-workspace/vllm/vllm/entrypoints/openai/engine/protocol.py":"2ca4ccb38beaff09bf3b31e8990ca036bd008b9e5caacbc20889b8f4d7dc2529","/vllm-workspace/vllm/vllm/entrypoints/openai/engine/serving.py":"38b242a091b2b4502a58b7d9b8a274ac17611b383fecc30e9b714f5da9c8dc75"})
RUNTIME_PINS.update({"/vllm-workspace/vllm-ascend/vllm_ascend/worker/npu_input_batch.py":"a4dc08a9918f07797622f8d0915785e8c7b6899e0d10d92603e1dddec218acc3","/vllm-workspace/vllm-ascend/vllm_ascend/worker/block_table.py":"8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a"})
HOST_DEPENDENCIES={"/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/full_matrix_host_v2/host.py":"ab0296c698df00c9c3b2ce377601f6d6723adde6efb4a9e65407beca51ba5f86","/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/saved_step_native_order_v2/host_run.py":"86c1ca7f59c6ad5b2b4d5efb155394455a12376cf368e06f9e2e13d39b7192fc","/opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/short_horizon_h8_gate_v4/host_run.py":"4ddd75d6ce7558f0131992da3a5514df43dfb4b33f45674722ba5769ecef5e20"}
OWN=["bridge.py","common.py","lifecycle.py","workspace_budget.py","source_contract.py","full_graph_pa.py","original_terminal.py","sitecustomize.py","test_bridge.py","source_gate.py","actual_replay.py","full_entry.py","consume_full.py","task_contract.py","test_replay.py","TASK_EVIDENCE.json","fa_numeric.py","model_matrix.py","evidence.py","gdn_state.py","test_gdn_state.py","service_contract.py","bench.py","host_run.py","gdn_metadata.py","gdn_observer.py","gdn_source.py","test_gdn_metadata.py","fa_model_numeric.py","full_cpu_preflight.py","gdn_model_observer.py","allocator_coverage.py","consume_model.py","model_cpu_check.py","model_workload.py","test_model_workload.py","formal_stats.py","test_formal_stats.py","wire.py","consume_service.py","test_wire.py","allocation_contract.py","long_workspace.py","no_pa_full.py","test_allocation.py","test_no_pa.py","ann_snapshot.py","ann_model_state.py","ann_model_oracle.py","ann_fa_consumer.py","test_ann_aggregate.py","entry.py","component_handoff.py","test_component_handoff.py","test_fp32_model_adapter.py","long_independent_oracle.py","gdn_stream.py"]
def require(v,m):
 if not v:raise ValueError(m)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def sha(path):
 p=Path(path);require(p.is_absolute() and p.is_file() and not p.is_symlink(),"exact ordinary source/evidence")
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()
def bound(path,digest):
 p=Path(path);require(p.is_absolute() and ".." not in p.parts and re.fullmatch("[a-f0-9]{64}",digest or "") and sha(p)==digest,"exact immutable SHA Ref")
 return dict(path=str(p),sha256=digest)
def obj(r):bound(r["path"],r["sha256"]);return json.loads(Path(r["path"]).read_bytes())
def module(path,digest,name):
 bound(path,digest);s=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(s)
 previous=sys.modules.get(name);sys.modules[name]=m
 try:s.loader.exec_module(m)
 except BaseException:
  if previous is None:sys.modules.pop(name,None)
  else:sys.modules[name]=previous
  raise
 return m
def write(path,value):
 # Publish only complete immutable bytes. Never replace final; retain failed tmp.
 import secrets
 data=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n"
 require(len(data)<=2*1024**2,"bounded diagnostic JSON")
 final=Path(path);tmp=final.with_name("."+final.name+".pending-"+secrets.token_hex(16))
 try:
  with tmp.open("xb") as f:
   require(f.write(data)==len(data),"full atomic JSON temporary write")
   f.flush();os.fsync(f.fileno())
  os.link(tmp,final,follow_symlinks=False) # exclusive existing-final rejection
  directory=os.open(str(final.parent),os.O_RDONLY|os.O_DIRECTORY)
  try:
   os.fsync(directory) # complete final published before success-only temp removal
   tmp.unlink()
   os.fsync(directory)
  finally:os.close(directory)
 except BaseException:
  print("SPARQ_ATOMIC_JSON_FAILURE "+json.dumps(dict(final=str(final),retained_temporary=str(tmp))),file=sys.stderr,flush=True)
  raise # original first exception; no quiet deletion, replacement or retry
 return bound(final,sha(final))

def packet_source(path,digest):
 """Own/source-only preparation context: does NOT assert proposed canonical
 manifest is already applied, nor grant complete component/model permission.
 All code/private author/public source bytes are still bound and verified.
 """
 execution_clock()
 ref=bound(path,digest);m=obj(ref)
 require(path==str(ROOT/"SOURCE_MANIFEST.json") and m["schema"]=="sparq.author-ann-fp32-stock-full-source/v3" and
  m["ready"] is False and m["observer_output_budget"]["protocol"]==MODEL_GDN_PROTOCOL and set(m["files"])==set(OWN) and m["source_pins"]==PINS and
  m["runtime_pins"]==RUNTIME_PINS and m["host_dependencies"]==HOST_DEPENDENCIES and
  m["source_count"]==len(OWN)+len(PINS)+len(HOST_DEPENDENCIES),"exact own aggregate code and public source pins")
 for name,want in m["files"].items():bound(ROOT/name,want)
 for name,want in PINS.items():
  if name!=str(KERNEL/"SOURCE_MANIFEST.json"):bound(name,want)
 for name,want in HOST_DEPENDENCIES.items():bound(name,want)
 private=obj(dict(path=str(AUTHOR_PRIVATE/"SOURCE_MANIFEST.json"),sha256=PINS[str(AUTHOR_PRIVATE/"SOURCE_MANIFEST.json")]))
 for name,want in private["files"].items():bound(AUTHOR_PRIVATE/name,want)
 require(private["source_count"]==43,"frozen author v2 private closure declared; no native result")
 return ref,m["files"]

def source(path,digest):
 execution_clock()
 ref=bound(path,digest);m=obj(ref)
 require(path==str(ROOT/"SOURCE_MANIFEST.json") and m["schema"]=="sparq.author-ann-fp32-stock-full-source/v3" and
  m["ready"] is False and set(m["files"])==set(OWN) and m["source_pins"]==PINS and
  m["runtime_pins"]==RUNTIME_PINS and m["host_dependencies"]==HOST_DEPENDENCIES and m["source_count"]==len(OWN)+len(PINS)+len(HOST_DEPENDENCIES),"exact new source closure/count; no runtime grant")
 for name,want in m["files"].items():bound(ROOT/name,want)
 for name,want in PINS.items():bound(name,want)
 for name,want in HOST_DEPENDENCIES.items():bound(name,want)
 km=obj(dict(path=str(KERNEL/"SOURCE_MANIFEST.json"),sha256=KERNEL_SHA))
 require(km["source_count"]==42 and len(km["files"])==31 and km["registered_author_successor"]["protocol"]==AUTHOR_PROTOCOL,"exact NEW author v2 full41-source mechanism; old011 rejected")
 for name,want in km["files"].items():bound(KERNEL/name,want)
 for name,want in km["dependencies"].items():bound(name,want)
 for value in [km["native_device_operator"],*km["model_sources"].values()]:
  r=value["captured_source_ref"];bound(r["path"],r["sha256"])
 return ref,m["files"]
USER72H_REF={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/USER_72H_PROTOCOL_20261009.json","sha256":"b605d2a01118c4087e3450b3d800ef5bf40f6d0f882c1606a1e9117ed56151d1"}
NATIVE_EXECUTION_CLOCK={"schema":"sparq.user72h-execution-clock/v1","owner":"sparq-author-ann-fixed-capacity-repair/v1","authorization":{"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/USER_72H_PROTOCOL_20261009.json","sha256":"b605d2a01118c4087e3450b3d800ef5bf40f6d0f882c1606a1e9117ed56151d1"},"repair_cutoff_utc":"2026-10-10T07:00:25Z","repair_cutoff_epoch":1791615625,"total_cutoff_utc":"2026-10-12T07:00:25Z","total_cutoff_epoch":1791788425,"original_ba508_status":"FAILED-not-promoted"}
MODEL_EXECUTION_CLOCK=dict(schema="sparq.user72h-full-model-clock/v1",
 owner="sparq-author-ann-fixed-capacity-full-model/v1",authorization=USER72H_REF,
 total_cutoff_utc="2026-10-12T07:00:25Z",total_cutoff_epoch=1791788425,
 first_repair_cutoff_utc="2026-10-10T07:00:25Z",first_repair_cutoff_epoch=1791615625,
 old_ba508_status="FAILED-not-promoted",whole_phase_seconds=5400,cleanup_included_seconds=90)
PINS[USER72H_REF["path"]]=USER72H_REF["sha256"]
def execution_clock():
 x=obj(USER72H_REF)
 require(x.get("schema")=="paper-portfolio.user-time-protocol/v1" and
  x.get("recorded_at_utc")=="2026-10-09T07:00:25Z" and
  x.get("first_candidate_repair_cutoff_utc")=="2026-10-10T07:00:25Z" and
  x.get("first_candidate_repair_cutoff_epoch")==1791615625 and
  x.get("total_cutoff_utc")=="2026-10-12T07:00:25Z" and
  x.get("total_cutoff_epoch")==1791788425 and
  x.get("old_cutoffs_unchanged") is True and x.get("old_failures_unchanged") is True and
  x.get("physical_npus")==[4,5,6,7] and x.get("protected_physical_npus")==[0,1,2,3],
  "actual immutable human72h authorization; no paper clock reset/old failure promotion")
 return dict(MODEL_EXECUTION_CLOCK)
def validate_execution_clock(plan,host):
 expected=execution_clock()
 require(plan["execution_clock"]==host["execution_clock"]==expected and
  plan["cutoff"]=="2026-10-12T07:00:25+00:00" and
  plan["phase_seconds"]==expected["whole_phase_seconds"] and
  plan["cleanup_seconds"]==expected["cleanup_included_seconds"],
  "same whole original source-bound model clock/5400/90, not a successor-reset lease")

def component(r,replay=False):
 import component_handoff as h
 h.source_interfaces()
 x=obj(r);km=obj(dict(path=str(KERNEL/"SOURCE_MANIFEST.json"),sha256=KERNEL_SHA))
 require(km["execution_clock"]==NATIVE_EXECUTION_CLOCK and x.get("execution_clock")==NATIVE_EXECUTION_CLOCK and
  x.get("original_ba508_numeric_status")=="failed-not-promoted","new immutable complete v10 numeric authority; old ba508 expired/failed")
 require(x.get("schema")=="sparq.complete-token-component/v9-author-ann-FP32-compensation" and x.get("precision_contract")==AUTHOR_PROTOCOL and x.get("author_literal_output_hard_gate") is False and
  x.get("original_BF16_dual_gate_status")=="FAILED-not-promoted" and x.get("original009_numeric_status")=="failed-not-promoted" and x.get("original011_numeric_status")=="failed-not-promoted" and x.get("author_commit")=="554ea6db219405becbdc0a126984a19f181bdc69" and x.get("source_manifest")==dict(path=str(KERNEL/"SOURCE_MANIFEST.json"),sha256=KERNEL_SHA) and
  x.get("source_files")==km["files"] and all(x.get(k) is True for k in
   ("MAIN_original_operation_authority_verified","physical_NPU_process_authority_verified","owned_stop_retention_verified")) and
  x.get("cases")==128 and x.get("actual_numerical_steps")==20480,
  "MAIN original complete physical kernel consumer authority required before TP4; fixtures/partial/failure forbidden")
 require(all(type(x.get(k)) is dict and set(x[k])=={"path","sha256"} for k in
  ("original_terminal","host_result","actual_report","native_no_device_abi")),"whole original kernel terminal/result/report/ABI Refs are mandatory, not boolean-only authority")
 from original_terminal import original_terminal
 origin=original_terminal(obj(x["original_terminal"]),"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 authority=obj(x["host_result"]);record=origin["record"];output=Path(authority["output_dir"])
 expected=["/usr/bin/python3","-B",str(KERNEL/"numeric_gate.py"),"--host-execute",
  "--source-manifest",str(KERNEL/"SOURCE_MANIFEST.json"),"--source-manifest-sha256",KERNEL_SHA,"--output",str(output)]
 markers=[l for l in record["stdout"].splitlines() if l.startswith("MAIN_SPARQ_TOKEN_V5_HOST ")]
 require(authority["schema"]=="sparq.token-host-result/v4" and authority["status"]=="kernel_numerics_checked" and
  authority["source_manifest"]==x["source_manifest"] and authority["sources_before"]==authority["sources_after"]==km["files"] and
  authority["primary_error"] is None and authority["secondary_errors"]==[] and
  [record["command"],*record["args"]]==authority["actual_host_argv"]==authority["expected_host_argv"]==expected and
  origin["operation_id"]==x["original_operation_id"] and x["original_record_origin"]==origin["record_origin"] and
  x["original_terminal_shape"]==origin["origin_shape"] and len(markers)==1 and
  json.loads(markers[0].split(" ",1)[1])==dict(result=x["host_result"],status="kernel_numerics_checked",
   source_manifest=x["source_manifest"],host_script_sha256=km["files"]["host.py"],entry_script_sha256=km["files"]["numeric_gate.py"]),
  "actual whole original v6 kernel terminal/operation/fullargv/source/stdout marker -> immutable RESULT")
 require(x["host_result"]["path"]==str(output/"RESULT.json") and x["actual_report"]==authority["producer_report"] and
  x["actual_report"]["path"]==str(output/"gate/REPORT.json") and x["native_no_device_abi"]==authority["native_no_device_abi"] and
  Path("/cache/cch") in output.parents and output.resolve()==output and output.is_dir() and not output.is_symlink(),
  "original exact owned kernel output/report/ABI tree")
 if replay:
  import sys,importlib
  before=list(sys.path)
  try:
   sys.path.insert(0,str(KERNEL))
   consumer=module(KERNEL/"consume_numeric.py",km["files"]["consume_numeric.py"],"_sparq_tp4_v6_original_numeric_consumer")
   for name,file in (("receipt","receipt.py"),("numeric_gate","numeric_gate.py"),("preflight","preflight.py"),("host","host.py")):
    imported=importlib.import_module(name)
    require(imported is not None and Path(imported.__file__).resolve()==KERNEL/file and sha(imported.__file__)==km["files"][file],
     "exact same canonical v6 kernel consumer imports; no cached foreign packet")
   proof=authority["source_device_proof"]
   checked=consumer.consume(output/"gate",x["original_terminal"]["path"],x["original_terminal"]["sha256"],
    proof["path"],"lgw_a6109c51076a4a2c9d2674ca5a8704a0",x["source_manifest"],km["files"],
    x["host_result"]["path"],x["host_result"]["sha256"])
   require(canonical(checked)==canonical(x),"MAIN independent whole original full128case20480step kernel consumer replay, not self-declared booleans")
  finally:sys.path[:]=before
 return x

def actual_component(path,digest):
 # Neither saved-checkpoint16 diagnostic nor software proof is model authority.
 return component(bound(path,digest),replay=True)
def runtime_sources(attention,runner,acl):
 require(Path(attention.__file__).resolve()==Path("/vllm-workspace/vllm-ascend/vllm_ascend/attention/attention_v1.py") and
  Path(runner.__file__).resolve()==Path("/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py") and
  Path(acl.__file__).resolve()==Path("/vllm-workspace/vllm-ascend/vllm_ascend/compilation/acl_graph.py"),"exact deployed module source locations")
 for path,want in RUNTIME_PINS.items():bound(path,want)
 for name,want in obj(dict(path=str(KERNEL/"SOURCE_MANIFEST.json"),sha256=KERNEL_SHA))["files"].items():bound(KERNEL/name,want)
 return dict(runtime_sources_checked=True,model_ready=False)
_COUNTER={}
def event(directory,rank,kind,value,source,authority):
 root=Path(directory)
 require(root.is_absolute() and root.resolve()==root and root.is_dir() and not root.is_symlink() and
  Path("/cache/cch") in root.parents and type(rank) is int and rank in range(4) and
  re.fullmatch("[a-z0-9-]+",kind),"exact owned diagnostic trace root/rank/kind; formal trace OFF")
 i=_COUNTER.get(rank,0)+1;_COUNTER[rank]=i
 return write(root/("rank%d-%08d-%s.json"%(rank,i,kind)),
  dict(schema="sparq.actual-full-model-observation/v3",rank=rank,kind=kind,value=value,
   source=source,kernel_authority=dict(source_manifest=authority["source_manifest"],
    original_terminal=authority["original_terminal"]),model_ready=False))
