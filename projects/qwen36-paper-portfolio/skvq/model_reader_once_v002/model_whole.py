"""Independent actual terminal/Owned/all4 activation+128-frame math consumer.
No Torch, model execution or authority from a fixture. This is only B1 eager FA
numeric smoke: GDN content, complete176, graph, matched1024 and tasks remain pending.
"""
import argparse,copy,json,re
from pathlib import Path
import bridge_contract as B
import model_host as H
def host_argv(source,root,reader_file):
    return ["/usr/bin/env","MAIN_SKVQ_MODEL_READER_HOST_ENABLE=1",H.PRLIMIT,"--cpu=9000:9000","--",
      "/usr/bin/python3","-B",str(B.ROOT/"model_host.py"),"--execute","--source-manifest-sha256",
      source["sha256"],"--reader-whole-ref-json",str(reader_file),"--output",str(root)]
def child(C,row,cid,args,npu):
    value=C.obj(row);argv=[H.DOCKER,"exec"]
    if npu:argv.extend(("--env","MAIN_OWNED_CID="+cid))
    argv.extend((cid,"/bin/bash","-c",'source /usr/local/Ascend/cann-9.1.0/set_env.sh && exec "$@"',"skvq-owned",H.PY,"-B",*args))
    B.need(value["argv"]==argv and value["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
      value["exit_code"]==0 and value["terminated"]is True and value["primary"]is None,"actual successful exact child command")
    C.read(value["stderr"]);C.read(value["stdout"]);return value
def check_owned(C,e,index,source,root,mounts,Controller):
    npu=index==1;phase=("model-cpu","model-tp4","model-independent")[index];expected=dict(mounts)
    if npu:expected["/usr/local/Ascend/driver"]=("/usr/local/Ascend/driver",False)
    actual={d:(s,bool(rw))for d,(s,rw)in e["mounts"].items()}
    devices=({"/dev/davinci"+str(i):"/dev/davinci"+str(i-4)for i in range(4,8)}|
      {"/dev/"+n:"/dev/"+n for n in("davinci_manager","devmm_svm","hisi_hdc")})if npu else{}
    B.need(e["phase"]==phase and e["npu"]is npu and e["devices"]==devices and actual==expected and
      e["mem"]==(64 if npu else 8)*H.GIB and e["source"]==source["sha256"]and e["env"]==H.environment(npu,root)and
      e["released"]is True and re.fullmatch("[0-9a-f]{64}",e["cid"]),"three exact actual owned stage namespaces")
    normalized=copy.deepcopy(e);normalized["mounts"]=actual
    release=H.release(C,normalized,Controller)
    stop=C.obj(release["stop"]);raw=C.obj(release["inspect"])
    for value,argv in((stop,[H.DOCKER,"stop","--time","15",e["cid"]]),(raw,[H.DOCKER,"inspect",e["cid"]])):
        B.need(value["argv"]==argv and value["actual_wrapped_argv"]==[H.PRLIMIT,"--as=unlimited","--",*argv]and
          value["exit_code"]==0,"actual exact-owned stop/final inspect original")
    B.need(("release_smi"in release)==npu,"Devices[] cleanup does not demand or claim NPU idle")
    value=C.obj(e["resource_ref"]);R=H.R
    B.need(R.allocate(value["host_cpu"],value["daemon_cpu"])==value["allocation"],"original source7CPU/common ancestor replay")
    floor=R.memory_admit(value["host_memory"],value["daemon_memory"],e["mem"])
    B.need(value["ordinary_floor_bytes"]==floor==e["mem"]+R.HOST+R.RESERVE and value["memory"]["MemAvailable"]>=floor and
      value["memory"]["SwapTotal"]==value["memory"]["SwapFree"]and value["disk_available_bytes"]>=(24 if npu else 8)*H.GIB,
      "actual sequential72.5/16.5GiB RAM+disk and immutable reserve, no HugeTLB")
    saved=C.obj(e["mount_preflight_ref"]);fresh=H.mount_preflight(C).observe(expected,phase,source)
    B.need(saved["source_ref"]==source and saved["phase"]==phase and saved["passed"]is fresh["passed"]is True and
      len(saved["mounts"])==len(fresh["mounts"]),"actual original/current all exact mounts")
    for a,b in zip(saved["mounts"],fresh["mounts"]):
        B.need({k:v for k,v in a.items()if k!="identity"}=={k:v for k,v in b.items()if k!="identity"},"same complete mount paths/kinds")
        fields=("dev","ino","mode")if a["kind"]=="directory"else tuple(a["identity"])
        B.need(all(a["identity"][k]==b["identity"][k]for k in fields),"actual stable mount object identity")
    return release
def observations(C,host,source):
    import reader_whole as W
    PC=C.load("process_cmdline",C.host_bindings()["process_cmdline.py"]);proofs=[];e=host["owned"][1]
    for ref in host["actual_npu_observations"]:
        v=C.obj(ref);smi=C.obj(v["smi"])
        B.need(smi["argv"]==[H.SMI,"info"]and smi["exit_code"]==0,"actual original all4 SMI")
        W.protected(C.obj(v["protected_boundary_ref"]),host,v["smi"])
        actual=C.load("_skvq_model_hbm",C.host_bindings()["physical_hbm.py"]).actual_hbm
        B.need(v["actual_hbm"]==[actual(smi["stdout"],card)for card in(4,5,6,7)],"actual all4 physical3GiB reserve replay")
        for p in v["proofs"]:
            B.need(p["physical"]in(4,5,6,7)and p["chip"]==0 and e["cid"]in p["cgroup"]and
              p["namespace_pids"][0]==p["pid"],"all actual own worker/process maps, never0-3")
            PC.consume(C.obj(p["actual_cmdline_raw_ref"]),p,source);proofs.append(p)
    B.need(proofs,"actual host NPU proof required");return proofs
def rank_process(C,identity,proofs,cid,rank):
    W,_=C.writer_modules();rows=C.obj(W.CAPTURE)["files"]
    row=next(x for x in rows if x["path"].endswith("/tp_provider_current.py"))
    C.load("tp_provider_current",row).consume_identity(identity,rank)
    B.need(identity["public_TP_rank"]==rank and identity["groups"]["tp"]["world_size"]==4,
      "actual source-qualified worker initialized TP rank")
    candidates=[p for p in proofs if p["physical"]==rank+4 and p["namespace_pids"][-1]==identity["pid"]and
      p["start_ticks"]==identity["pid_start_ticks"]and cid in p["cgroup"]]
    B.need(candidates,"actual matching physical-card/namespacePID/start/cgroup; never inferred from rank text")
    return candidates
def math_rows(value,C,cohort,source):
    B.need(value["schema"]=="skvq.compiled-reader.model-independent/v1"and
      value["status"]=="ALL4_ALL16_TWO_DECODE_NUMERIC_SMOKE_CONSUMED"and value["source_ref"]==B.READER and
      value["cohort_ref"]==cohort and value["actual_frames"]==128 and value["actual_output_elements"]==196608 and
      value["threshold_relative_rms"]==.005 and value["actual_prompt_tokens"]==32768 and
      value["actual_native_decode_steps"]==2 and all(value[k]is False for k in B.false_scopes()),
      "actual full128 independent whole output mathematics, not source/fixture certificate")
    want={(r,"model.layers.%d.self_attn"%l,n)for r in range(4)for l in range(3,64,4)for n in(32769,32770)};seen=set()
    for row in value["checked"]:
        key=(row["rank"],row["layer"],row["length"])
        B.need(key in want and key not in seen and row["all1536_output_elements_checked"]is True and
          row["complete_original_quantized_KV_bytes_checked"]is True and row["complete_native_sink_recent_edges_checked"]is True,
          "unique complete all4/all16/two-step math domain")
        seen.add(key);frame=C.obj(row["frame_ref"])
        B.need(frame["source_ref"]==B.READER and frame["logical_layer"]==key[1]and frame["length"]==key[2],"same original byte-bound raw frame")
        B.need(set(row["metrics"])=={"scores","probabilities","output"}and len(row["heads"])==6,"all stages/every head")
        for name,m in row["metrics"].items():
            B.need(m["elements"]==(1536 if name=="output"else 6*key[2])and m["all_finite"]is True and
              m["threshold_relative_rms"]==.005 and 0<=m["relative_rms"]<=.005,"full independent finite/RMS")
        for m in row["heads"]:
            B.need(m["elements"]==256 and m["all_finite"]is True and m["threshold_relative_rms"]==.005 and
              0<=m["relative_rms"]<=.005,"all6 independent output heads")
    B.need(seen==want,"no missing/later duplicate numeric rows");return value
def consume(root,original_ref,expected):
    C,source,m=B.source(expected);H.components(C);root=Path(root)
    B.need(root.parent==B.ROOT.parent and re.fullmatch("run-skvq-model-reader-002-[a-zA-Z0-9-]+",root.name),"exact whole model root")
    href=C.ref(root/"HOST_RESULT.json");host=C.obj(href)
    B.need(host["schema"]=="skvq.model-reader.host/v1"and host["status"]=="ACTUAL_B1_NUMERIC_PENDING_WHOLE"and
      host["source_ref"]==source and host["reader_source_ref"]==B.READER and host["primary"]is None and not host["secondary"]and
      len(host["owned"])==len({e["cid"]for e in host["owned"]})==3 and host["model_block_seconds"]==5400 and
      host["CPU_block_seconds"]==3600 and host["total_seconds"]==9000 and host["cleanup_included_seconds"]==360 and
      0<host["elapsed_seconds"]<=9000 and 0<=host["actual_cleanup_seconds"]<=360 and
      host["portfolio_cutoff_epoch"]==B.CUT and host["CPU_QUEUE_no_peer_admission"]is True and
      host["native_cache_retained_common_bytes"]==6*H.GIB and all(host[k]is False for k in B.false_scopes()),
      "actual successful whole fixed original clock/budget, failures remain failed")
    file=Path(host["reader_whole_ref_file"]["path"]);C.read(host["reader_whole_ref_file"])
    B.need(json.loads(file.read_bytes())==host["reader_whole_ref"],"same actual prerequisite descriptor bytes")
    import reader_whole as W
    W.original(C.obj(original_ref),host_argv(source,root,file));pre=C.reader_whole(host["reader_whole_ref"])
    B.prompt(C,host["prompt_ref"]);mounts=H.mount_set(C,source,root,host["reader_whole_ref"])
    Controller=H.control_class(C,source,mounts,H.TOTAL)
    B.need(host["original_Control_source"]==Controller.donor_source and host["original_Control_AST"]==Controller.original_ast_sha256 and
      host["adapted_Control_AST"]==Controller.adapted_ast_sha256 and host["literal_delta"]==Controller.literal_delta,
      "unchanged inherited source-qualified safe Control with one registered disk delta")
    releases=[check_owned(C,e,i,source,root,mounts,Controller)for i,e in enumerate(host["owned"])];proofs=observations(C,host,source)
    result=host["result"];B.need(set(result["actual_cli_refs"])=={"cpu","n1","model","independent"},"four exact actual child stages")
    outputs={"cpu":result["cpu_ref"],"n1":result["n1_ref"],"model":result["producer_ref"],"independent":result["independent_ref"]}
    for name,index in(("cpu",0),("n1",1),("model",1),("independent",2)):
        raw=child(C,result["actual_cli_refs"][name],host["owned"][index]["cid"],H.args(name,source,root),index==1)
        lines=Path(raw["stdout"]["path"]).read_text().splitlines()
        B.need(lines and json.loads(lines[-1])==outputs[name],"actual final stdout result Ref; native log prefix retained")
    cpu=C.obj(result["cpu_ref"]);n1=C.obj(result["n1_ref"])
    B.need(cpu["source_ref"]==n1["source_ref"]==source and cpu["status"]=="ACTUAL_READER_PROMPT_PARSER_RPC_CHECKED"and
      cpu["reader_whole_ref"]==host["reader_whole_ref"]and cpu["prompt_ref"]==host["prompt_ref"]and n1["cpu_ref"]==result["cpu_ref"]and
      n1["full_engine_configuration_checked"]is True and n1["weights_loaded"]is False and len(n1["rank_refs"])==4,
      "actual current CPU partial->all4 full config beforeweights")
    from actual_config import match
    match(cpu["configuration"],n1["actual_configuration"])
    fmt=C.load("_skvq_model_actual_n1_format",C.host_bindings()["n1_format.py"])
    for ref in n1["rank_refs"]:fmt.consume_row(C.obj(ref),source)
    admission=C.obj(result["admission_ref"]);gate=C.obj(admission["source_gate_ref"]);clock=C.obj(admission["clock_ref"])
    B.need(admission["source_ref"]==source and admission["reader_whole_ref"]==host["reader_whole_ref"]and
      admission["prompt_ref"]==host["prompt_ref"]and admission["n1_ref"]==result["n1_ref"]and
      admission["resource_ref"]==host["owned"][1]["resource_ref"]and C.obj(admission["owned_ref"])["cid"]==host["owned"][1]["cid"]and
      admission["cid"]==host["owned"][1]["cid"]and gate["source_ref"]==source and gate["complete_source_bytes_checked"]is True and
      clock["source_ref"]==source and clock["protocol_ref"]==C.CLOCK and clock["portfolio_cutoff_epoch"]==B.CUT and
      clock["model_block_seconds"]==5400 and clock["cleanup_seconds"]==180 and
      admission["observed_epoch"]+admission["total_seconds"]<=B.CUT,"actual source/clock/owner admission original semantics")
    producer=C.obj(result["producer_ref"]);cohort=C.obj(result["cohort_ref"])
    B.need(producer["schema"]=="skvq.model-reader.producer/v1"and
      producer["status"]=="ACTUAL_ALL4_FIRST_TWO_DECODE_RAW_PENDING_OWNED_RELEASE"and producer["source_ref"]==source and
      producer["reader_source_ref"]==B.READER and producer["primary"]is None and producer["admission_ref"]==result["admission_ref"]and
      producer["prompt_ref"]==host["prompt_ref"]and len(producer["installs"])==len(producer["finals"])==4 and
      len(producer["restore_results"])==4 and all(x["restored"]is True for x in producer["restore_results"]),
      "actual registered+activated+restored producer, not enable flag")
    B.need(cohort["bridge_source_ref"]==source and cohort["source_ref"]==B.READER and
      cohort["release_ref"]==host["owned"][1]["release_ref"]and cohort["producer_ref"]==result["producer_ref"]and
      cohort["reader_whole_ref"]==host["reader_whole_ref"]and cohort["writer_whole_ref"]==pre["writer_whole_ref"]and
      cohort["owned_release_independently_consumed"]is True,"explicit native release->separate longCPU math")
    request=C.obj(producer["actual_request_output_ref"]);ranks=set()
    B.need(request["prompt_ref"]==host["prompt_ref"]and request["prompt_tokens"]==32768 and
      request["requested_output_tokens"]==3 and request["finished"]is True and request["native_finish_still_required"]is True and
      len(request["output_token_ids"])==3 and all(type(x)is int and x>=0 for x in request["output_token_ids"]),
      "same actual original prompt/three outputs; native finish independently required")
    for install,final in zip(sorted(producer["installs"],key=lambda x:x["rank"]),sorted(producer["finals"],key=lambda x:x["rank"])):
        rank=install["rank"];B.need(type(rank)is int and rank==final["rank"]and rank not in ranks and 0<=rank<4,"all unique actual rank RPC")
        ranks.add(rank);installed=C.obj(install["install_ref"]);finish=C.obj(final["final_ref"]);identity=finish["rank_identity"]
        rank_process(C,identity,proofs,host["owned"][1]["cid"],rank)
        from model_factory import factory_type
        _,expected_delta=factory_type(C);delta=C.obj(installed["factory_delta_ref"])
        reader_install=C.obj(installed["reader_install_ref"])
        B.need(delta==dict(source_ref=source,reader_source_ref=B.READER,geometry_ref=installed["geometry_ref"],**expected_delta)and
          reader_install["source_ref"]==B.READER and reader_install["rank_identity"]==identity and
          finish["install_ref"]==installed["reader_install_ref"],
          "actual new Factory bound to exact own+dependency helper and original captured live identity")
        B.need(installed["source_ref"]==source and installed["reader_source_ref"]==B.READER and installed["rank"]==rank and
          installed["actual_instance_hooks"]==32 and installed["qualification"]["installed"]is True and
          finish["source_ref"]==B.READER and finish["restored"]is True and finish["actual_native_prefill_calls"]==16 and
          finish["actual_compiled_decode_calls"]==32 and finish["GDN48_function_identities_unchanged"]is True and
          finish["actual_original_update_restored"]is True,"actual all32 owned hooks/nativeprefill/GDNfunctions/final restoration")
        geom=C.obj(installed["geometry_ref"])
        B.need(geom["source_ref"]==source and geom["rank"]==rank and geom["native_cache_budget_bytes"]==6*H.GIB and
          geom["minimum_logical_capacity"]==33792 and len(geom["FA"])==16 and
          {x["logical_layer"]for x in geom["FA"]}=={"model.layers.%d.self_attn"%l for l in range(3,64,4)} and
          len({x["native_name"]for x in geom["FA"]})==16 and
          all(x["logical_capacity"]>=33792 for x in geom["FA"])and
          geom["physical_declared_bytes"]==sum(x["size"]for x in geom["physical_allocations"])<=6*H.GIB,
          "actual source-qualified native6GiB capacity/slab plan, no savings claim")
        native=C.obj(finish["actual_native_finished_ref"])
        B.need(native["rank_identity"]==identity and native["requests_after"]==native["input_batch_after"]==[]and
          native["called_original_update"]is True and len(native["finished_req_ids"])==1,"all4 actual original native retirement")
    B.need(ranks==set(range(4))and cohort["rank_final_refs"]==[x["final_ref"]for x in sorted(producer["finals"],key=lambda x:x["rank"])],
      "same all4 complete producer/final index")
    numeric=math_rows(C.obj(result["independent_ref"]),C,result["cohort_ref"],source)
    B.need(numeric["writer_whole_ref"]==pre["writer_whole_ref"],"same actual original calibration/writer")
    B.need([x["phase"]for x in host["capspent"]]==["model-cpu","model-tp4","model-independent"]and
      [x["cid"]for x in host["capspent"]]==[e["cid"]for e in host["owned"]]and
      [x["memory"]for x in host["capspent"]]==[8*H.GIB,64*H.GIB,8*H.GIB]and
      all(x["cpu"]==4 for x in host["capspent"]),"actual three sequential quotas; no invented overlap")
    budget=C.load("_skvq_model_actual_output_budget",C.BUDGET);B.need(budget.consume(host["output_budget_snapshot"],root)<=H.OUTPUT_CAP,"actual output16GiB snapshot")
    H.snapshot(C,root);B.need(C.ref(href["path"])==href and B.source(expected)[1]==source,"quiescent whole/source after consumption")
    return dict(schema="skvq.model-reader.whole/v1",status="OWNED_ALL4_B1_FIRST_TWO_DECODE_FA_NUMERIC_CONSUMED",
      source_ref=source,reader_source_ref=B.READER,host_result_ref=href,original_ref=original_ref,
      reader_whole_ref=host["reader_whole_ref"],producer_ref=result["producer_ref"],independent_ref=result["independent_ref"],
      actual_frames=128,actual_output_elements=196608,actual_native_prefill_calls=64,actual_compiled_decode_calls=128,
      actual_prompt_tokens=32768,requested_output_tokens=3,all4_actual_native_finished_and_restore_checked=True,
      actual_model_eager_FA_activation_and_independent_numeric_checked=True,GDN48_function_identity_only_not_content=True,
      common_native_dense_cache_bytes=6*H.GIB,no_memory_or_E2E_claim=True,
      remaining=["GDN48 content/whole176/mixed/reset/fork/graph","paired1024 performance","official final tasks"],**B.false_scopes())
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--root");p.add_argument("--original-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**B.false_scopes())));return
    B.need(a.root and a.original_ref_json and Path(a.output)==Path(a.root)/"MODEL_WHOLE.json","one exact new independent sink")
    C,_,_=B.source(a.source_manifest_sha256)
    print(json.dumps(C.publish(a.output,consume(a.root,json.loads(Path(a.original_ref_json).read_bytes()),a.source_manifest_sha256)),sort_keys=True))
if __name__=="__main__":main()
