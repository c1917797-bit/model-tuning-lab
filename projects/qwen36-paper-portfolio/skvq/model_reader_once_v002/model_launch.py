"""Actual same-image LLM+named RPC once, never host admission or performance grant."""
import argparse,json,os,sys,time,traceback
from pathlib import Path
import bridge_contract as B
from model_options import kwargs
import model_extension as E
LLM_SHA="fd28c3f53740d196689ac97ca566bd23879d082b3e9c7eb9ca20f0a88caf6e7e"
def run(expected,reader_ref,prompt_ref,admission_ref,output):
    C,source,m=B.source(expected);whole=C.reader_whole(reader_ref);prompt=B.prompt(C,prompt_ref);admission=C.obj(admission_ref)
    B.need(os.environ.get("MAIN_SKVQ_COMPILED_READER_MODEL_ENABLE")=="1"and
      os.environ.get("MAIN_OWNED_CID")==admission["cid"]and os.environ.get("ASCEND_RT_VISIBLE_DEVICES")=="0,1,2,3",
      "MAIN owned all4 explicit opt-in")
    root=Path(output)
    B.need(root.is_absolute()and root.parent.is_dir()and not root.exists(),"absent model producer child within actual owned RW mount")
    B.need(admission["schema"]=="skvq.model-reader.admission/v1"and admission["source_ref"]==source and
      admission["reader_whole_ref"]==reader_ref and admission["prompt_ref"]==prompt_ref and
      admission["physical_cards"]==[4,5,6,7]and admission["logical_devices"]==[0,1,2,3]and
      admission["guest_memory_bytes"]==64*2**30 and admission["host_memory_bytes"]==512*2**20 and
      admission["ordinary_reserve_bytes"]==8*2**30 and admission["joint_cpu_budget"]==7 and
      admission["portfolio_cutoff_epoch"]==B.CUT and
      type(admission["total_seconds"])is int and 600<=admission["total_seconds"]<=5400 and
      time.time()+admission["total_seconds"]<=B.CUT and
      0<=time.time()-admission["observed_epoch"]<=60 and admission["output_root"]==str(root),
      "actual fresh pre-create budget/source/data admission, not flags")
    for key in("n1_ref","resource_ref","owned_ref","source_gate_ref","clock_ref"):C.obj(admission[key])
    n1=C.obj(admission["n1_ref"])
    B.need(n1["schema"]=="skvq.model-reader.N1/v1"and n1["source_ref"]==source and
      n1["full_engine_configuration_checked"]is True and len(n1["rank_refs"])==4,"actual beforeweights all4/config prerequisites")
    root.mkdir();C.atomic(root/"RAW_BEFORE_LLM.json",dict(source_ref=source,reader_whole_ref=reader_ref,prompt_ref=prompt_ref,
      admission_ref=admission_ref,identity=__import__("numeric").identity(),kwargs=kwargs(),**B.false_scopes()))
    from model_startup import parent
    startup_ref=parent(C,source,root)
    llm=None;primary=None;restored=[];installs=[];finals=[];status=[];output_ref=None;began=time.monotonic()
    try:
        from vllm.entrypoints.llm import LLM
        from vllm import SamplingParams
        B.need(C.ref(sys.modules["vllm.entrypoints.llm"].__file__)["sha256"]==LLM_SHA,"actual unchanged LLM class")
        llm=LLM(**kwargs())
        reader_file=root/"READER_REF.json";prompt_file=root/"PROMPT_REF.json"
        C.atomic(reader_file,reader_ref);C.atomic(prompt_file,prompt_ref)
        installs=llm.collective_rpc(E.METHODS[0],timeout=120,args=(str(reader_file),str(prompt_file),str(root),source["sha256"]))
        B.need(len(installs)==4 and {x["rank"]for x in installs}==set(range(4)),"all4 actual same worker installs")
        C.atomic(root/"INSTALL_RESULTS.json",installs)
        params=SamplingParams(temperature=0,max_tokens=3,min_tokens=3,ignore_eos=True)
        outputs=llm.generate([dict(prompt_token_ids=prompt["token_ids"])],params,use_tqdm=False)
        B.need(len(outputs)==1 and outputs[0].finished and outputs[0].prompt_token_ids==prompt["token_ids"]and
          len(outputs[0].outputs)==1 and len(outputs[0].outputs[0].token_ids)==3,"true32768+3 outputs, two actual decode calls")
        output_ref=C.atomic(root/"REAL_REQUEST_OUTPUT.json",dict(request_id=outputs[0].request_id,
          prompt_ref=prompt_ref,prompt_tokens=32768,output_token_ids=list(outputs[0].outputs[0].token_ids),
          finished=True,requested_output_tokens=3,native_finish_still_required=True))
        # The actual independent EngineCore dispatches its pending finished set.
        # Poll only the real worker status; do not inject a dummy request/tick.
        finish_end=time.monotonic()+45;status_samples=[]
        while True:
            status=llm.collective_rpc(E.METHODS[1],timeout=30)
            status_samples.append(C.atomic(root/("NATIVE_STATUS-%d.json"%len(status_samples)),status))
            B.need(len(status)==4 and {x["rank"]for x in status}==set(range(4))and
              all(x["poisoned"]is False for x in status),"all4 actual native status/first fault")
            if all(x["native_finished_ref"]is not None for x in status):break
            B.need(time.monotonic()<finish_end,"actual native finished dispatch still pending; not HTTP DONE")
            time.sleep(.1)
        B.need(len(status)==4 and {x["rank"]for x in status}==set(range(4))and
          all(x["actual_native_prefill_calls"]==16 and x["actual_compiled_decode_calls"]==32 and
            x["native_finished_ref"]is not None and x["poisoned"]is False for x in status),
          "all4 nativeprefill/two real packeddecode and actual native finish; DONE never substitutes")
        finals=llm.collective_rpc(E.METHODS[2],timeout=120)
        B.need(len(finals)==4 and {x["rank"]for x in finals}==set(range(4)),"all4 actual restored FINAL receipts")
    except BaseException as e:primary=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    finally:
        if llm is not None:
            try:restored=llm.collective_rpc(E.METHODS[3],timeout=60)
            except BaseException as e:restored=[dict(error=repr(e),actual_restore_failed=True)]
        value=dict(schema="skvq.model-reader.producer/v1",
          status="ACTUAL_ALL4_FIRST_TWO_DECODE_RAW_PENDING_OWNED_RELEASE"if primary is None else"FAILED",
          source_ref=source,reader_source_ref=B.READER,reader_whole_ref=reader_ref,writer_whole_ref=whole["writer_whole_ref"],
          prompt_ref=prompt_ref,admission_ref=admission_ref,startup_ref=startup_ref,installs=installs,status_results=status,
          finals=finals,restore_results=restored,native_status_refs=locals().get("status_samples",[]),actual_request_output_ref=output_ref,primary=primary,
          elapsed_seconds=time.monotonic()-began,actual_prompt_tokens=32768,requested_output_tokens=3,
          actual_native_decode_steps=2,GDN48_function_identity_only_not_numerical=True,
          native_dense_cache_and_prefill_retained=True,formal_performance_unmeasured=True,**B.false_scopes())
        row=C.atomic(root/"PRODUCER_RESULT.json",value)
    B.need(primary is None and len(restored)==4 and all(x.get("restored")is True for x in restored),
      "actual producer/restore failure retained, not model qualification")
    return row
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--reader-whole-ref-json");p.add_argument("--prompt-ref-json");p.add_argument("--admission-ref-json");p.add_argument("--output")
    a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**B.false_scopes())));return
    C,source,m=B.source(a.source_manifest_sha256)
    refs=[json.loads(Path(v).read_bytes())for v in(a.reader_whole_ref_json,a.prompt_ref_json,a.admission_ref_json)]
    print(json.dumps(run(a.source_manifest_sha256,*refs,a.output),sort_keys=True))
if __name__=="__main__":main()
