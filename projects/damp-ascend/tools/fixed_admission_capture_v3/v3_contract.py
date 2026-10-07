"""Default-OFF source-only v3 contract. No runtime imports or artifact creation."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v3"
V2=ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v2"
V1=ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v1"
V2_MANIFEST_SHA="b7a067ff84174f9ccdb5d1f87662aca78aa19bbea4ac62d1a1aff6829c681af0"
OBSERVER_SHA="5d9f3f55a00ed4ffc9884fbeeaccf9167f5f632d12f9dd049ba76e662cdcb4aa"
RUN_SHA="34149654e56a2e5da25c0a527f8126dc4ec280e6908ea2812aeac0fe3dfd18b7"
RUNTIME={
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py":"94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
 "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py":"42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16",
 "/vllm-workspace/vllm-ascend/vllm_ascend/worker/npu_input_batch.py":"a4dc08a9918f07797622f8d0915785e8c7b6899e0d10d92603e1dddec218acc3",
}
def require(value,message):
 if not value: raise ValueError(message)
def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
 return h.hexdigest()
def canonical(value):
 return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False,ensure_ascii=False).encode()
def load_v2():
 require(file_sha(V2/"SOURCE_MANIFEST.json")==V2_MANIFEST_SHA,"frozen v2 manifest drift")
 if str(V2) not in sys.path:sys.path.insert(0,str(V2))
 import v2_contract
 require(Path(v2_contract.__file__).resolve()==V2/"v2_contract.py","wrong frozen v2 contract")
 return v2_contract
def source_contract():
 m=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
 require(m["schema"]=="damp-fixed-admission-sources/v3","wrong v3 schema")
 for name,digest in m["files"].items():require(file_sha(HERE/name)==digest,"new source drift: "+name)
 frozen=load_v2().source_contract()
 require(file_sha(V2/"v2_observer.py")==OBSERVER_SHA and file_sha(V2/"run.py")==RUN_SHA,
         "frozen observer/controller changed")
 return {"schema":m["schema"],"manifest_sha256":file_sha(HERE/"SOURCE_MANIFEST.json"),
         "frozen_v2":frozen,"status":"prepared-not-native-verified",
         "source_lock_issued":False}
def private_run():
 source_contract()
 name="_damp_fixed_v3_private_v2_driver"
 if name not in sys.modules:
  spec=importlib.util.spec_from_file_location(name,V2/"run.py")
  m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
 return sys.modules[name]
def inventory(entries):
 rows=[e for e in entries if e.group=="vllm.general_plugins" and e.name=="damp_capture"]
 require(len(rows)==1 and rows[0].value=="damp_fixed_v3:register","wrong/duplicate v3 entrypoint")
 return {"group":rows[0].group,"name":rows[0].name,"value":rows[0].value}
