"""MAIN-only exact source14 Control reuse. CPU8 -> TP4 -> stop-retain -> CPU8.
Only disk320->24GiB and independent cleanup/time scopes change. No NPU idle gate
in Devices[] observation/cleanup, but CPU_QUEUE: no concurrent-peer admission.
5400 model block incl180cleanup +3600 CPU block incl180cleanup, immutable cutoff.
"""
import argparse,ast,hashlib,json,os,re,resource,shutil,subprocess,sys,time,traceback,types
from pathlib import Path
import bridge_contract as B
TOTAL=5400;CPU_TOTAL=3600;CLEANUP=180;GIB=2**30;OUTPUT_CAP=16*GIB
OWNER="skvq-model-reader-once-v1-002";IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PY="/usr/local/python3.12.13/bin/python3";DOCKER="/usr/bin/docker";PRLIMIT="/usr/bin/prlimit";SMI="/usr/local/sbin/npu-smi"
R=None
def components(C):
    global R
    row=C.host_bindings()["resources.py"];R=C.load("_skvq_model_original_resources",row);R.helper();return R
def newroot(value):
    p=Path(value);B.need(p.is_absolute()and".."not in p.parts and p.parent==B.ROOT.parent and
      p.parent.resolve()==p.parent and re.fullmatch("run-skvq-model-reader-002-[a-zA-Z0-9-]+",p.name)and
      not p.exists()and not p.is_symlink(),"exact absent model hostroot")
    p.mkdir(mode=0o700);return p
def environment(npu,out):
    return dict(ASCEND_RT_VISIBLE_DEVICES="0,1,2,3"if npu else"",TORCH_DEVICE_BACKEND_AUTOLOAD="0",
      MAIN_SKVQ_COMPILED_READER_MODEL_ENABLE="1"if npu else"0",QWEN36_SKVQ_COMPILED_READER_ENABLE="1"if npu else"0",
      QWEN36_SKVQ_TP4_CAPTURE_ENABLE="1"if npu else"0",VLLM_WORKER_MULTIPROC_METHOD="spawn",
      VLLM_ALLOW_INSECURE_SERIALIZATION="0",VLLM_ENABLE_V1_MULTIPROCESSING="1",PYTHONDONTWRITEBYTECODE="1",
      OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",TMPDIR="/tmp",
      TRITON_CACHE_DIR=str(out/"jit-cache"))
def args(stage,source,out):
    base=["--execute","--source-manifest-sha256",source["sha256"]]
    if stage=="cpu":return [str(B.ROOT/"model_cpu.py"),*base,"--reader-whole-ref-json",str(out/"READER_REF.json"),
      "--prompt-ref-json",str(out/"PROMPT_REF.json"),"--output",str(out/"cpu/RESULT.json")]
    if stage=="n1":return [str(B.ROOT/"model_n1.py"),*base,"--cpu-ref-json",str(out/"CPU_REF.json"),"--output",str(out/"candidate/N1.json")]
    if stage=="model":return [str(B.ROOT/"model_launch.py"),*base,"--reader-whole-ref-json",str(out/"READER_REF.json"),
      "--prompt-ref-json",str(out/"PROMPT_REF.json"),"--admission-ref-json",str(out/"ADMISSION_REF.json"),
      "--output",str(out/"candidate/model")]
    if stage=="independent":return [str(Path(B.READER["path"]).parent/"model_consume.py"),"--execute",
      "--source-manifest-sha256",B.READER["sha256"],"--cohort-ref-json",str(out/"COHORT_REF.json"),
      "--output",str(out/"independent/RESULT.json")]
    raise ValueError("four actual source-bound stages")
def mount_set(C,source,out,reader_ref):
    values=[];row=reader_ref
    for key in("writer_whole_ref","calibration_whole_ref","capture_whole_ref",None):
        value=C.obj(row);values.append((row,value))
        if key is not None:row=value[key]
    mounts={str(B.ROOT):(str(B.ROOT),False),str(Path(B.READER["path"]).parent):(str(Path(B.READER["path"]).parent),False),
      "/cache/efim/Qwen3.6-27B":("/cache/efim/Qwen3.6-27B",False)}
    for row,value in values:
        p=Path(value["host_result_ref"]["path"]).parent
        B.need(p.parent==B.ROOT.parent,"exact known predecessor hostroot, never broad cache")
        mounts[str(p)]=(str(p),False)
    references=[B.ORIGINAL_PROMPT,*C.obj(source)["dependencies"]]
    for row,value in values:references.extend((row,value["original_ref"]))
    for ref in references:
        C.read(ref);p=Path(ref["path"])
        if not any(p==Path(q)or Path(q)in p.parents for q in mounts):mounts[str(p)]=(str(p),False)
    mounts[str(out)]=(str(out),True);return mounts
def mount_preflight(C):
    original=C.load("_skvq_model_mount_primitives",C.host_bindings()["mount_preflight.py"])
    def observe(mounts,phase,source):
        rows,errors=original.inspect_mounts(mounts)
        return dict(schema="skvq.model-reader.mounts/v1",source_ref=source,phase=phase,mounts=rows,errors=errors,passed=not errors)
    return types.SimpleNamespace(observe=observe)
def snapshot(C,out):
    budget=C.load("_skvq_model_actual_output_budget",C.BUDGET);v=budget.scan(out);used=budget.consume(v,out)
    B.need(v["socket_policy"]==dict(parents=[],ipc_source=None)and not v["sockets"]and used<=OUTPUT_CAP,
      "all model raw/JIT/logs16GiB single snapshot; no IPC/socket exception")
    return v
def control_class(C,source,mounts,total):
    B.need(total in(TOTAL,CPU_TOTAL),"only preregistered two time blocks")
    C.load("current_contract",C.host_bindings()["current_contract.py"])
    C.load("process_cmdline",C.host_bindings()["process_cmdline.py"])
    row=C.host_bindings()["MAIN_HOST.py"];tree=ast.parse(C.read(row),row["path"])
    nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Control"]
    B.need(len(nodes)==1,"one exact inherited source14 Control")
    node=nodes[0];before=ast.dump(node,include_attributes=False);changes=[]
    for n in ast.walk(node):
        if (isinstance(n,ast.BinOp)and isinstance(n.op,ast.Mult)and isinstance(n.left,ast.Constant)and n.left.value==320 and
          isinstance(n.right,ast.Name)and n.right.id=="GIB"):
            n.left.value=24;changes.append("disk320->24GiB")
    B.need(changes==["disk320->24GiB"],"one exact model-output disk prerequisite delta")
    scope=dict(__name__="_skvq_model_exact_owned_control",Path=Path,os=os,json=json,re=re,subprocess=subprocess,time=time,
      traceback=traceback,shutil=shutil,TOTAL=total,CLEANUP=CLEANUP,DEADLINE=B.CUT,OWNER=OWNER,HERE=B.ROOT,IMAGE=IMAGE,
      PY=PY,DOCKER=DOCKER,PRLIMIT=PRLIMIT,SMI=SMI,GIB=GIB,R=R,M=mount_preflight(C),C=C,
      closure=lambda:source,reference=C.ref,publish_json=C.publish,require=B.need,
      actual_hbm=C.load("_skvq_model_hbm",C.host_bindings()["physical_hbm.py"]).actual_hbm)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),row["path"],"exec"),scope)
    Original=scope["Control"]
    class ModelControl(Original):
        def env(self,npu):return environment(npu,self.out)
        def mounts(self,npu,inputs=None):
            B.need(inputs is None,"prebound exact model evidence only")
            value=dict(mounts)
            if npu:value["/usr/local/Ascend/driver"]=("/usr/local/Ascend/driver",False)
            return value
        def guard(self):
            value=super().guard();self.save("OUTPUT16GIB_SNAPSHOT",snapshot(C,self.out));return value
    ModelControl.donor_source=row;ModelControl.original_ast_sha256=hashlib.sha256(before.encode()).hexdigest()
    ModelControl.adapted_ast_sha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()
    ModelControl.literal_delta=changes;return ModelControl
def payload(C,ctl):
    row=C.host_bindings()["MAIN_HOST.py"];tree=ast.parse(C.read(row),row["path"])
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="payload"]
    B.need(len(nodes)==1,"one actual full indexed weight hasher")
    scope=dict(Path=Path,json=json,hashlib=hashlib,MODEL=Path("/cache/efim/Qwen3.6-27B"),GIB=GIB,reference=C.ref,require=B.need)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),row["path"],"exec"),scope);return scope["payload"](ctl)
def release(C,e,Controller):
    value=C.obj(e["release_ref"])
    B.need(value["cid"]==e["cid"]and value["released"]is True and value["retained"]is True and value["deleted"]is False and
      value["noOOM"]is True and not value.get("secondary"),"actual exact stop-retain required before CPU oracle")
    raw=C.obj(value["inspect"]);rows=json.loads(raw["stdout"])
    normalized=dict(e,mounts={d:(s,bool(rw))for d,(s,rw)in e["mounts"].items()})
    B.need(len(rows)==1 and raw["exit_code"]==0,"actual single final owned inspect")
    Controller.validate(None,rows[0],normalized)
    x=rows[0];B.need(x["State"]["Running"]is False and x["State"]["Pid"]==0 and
      x["State"]["OOMKilled"]is False and not x.get("ExecIDs"),"actual exact process/resource release")
    return value
def admission(C,ctl,source,reader_ref,prompt_ref,n1_ref,out):
    ctl.observe();clock=ctl.save("FIXED_MODEL_CLOCK",dict(source_ref=source,protocol_ref=C.CLOCK,
      observed_epoch=time.time(),portfolio_cutoff_epoch=B.CUT,model_block_seconds=TOTAL,cleanup_seconds=CLEANUP))
    gate=ctl.save("ACTUAL_MODEL_SOURCE_GATE",dict(source_ref=source,reader_source_ref=B.READER,
      reader_whole_ref=reader_ref,prompt_ref=prompt_ref,complete_source_bytes_checked=True))
    owned=ctl.save("ACTUAL_MODEL_OWNED",ctl.current)
    seconds=int(ctl.left(cap=TOTAL));B.need(seconds>=600,"whole model remaining same block includes cleanup")
    row=C.atomic(out/"ADMISSION.json",dict(schema="skvq.model-reader.admission/v1",source_ref=source,
      reader_whole_ref=reader_ref,prompt_ref=prompt_ref,n1_ref=n1_ref,resource_ref=ctl.current["resource_ref"],
      owned_ref=owned,source_gate_ref=gate,clock_ref=clock,cid=ctl.current["cid"],physical_cards=[4,5,6,7],logical_devices=[0,1,2,3],
      guest_memory_bytes=64*GIB,host_memory_bytes=R.HOST,ordinary_reserve_bytes=R.RESERVE,joint_cpu_budget=7,
      portfolio_cutoff_epoch=B.CUT,total_seconds=seconds,observed_epoch=time.time(),output_root=str(out/"candidate/model")))
    C.atomic(out/"ADMISSION_REF.json",row);return row
def execute(a):
    B.need(os.environ.get("MAIN_SKVQ_MODEL_READER_HOST_ENABLE")=="1"and time.time()+TOTAL+CPU_TOTAL<=B.CUT,
      "explicit MAIN fixed9000incl360 before original cutoff")
    C,source,m=B.source(a.source_manifest_sha256);file=Path(a.reader_whole_ref_json)
    reader_ref=json.loads(file.read_bytes());whole=C.reader_whole(reader_ref);components(C)
    v=R.helper().cpu_view(os.getpid());os.sched_setaffinity(0,{min(v["effective_cpus"])})
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);B.need(hard==resource.RLIM_INFINITY,"Docker-only AS restoration")
    resource.setrlimit(resource.RLIMIT_AS,(R.HOST,hard));out=newroot(a.output)
    for name in("cpu","candidate","independent","tmp","jit-cache"):(out/name).mkdir(mode=0o700)
    C.atomic(out/"READER_REF.json",reader_ref);prompt_ref=B.make_prompt(C,source,out/"PROMPT.json")
    C.atomic(out/"PROMPT_REF.json",prompt_ref);mounts=mount_set(C,source,out,reader_ref)
    Controller=control_class(C,source,mounts,TOTAL);ctl=Controller(out);controllers=[ctl];result=None
    cpu=n1=producer=cohort=independent=ar=None;clis={};rawpayload=None;began=time.monotonic()
    try:
        rawpayload=payload(C,ctl)
        ctl.create("model-cpu",False,8*GIB)
        clis["cpu"]=ctl.exec("model-cpu",args("cpu",source,out),cap=900)
        cpu=C.ref(out/"cpu/RESULT.json");value=C.obj(cpu)
        B.need(value["source_ref"]==source and value["status"]=="ACTUAL_READER_PROMPT_PARSER_RPC_CHECKED"and
          value["configuration"]["full_engine_config_verified"]is False,"actual partial CPU prerequisite")
        C.atomic(out/"CPU_REF.json",cpu);ctl.cleanup();B.need(not ctl.secondary,"CPU stop-retain before TP4")
        ctl.create("model-tp4",True,64*GIB);env={"MAIN_OWNED_CID":ctl.current["cid"]}
        clis["n1"]=ctl.exec("model-N1",args("n1",source,out),True,240,env)
        n1=C.ref(out/"candidate/N1.json");B.need(C.obj(n1)["full_engine_configuration_checked"]is True,"real all4/config beforeweights")
        ar=admission(C,ctl,source,reader_ref,prompt_ref,n1,out)
        clis["model"]=ctl.exec("model-B1",args("model",source,out),True,ctl.left(cap=TOTAL),env)
        producer=C.ref(out/"candidate/model/PRODUCER_RESULT.json");value=C.obj(producer)
        B.need(value["source_ref"]==source and value["status"]=="ACTUAL_ALL4_FIRST_TWO_DECODE_RAW_PENDING_OWNED_RELEASE"and
          value["primary"]is None and len(value["finals"])==4,"actual all4 raw/final, not numerical PASS")
        ctl.cleanup();B.need(not ctl.secondary,"exact TP4 stop-retain before long reference")
        released=release(C,ctl.owned[-1],Controller)
        cohort=C.atomic(out/"COHORT.json",dict(schema="skvq.compiled-reader.model-cohort/v1",source_ref=B.READER,
          bridge_source_ref=source,status="ACTUAL_ALL4_FIRST_TWO_DECODE_RAW_RELEASED_PENDING_CPU",
          rank_final_refs=[x["final_ref"]for x in sorted(value["finals"],key=lambda x:x["rank"])],
          reader_whole_ref=reader_ref,writer_whole_ref=whole["writer_whole_ref"],prompt_ref=prompt_ref,
          actual_prompt_tokens=32768,requested_output_tokens=3,actual_native_decode_steps=2,
          owned_release_independently_consumed=True,release_ref=ctl.owned[-1]["release_ref"],producer_ref=producer,**B.false_scopes()))
        C.atomic(out/"COHORT_REF.json",cohort)
        Next=control_class(C,source,mounts,CPU_TOTAL);ctl=Next(out);controllers.append(ctl)
        ctl.create("model-independent",False,8*GIB)
        clis["independent"]=ctl.exec("model-independent",args("independent",source,out),cap=ctl.left(cap=CPU_TOTAL))
        independent=C.ref(out/"independent/RESULT.json");value=C.obj(independent)
        B.need(value["source_ref"]==B.READER and value["status"]=="ALL4_ALL16_TWO_DECODE_NUMERIC_SMOKE_CONSUMED"and
          value["cohort_ref"]==cohort and value["actual_frames"]==128 and value["actual_output_elements"]==196608,
          "real all128 full1536 independent SKVQ original equations")
        ctl.cleanup();B.need(not ctl.secondary,"after-release CPU stop-retain")
        B.need(payload(C,ctl)==rawpayload,"unchanged all actual original weights after model")
        result=dict(cpu_ref=cpu,n1_ref=n1,admission_ref=ar,producer_ref=producer,cohort_ref=cohort,
          independent_ref=independent,actual_cli_refs=clis)
    except BaseException as e:ctl.primary=e
    finally:
        for one in controllers:
            try:one.cleanup()
            except BaseException as e:one.secondary.append("cleanup: "+repr(e))
        primary=next((repr(one.primary)for one in controllers if one.primary),None)
        secondary=[e for one in controllers for e in one.secondary];snap=None
        try:snap=snapshot(C,out)
        except BaseException as e:secondary.append("output: "+repr(e))
        terminal=dict(schema="skvq.model-reader.host/v1",status="ACTUAL_B1_NUMERIC_PENDING_WHOLE"if result and not primary and not secondary else"FAILED",
          source_ref=source,reader_source_ref=B.READER,reader_whole_ref=reader_ref,reader_whole_ref_file=C.ref(file),
          prompt_ref=prompt_ref,result=result,primary=primary,secondary=secondary,owned=[e for one in controllers for e in one.owned],
          capspent=[e for one in controllers for e in one.spend],actual_payload=rawpayload,elapsed_seconds=time.monotonic()-began,
          model_block_seconds=TOTAL,CPU_block_seconds=CPU_TOTAL,total_seconds=TOTAL+CPU_TOTAL,
          cleanup_included_seconds=2*CLEANUP,actual_cleanup_seconds=sum(one.cleanup_spent for one in controllers),
          portfolio_cutoff_epoch=B.CUT,original_Control_source=Controller.donor_source,
          original_Control_AST=Controller.original_ast_sha256,adapted_Control_AST=Controller.adapted_ast_sha256,
          literal_delta=Controller.literal_delta,host_pid=os.getpid(),protected0_3=controllers[0].protected,
          actual_npu_observations=controllers[0].observations,output_budget_snapshot=snap,output_peak_not_measured=True,
          CPU_QUEUE_no_peer_admission=True,native_cache_retained_common_bytes=6*GIB,
          GDN48_content_pending=True,formal_performance_unmeasured=True,**B.false_scopes())
        row=C.publish(out/"HOST_RESULT.json",terminal);print(json.dumps(row,sort_keys=True),flush=True)
    B.need(terminal["primary"]is None and not terminal["secondary"],"whole original failure cannot promote")
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--reader-whole-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**B.false_scopes())));return
    B.need(a.reader_whole_ref_json and a.output,"real prerequisite/new root");execute(a)
if __name__=="__main__":main()
