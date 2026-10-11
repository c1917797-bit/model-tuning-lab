"""Explicit source-bound derived CPU consumer. Old014 remains producer identity."""
import ast,hashlib,importlib.util,json,os,re,sys,time
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent
ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-capture014-offline-consumer-v1-004")
CAPTURE={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/SOURCE_MANIFEST.json","bytes":82562,"sha256":"9c7b1118b1cd1f2a20ab7fde0ecb98031bf14289c9c795c18f48de9cdb805acd"}
RAW_ROOT=PurePosixPath("/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-skvq-current72h-projection-014-main-20261010-001")
FAILED_ORIGINAL={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN_SKVQ014_05A7_FAILED_ORIGINAL_20261011.json","bytes":4349,"sha256":"8f35cb6b73d3c4576a38d26ecdc11149469b6fbe68a2b492e337e5aea4df0d99"}
DIFF_ORIGINAL={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN_SKVQ014_IDENTITY_DIFF_05C4_ORIGINAL_20261011.json","bytes":6162,"sha256":"c5801d74d15f3f5779101280dd0ceed43cf81c3571404dc74f4a4f716a7a8481"}
RELEASE_ORIGINAL={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN_SKVQ014_RELEASE_05C2_ORIGINAL_20261011.json","bytes":52527,"sha256":"3a065732913ed980b1d6a65ede122645578a9bca6dffe7be25b9a8c52ee0144d"}
CUT=1791788425
def need(value,message):
    if not value:raise ValueError(message)
def ref(path):
    p=Path(path);need(p.is_absolute()and".."not in p.parts and p.is_file(),"absolute ordinary file Ref")
    for q in(p,)+tuple(p.parents):need(not q.is_symlink(),"symlink source/evidence forbidden")
    h=hashlib.sha256()
    with p.open("rb")as f:
        for b in iter(lambda:f.read(2**20),b""):h.update(b)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def checked(value):
    need(type(value)is dict and set(value)=={"path","bytes","sha256"}and
      type(value["bytes"])is int and value["bytes"]>0 and re.fullmatch("[0-9a-f]{64}",value["sha256"]),
      "strict exact3Ref; no coercion or extra fields")
    need(ref(value["path"])==value,"entire original file bytes/size/SHA");return value
def obj(value):
    checked(value);v=json.loads(Path(value["path"]).read_bytes());checked(value);return v
def source(expected):
    row=ref(HERE/"SOURCE_MANIFEST.json")
    need(row["sha256"]==expected and HERE==ROOT,"declared installed derived source/SHA")
    m=obj(row)
    need(m["schema"]=="skvq.capture014.offline.sources/v1"and m["root"]==str(ROOT)and
      m["default_enabled"]is False and m["producer_source_ref"]==CAPTURE and
      m["portfolio_cutoff_epoch"]==CUT,"one current derived source, not altered014")
    seen=set()
    for r in m["files"]+m["dependencies"]:
        checked(r);need(r["path"]not in seen,"unique full source closure");seen.add(r["path"])
        if r["path"].endswith(".py"):compile(Path(r["path"]).read_bytes(),r["path"],"exec")
    old=obj(CAPTURE)
    need(all(r in m["dependencies"]for r in[CAPTURE,*old["files"],*old["dependencies"],
      FAILED_ORIGINAL,DIFF_ORIGINAL,RELEASE_ORIGINAL]),"entire immutable014 plus actual failure evidence closure")
    need(len(seen)==m["source_count"]and len(m["files"])==m["own_file_count"],"actual source counts")
    return row
def load(name,row):
    checked(row)
    old=sys.modules.get(name)
    if old is not None:
        need(getattr(old,"__file__",None)is not None and ref(old.__file__)==row,
          "cached module must have this exact original source; never delete or rebind")
        return old
    spec=importlib.util.spec_from_file_location(name,row["path"])
    need(spec is not None and spec.loader is not None,"explicit exact source loader")
    value=importlib.util.module_from_spec(spec);sys.modules[name]=value
    spec.loader.exec_module(value)
    need(ref(value.__file__)==row,"loaded whole source identity")
    return value
def original_modules(consumer_source):
    manifest=obj(consumer_source);old=obj(CAPTURE);rows={Path(r["path"]).name:r for r in old["files"]}
    def owned(name,file):return load(name,rows[file])
    for directory in (str(HERE),str(Path(CAPTURE["path"]).parent)):
        if directory not in sys.path:sys.path.insert(0,directory)
    C=owned("current_contract","current_contract.py")
    if C.EXPECTED is None:C.configure(CAPTURE["sha256"])
    else:need(C.EXPECTED==CAPTURE["sha256"],"one immutable original capture source context")
    need(C.source()==CAPTURE,"actual whole014 producer closure")
    base=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
    dependencies={r["path"]:r for r in old["dependencies"]}
    for p in (base,base.parent/"skvq-tp4-qkv-loader-order-v1-001",
              base.parent/"skvq-calibration-boundary-v1-001",base.parent/"skvq-preprojection-capture-adapter-v1-001"):
        if str(p)not in sys.path:sys.path.insert(0,str(p))
    load("io_contract",dependencies[str(base/"io_contract.py")])
    load("consume_inputs",dependencies[str(base/"consume_inputs.py")])
    for name in ("spawn_startup","rpc_extension","physical_hbm","mount_preflight",
      "input_dependency","engine_config","process_cmdline","n1_format","resources","model_kwargs"):
        owned(name,name+".py")
    owned("tp_provider_current","tp_provider_current.py")
    owned("consume_text_input_current","consume_text_input_current.py")
    owned("consume_capture","consume_capture_current.py")
    owned("order_oracle_current","order_oracle_current.py") # N1 qualifier remains original.
    own={Path(r["path"]).name:r for r in manifest["files"]}
    load("capture_identity",own["capture_identity.py"])
    load("order_oracle_derived",own["order_oracle_derived.py"])
    loader=load("consume_loader_derived",own["consume_loader_derived.py"])
    stage=owned("consume_stage","consume_stage.py")
    # Its original combine/cohort only; validators/run never called or patched.
    stage.cohort(obj(ref(RAW_ROOT/"run-skvq-capture-projection-001-main"/"PRODUCER_RESULT.json")),CAPTURE)
    for p in (base,base.parent/"skvq-tp4-qkv-loader-order-v1-001",
              base.parent/"skvq-calibration-boundary-v1-001",base.parent/"skvq-preprojection-capture-adapter-v1-001"):
        if str(p)not in sys.path:sys.path.insert(0,str(p))
    load("contracts",dependencies[str(base.parent/"skvq-calibration-boundary-v1-001"/"contracts.py")])
    projection=owned("_skvq014_immutable_projection","consume_projection_current.py")
    load("previous_failure",own["previous_failure.py"])
    load("consume_previous_host",own["consume_previous_host.py"])
    load("identity_preflight",own["identity_preflight.py"])
    return C,loader,projection,stage
def cpu_only():
    need("torch"not in sys.modules and"torch_npu"not in sys.modules,"no framework imported")
    need(not list(Path("/dev").glob("davinci*"))and
      not any(Path("/dev",n).exists()for n in("devmm_svm","hisi_hdc")),"actual Devices[] CPU only")
def publish(path,value):
    old=obj(CAPTURE)
    r=next(x for x in old["dependencies"]if x["path"].endswith("/skvq-calibration-capture-chain-v1-001/io_contract.py"))
    return load("io_contract",r).publish_json(path,value)
