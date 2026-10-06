"""MAIN-executed inside-container launcher. Preparation does not launch it."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from contract import (COMMON, COMPLETION_SOURCES, IMAGE, LIBRARY_SHA, PLUGIN_SHA, budget, require, sha,
                      validate_identity, validate_native_gate, write_new)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--arm", choices=("dense","candidate"), required=True)
    p.add_argument("--identity", type=Path, required=True)
    p.add_argument("--native-gate", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--model", type=Path, default=Path("/models/Qwen3.6-27B"))
    p.add_argument("--library", type=Path, default=Path("/kvbuffer-results/build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so"))
    p.add_argument("--prepare-only", action="store_true",
                   help="NO-model config/source/argv check inside exact image; exits before exec")
    a=p.parse_args()
    root=a.output_dir.resolve()
    require(Path("/kvbuffer-results") in root.parents and not root.exists(), "new arm dir outside/freshness guard")
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3", "parent-mapped logical0..3 only")
    gate=json.loads(a.native_gate.read_text()); validate_native_gate(gate)
    ident=json.loads(a.identity.read_text()); validate_identity(ident,sha(a.native_gate),a.arm,a.port)
    project=Path(__file__).resolve().parents[2]
    require(sha(project/"plugin/kvbuffer_parallel/patch.py") == PLUGIN_SHA and
            sha(a.library) == LIBRARY_SHA, "frozen plugin/library changed")
    sys.path.insert(0,str(project/"plugin"))
    from kvbuffer_parallel.contract import source_identity, MODEL_CONFIG
    require(sha(a.model/"config.json") == MODEL_CONFIG, "checkpoint config identity changed")
    sources=source_identity()
    require({p:sha(p) for p in COMPLETION_SOURCES} == COMPLETION_SOURCES,
            "token-ID/usage streaming source identity changed")
    root.mkdir(parents=True,exist_ok=False)
    env=os.environ
    existing=env.get("PYTHONPATH","")
    env["PYTHONPATH"]=str(project/"plugin")+":"+str(Path(__file__).parent)+(":"+existing if existing else "")
    env["VLLM_PLUGINS"]="ascend,ascend_kv_connector,ascend_model,ascend_model_loader,kvbuffer_parallel,kvbuffer_service"
    env["VLLM_USE_V1"]="1"; env["VLLM_WORKER_MULTIPROC_METHOD"]="spawn"
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env["QWEN36_KVBP_ENABLE"]="1" if a.arm=="candidate" else "0"
    env["QWEN36_KVBP_LIBRARY"]=str(a.library); env["QWEN36_KVBP_LIBRARY_SHA256"]=LIBRARY_SHA
    env["QWEN36_KVBP_MODEL_CONFIG"]=str(a.model/"config.json")
    env["QWEN36_KVBP_AUDIT"]=str(root/"candidate-evidence.jsonl")
    env["QWEN36_KVBP_AUX_BUDGET_BYTES"]=str(budget(a.arm)["auxiliary_reserved_bytes"])
    env["QWEN36_KVBP_TOTAL_BUDGET_BYTES"]=str(budget(a.arm)["common_total_bytes"])
    env["KVBP_SERVICE_EVIDENCE"]="1";env["KVBP_SERVICE_ARM"]=a.arm
    env["KVBP_SERVICE_OUTPUT"]=str(root)
    argv=[sys.executable,"-m","vllm.entrypoints.openai.api_server","--model",str(a.model),
          "--served-model-name","qwen36-kvbp-p1","--tensor-parallel-size","4",
          "--data-parallel-size","1","--dtype","bfloat16","--seed","0",
          "--max-model-len","40960","--max-num-batched-tokens","40960","--max-num-seqs","16",
          "--no-enable-prefix-caching","--mamba-cache-mode","none","--no-enable-chunked-prefill",
          "--enforce-eager","--disable-log-stats","--kv-cache-memory-bytes",str(budget(a.arm)["native_bytes"]),
          "--host","127.0.0.1","--port",str(a.port)]
    manifest=dict(schema="kvbp.service-arm/v1", arm=a.arm, common=COMMON, image_id=IMAGE,
                  model_config_sha256=MODEL_CONFIG, native_gate_sha256=sha(a.native_gate),
                  library_sha256=LIBRARY_SHA, plugin_sha256=PLUGIN_SHA, sources=sources,
                  identity_sha256=sha(a.identity), budget=budget(a.arm), argv=argv,
                  completion_sources=COMPLETION_SOURCES,
                  service_sources={str(p.relative_to(Path(__file__).parent)):sha(p)
                                   for p in Path(__file__).parent.rglob("*") if p.is_file()},
                  common_runtime_env={k:env.get(k) for k in (
                      "VLLM_USE_V1","VLLM_PLUGINS","VLLM_WORKER_MULTIPROC_METHOD",
                      "ASCEND_RT_VISIBLE_DEVICES","ASCEND_LAUNCH_BLOCKING",
                      "VLLM_ASCEND_ENABLE_FLASHCOMM1","VLLM_ASCEND_ENABLE_FLASHCOMM2",
                      "VLLM_ASCEND_ENABLE_MATMUL_ALLREDUCE","HCCL_OP_BASE_FFTS_MODE",
                      "PYTHONPATH","LD_LIBRARY_PATH")},
                  evidence_scope="same-eager-prefix-off-P1-screen-not-final-acceptance",
                  evidence_observer="same-metadata-runner-wrapper-both-arms-no-NPU-read-or-sync",
                  prepare_only=a.prepare_only)
    write_new(root/"ARM.json",manifest)
    if a.prepare_only:
        print(json.dumps(manifest,sort_keys=True));return
    os.execv(sys.executable,argv)

if __name__=="__main__":main()
