"""KIVI matched fixed1024 source contract, no controller or model authority.
Derived from exact SparQ common/service/entry transport; eager is common to BOTH
arms. Importing or printing this definition grants no device/model execution.
"""
import argparse,copy,json,math
PY="/usr/local/python3.12.13/bin/python3"
MODEL_NAME="qwen36-kivi-tp4"
KERNEL_SHA="ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a"
CUTOFF="2026-10-12T07:00:25Z"
PROTOCOL=dict(requests=40,concurrency=16,input_tokens=32768,shared_prefix_tokens=16384,
              output_tokens=1024,temperature=0,seed=0,ignore_eos=True,warmups=2,
              prompt_kind="raw-token-ids-no-chat-template",thinking_mode_enabled=False)
COMPILATION=dict(cudagraph_mode="NONE")
ADDITIONAL=dict(pa_shape_list=list(range(1,17)))
COMMON=dict(tensor_parallel_size=4,data_parallel_size=1,dtype="bfloat16",max_model_len=40960,
    max_num_batched_tokens=40960,max_num_seqs=16,enforce_eager=True,enable_prefix_caching=False,
    mamba_cache_mode="none",enable_chunked_prefill=False,async_scheduling=False,seed=0,
    kv_cache_memory_bytes=10*1024**3,compilation_config=COMPILATION,additional_config=ADDITIONAL)
ALGORITHM_FLAGS=("QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE",
    "QWEN36_KIVI_PACKED_QKAV_OWNED_SEAM","QWEN36_KIVI_PACKED_QKAV_QWEN_INSTALLER",
    "QWEN36_KIVI_OBSERVER_OFF_TIMING","QWEN36_KIVI_ACTUAL_INGRESS_BINDING",
    "QWEN36_KIVI_LAYOUT_DIAGNOSTIC","QWEN36_KIVI_FIELD_GEOMETRY_DIAGNOSTIC")
def require(ok,message):
    if not ok:raise ValueError(message)
def prompt_ids(i):
    require(type(i)is int and 0<=i<40,"fixed40 index")
    return [1000+j%257 for j in range(16384)]+[2000+(i*131+j*17)%4093 for j in range(16384)]
def server_argv(port):
    require(type(port)is int and 1024<port<65536,"MAIN isolated port")
    return [PY,"-m","vllm.entrypoints.openai.api_server","--model","/models/Qwen3.6-27B",
        "--served-model-name",MODEL_NAME,"--tensor-parallel-size","4","--data-parallel-size","1","--dtype","bfloat16",
        "--seed","0","--max-model-len","40960","--max-num-batched-tokens","40960","--max-num-seqs","16",
        "--no-enable-prefix-caching","--mamba-cache-mode","none","--no-enable-chunked-prefill","--no-async-scheduling",
        "--disable-log-stats","--kv-cache-memory-bytes",str(10*1024**3),"--enforce-eager",
        "--compilation-config",json.dumps(COMPILATION,separators=(",",":")),
        "--additional-config",json.dumps(ADDITIONAL,separators=(",",":")),"--host","127.0.0.1","--port",str(port)]
def arm(arm,bits):
    require(arm in("dense","candidate") and type(bits)is int and bits in(2,4),"fixed preregistered algorithm bits")
    return dict(arm=arm,common=copy.deepcopy(COMMON),protocol=copy.deepcopy(PROTOCOL),
        algorithm=dict(name="KIVI-packed3",enabled=arm=="candidate",bits=bits,kernel_sha256=KERNEL_SHA),
        env={key:"1"if arm=="candidate"else"0"for key in ALGORITHM_FLAGS},
        worker_factory_required=arm=="candidate",capture_raw=False,diagnostic=False,first_decode_capture_only=False,
        allocation_replaced=False,metadata_graph=False,run_authority=False,performance_ready=False)
def pair(bits):
    return [arm(label,bits)for label in("dense","candidate")]
def validate_pair(dense,candidate):
    require(dense==arm("dense",dense["algorithm"]["bits"])
            and candidate==arm("candidate",candidate["algorithm"]["bits"])
            and dense["algorithm"]["bits"]==candidate["algorithm"]["bits"],"one exact ON/OFF algorithm delta")
    require(dense["common"]==candidate["common"]==COMMON and dense["protocol"]==candidate["protocol"]==PROTOCOL,
            "same eager/common optimization, original queued HTTP40/C16/1024/2warmups")
    return True
def metrics(dense,candidate):
    for row in(dense,candidate):
        require(set(row)=={"output_tokens_per_second","wall_seconds","mean_ttft_seconds","mean_tpot_seconds"}
                and all(type(v)in(int,float)and math.isfinite(v)and v>0 for v in row.values()),
                "complete positive actual wire metrics")
    ratio=candidate["output_tokens_per_second"]/dense["output_tokens_per_second"]
    return dict(throughput_ratio=ratio,throughput_improvement_percent=(ratio-1)*100,
                dense=dense,candidate=candidate,worth_three_pairs=ratio>=1.10,
                TTFT_and_TPOT_reported_separately=True,three_pairs_verified=False,
                performance_accepted=False,all_request_worker_retirement_verified=False,
                final_stability_verified=False,final_task_accuracy_verified=False,ready=False)
def pending():
    return ["same-source full-model independent numerical and GDN/lifecycle authority",
            "actual mixed native-prefill/packed-decode NPU output and slot reuse validation",
            "frozen timing worker/bootstrap with same model_qualify for producer and installer",
            "existing owned controller/server transport facade bound to KIVI source",
            "original terminal/resource/retirement consumer for both eager arms"]
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--execute",action="store_true");p.add_argument("--entry-contract-only",action="store_true")
    p.add_argument("--bits",type=int,choices=(2,4),default=2);a=p.parse_args(argv)
    # No fake model-ready schema/callback, legacy SparQ permission or new controller.
    require(not a.execute,"KIVI model/full-lifecycle prerequisite is not yet available; no controller/server import or run")
    if a.entry_contract_only:
        arms=pair(a.bits);validate_pair(*arms)
        print(json.dumps(dict(schema="kivi.matched1024-source-contract/v1",arms=arms,
            pending=pending(),cutoff=CUTOFF,model_ready=False,performance_ready=False,run_authority=False)))
    else:print(json.dumps(dict(enabled=False,model_ready=False,performance_ready=False,run_authority=False)))
if __name__=="__main__":main()
