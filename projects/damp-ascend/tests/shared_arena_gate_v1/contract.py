"""Stdlib source/mapping/byte-layout contract for the NEW shared-arena gate."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[1]
REPO = PROJECT.parents[1]
OLD = PROJECT / "operator/production_integer_compaction_v1"
WRAPPER = PROJECT / "operator/arena_wrapper_v2"
NAMESPACE = "qwen36_damp_arena_v2"
LIBRARY = "libqwen36_gdn_damp_arena_v2_decode_ops.so"
KERNEL = "qwen36_gdn_damp_arena_v2_decode_kernel"
SOURCE_SHA = "c05354c54175bcaa15c1637ff335febcc2500b0c0489e37db5354d65d4a5001f"
IMAGE = "sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
OPP_SHA = "841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6"
LIMITS = {"state": 1e-5, "output": 0.00303}
BATCH_PHYSICAL = {1: 4, 16: 7}
LAYOUTS = ("adjacent", "guard_gaps")
OWN_NAMES = ("contract.py", "arena_adapter.py", "run_shared_arena_gate.py",
             "test_software_contract.py", "README.md")
PINNED = {
 "projects/damp-ascend/operator/production_integer_compaction_v1/tests/gate_contract.py": "b49b8113b77f2318d434fbca5beedbcc23b5a186b291e479c2cf1bd428b217a0",
 "projects/damp-ascend/operator/production_integer_compaction_v1/tests/candidate_adapter.py": "43d4639d1ac0d737392fab8526aba14af0b1e50161a1940855b71822b18e6a7c",
 "projects/damp-ascend/operator/production_integer_compaction_v1/tests/protocols.py": "7a0747c8c1a1f246f32ec3ad32ab53cd7a5027339a5c8584d5552ae1508f7340",
 "projects/damp-ascend/operator/production_integer_compaction_v1/tests/run_npu_gate.py": "9d2ff5e8eed33c5ec3719dcee2748908924c8ce7151a2e3d2b4d582d285c1c1c",
 "projects/damp-ascend/operator/production_integer_compaction_v1/graph_gate_v1/graph_contract.py": "b31984a9c0a074812bd859b75316188475c445848832478974c543aa733727f6",
 "projects/damp-ascend/operator/production_integer_compaction_v1/graph_gate_v1/graph_protocol.py": "35df04f1f8453a9c68f728cce65d4d4821906204fd74502a0cf900bab4e8b4ca",
 "projects/damp-ascend/tests/restricted_native_golden_gate.py": "f8b04cc7650cf2cc330a526cb261ffd85062454e56e1a9692b5913c18445a6b4",
 "projects/damp-ascend/tests/general_sr_native_gate.py": "7eed726fd46e2e39c6bdd560fb769742d32d68861efb075fbca9647f976b4155",
 "projects/damp-ascend/tests/general_sr_contract.py": "6606bd18e1c29d50a063ba0742b8fb7b8b8d5a8f6e12a6f4a755004d74bfc2ad",
 "projects/damp-ascend/tests/native_compressed_golden.py": "95d11c42bea88daa14dbb2ce462e16a7d1864b3f2169faf360942fb0c16bea19",
 "projects/damp-ascend/tests/native_call_contract.py": "162dba2a653b7c1fabd20eb24bc75d99225584ca48c4bd10c89eece5bc2fc1d5",
 "projects/damp-ascend/tests/independent_oracle.py": "fc92395d65db63810ff70341dca255f7f4455d80f0fccbe80f48ff3bb679625a",
 "projects/damp-ascend/operator/diagnostic/run_saved_step45_trace.py": "64cc9ee98a6354d16a49fa90f9c16170d9852c080cf576fad03e3183b4eb0b9a",
}
REGION_SPECS = (
    ("conv", 2, (3, 2560)),
    ("high", 2, (12, 128, 16)),
    ("low", 1, (12, 128, 112)),
    ("scales", 4, (12, 4, 112)),
)
UINTPTR_MAX = 2**64-1

def require(ok, reason):
    if not ok: raise ValueError(reason)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

def checked(path, digest):
    path = Path(path)
    require(path.is_absolute() and path.is_file(), "absolute existing source/receipt required")
    require(isinstance(digest,str) and len(digest)==64 and
            all(c in "0123456789abcdef" for c in digest), "lowercase SHA256 required")
    require(sha(path)==digest, "identity changed: "+str(path))
    return path.resolve()

def product(shape):
    result=1
    for dimension in shape:
        require(type(dimension) is int and dimension>0,"positive dimensions")
        result*=dimension
    return result

def layout(slots, kind):
    require(type(slots) is int and slots in (4,19),"only B1/B16 plus3 slots")
    require(kind in LAYOUTS,"unknown arena layout")
    # Guarded nonzero outer offset. Adjacent mirrors allocator's advancing SoA.
    cursor=96
    regions={}
    gaps=(0,0,0,0) if kind=="adjacent" else (32,64,96,32)
    for (name,width,shape),gap in zip(REGION_SPECS,gaps):
        cursor+=gap
        size=slots*product(shape)*width
        regions[name]={"offset":cursor,"bytes":size,"dtype_bytes":width,
                       "shape":(slots,)+shape}
        cursor+=size
    return {"kind":kind,"slots":slots,"prefix":96,"regions":regions,
            "total_bytes":cursor+128}

def span(pointer, count, width, base, storage_bytes, offset_elements):
    for value in (pointer,count,width,base,storage_bytes,offset_elements):
        require(type(value) is int,"integer span field")
    require(base>0 and pointer>0 and count>0 and width>0 and storage_bytes>0 and offset_elements>=0,
            "nonempty positive backing/view")
    require(pointer%32==0,"actual data pointer alignment")
    require(base<=UINTPTR_MAX and storage_bytes<=UINTPTR_MAX-base,"backing addition overflow")
    require(count<=UINTPTR_MAX//width and offset_elements<=UINTPTR_MAX//width,"view multiply overflow")
    offset=offset_elements*width
    require(offset<storage_bytes and pointer==base+offset,"typed pointer/storage_offset mismatch")
    size=count*width
    require(size<=base+storage_bytes-pointer,"view out of backing bounds")
    return pointer,pointer+size

def disjoint(a,b):
    return a[1]<=b[0] or b[1]<=a[0]

def protected_ranges(spec):
    result=[];cursor=0
    for name in ("high","low","scales"):
        region=spec["regions"][name]
        if cursor<region["offset"]: result.append((cursor,region["offset"]))
        cursor=region["offset"]+region["bytes"]
    if cursor<spec["total_bytes"]:result.append((cursor,spec["total_bytes"]))
    return result

def validate_device(proof, batch, now_ns):
    physical=BATCH_PHYSICAL[batch]
    require(proof.get("physical_npu_ids")==[physical] and
            proof.get("logical_to_physical")=={"0":physical},"batch shard physical mapping mismatch")
    require(proof.get("privileged") is False and proof.get("exclusive_resource_check_passed") is True,
            "fresh nonprivileged exclusive-resource authority required")
    when=proof.get("observed_at_unix_ns")
    require(type(when) is int and 0<=now_ns-when<=1800*10**9,"fresh <=30min nonfuture device proof")
    return True

def runtime_names():
    return set(PINNED)|{str((BASE/n).relative_to(REPO)) for n in OWN_NAMES}

def source_bindings(args):
    runtime_file=checked(args.runtime_manifest,args.runtime_manifest_sha256)
    require(runtime_file==(BASE/"runtime_manifest.json").resolve(),"exact new runtime manifest path")
    runtime=json.loads(runtime_file.read_text())
    require(runtime.get("schema")=="damp_shared_arena_gate_runtime_v1" and
            set(runtime.get("sources",{}))==runtime_names(),"exact new runtime+frozen protocols required")
    for name,digest in runtime["sources"].items():
        path=(REPO/name).resolve()
        require(REPO in path.parents and sha(path)==digest,"runtime/source changed "+name)
    require(all(runtime["sources"][n]==h for n,h in PINNED.items()),"frozen independent protocols drift")
    source=checked(args.source_manifest,args.source_manifest_sha256)
    require(source==(WRAPPER/"source_manifest.json").resolve() and sha(source)==SOURCE_SHA,"exact arena wrapper source manifest")
    manifest=json.loads(source.read_text())
    require(manifest.get("schema")=="damp_arena_wrapper_sources_v2" and
            manifest.get("namespace")==NAMESPACE and manifest.get("target_kernel")==KERNEL and
            manifest.get("target_library")==LIBRARY,"explicit v2 wrapper required")
    compiled=manifest["compiled_sources"]
    require(len(compiled)==9,"five new wrapper sources plus four frozen numerical headers")
    for name,digest in compiled.items():
        path=(REPO/name).resolve()
        require(REPO in path.parents and sha(path)==digest,"compiled source changed "+name)
    library=checked(args.library,args.library_sha256)
    require(library.name==LIBRARY,"wrong shared-arena candidate SO")
    receipt_path=checked(args.build_receipt,args.build_receipt_sha256)
    receipt=json.loads(receipt_path.read_text())
    require(receipt.get("schema")=="damp_arena_wrapper_build_v2" and
            receipt.get("status")=="compiled_no_device" and receipt.get("npu_executed") is False and
            receipt.get("namespace")==NAMESPACE and receipt.get("sources")==compiled and
            receipt.get("source_manifest_sha256")==SOURCE_SHA and
            receipt.get("library_sha256")==args.library_sha256 and receipt.get("image_id")==IMAGE,
            "actual successful v2 compile receipt/source/library/image binding")
    require(receipt.get("npu_arch")=="dav-2201","actual target architecture")
    commands=receipt.get("commands")
    require(isinstance(commands,list) and len(commands)>=2 and
            all(c.get("exit_code")==0 and c.get("command") and
                isinstance(c.get("log_sha256"),str) and len(c["log_sha256"])==64 for c in commands),
            "actual configure/build commands and immutable logs")
    for command in commands:
        if command.get("log_path"):checked(command["log_path"],command["log_sha256"])
    symbol=receipt.get("exported_kernel",{})
    require(symbol.get("name")==KERNEL and symbol.get("defined") is True and
            symbol.get("type") in ("T","W"),"actual defined kernel export, not UND")
    checked(symbol["audit_path"],symbol["audit_sha256"])
    identity=receipt.get("cann_identity",{})
    require(identity.get("root")=="/usr/local/Ascend/cann-9.1.0" and
            identity.get("opp_version_info_sha256")==OPP_SHA and
            receipt.get("cann_version_info_sha256")==OPP_SHA and
            "Version=9.1.0" in identity.get("version_info","").splitlines(),"actual OPP9.1 source identity")
    return {"compiled_sources":compiled,"runtime_sources":runtime["sources"],
            "source_manifest_sha256":sha(source),"runtime_manifest_sha256":sha(runtime_file),
            "build_receipt":receipt,"build_receipt_path":str(receipt_path),
            "build_receipt_sha256":sha(receipt_path),"library":str(library),"library_sha256":sha(library)}

def new_output(path):
    path=Path(path).resolve()
    require(path.is_absolute() and not path.exists() and path!=REPO and REPO not in path.parents,
            "nonexistent external output root; no overwrite")
    path.mkdir(parents=False,exist_ok=False)
    return path
