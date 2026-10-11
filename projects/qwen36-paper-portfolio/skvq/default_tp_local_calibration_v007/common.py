"""DEFAULT OFF source/actual-capture contracts, no device or model imports."""
import ast,hashlib,importlib.util,json,math,os,re,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-default-tp-local-calibration-v1-007")
CAPTURE={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/SOURCE_MANIFEST.json","bytes":82562,"sha256":"9c7b1118b1cd1f2a20ab7fde0ecb98031bf14289c9c795c18f48de9cdb805acd"}
CAPTURE_BINDINGS={"current_contract.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/current_contract.py","bytes":5755,"sha256":"68c6f47eb589189bc1430a16b5001f6bc9b6456788e4feae0dbdcdc3b70f4bdb"},"consume_whole.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/consume_whole.py","bytes":3029,"sha256":"6784108006c973a394c1846e7d8d4dd59ebcb629a2e7b65101b4747216dfeea4"},"consume_stage.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/consume_stage.py","bytes":6267,"sha256":"c9538d88c3347c6aafe28d07d1efbf15979b4e3bbf8d02d1db7a938e0a93d5b4"},"MAIN_HOST.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/MAIN_HOST.py","bytes":25396,"sha256":"05b1522a2ef0a9ccc7f203818378d064c910cb4fdab0f3c753fa44792cf962e4"},"resources.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/resources.py","bytes":6404,"sha256":"660cdd7e2639db7fbf4400a257de116b264bba9c42a530df2fe5bc734ae9624c"},"mount_preflight.py":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-preprojection-current72h-v1-014/mount_preflight.py","bytes":9233,"sha256":"b1d94c72d7a710ecca4cae30d390def36379943a23ab8c794ad25efae17fc42c"}}
CUT=1791788425
DERIVED={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-capture014-offline-consumer-v1-001/SOURCE_MANIFEST.json","bytes":50965,"sha256":"33e04ccc8ab5898aa148ec847c31f0d4eceb3d6099c8bb701b1c9d082e5f2aed"}
FAILED_ORIGINAL={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN_SKVQ014_05A7_FAILED_ORIGINAL_20261011.json","bytes":4349,"sha256":"8f35cb6b73d3c4576a38d26ecdc11149469b6fbe68a2b492e337e5aea4df0d99"}
CLOCK={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/USER_72H_PROTOCOL_20261009.json","bytes":1379,"sha256":"b605d2a01118c4087e3450b3d800ef5bf40f6d0f882c1606a1e9117ed56151d1"}
LAYERS=tuple("model.layers."+str(i)+".self_attn"for i in range(3,64,4))
WRITER_CALIBRATION={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-writer-v1-004/source/qwen36_skvq_writer/calibration.py","bytes":2767,"sha256":"85db8e0401acf41446b8fd14d73df53e93276021959a8d7caf8461cbbaa398ea"}
def need(v,m):
    if not v:raise ValueError(m)
def reference(path):
    p=Path(path);need(p.is_absolute()and".."not in p.parts and p.is_file(),"absolute ordinary Ref")
    for x in(p,)+tuple(p.parents):need(not x.is_symlink(),"no symlink Ref")
    h=hashlib.sha256()
    with p.open("rb")as f:
        for b in iter(lambda:f.read(2**20),b""):h.update(b)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
def bound(ref,limit=8*2**20):
    need(type(ref)is dict and set(ref)=={"path","bytes","sha256"}and type(ref["bytes"])is int and 0<ref["bytes"]<=limit
      and re.fullmatch("[0-9a-f]{64}",ref["sha256"]),"strict bounded3Ref")
    need(reference(ref["path"])==ref,"entire byte/size/SHA")
    value=json.loads(Path(ref["path"]).read_bytes());need(reference(ref["path"])==ref,"immutable parse");return value
def source(expected):
    ref=reference(HERE/"SOURCE_MANIFEST.json")
    need(ref["sha256"]==expected and HERE==ROOT,"declared source root/SHA; local software not admission")
    m=bound(ref);need(m["schema"]=="skvq.default-tp-local.sources/v1"and m["root"]==str(ROOT)and m["default_enabled"]is False and m["clock"]==CLOCK and m["portfolio_cutoff_epoch"]==CUT,"current source schema")
    seen=set()
    for row in m["files"]+m["dependencies"]:
        need(reference(row["path"])==row and row["path"]not in seen,"full unique source closure");seen.add(row["path"])
        if row["path"].endswith(".py"):compile(Path(row["path"]).read_bytes(),row["path"],"exec")
    need(len(seen)==m["source_count"],"full actual source count")
    old=bound(CAPTURE);derived=bound(DERIVED)
    need(m["derived_capture_consumer_source_ref"]==DERIVED and
      all(r in m["dependencies"]for r in[DERIVED,*derived["files"],*derived["dependencies"],CAPTURE,*old["files"],*old["dependencies"]]),
      "entire original producer and separate derived consumer closures")
    bound(CLOCK);need(time.time()+600<=CUT,"fixed portfolio cutoff/600-second stage fit")
    return ref
def cpu_only():
    need("torch"not in sys.modules and"torch_npu"not in sys.modules,"no framework import before Devices[] gate")
    need(not list(Path("/dev").glob("davinci*"))and not any(Path("/dev",x).exists()for x in("devmm_svm","hisi_hdc")),"Devices[] CPU only")
def donor(name,path,expected):
    old=sys.modules.get(name)
    if old is not None:
        need(reference(old.__file__)["sha256"]==expected and Path(old.__file__)==Path(path),"cached source-qualified donor")
        return old
    need(reference(path)["sha256"]==expected,"actual donor source")
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v
    spec.loader.exec_module(v);need(reference(v.__file__)["sha256"]==expected,"loaded actual donor");return v
def writer_calibration():
    need(reference(WRITER_CALIBRATION["path"])==WRITER_CALIBRATION,"original writer calibration bytes")
    return donor("_skvq_default_writer_calibration",WRITER_CALIBRATION["path"],WRITER_CALIBRATION["sha256"])
def atomic():
    p="/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001/io_contract.py"
    return donor("io_contract",p,"365dd5873a07d8b3e6ef2e0ae2f91852a1a63e653f0562f5809a3a61e0c7d76c")
def publish(path,value):return atomic().publish_json(path,value)
def stage_root(path):
    """Only MAIN precreates/mounts this unique existing guest work leaf.
    Source/Devices[]/actual owned host admission remain external and mandatory.
    """
    p=Path(path)
    need(p.is_absolute()and".."not in p.parts and p.name=="work"and p.parent.parent==ROOT.parent and p.parent.parent.resolve()==p.parent.parent and
      re.fullmatch("run-skvq-default-tp-local-007-[a-zA-Z0-9-]+",p.parent.name)and p.is_dir(),"exact existing owned guest stage leaf")
    for q in(p,)+tuple(p.parents):need(not q.is_symlink(),"no guest stage symlink")
    need(p.resolve()==p,"actual canonical stage root")
    return p
def output_root(path):
    p=Path(path)
    need(p.name in("library","producer")and not p.exists()and not p.is_symlink(),"exact absent library/producer child, not host mount root")
    stage_root(p.parent)
    p.mkdir(mode=0o700);return p
def author_sources(out):
    b=json.loads((HERE/"author_sources.json").read_bytes())
    need(b["schema"]=="skvq.fixedcommit.author-raw-utf8/v1"and b["commit"]=="fdfc7ec315c16293f68dd771850b47f5199787fc","fixed author raw commit")
    target=out/"author";target.mkdir();refs={}
    for row in b["files"]:
        raw=row["text"].encode("utf-8")
        need(len(raw)==row["bytes"]and hashlib.sha256(raw).hexdigest()==row["sha256"]and row["name"]not in refs,"original UTF8 bytes including EOF")
        refs[row["name"]]=atomic().publish_bytes(target/row["name"],raw)
    need(set(refs)=={"calibration.py","KV_process.py","KVcache_manager.py","calib_config.py","README.md","LICENSE"},"all exact six source identities")
    return refs
def feature_dtype(original,mode):
    if mode=="original"and original=="torch.float16":return original
    if mode=="bf16-exact-cpu32"and original=="torch.bfloat16":return"torch.float32"
    raise ValueError("explicit BF16 exact-value CPU32 adaptation; not official FP16 calibration")

def model_payload_identity(payload):
    """Digest exact already host-hashed index/shard identities, not a marketing name.
    Old capture hashed before; the new derived raw whole independently hashes
    all payload bytes after release. This fit stage verifies that explicit pair,
    and the immutable index, without claiming old05a7 had a successful after.
    """
    need(type(payload)is dict and set(payload)=={"index","shards","actual_weight_publisher_identity_pending","path_is_not_marketing_identity"}and
      payload["actual_weight_publisher_identity_pending"]is True and payload["path_is_not_marketing_identity"]is True,
      "source-bound actual indexed payload; no publisher claim")
    index=payload["index"];body=bound(index)
    need(index["path"]=="/cache/efim/Qwen3.6-27B/model.safetensors.index.json"and type(body.get("weight_map"))is dict and body["weight_map"],
      "actual indexed same checkpoint")
    names=sorted(set(body["weight_map"].values()))
    need(all(type(k)is str and type(v)is str for k,v in body["weight_map"].items())and
      all(Path(n).name==n and n.endswith(".safetensors")for n in names)and 1<=len(names)<=128,
      "actual complete safe indexed shard names")
    rows=payload["shards"]
    need(type(rows)is list and len(rows)==len(names),"complete actual whole-index shard identities")
    for row,name in zip(rows,names):
        need(type(row)is dict and set(row)=={"path","bytes","sha256"}and row["path"]=="/cache/efim/Qwen3.6-27B/"+name and
          type(row["bytes"])is int and row["bytes"]>0 and re.fullmatch("[0-9a-f]{64}",row["sha256"]),
          "exact sorted original host-hashed shard Ref; bool/extra/foreign/missing rejected")
    identity=dict(schema="skvq.actual-indexed-payload-identity/v1",index_ref=index,shard_refs=rows)
    canonical=json.dumps(identity,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
    return dict(model_sha256=hashlib.sha256(canonical).hexdigest(),identity=identity,
      model_sha256_kind="canonical full indexed-payload Ref digest; not one-file SHA or author supplied",
      shard_bytes_rehashed_by_this_stage=False,prior_actual_host_before_after_full_payload_hash_required=True,
      publisher_identity_still_pending=True)
