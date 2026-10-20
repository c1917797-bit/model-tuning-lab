"""Freeze copied BOLE model bundle with explicit source-delta provenance."""
from pathlib import Path
import ast,hashlib,json
OLD=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/bole-model-root-repeat-witness-renew24h-v1-20261020-006-repair12-workerledger")
NEW=Path("/opt/host/vnf/austinov/bole-model-fa64-fp16-20261020T154710Z-r19")
OUT="/opt/host/vnf/austinov/run-bole-model-fa64-fp16-20261020T154710Z-r19"
TASK=Path("/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z")
def ref(p):
 p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def write(p,j):p.write_text(json.dumps(j,sort_keys=True,allow_nan=False)+"\n")
actual=(NEW/"model_entry.py").read_text()
marker="  from fa_fp16_boundary import FiaBoundary\n  boundary=FiaBoundary(t,self.torch_npu,trial)\n  out,_=self.A.native(t,boundary,trial,actual_fia,sparse_mode=1)"
assert actual.replace(marker,"  out,_=self.A.native(t,self.torch_npu,trial,actual_fia,sparse_mode=1)")== (OLD/"model_entry.py").read_text(),"exact sole runtime boundary delta"
original=json.loads((OLD/"SOURCE_TEMPLATE.json").read_text())
m=json.loads((OLD/"SOURCE_TEMPLATE.json").read_text())
m["root"]=str(NEW);m["output_root"]=OUT;m["model_receipt_root"]=OUT+"/dense/receipts"
m["authority_ref"]=ref(TASK/"MODEL_AUTHORITY.json")
ledger={}
for name,r in original["files"].items():
 if r["path"].startswith(str(OLD)+"/") and (NEW/name).is_file():
  before=Path(r["path"]).read_text();after=(NEW/name).read_text()
  if before!=after:ledger[name]=dict(before=ref(Path(r["path"])),after=ref(NEW/name),edits=[dict(before=before,after=after)])
write(NEW/"FA_BOUNDARY_EDITS_R14.json",ledger)
deltas=[]
for name,r in list(m["files"].items()):
 if r["path"].startswith(str(OLD)+"/"):
  new=NEW/Path(r["path"]).relative_to(OLD);updated=ref(new)
  if updated["sha256"]!=r["sha256"]:deltas.append(dict(file=name,before=r,after=updated))
  m["files"][name]=updated
for name in ("fa_fp16_boundary.py","test_fa_fp16_boundary.py","repair14_ledger.py","test_repair14_delta.py","FA_BOUNDARY_EDITS_R14.json","observer_race_repair.py","test_observer_race_repair.py"):m["files"][name]=ref(NEW/name)
for i,r in enumerate(m["dependencies"]):
 if r["path"].startswith(str(OLD)+"/"):m["dependencies"][i]=ref(NEW/Path(r["path"]).relative_to(OLD))
m["fp16_boundary_repair"]=dict(predecessor=ref(OLD/"SOURCE_BOUND.json"),
 source_delta=deltas,implementation=m["files"]["fa_fp16_boundary.py"],
 independent_reference_unchanged=ref(NEW/"independent_model.py")==dict(ref(OLD/"independent_model.py"),path=str(NEW/"independent_model.py")),
 fa64_result=ref(Path("/opt/host/vnf/austinov/run-bole-fa64-20261020T154710Z-v3")/"replay/data/RESULT.json"),
 required_sameimage_software_cases=150,model_ready=False,whole_model_qualified=False)
for f in NEW.rglob("*.py"):ast.parse(f.read_bytes(),filename=str(f))
write(NEW/"SOURCE_TEMPLATE.json",m);write(NEW/"SOURCE.json",m)
commands=json.loads((OLD/"COMMANDS.json").read_text())
def convert(v):
 if isinstance(v,dict):return {k:convert(x)for k,x in v.items()}
 if isinstance(v,list):return [convert(x)for x in v]
 if isinstance(v,str):return v.replace(str(OLD),str(NEW)).replace("/opt/host/vnf/austinov/run-bole-model131repair12-MAIN-20261020T123000Z",OUT).replace("/opt/host/vnf/austinov/run-bole-model131repair12-CPU-20261020T123000Z",OUT+"-CPU")
 return v
commands=convert(commands);commands["source"]=ref(NEW/"SOURCE_TEMPLATE.json")
commands["required_sameimage_software_cases"]=150;commands["NPU_authorized"]=True
commands["bind"][commands["bind"].index("--reviewed-template-ref")+1]=json.dumps(ref(NEW/"SOURCE_TEMPLATE.json"))
write(NEW/"COMMANDS.json",commands)
write(NEW/"SOURCE_DELTAS_R13.json",dict(predecessor=ref(OLD/"SOURCE_BOUND.json"),deltas=deltas,new_files=[m["files"][x]for x in ("fa_fp16_boundary.py","test_fa_fp16_boundary.py","repair14_ledger.py","test_repair14_delta.py","FA_BOUNDARY_EDITS_R14.json","observer_race_repair.py","test_observer_race_repair.py")],mathematical_reference_unchanged=m["fp16_boundary_repair"]["independent_reference_unchanged"]))
print(json.dumps(dict(template=ref(NEW/"SOURCE_TEMPLATE.json"),changed=[x["file"]for x in deltas],files=len(m["files"]),reference_unchanged=m["fp16_boundary_repair"]["independent_reference_unchanged"])))
