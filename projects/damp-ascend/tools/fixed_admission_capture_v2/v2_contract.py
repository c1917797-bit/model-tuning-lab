"""NEW v2 sources only. Imports are stdlib; no Docker/Torch/default writes."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
HERE=ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v2"
OLD=ROOT/"projects/damp-ascend/tools/fixed_admission_capture_v1"
OLD_MANIFEST_SHA="a685970e567b629016470f9a821e97ceb9007404f9a3065615715ce1c0f51aae"
OLD_RUN_SHA="2c84e03dd9a8c3fc6876a1d2ac362413fef3ba21a368749ad5b4b0e6d3aa0107"
OLD_OBSERVER_SHA="1e325b09615a96d874529a155be601bb2ca4e280c44edbef23ad2a2f1ee6b7ce"
BINDINGS_SHA="137c71b0a3f2b4dac5d82be53a25d01de39b78a77b14db4d8b9e470181003525"

def require(value,message):
    if not value: raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def v1():
    path=OLD/"diag_contract.py"
    require(file_sha(path)=="b1d6096bb5852a8de3c500e0519c1f95e78e6ea078e279c3f1c5a49929860c11",
            "frozen v1 contract drift")
    if str(OLD) not in sys.path: sys.path.insert(0,str(OLD))
    import diag_contract
    require(Path(diag_contract.__file__).resolve()==path,"wrong frozen contract import")
    return diag_contract

def source_contract():
    m=json.loads((HERE/"SOURCE_MANIFEST.json").read_text())
    require(m["schema"]=="damp-fixed-admission-sources/v2","wrong NEW packet")
    for name,sha in m["files"].items():
        require(file_sha(HERE/name)==sha,"NEW source drift: "+name)
    require(file_sha(OLD/"SOURCE_MANIFEST.json")==OLD_MANIFEST_SHA,"frozen v1 manifest drift")
    old=v1().source_contract()  # exact 13 + 28 existing closure, not new execution.
    require(file_sha(ROOT/"projects/damp-ascend/collector/damp_capture/bindings.py")==BINDINGS_SHA,
            "frozen binding body drift")
    return {"schema":m["schema"],"manifest_sha256":file_sha(HERE/"SOURCE_MANIFEST.json"),
            "frozen_v1":old,"status":"source_prepared_not_native_verified"}

def frozen_run():
    source_contract()
    path=OLD/"run.py"
    require(file_sha(path)==OLD_RUN_SHA,"frozen Controller drift")
    name="_damp_fixed_v2_private_frozen_controller"
    if name in sys.modules:
        require(Path(sys.modules[name].__file__).resolve()==path,"private Controller source changed")
        return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module

def inventory(entries):
    rows=[e for e in entries if e.group=="vllm.general_plugins" and e.name=="damp_capture"]
    require(len(rows)==1 and rows[0].value=="damp_fixed_v2:register",
            "duplicate/wrong v2 entrypoint")
    return {"group":rows[0].group,"name":rows[0].name,"value":rows[0].value}
