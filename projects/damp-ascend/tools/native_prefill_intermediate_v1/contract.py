"""Source-only admission for the NEW true-P intermediate native gate."""
from pathlib import Path
import hashlib
import json
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
PROJECT=REPO/"projects/damp-ascend"
LEGACY=PROJECT/"operator/prefill_pack_v1/selected_slot_v1/gate_v1"
LEGACY_RUNTIME_SHA="7ea60a45ea46f28811c16455885eab46dbd78bce5586a8914f06a701dbcd4ed1"
ANCHOR_SHA="d4d71a45ae75c36a6ed9f5dc02c23272a1fef44e18f0a62226b4fcb3b35423d8"
REFERENCE_SO_SHA="853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8"
BUILDER="/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py"
BUILDER_SHA="42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16"
BUILDER_SNAPSHOT=Path("/cache/cch/qwen36-damp-20261006/runtime-native-builder-snapshot-v1/gdn_attn_builder.py")
BUILDER_MANIFEST=BUILDER_SNAPSHOT.parent/"MANIFEST.json"
BUILDER_MANIFEST_SHA="b05d03335c10dfb3b0e7ed5f8b691ac0e95529d424cac39f85c1d31b1d710b46"
CUTOFF_NS=1791362883000000000
SHARDS={"P2-8":tuple(range(2,9)),"P9-15":tuple(range(9,16))}

def require(ok,message):
    if not ok: raise RuntimeError(message)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def bound(path,digest):
    require(isinstance(digest,str) and len(digest)==64 and
            all(x in "0123456789abcdef" for x in digest),"explicit SHA256 required")
    require(sha(path)==digest,"SHA mismatch: "+str(path))
    return json.loads(Path(path).read_text())

def deadline(now_ns=None):
    now_ns=time.time_ns() if now_ns is None else now_ns
    require(type(now_ns) is int and now_ns<CUTOFF_NS,"original DAMP deadline; no extension")

def matrix(shard):
    require(shard in SHARDS,"explicit complete P2-8 or P9-15 shard")
    return SHARDS[shard]

def counts(shard):
    ps=matrix(shard);total=sum(ps)
    return {"native_cases":len(ps)*4,"decode_turns":len(ps)*4*160,
            "row_reference_calls":total*4*160,
            "native_fraction_decisions":total*4*12*128*128,
            "anchor_full_reference_calls":1,"anchor_row_reference_calls":16}

def source_check(packet_sha=None):
    packet_path=HERE/"PACKET.json"
    packet=bound(packet_path,packet_sha) if packet_sha else json.loads(packet_path.read_text())
    require(packet.get("schema")=="damp-native-prefill-intermediate-packet/v1" and
            packet.get("default_enabled") is False,"NEW packet identity/default OFF")
    for path,digest in packet["sources"].items():
        require(sha(REPO/path)==digest,"NEW source drift: "+path)
    legacy=bound(LEGACY/"RUNTIME_MANIFEST.json",LEGACY_RUNTIME_SHA)
    for group in ("sources","dependencies"):
        for path,digest in legacy[group].items():
            require(sha(REPO/path)==digest,"frozen dependency drift: "+path)
    builder=bound(BUILDER_MANIFEST,BUILDER_MANIFEST_SHA)
    require(builder.get("schema")=="damp-actual-image-builder-source/v1" and
            builder.get("source_path")==BUILDER and builder.get("host_snapshot_path")==str(BUILDER_SNAPSHOT) and
            builder.get("sha256")==BUILDER_SHA and builder.get("bytes")==40595 and
            builder.get("container_started") is False and builder.get("npu_executed") is False and
            sha(BUILDER_SNAPSHOT)==BUILDER_SHA,"actual readonly builder snapshot identity")
    return packet,legacy

def admission(args):
    deadline()
    require(args.packet_sha256 is not None,"external NEW packet authority")
    packet,runtime=source_check(args.packet_sha256)
    require(args.legacy_runtime_manifest_sha256==LEGACY_RUNTIME_SHA,"frozen legacy runtime authority")
    matrix(args.shard)
    names=("preflight","build_receipt","library","out","decode_build_receipt",
           "decode_library","decode_library_sha256","native_anchor_report",
           "reference_library","reference_library_sha256","builder_snapshot","builder_sha256")
    require(all(getattr(args,n) is not None for n in names),"all explicit source/build/native/proof authorities")
    import sys
    sys.path.insert(0,str(LEGACY))
    import selected_contract as old
    source=old.bound_json(LEGACY.parent/"source_manifest.json",old.SELECTED_MANIFEST_SHA)
    require(source["compiled_sources"]==old.COMPILED,"actual selected compiled closure")
    build=old.validate_build(old.bound_json(args.build_receipt,old.SELECTED_BUILD_SHA))
    require(args.library.name=="libqwen36_damp_selected_prefill_v1_ops.so" and
            sha(args.library)==old.SELECTED_SO_SHA,"actual selected SO")
    decode=old.bound_json(args.decode_build_receipt,old.ALL_BATCH_BUILD_SHA)
    decode_manifest=old.bound_json(PROJECT/"operator/all_batch_wrapper_v3/source_manifest.json",
                                  old.ALL_BATCH_MANIFEST_SHA)
    old.require_decode_admission(decode,decode_manifest,args.decode_library_sha256)
    require(args.decode_library.name=="libqwen36_gdn_damp_all_batch_v3_decode_ops.so" and
            sha(args.decode_library)==old.ALL_BATCH_SO_SHA,"actual allbatch SO")
    for receipt in (build,decode):
        for row in receipt["commands"]:
            require(sha(row["log_path"])==row["log_sha256"],"actual build command log")
        symbol=receipt["exported_kernel"]
        require(sha(symbol["audit_path"])==symbol["audit_sha256"],"actual export audit")
    require(sha(build["cann_identity"]["opp_version_info_path"])==old.OPP_SHA,"actual OPP bytes")
    anchor=old.bound_json(args.native_anchor_report,ANCHOR_SHA)
    native=old.validate_anchor(anchor)
    require(args.reference_library_sha256==REFERENCE_SO_SHA and
            native["reference_library_sha256"]==REFERENCE_SO_SHA and
            sha(args.reference_library)==REFERENCE_SO_SHA,"original native-anchored reference")
    require(sha(native["native_runtime_library_path"])==native["native_runtime_library_sha256"],
            "actual original native library")
    for path,digest in runtime["actual_image_sources"].items():
        require(sha(path)==digest,"actual-image source drift: "+path)
    require(args.builder_snapshot==BUILDER_SNAPSHOT and args.builder_sha256==BUILDER_SHA and
            sha(args.builder_snapshot)==BUILDER_SHA and sha(BUILDER)==BUILDER_SHA,"actual-image builder and readonly snapshot exact bytes")
    proof=json.loads(args.preflight.read_text())
    old.validate_proof(proof,args.physical_card)
    root=args.out.resolve()
    require(args.out.is_absolute() and root!=REPO and REPO not in root.parents and
            str(root)!="/" and not root.exists(),"new external non-overwriting output")
    return {"packet_sha256":sha(HERE/"PACKET.json"),"legacy_runtime_sha256":LEGACY_RUNTIME_SHA,
            "sources":packet["sources"],"legacy_sources":runtime["sources"],
            "legacy_dependencies":runtime["dependencies"],"actual_image_sources":runtime["actual_image_sources"],
            "native":native,"selected_library_sha256":old.SELECTED_SO_SHA,
            "decode_library_sha256":old.ALL_BATCH_SO_SHA,"reference_library_sha256":REFERENCE_SO_SHA,
            "builder":{"actual_path":BUILDER,"snapshot_path":str(args.builder_snapshot),
                       "sha256":args.builder_sha256,"manifest_sha256":BUILDER_MANIFEST_SHA},"device_proof":proof,
            "image_id":old.IMAGE,"limits":old.LIMITS,"counts":counts(args.shard)}

def after_check(args,binding):
    source_check(args.packet_sha256)
    for path,digest in binding["actual_image_sources"].items():
        require(sha(path)==digest,"end actual-image source drift")
    require(sha(BUILDER)==binding["builder"]["sha256"] and
            sha(args.builder_snapshot)==binding["builder"]["sha256"],"end builder source drift")
