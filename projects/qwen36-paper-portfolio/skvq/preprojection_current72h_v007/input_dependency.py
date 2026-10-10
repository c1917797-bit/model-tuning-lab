"""Source-bound offline CPU input dependencies; no Torch, device or network."""
import hashlib,importlib,importlib.machinery,json,os,re,stat,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import current_contract as C
BASE=Path("/cache/cch/qwen36-paper-preparation-20261007/lowbit/skvq-calibration-capture-chain-v1-001")
def require(value,message):
    if not value:raise ValueError(message)
def file_identity(st):return(st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
def ref(path):
    p=Path(path);require(p.is_absolute()and".."not in p.parts,"exact dependency path")
    for q in(p,)+tuple(p.parents):require(not q.is_symlink(),"dependency symlink refused")
    require(p.is_file(),"actual ordinary dependency file")
    before=p.stat();h=hashlib.sha256()
    with p.open("rb")as f:
        require(file_identity(os.fstat(f.fileno()))==file_identity(before),"opened dependency identity")
        for b in iter(lambda:f.read(2**20),b""):h.update(b)
        require(file_identity(os.fstat(f.fileno()))==file_identity(before),"dependency changed during hash")
    require(file_identity(p.stat())==file_identity(before),"dependency path changed after hash")
    return dict(path=str(p),bytes=before.st_size,sha256=h.hexdigest())
def validate_lock(value):
    require(type(value)is dict and set(value)=={"schema","root","packages","files","python_cache_tag","pyarrow_version","expected_origins","read_only","source_owner"},
      "complete explicit CPU dependency lock, no schema union")
    require(value["schema"]=="skvq.input-cpu-dependencies/v1"and value["read_only"]is True and
      value["source_owner"]=="MAIN-frozen-offline-dependency"and value["python_cache_tag"]=="cpython-312"and
      type(value["pyarrow_version"])is str and value["pyarrow_version"],"source-bound CPython3.12 PyArrow identity")
    root=Path(value["root"]);require(root.is_absolute()and".."not in root.parts,"exact dependency root")
    packages=value["packages"]
    require(type(packages)is list and len(packages)==2 and len(set(packages))==2 and
      "pyarrow"in packages and any(re.fullmatch(r"pyarrow-[a-zA-Z0-9.+-]+\.dist-info",x)for x in packages),
      "only pyarrow and its exact dist-info, not a broad site-packages import")
    require(type(value["files"])is list and value["files"],"complete immutable package files")
    seen=set()
    for r in value["files"]:
        require(type(r)is dict and set(r)=={"path","bytes","sha256"}and type(r["bytes"])is int and r["bytes"]>=0 and
          type(r["sha256"])is str and re.fullmatch("[0-9a-f]{64}",r["sha256"]),"strict full dependency Ref; bool/extra refused")
        p=Path(r["path"]);require(p.is_absolute()and".."not in p.parts and p.is_relative_to(root)and
          p.relative_to(root).parts[0]in packages and str(p)not in seen,"unique exact files inside two packages")
        seen.add(str(p))
    origins=value["expected_origins"]
    require(type(origins)is dict and set(origins)=={"pyarrow","pyarrow.parquet","pyarrow.lib"}and
      all(type(p)is str and p in seen for p in origins.values()),"actual three module origins, no guessed extension path")
    return value
def lock():
    source=C.source();m=json.loads(Path(source["path"]).read_bytes())
    r=m["cpu_input_dependency_lock_ref"];C.checked(r)
    value=validate_lock(json.loads(Path(r["path"]).read_bytes()))
    require(value["root"]==m["cpu_input_dependency_root"],"one manifest-bound dependency root")
    inventory=m["cpu_input_dependency_inventory_ref"];C.checked(inventory)
    tree=json.loads(Path(inventory["path"]).read_bytes())
    require(set(tree)=={"schema","root","files"}and tree["schema"]=="skvq.isolated.pyarrow-files/v1"and
      tree["root"]==value["root"]and sorted(value["files"],key=lambda x:x["path"])==sorted(
      [dict(path=str(Path(tree["root"])/x["relative"]),bytes=x["bytes"],sha256=x["sha256"])for x in tree["files"]],key=lambda x:x["path"]),
      "complete MAIN actual extracted tree, not a reduced or invented dependency lock")
    return value,r,source
def verify_files(value):
    value=validate_lock(value);root=Path(value["root"])
    for q in(root,)+tuple(root.parents):require(not q.is_symlink(),"dependency root symlink refused")
    require(root.is_dir(),"actual isolated dependency root")
    # Only the two declared package trees are mounted/read. Root siblings are
    # neither trusted nor added as mounts; no entire host site-packages exposure.
    actual=[]
    for name in value["packages"]:
        p=root/name;require(p.is_dir()and not p.is_symlink(),"actual readonly package directory")
        for item in sorted(p.rglob("*")):
            require(not item.is_symlink()and(stat.S_ISREG(item.lstat().st_mode)or stat.S_ISDIR(item.lstat().st_mode)),
              "dependency tree ordinary files/directories only")
            if item.is_file():actual.append(ref(item))
    require(sorted(actual,key=lambda x:x["path"])==sorted(value["files"],key=lambda x:x["path"]),
      "entire source package byte closure; missing/extra/changed files rejected")
    return actual
def mounts():
    value,_,_=lock();verify_files(value);root=Path(value["root"])
    return {str(root/name):(str(root/name),False)for name in value["packages"]}
def module_ref(module,value):
    require(type(module).__name__=="module"and getattr(module,"__spec__",None)is not None and
      isinstance(module.__spec__.loader,(importlib.machinery.SourceFileLoader,importlib.machinery.ExtensionFileLoader))and
      getattr(module,"__file__",None)==module.__spec__.origin,"real source/extension module; no stub/cache substitution")
    if module.__name__=="pyarrow.lib":require(isinstance(module.__spec__.loader,importlib.machinery.ExtensionFileLoader),"real PyArrow native extension, not Python stub")
    r=ref(module.__file__);require(r in value["files"],"actual dependency module is source-pinned")
    if module.__name__ in value["expected_origins"]:
        require(r["path"]==value["expected_origins"][module.__name__],"expected actual origin, not another installed pyarrow")
    return r
def install(value):
    verify_files(value)
    require(sys.implementation.cache_tag==value["python_cache_tag"],"actual interpreter ABI, not host wheel reuse by assumption")
    root=value["root"]
    # The same explicit two readonly package trees serve this fresh interpreter
    # and the original builder's fresh child. No PYTHONPATH wildcard or image edit.
    if root not in sys.path:sys.path.insert(0,root)
    pyarrow=importlib.import_module("pyarrow");parquet=importlib.import_module("pyarrow.parquet")
    require(pyarrow.__version__==value["pyarrow_version"],"actual frozen PyArrow version")
    return module_refs(value)
def module_refs(value):
    result={}
    for name,module in sorted(sys.modules.items()):
        if name=="pyarrow"or name.startswith("pyarrow."):result[name]=module_ref(module,value)
    require(set(value["expected_origins"])<=set(result),"all real three module origins executed")
    require("torch"not in sys.modules and"torch_npu"not in sys.modules,"input dependency stage never imports Torch")
    return result
def original_builder():
    C.source()
    manifest=json.loads(Path(C.source()["path"]).read_bytes())
    def load(name,file):
        path=BASE/file;expected=next(r for r in manifest["dependencies"]if r["path"]==str(path))
        C.checked(expected);cached=sys.modules.get(name)
        if cached is not None:
            require(getattr(cached,"__file__",None)is not None and C.reference(cached.__file__)==expected,
              "cached original input source must match full identity");return cached
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module;spec.loader.exec_module(module);require(C.reference(module.__file__)==expected,"original input source byte unchanged")
        return module
    load("io_contract","io_contract.py")
    return load("_skvq_original_input_builder","build_inputs.py")
def consume(value,source,lock_ref,dependency):
    require(type(value)is dict and set(value)=={"schema","status","source_ref","dependency_lock_ref","python_cache_tag","pyarrow_version","actual_modules","first_records","tokenizer_json_ref","builder_ref","NPU_access","Torch_imported","model_ready","full_input_producer_pending"}and value["schema"]=="skvq.actual-input-dependency-probe/v1"and
      value["status"]=="ACTUAL_INPUT_DEPENDENCIES_AND_NINE_FIRST_RECORDS_CHECKED"and
      value["source_ref"]==source and value["dependency_lock_ref"]==lock_ref and value["NPU_access"]is False and
      value["Torch_imported"]is False and value["model_ready"]is False and len(value["first_records"])==9,
      "real same-source CPU dependency preflight, not input/model PASS")
    verify_files(dependency)
    require(value["python_cache_tag"]==dependency["python_cache_tag"]and value["pyarrow_version"]==dependency["pyarrow_version"]and
      set(dependency["expected_origins"])<=set(value["actual_modules"]),"same actual ABI/version/origins")
    for name,r in value["actual_modules"].items():
        require(name=="pyarrow"or name.startswith("pyarrow."),"only actual PyArrow module evidence")
        require(ref(r["path"])==r and r in dependency["files"],"actual entire module bytes remain source-pinned")
        if name in dependency["expected_origins"]:require(r["path"]==dependency["expected_origins"][name],"same exact origin")
    builder=original_builder()
    require(value["builder_ref"]==C.reference(BASE/"build_inputs.py")and
      value["tokenizer_json_ref"]==C.reference(Path(builder.MODEL)/"tokenizer.json")and
      value["tokenizer_json_ref"]["sha256"]==builder.HASHES["tokenizer.json"]and
      value["full_input_producer_pending"]is True,"original builder/tokenizer and no premature full-input authority")
    for row,a in zip(value["first_records"],builder.PLAN["artifacts"]):
        path=str(Path(builder.PLAN["root"])/a["repository"].replace("/","--")/a["revision"]/a["path"])
        require(type(row)is dict and set(row)=={"artifact_path","artifact_sha256","domain","format","row_number","text_sha256","token_ids_sha256","tokens","tokenizer_no_special_tokens","first_record_only"}and
          row["artifact_path"]==path and row["artifact_sha256"]==a["sha256"]and row["domain"]==a["domain"]and row["format"]==a["format"]and
          type(row["row_number"])is int and row["row_number"]>=0 and type(row["tokens"])is int and 0<row["tokens"]<=262144 and
          row["tokenizer_no_special_tokens"]is True and row["first_record_only"]is True and
          all(type(row[k])is str and re.fullmatch("[0-9a-f]{64}",row[k])for k in("text_sha256","token_ids_sha256")),
          "all nine actual first-record provenance, no empty/extra/eval/source substitution")
    return value
def probe():
    require(not list(Path("/dev").glob("davinci*"))and not any(Path("/dev",x).exists()for x in("devmm_svm","hisi_hdc")),
      "real Devices[] dependency stage")
    dependency,lock_ref,source=lock();modules=install(dependency);builder=original_builder()
    artifacts=builder.actual_artifacts()
    from tokenizers import Tokenizer
    tokenizer=Tokenizer.from_file(str(Path(builder.MODEL)/"tokenizer.json"));rows=[]
    for a in artifacts:
        number,row=next(builder.records(a));text=builder.record_text(a,row)
        ids=list(tokenizer.encode(text,add_special_tokens=False).ids)
        require(ids and len(ids)<=262144 and all(type(i)is int and 0<=i<248320 for i in ids),"actual frozen tokenizer first-row vocabulary")
        rows.append(dict(artifact_path=a["artifact_path"],artifact_sha256=a["sha256"],domain=a["domain"],format=a["format"],
          row_number=number,text_sha256=hashlib.sha256(text.encode()).hexdigest(),
          token_ids_sha256=hashlib.sha256(builder.pack_ids(ids)).hexdigest(),tokens=len(ids),
          tokenizer_no_special_tokens=True,first_record_only=True))
    modules=module_refs(dependency)
    result=dict(schema="skvq.actual-input-dependency-probe/v1",status="ACTUAL_INPUT_DEPENDENCIES_AND_NINE_FIRST_RECORDS_CHECKED",
      source_ref=source,dependency_lock_ref=lock_ref,python_cache_tag=sys.implementation.cache_tag,pyarrow_version=dependency["pyarrow_version"],
      actual_modules=modules,first_records=rows,tokenizer_json_ref=C.reference(Path(builder.MODEL)/"tokenizer.json"),
      builder_ref=C.reference(BASE/"build_inputs.py"),NPU_access=False,Torch_imported=False,model_ready=False,
      full_input_producer_pending=True)
    require("torch"not in sys.modules and"torch_npu"not in sys.modules,"no hidden framework import")
    return result
def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,NPU_access=False,model_ready=False)));return
    C.configure(a.source_manifest_sha256);value=probe()
    sys.path.insert(0,str(BASE));from io_contract import publish_json
    print(json.dumps(publish_json(a.output,value),sort_keys=True))
if __name__=="__main__":main()
