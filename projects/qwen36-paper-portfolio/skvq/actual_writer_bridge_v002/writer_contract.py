"""Default OFF: exact capture/calibration/writer source identity; no native import."""
import ast,hashlib,importlib.util,json,os,re,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-actual-writer-bridge-v1-002")
CUT=1791788425
CAPTURE={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/SOURCE_MANIFEST.json","bytes":82562,"sha256":"9c7b1118b1cd1f2a20ab7fde0ecb98031bf14289c9c795c18f48de9cdb805acd"}
CALIBRATION={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-default-tp-local-calibration-v1-006/SOURCE_MANIFEST.json","bytes":52456,"sha256":"07b526100b7184b4555138a7318c5f4a7c45ac451207ea96f656173cba1366c1"}
WRITER={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-writer-v1-004/source/qwen36_skvq_writer/device_writer.py","bytes":2386,"sha256":"4fe983904f436496c4d8ff74517f0b330bf8cf8942c09ed01c5f653ff9ed9081"}
LAYOUT={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-writer-v1-004/source/qwen36_skvq_writer/calibration.py","bytes":2767,"sha256":"85db8e0401acf41446b8fd14d73df53e93276021959a8d7caf8461cbbaa398ea"}
IO={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001/io_contract.py","bytes":4521,"sha256":"365dd5873a07d8b3e6ef2e0ae2f91852a1a63e653f0562f5809a3a61e0c7d76c"}
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
LAYERS=tuple("model.layers."+str(i)+".self_attn"for i in range(3,64,4))
TOKENS=4096;DIM=256;SINK=5;WINDOW=128;START=SINK;STOP=TOKENS-WINDOW
OUTPUT_CAP=1073741824
def need(value,message):
    if not value:raise ValueError(message)
def ref(path):
    p=Path(path);need(p.is_absolute()and".."not in p.parts and p.is_file(),"absolute regular Ref")
    for q in(p,)+tuple(p.parents):need(not q.is_symlink(),"no source/output Ref symlink")
    h=hashlib.sha256()
    with p.open("rb")as f:
        for raw in iter(lambda:f.read(2**20),b""):h.update(raw)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def checked(value,limit=64*2**20):
    need(type(value)is dict and set(value)=={"path","bytes","sha256"}and type(value["bytes"])is int and
      0<value["bytes"]<=limit and re.fullmatch("[0-9a-f]{64}",value["sha256"]),"strict 3Ref/size/type")
    need(ref(value["path"])==value,"whole actual bytes/size/SHA");return Path(value["path"]).read_bytes()
def obj(value,limit=64*2**20):
    raw=checked(value,limit);body=json.loads(raw);need(ref(value["path"])==value,"immutable original JSON");return body
def module(name,row):
    checked(row);old=sys.modules.get(name)
    if old is not None:
        need(getattr(old,"__file__",None)and ref(old.__file__)==row,"cached exact source; no unknown replacement")
        return old
    spec=importlib.util.spec_from_file_location(name,row["path"]);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);need(ref(value.__file__)==row,"actual loaded exact source")
    return value
def source(expected,*,device_stage=False):
    row=ref(HERE/"SOURCE_MANIFEST.json")
    need(HERE==ROOT and row["sha256"]==expected,"unique installed writer-bridge source")
    body=obj(row)
    need(body["schema"]=="skvq.actual-writer-bridge.sources/v1"and body["root"]==str(ROOT)and
      body["default_enabled"]is False and body["capture_source"]==CAPTURE and body["calibration_source"]==CALIBRATION and
      body["writer_source"]==WRITER and body["portfolio_cutoff_epoch"]==CUT,"explicit sources/fixed cutoff")
    seen=set()
    for r in body["files"]+body["dependencies"]:
        checked(r);need(r["path"]not in seen,"unique actual source closure");seen.add(r["path"])
        if r["path"].endswith(".py"):compile(Path(r["path"]).read_bytes(),r["path"],"exec")
    need(len(seen)==body["source_count"],"complete actual source count")
    if device_stage:need(time.time()+1800<=CUT,"fixed deadline and 1800 including90 fit; no renewal")
    return row
def publish(path,value):
    return module("_skvq_writer_bridge_atomic",IO).publish_json(path,value)
def raw(path,value):
    return module("_skvq_writer_bridge_atomic",IO).publish_bytes(path,value)
def scopes():
    return dict(native_ready=False,model_ready=False,performance_ready=False,task_ready=False,whole_176=False,
      packed_reader_verified=False,attention_output_verified=False,graph_verified=False,lifecycle_verified=False)
def extent(starts,bits):
    need(type(bits)is int and bits in(2,4),"Q2/Q4")
    need(type(starts)is list and len(starts)==5 and starts[0]==0 and starts[-1]==DIM and
      all(type(x)is int for x in starts)and all(a<b for a,b in zip(starts,starts[1:])),
      "actual KMeans4 nonempty local256 groups")
    return sum((b-a+8//bits-1)//(8//bits)for a,b in zip(starts,starts[1:]))
def layout(value):
    need(type(value)is dict and set(value)=={"permutation","starts","smooth","clip"}and
      type(value["permutation"])is list and len(value["permutation"])==DIM and
      all(type(i)is int for i in value["permutation"])and sorted(value["permutation"])==list(range(DIM)),
      "all256 local permutation, not cross-rank truncation")
    extent(value["starts"],2)
    need(value["smooth"]==[1.]*DIM and value["clip"]==.95,"default smoothOFF/fixed.95")
    return value
def device_proof(value,source_ref,plan_ref):
    """Guest checks exact evidence bytes only. Whole owned-host semantics remain REQUIRED."""
    need(value["schema"]=="skvq.actual-writer.owned-device-proof/v1"and value["source_ref"]==source_ref and
      value["input_plan_ref"]==plan_ref and value["image"]==IMAGE and type(value["physical_card"])is int and
      value["physical_card"]==4 and type(value["logical_device"])is int and value["logical_device"]==0 and
      re.fullmatch("[0-9a-f]{64}",value["cid"]),"explicit single physical4/logical0/current image/CID")
    for key in("source_gate_ref","mapping_ref","resource_ref","clock_ref","owned_ref","fresh_canary_ref"):
        obj(value[key])
    prior=obj(value["prior_numpy_ref"])
    need(prior["schema"]=="skvq.actual-writer.numpy-preflight/v1"and
      prior["status"]=="ACTUAL_NUMPY_SCALAR_BYTES_BITWISE_CHECKED"and prior["source_ref"]==source_ref and
      prior["input_plan_ref"]==plan_ref and prior["actual_configurations"]==24 and len(prior["configurations"])==24 and
      prior["no_torch"]is True and prior["Devices_empty"]is True and
      all(prior[k]is False for k in scopes()),"actual source-qualified NumPy scalar parity before ANY writer NPU")
    need(value["host_owned_semantic_consumer_required"]is True,"source/owner/resource/map semantics not granted by guest")
    return value
def new_output(path):
    p=Path(path)
    need(p.is_absolute()and".."not in p.parts and p.parent.is_dir()and p.parent.resolve()==p.parent and
      p.name in("plan","numeric")and not p.exists()and not p.is_symlink(),"unique absent child under MAIN owned mount")
    p.mkdir(mode=0o700);return p

HOST_BINDINGS={"MAIN_HOST.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/MAIN_HOST.py","bytes":25396,"sha256":"05b1522a2ef0a9ccc7f203818378d064c910cb4fdab0f3c753fa44792cf962e4"},"resources.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/resources.py","bytes":6404,"sha256":"660cdd7e2639db7fbf4400a257de116b264bba9c42a530df2fe5bc734ae9624c"},"mount_preflight.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/mount_preflight.py","bytes":9233,"sha256":"b1d94c72d7a710ecca4cae30d390def36379943a23ab8c794ad25efae17fc42c"},"current_contract.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/current_contract.py","bytes":5755,"sha256":"68c6f47eb589189bc1430a16b5001f6bc9b6456788e4feae0dbdcdc3b70f4bdb"},"physical_hbm.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/physical_hbm.py","bytes":2357,"sha256":"82499711a2111a7fbc0d466bffe3faadf92e88b9e0bf544d1611d33da7d3b314"},"n1_format.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/n1_format.py","bytes":5581,"sha256":"81281da0532d29ef0984ec2dea8e649e0e5c4e31220059fcab91fe11eb11582a"},"process_cmdline.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/process_cmdline.py","bytes":4083,"sha256":"289d0e3b568c2f56b81e8cf585e1a1d84ce24a9672b7468e69db11b55bc5834b"}}
CLOCK={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/USER_72H_PROTOCOL_20261009.json","bytes":1379,"sha256":"b605d2a01118c4087e3450b3d800ef5bf40f6d0f882c1606a1e9117ed56151d1"}
BUDGET={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/adakv030-fa-physical-layout-observation-v6-user72h-20261010/output_budget.py","bytes":16355,"sha256":"44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad"}
def protected_module():
    return module("_skvq_writer_protected_source",HOST_BINDINGS["current_contract.py"]).protected_module()
def snapshot(root):
    reader=module("_skvq_writer_actual_budget",BUDGET)
    value=reader.scan(root);used=reader.consume(value,root)
    need(value["socket_policy"]==dict(parents=[],ipc_source=None)and not value["sockets"]and used<=OUTPUT_CAP,
      "complete actual output1GiB, no IPC/socket authority")
    return value
