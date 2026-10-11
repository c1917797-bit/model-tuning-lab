"""Default-OFF bridge identity. Reuses frozen reader001; never modifies its globals."""
import importlib.util,json,os,re,sys,time
from pathlib import Path
ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-model-reader-once-v1-002")
HERE=Path(__file__).resolve().parent
READER={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-compiled-reader-v1-001/SOURCE_MANIFEST.json","bytes":58779,"sha256":"67a07f213095e2193c1979d1fde5ad72a985d0aa9a3fb32b0eef64037770c6a1"}
CUT=1791788425
ORIGINAL_PROMPT={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-kivi-model-firstdecode-main-20261010-018/candidate/INPUT_PROTOCOL.json","bytes":164697,"sha256":"45433e3876bc08799424587baa5261679fb65eaa656f81519ed265ca8c654ff3"}
def need(x,m):
    if not x:raise ValueError(m)
def bootstrap():
    from hashlib import sha256
    p=Path(READER["path"]);raw=p.read_bytes()
    need(len(raw)==READER["bytes"]and sha256(raw).hexdigest()==READER["sha256"],"exact frozen reader manifest")
    rows=json.loads(raw)["files"];row=next(r for r in rows if r["path"].endswith("/contract.py"))
    old=sys.modules.get("contract")
    if old is None:
        need(Path(row["path"]).is_file(),"real declared reader contract")
        spec=importlib.util.spec_from_file_location("contract",row["path"]);old=importlib.util.module_from_spec(spec)
        sys.modules["contract"]=old;spec.loader.exec_module(old)
    need(old.ref(old.__file__)==row,"cached contract exact source; do not substitute unknown namespace")
    old.source(READER["sha256"])
    # The actual child starts clean, explicit original module names are mandatory.
    original=list(sys.path)
    try:
        sys.path.insert(0,str(Path(READER["path"]).parent))
        for name in("layout","kernel","reference","numeric","reader_host","reader_whole","reader_consume","reader_cpu","reader_canary",
          "runtime_cache","native_binding","model_raw","native_finish","worker_patch","model_runtime","model_consume"):
            old.load(name,next(r for r in rows if r["path"].endswith("/"+name+".py")))
    finally:sys.path[:]=original
    return old
def runtime_metadata(manifest,reader):
    rows=manifest["files"]+manifest["dependencies"]
    chain=manifest["native_format_patch_chain"]
    need(type(chain)is dict and set(chain)=={"root","loader","exports","format","patch_manager","npu_patches"}and
      chain==reader["native_format_patch_chain"],"actual same frozen six-source native export/format chain")
    refs=[READER,ORIGINAL_PROMPT,*chain.values(),*manifest["host_bindings"].values()]
    for key in("runtime_configuration_sources","multiprocessing_runtime_sources","rpc_runtime_sources",
      "native_tp_runtime_sources","native_qkv_runtime_sources","native_text_input_runtime_sources"):
        refs.extend(x["snapshot"]for x in manifest[key])
    need(all(ref in rows for ref in refs),"every accessed runtime metadata Ref in exact model source closure")
    return refs

def source(expected):
    C=bootstrap();r=C.ref(HERE/"SOURCE_MANIFEST.json");m=C.obj(r)
    need(HERE==ROOT and r["sha256"]==expected and m["schema"]=="skvq.model-reader-once.sources/v1"and
      m["default_enabled"]is False and m["reader_source_ref"]==READER and m["portfolio_cutoff_epoch"]==CUT,
      "unique model bridge source/fixed clock")
    runtime_metadata(m,C.obj(READER))
    rows=m["files"]+m["dependencies"];need(len({v["path"]for v in rows})==len(rows)==m["source_count"],"complete unique model bridge closure")
    for row in rows:
        data=C.read(row)
        if row["path"].endswith(".py"):compile(data,row["path"],"exec")
    return C,r,m
def prompt(C,r):
    value=C.obj(r)
    need(value["schema"]=="skvq.first-decode.prompt/v1"and value["source_ref"]==READER and
      len(value["token_ids"])==32768 and all(type(i)is int and 0<=i<2**31 for i in value["token_ids"]),
      "actual frozen source-bound32768 token IDs, not generated fake input receipt")
    # Retain explicit byte-linked original input, with exact token identity.
    need(value["original_input_ref"]==ORIGINAL_PROMPT,"one actually archived token-ID input; not model PASS")
    origin=C.obj(value["original_input_ref"])
    need(origin["body"]["prompt"]==value["token_ids"]and origin["prompt_tokens"]==32768 and value["original_input_ref"]!=r,
      "actual original prompt byte provenance; no reconstructed candidate input")
    return value
def make_prompt(C,source,output):
    origin=C.obj(ORIGINAL_PROMPT);tokens=origin["body"]["prompt"]
    need(origin["prompt_tokens"]==len(tokens)==32768 and all(type(i)is int and 0<=i<2**31 for i in tokens),
      "actual unchanged original input token domain")
    row=C.atomic(output,dict(schema="skvq.first-decode.prompt/v1",source_ref=READER,
      bridge_source_ref=source,original_input_ref=ORIGINAL_PROMPT,token_ids=tokens,
      new_requested_output_tokens=3,input_only_no_predecessor_model_authority=True))
    prompt(C,row);return row
def false_scopes():return dict(native_ready=False,model_ready=False,performance_ready=False,task_ready=False,
    whole_176=False,graph_verified=False,lifecycle_verified=False)
