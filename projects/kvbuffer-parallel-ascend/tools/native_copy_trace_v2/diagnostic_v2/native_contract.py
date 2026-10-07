#!/usr/bin/env python3
"""Actual source/build/Meta consumers; no NPU initialization, no legacy PASS wrapper."""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab")
PROJECT=ROOT/"projects/kvbuffer-parallel-ascend"
HERE=PROJECT/"tools/native_copy_trace_v2/diagnostic_v2"
TOOLS=PROJECT/"tools/native_copy_trace_v2"
BUILDER=TOOLS/"build_no_device_v3.py"
BUILDER_SHA="9e3fac5cfd2e5a6281fdfeb3d1a5199cb8bc9678cf0fc55addce4463a86a5a91"
MANIFEST_SHA="ab34453481db93db73acf66461b93e8a2213cde0d0001fbbc80556fdd0c6d5ba"
BUILD=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-copy-trace-v3-20261007-1400")
NS="qwen36_native_recurrent_copy_trace_v2"
REFS={
 "library":{"path":str(BUILD/"build/libqwen36_native_recurrent_copy_trace_v2_ops.so"),"sha256":"70796b3a9ef173e15962401ee893d01a7fbea40018d9879d1d98da3b2afafe65"},
 "build":{"path":str(BUILD/"build-receipt.json"),"sha256":"71b7de2e279897bc4df801a38a3e0305062bc2b27128d86ca91ae9d8a1f35de1"},
 "meta":{"path":str(BUILD/"meta-receipt.json"),"sha256":"e5cfa8e37c2d259b1a0ef5a993b678db18431050e67df89bed7129baffdfcde6"}}
CANDIDATE_RAW=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006/candidate-ub-trace-diagnostic-v2-20261007/diagnostic/trace-eager-raw.pt")
CANDIDATE_RAW_SHA="dc8a899dcc0ac2ef8eea3ae3d4fcf7f233bb09abbf5d5db1890304811ebf564e"
CANDIDATE_REPORT=CANDIDATE_RAW.parent/"report-006.json"
CANDIDATE_REPORT_SHA="c29dea1650bde04d5300c78f8a86fea51064d9cefb434e1d391f00aeb493ead9"
def require(v,s):
    if not v:raise ValueError(s)
def sha(p):
    p=Path(p);require(p.is_file() and not p.is_symlink(),"ordinary actual source/evidence")
    return hashlib.sha256(p.read_bytes()).hexdigest()
def module(p,digest,name):
    require(sha(p)==digest,"actual helper source drift")
    sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp)
    sys.modules[name]=m;sp.loader.exec_module(m);return m
def sources():
    sys.path.insert(0,str(TOOLS))
    b=module(BUILDER,BUILDER_SHA,"_kvbp_native_trace_v3_builder")
    b.EXPECTED_MANIFEST=MANIFEST_SHA
    m,s=b.manifest()
    audit=module(TOOLS/"audit_sources_v3.py",m["files"][str((TOOLS/"audit_sources_v3.py").relative_to(ROOT))],"_native_audit_v3")
    audit.audit()
    return m,s
def consume(refs,m,s):
    require(refs==REFS,"actual independently pinned native Refs")
    for v in refs.values():require(sha(v["path"])==v["sha256"],"actual artifact changed")
    b=json.loads(Path(refs["build"]["path"]).read_bytes())
    meta=json.loads(Path(refs["meta"]["path"]).read_bytes())
    require(b["schema"]=="kvbp.native-recurrent-copy-trace-build/v3" and
            b["status"]=="compiled_no_device" and b["npu_executed"] is False and
            b["namespace"]==NS and b["npu_arch"]=="dav-2201" and b["image_id"]==m["image_id"] and
            b["sources"]==m["operator_sources"] and b["sources_before"]==s and b["sources_after"]==s and
            b["library_sha256"]==refs["library"]["sha256"] and len(b["commands"])==2 and
            all(x["exit_code"]==0 for x in b["commands"]) and
            b["exported_kernel"]=={"name":NS+"_kernel","defined":True,"type":"T"} and
            sha(b["source_archive"]["path"])==b["source_archive"]["sha256"],
            "actual v3 build/export/source archive provenance")
    expected_decode=NS+"::decode_trace(Tensor query, Tensor key, Tensor value, Tensor g, Tensor beta, Tensor(a!) state, Tensor actual_seq_lengths, Tensor state_indices, Tensor(b!) precast_trace, Tensor(c!) selected_state_trace) -> Tensor"
    require(meta["schema"]=="kvbp.native-recurrent-copy-trace-meta/v2" and
            meta["status"]=="actual-load-schema-meta-only" and meta["library"]==refs["library"] and
            meta["positive_cases"]==3 and len(meta["negative_cases"])==22 and
            {(x["argument"],x["label"]) for x in meta["negative_cases"]}==
                {(i,label) for i in range(10) for label in ("dtype","shape")}|{(0,"noncontiguous query"),(8,"noncontiguous trace")} and
            meta["schemas_loaded"]=={"prepare":NS+"::prepare(Tensor query, Tensor state) -> ()",
              "tiling_info":NS+"::tiling_info(Tensor query, Tensor state) -> Tensor","decode_trace":expected_decode} and
            meta["npu_executed"] is False and meta["numeric_verified"] is False and meta["serving_ready"] is False and
            meta["mapped_library_lines"] and not any("(deleted)" in line for line in meta["mapped_library_lines"]),
            "actual load/schema/3+22 Meta provenance, not numerical proof")
    require(sha(CANDIDATE_RAW)==CANDIDATE_RAW_SHA and sha(CANDIDATE_REPORT)==CANDIDATE_REPORT_SHA,
            "immutable already-anchored actual candidate UB evidence")
    report=json.loads(CANDIDATE_REPORT.read_bytes())
    require(report["status"]=="anchored-copy-only-trace-diagnostic" and
            report["native_precast_observed"] is False and report["matrix_verified"] is False and
            len(report["cases"])==2 and all(all(c["non_interference"].values()) and
                all(c["trace_checks"].values()) and c["updated_ub_equals_actual_flush_base"] for c in report["cases"]),
            "real candidate trace anchors, not invented same-state input")
    return b,meta
