"""Default OFF source and strict byte transport; no hardware import/launch."""
import hashlib,importlib.util,json,re,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-compiled-reader-v1-001")
WRITER_SOURCE={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-actual-writer-bridge-v1-002/SOURCE_MANIFEST.json","bytes":51408,"sha256":"445b3f25bac488f1053b57e24c82177b833440b013faf6402b3153e4be73f433"}
CUT=1791788425
def need(v,m):
    if not v:raise ValueError(m)
def ref(path):
    p=Path(path);need(p.is_absolute()and".."not in p.parts and p.is_file(),"absolute regular file")
    for x in(p,)+tuple(p.parents):need(not x.is_symlink(),"no Ref symlink")
    h=hashlib.sha256()
    with p.open("rb")as f:
        for raw in iter(lambda:f.read(2**20),b""):h.update(raw)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def read(r,limit=64*2**20):
    need(type(r)is dict and set(r)=={"path","bytes","sha256"}and type(r["bytes"])is int and
      0<r["bytes"]<=limit and re.fullmatch("[a-f0-9]{64}",r["sha256"]),"strict three-key whole Ref")
    need(ref(r["path"])==r,"whole size/hash/source");return Path(r["path"]).read_bytes()
def obj(r):
    x=json.loads(read(r));need(ref(r["path"])==r,"immutable JSON");return x
def load(name,r):
    read(r);old=sys.modules.get(name)
    if old is not None:
        need(getattr(old,"__file__",None)and ref(old.__file__)==r,"cached module exact source")
        return old
    spec=importlib.util.spec_from_file_location(name,r["path"]);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);need(ref(m.__file__)==r,"actual module loaded bytes");return m
def source(sha,*,device=False):
    r=ref(HERE/"SOURCE_MANIFEST.json");m=obj(r)
    need(HERE==ROOT and r["sha256"]==sha and m["root"]==str(ROOT)and
      m["schema"]=="skvq.compiled-reader.sources/v1"and m["default_enabled"]is False and
      m["writer_source_ref"]==WRITER_SOURCE and m["portfolio_cutoff_epoch"]==CUT,"unique frozen reader/source/deadline")
    rows=m["files"]+m["dependencies"];need(len({x["path"]for x in rows})==len(rows)==m["source_count"],"complete unique source closure")
    for row in rows:
        raw=read(row)
        if row["path"].endswith(".py"):compile(raw,row["path"],"exec")
    if device:need(time.time()+1800<=CUT,"declared 1800 including90 fits unchanged deadline")
    return r
def writer_modules():
    m=obj(WRITER_SOURCE);rows={Path(r["path"]).name:r for r in m["files"]}
    for r in m["files"]+m["dependencies"]:read(r)
    for name in("writer_contract","writer_resources","writer_host","writer_inputs","writer_whole"):
        load(name,rows[name+".py"])
    return sys.modules["writer_contract"],sys.modules["writer_whole"]
def writer_whole(r):
    value=obj(r)
    need(value["schema"]=="skvq.actual-writer.whole/v1"and
      value["status"]=="OWNED_SINGLE4_ALL64_Q2Q4_WRITER_BYTES_CONSUMED"and
      value["source_ref"]==WRITER_SOURCE and value["actual_cases"]==128 and
      value["actual_axis_writer_calls"]==256 and value["whole_owned_cleanup_semantics_checked"]is True,
      "actual complete same writer whole, not fixture/source-only/failed")
    _,W=writer_modules()
    fresh=W.consume(Path(value["host_result_ref"]["path"]).parent,value["original_ref"],WRITER_SOURCE["sha256"])
    need(fresh==value,"actual original/cleanup/full independent writer replay")
    return value
def reader_whole(r):
    value=obj(r)
    need(value["schema"]=="skvq.compiled-reader.whole/v1"and
      value["status"]=="OWNED_SINGLE4_ALL64_Q2Q4_COMPILED_ATTENTION_CONSUMED"and
      value["source_ref"]==ref(HERE/"SOURCE_MANIFEST.json")and value["actual_cases"]==128 and
      value["actual_kernel_calls"]==384 and value["whole_owned_cleanup_semantics_checked"]is True,
      "actual current compiled reader whole; source/fixture/other paper cannot unlock model")
    import reader_whole as whole
    fresh=whole.consume(Path(value["host_result_ref"]["path"]).parent,value["original_ref"],value["source_ref"]["sha256"])
    need(fresh==value,"fresh original source/ownership/independent numerical replay")
    return value
def scopes():
    return dict(native_ready=False,model_ready=False,performance_ready=False,task_ready=False,
      whole_176=False,graph_verified=False,lifecycle_verified=False)
def atomic(path,value,*,binary=False):
    original=load("_skvq_reader_original_io",IO)
    return original.publish_bytes(path,value)if binary else original.publish_json(path,value)
def input_rows(whole):
    producer=obj(whole["producer_ref"]);plan=obj(whole["input_plan_ref"])
    need(len(plan["rows"])==64 and len(producer["cases"])==128,"actual complete writer inputs/results")
    rows={(x["rank"],x["logical_layer"]):x for x in plan["rows"]};out=[]
    for case in producer["cases"]:
        key=(case["rank"],case["logical_layer"]);item=rows[key];event=obj(item["event_ref"])
        q=event["snapshots"]["q"]
        need(q["shape"]==[4096,6,256]and q["snapshot_contiguous_independent_clone"]is True and
          q["dtype"]==item["axes"]["K"]["original_dtype"]==item["axes"]["V"]["original_dtype"]and
          q["ref"]["bytes"]==4096*1536*2,"actual same-input full Q6, original dtype")
        read(q["ref"])
        out.append(dict(rank=key[0],logical_layer=key[1],bits=case["bits"],query_full_ref=q["ref"],
          query_token_offset=4095,query_byte_slice=[4095*3072,4096*3072],
          axes=item["axes"],writer_axes=case["axes"],event_ref=item["event_ref"]))
    need([(x["rank"],x["logical_layer"],x["bits"])for x in out]==
      [(r,"model.layers."+str(l)+".self_attn",b)for r in range(4)for l in range(3,64,4)for b in(2,4)],
      "all64/Q2Q4 ordered exact coverage")
    return out
def proof(value,source_ref,whole_ref):
    need(value["schema"]=="skvq.compiled-reader.owned-proof/v1"and value["source_ref"]==source_ref and
      value["writer_whole_ref"]==whole_ref and value["image"]==
      "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"and
      value["physical_card"]==4 and type(value["physical_card"])is int and value["logical_device"]==0 and
      type(value["logical_device"])is int and re.fullmatch("[a-f0-9]{64}",value["cid"]),
      "MAIN owned singleton4 source/producer/image identity")
    for key in("source_gate_ref","mapping_ref","resource_ref","clock_ref","owned_ref","fresh_canary_ref"):obj(value[key])
    need(value["host_semantic_consumer_required"]is True,"guest not authorized to self-grant owner/resource semantics")
    return value

IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OUTPUT_CAP=1073741824
IO={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001/io_contract.py","bytes":4521,"sha256":"365dd5873a07d8b3e6ef2e0ae2f91852a1a63e653f0562f5809a3a61e0c7d76c"}
CLOCK={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/USER_72H_PROTOCOL_20261009.json","bytes":1379,"sha256":"b605d2a01118c4087e3450b3d800ef5bf40f6d0f882c1606a1e9117ed56151d1"}
BUDGET={"path":"/cache/cch/qwen36-paper-preparation-20261007/recurrent/adakv030-fa-physical-layout-observation-v6-user72h-20261010/output_budget.py","bytes":16355,"sha256":"44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad"}
def host_bindings():return writer_modules()[0].HOST_BINDINGS
def protected_module():return writer_modules()[0].protected_module()
def snapshot(root):
    module=load("_skvq_reader_actual_budget",BUDGET);value=module.scan(root);used=module.consume(value,root)
    need(value["socket_policy"]==dict(parents=[],ipc_source=None)and not value["sockets"]and used<=OUTPUT_CAP,
      "complete1GiB reader evidence; no socket policy or subtraction")
    return value
def publish(path,value):return load("_skvq_reader_original_io",IO).publish_json(path,value)
checked=read
module=load
