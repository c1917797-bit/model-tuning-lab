"""MAIN-only source-bound derivative of reviewed writer002 Control; no new controller.
CPU prerequisite -> owned physical4 canary/compiled QK+AV -> exact release -> Devices[] oracle.
Both1800 blocks include90cleanup. CPU_QUEUE: no cross-paper peer authority.
"""
import argparse,ast,hashlib,json,os,re,shutil,subprocess,sys,time,traceback,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import contract as C
TOTAL=1800;CLEANUP=90;GIB=2**30;OWNER="skvq-compiled-reader-v1-001"
IMAGE=C.IMAGE;PY="/usr/local/python3.12.13/bin/python3";DOCKER="/usr/bin/docker";PRLIMIT="/usr/bin/prlimit";SMI="/usr/local/sbin/npu-smi"
R=None
def components():
    global R
    C.writer_modules();R=sys.modules["writer_resources"];return R
def newroot(value):
    p=Path(value);C.need(p.is_absolute()and".."not in p.parts and p.parent==C.ROOT.parent and
      p.parent.resolve()==p.parent and re.fullmatch("run-skvq-compiled-reader-001-[a-zA-Z0-9-]+",p.name)and
      not p.exists()and not p.is_symlink(),"exact absent new reader host root")
    p.mkdir(mode=0o700);return p
def environment(npu,out):
    return dict(ASCEND_RT_VISIBLE_DEVICES="0"if npu else"",TORCH_DEVICE_BACKEND_AUTOLOAD="0",
      MAIN_SKVQ_COMPILED_READER_EXECUTE="1"if npu else"0",QWEN36_SKVQ_COMPILED_READER_ENABLE="1"if npu else"0",
      PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1",
      TMPDIR=str(out/"tmp"))
def args(stage,source,out,whole_file):
    base=["--execute","--source-manifest-sha256",source["sha256"]]
    if stage=="cpu":return [str(C.ROOT/"reader_cpu.py"),*base,"--writer-whole-ref-json",str(whole_file),"--output",str(out/"cpu/work/RESULT.json")]
    if stage=="canary":return [str(C.ROOT/"reader_canary.py"),*base,"--writer-whole-ref-json",str(whole_file),
      "--cpu-ref-json",str(out/"CPU_REF.json"),"--output",str(out/"candidate/work/CANARY.json")]
    if stage=="numeric":return [str(C.ROOT/"numeric.py"),*base,"--writer-whole-ref-json",str(whole_file),
      "--device-proof-ref-json",str(out/"candidate/work/DEVICE_PROOF_REF.json"),"--output",str(out/"candidate/work/numeric")]
    if stage=="independent":return [str(C.ROOT/"reader_consume.py"),*base,"--producer-ref-json",str(out/"NUMERIC_REF.json"),
      "--output",str(out/"candidate/work/numeric/INDEPENDENT.json")]
    raise ValueError("unique four actual reader stages")
def mount_set(out,whole_file,whole_ref):
    whole=C.writer_whole(whole_ref);writer_root=Path(whole["host_result_ref"]["path"]).parent
    calibration=C.obj(whole["calibration_whole_ref"]);calroot=Path(calibration["host_result_ref"]["path"]).parent
    capture=C.obj(calibration["capture_whole_ref"]);caproot=Path(capture["host_result_ref"]["path"]).parent
    C.need(writer_root.parent==calroot.parent==caproot.parent==C.ROOT.parent,"same exact experiment-parent roots")
    mounts={str(C.ROOT):(str(C.ROOT),False)}
    for p in(writer_root,calroot,caproot):mounts[str(p)]=(str(p),False)
    manifest=C.obj(C.ref(HERE/"SOURCE_MANIFEST.json"))
    for row in[whole_ref,C.ref(whole_file),*manifest["dependencies"]]:
        p=Path(row["path"])
        if not any(p==Path(q)or Path(q)in p.parents for q in mounts):mounts[str(p)]=(str(p),False)
    index="/cache/efim/Qwen3.6-27B/model.safetensors.index.json";mounts[index]=(index,False)
    mounts[str(out)]=(str(out),True)
    return mounts
def preflight_module():
    original=C.module("_skvq_reader_mount_primitives",C.host_bindings()["mount_preflight.py"])
    def observe(mounts,phase,source):
        rows,errors=original.inspect_mounts(mounts)
        return dict(schema="skvq.compiled-reader.mounts/v1",source_ref=source,phase=phase,mounts=rows,errors=errors,passed=not errors)
    return types.SimpleNamespace(observe=observe)
def control_hbm(text,card):
    return C.module("_skvq_reader_hbm",C.host_bindings()["physical_hbm.py"]).actual_hbm(text,card)
def control_class(source,mounts,preflight):
    # Exact source14 proc-byte helper preserves original Owned gate and padding.
    C.module("current_contract",C.host_bindings()["current_contract.py"])
    C.module("process_cmdline",C.host_bindings()["process_cmdline.py"])
    row=C.host_bindings()["MAIN_HOST.py"];tree=ast.parse(C.checked(row),filename=row["path"])
    original=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Control"]
    C.need(len(original)==1,"one exact reviewed Control")
    text=ast.unparse(original[0])
    replacements=[('h["NanoCpus"] == 4 * 10 ** 9','h["NanoCpus"] == 1 * 10 ** 9'),
      ("for card in (4, 5, 6, 7):","for card in (4,):"),("320 * GIB","9 * GIB"),("'--cpus', '4'","'--cpus', '1'"),
      ("cpu=4, started_elapsed=","cpu=1, started_elapsed=")]
    applied=[]
    for old,new in replacements:
        # ast.unparse quotes are deterministic for actual Python; tolerate no alternative body.
        old=old.replace('"',"'")if old.startswith('h[')else old
        new=new.replace('"',"'")if new.startswith('h[')else new
        C.need(text.count(old)==1,"exact narrow Control literal: "+old);text=text.replace(old,new);applied.append([old,new])
    adapted=ast.parse(text).body[0]
    scope=dict(__name__="_skvq_reader_exact_owned_control",Path=Path,os=os,json=json,re=re,subprocess=subprocess,
      time=time,traceback=traceback,shutil=shutil,TOTAL=TOTAL,CLEANUP=CLEANUP,DEADLINE=C.CUT,OWNER=OWNER,HERE=C.ROOT,
      IMAGE=IMAGE,PY=PY,DOCKER=DOCKER,PRLIMIT=PRLIMIT,SMI=SMI,GIB=GIB,R=R,M=preflight,C=C,
      closure=lambda:source,reference=C.ref,publish_json=C.publish,require=C.need,
      actual_hbm=C.module("_skvq_reader_hbm",C.host_bindings()["physical_hbm.py"]).actual_hbm)
    exec(compile(ast.Module(body=[adapted],type_ignores=[]),row["path"],"exec"),scope)
    original_class=scope["Control"]
    class ReaderControl(original_class):
        def devices(self,npu):
            return {"/dev/davinci4":"/dev/davinci0",**{"/dev/"+k:"/dev/"+k for k in("davinci_manager","devmm_svm","hisi_hdc")}}if npu else{}
        def env(self,npu):return environment(npu,self.out)
        def mounts(self,npu,inputs=None):
            C.need(inputs is None,"prebound exact calibration evidence only")
            value=dict(mounts)
            if npu:value["/usr/local/Ascend/driver"]=("/usr/local/Ascend/driver",False)
            return value
        def guard(self):
            value=super().guard()
            raw=C.snapshot(self.out);self.save("OUTPUT1GIB_SNAPSHOT",raw)
            return value
    ReaderControl.donor_source=row
    ReaderControl.original_ast_sha256=hashlib.sha256(ast.dump(original[0],include_attributes=False).encode()).hexdigest()
    ReaderControl.adapted_ast_sha256=hashlib.sha256(ast.dump(adapted,include_attributes=False).encode()).hexdigest()
    ReaderControl.literal_delta=applied
    return ReaderControl

def consume_cpu(value,source,whole):
    C.need(value["schema"]=="skvq.compiled-reader.cpu/v1"and value["status"]=="ACTUAL_WRITER128_AND_NUMPY12_CHECKED"and
      value["source_ref"]==source and value["writer_whole_ref"]==whole and value["actual_cases"]==128 and
      value["no_torch"]is True and value["Devices_empty"]is True and len(value["configurations"])==12 and
      all(x["all_outputs_bitwise"]is True for x in value["configurations"])and all(value[k]is False for k in C.scopes()),
      "actual complete CPU input/parity gate, not parser/source-only")
    return value
def consume_canary(value,source,whole,prior):
    C.need(value["schema"]=="skvq.compiled-reader.canary/v1"and value["status"]=="ACTUAL_SINGLE4_TINY_CHECKED"and
      value["source_ref"]==source and value["writer_whole_ref"]==whole and value["cpu_ref"]==prior and
      value["primary"]is None and value["physical_card"]==4 and value["logical_device"]==0 and
      value["identity"]==value["after_identity"]and all(value[k]is False for k in C.scopes()),"actual current tiny/source/identity")
    f=C.load("_skvq_reader_actual_format",C.host_bindings()["n1_format.py"])
    f.consume_raw(C.obj(value["original_observation_ref"]),value["actual_format"],rank=0,source=source,
      identity=value["identity"],after_identity=value["after_identity"])
    C.need(value["input"]==[1.,2.]and value["output"]==[4.,5.]and type(value["format"])is int and value["format"]==2,
      "actual tiny arithmetic and normalized exact ND")
    return value
def device_proof(ctl,source,whole,prior,canary,out):
    value=consume_canary(C.obj(canary),source,whole,prior)
    C.need(value["owned_cid"]==ctl.current["cid"],"same actual owned fresh canary")
    proofs=[p for r in ctl.observations for p in C.obj(r)["proofs"]if p["namespace_pids"][-1]==value["identity"]["pid"]and
      p["start_ticks"]==value["identity"]["start_ticks"]and p["physical"]==4]
    C.need(proofs,"actual original host SMI/proc mapping")
    clock=ctl.save("FIXED_CLOCK",dict(source_ref=source,protocol_ref=C.CLOCK,portfolio_cutoff_epoch=C.CUT,
      observed_epoch=time.time(),device_total_seconds=TOTAL,cleanup_included_seconds=CLEANUP))
    gate=ctl.save("ACTUAL_SOURCE_GATE",dict(source_ref=source,writer_source_ref=C.WRITER_SOURCE,writer_whole_ref=whole,
      entire_closure_bytes_checked=True))
    mapping=ctl.save("ACTUAL_SINGLE4_MAPPING",dict(source_ref=source,cid=ctl.current["cid"],physical_card=4,logical_device=0,
      devices=ctl.current["devices"],canary_ref=canary,actual_mapping_proofs=proofs,observations=ctl.observations))
    owned=ctl.save("ACTUAL_CURRENT_OWNED",ctl.current)
    body=dict(schema="skvq.compiled-reader.owned-proof/v1",source_ref=source,writer_whole_ref=whole,cpu_ref=prior,
      image=IMAGE,physical_card=4,logical_device=0,cid=ctl.current["cid"],source_gate_ref=gate,mapping_ref=mapping,
      resource_ref=ctl.current["resource_ref"],clock_ref=clock,owned_ref=owned,fresh_canary_ref=canary,
      host_semantic_consumer_required=True)
    row=C.publish(out/"candidate/work/DEVICE_PROOF.json",body);C.publish(out/"candidate/work/DEVICE_PROOF_REF.json",row)
    return row
def execute(a):
    import resource
    C.need(os.environ.get("MAIN_SKVQ_READER_HOST_ENABLE")=="1"and time.time()+2*TOTAL<=C.CUT,
      "explicit MAIN/fixed3600 includes180cleanup before immutable cutoff")
    source=C.source(a.source_manifest_sha256);whole_file=Path(a.writer_whole_ref_json)
    whole=json.loads(whole_file.read_bytes());C.writer_whole(whole);components()
    view=R.helper().cpu_view(os.getpid());os.sched_setaffinity(0,{min(view["effective_cpus"])})
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,"Docker CLI hard AS unlimited")
    resource.setrlimit(resource.RLIMIT_AS,(R.HOST,hard));out=newroot(a.output)
    for stage in("cpu","candidate","independent"):(out/stage/"work").mkdir(parents=True,mode=0o700)
    (out/"tmp").mkdir(mode=0o700)
    mounts=mount_set(out,whole_file,whole);Controller=control_class(source,mounts,preflight_module())
    ctl=Controller(out);controllers=[ctl];began=time.monotonic();result=None;clis={};prior=canary=proof=producer=independent=None
    try:
        ctl.create("reader-cpu",False,8*GIB)
        clis["cpu"]=ctl.exec("reader-cpu",args("cpu",source,out,whole_file),cap=600)
        prior=C.ref(out/"cpu/work/RESULT.json");consume_cpu(C.obj(prior),source,whole);C.publish(out/"CPU_REF.json",prior)
        ctl.cleanup();C.need(not ctl.secondary,"own CPU exact stop-retain before NPU")
        ctl.create("single4-reader",True,8*GIB);env={"MAIN_OWNED_CID":ctl.current["cid"]}
        clis["canary"]=ctl.exec("reader-canary",args("canary",source,out,whole_file),True,180,env)
        canary=C.ref(out/"candidate/work/CANARY.json");proof=device_proof(ctl,source,whole,prior,canary,out)
        clis["numeric"]=ctl.exec("reader-numeric",args("numeric",source,out,whole_file),True,ctl.left(cap=TOTAL),env)
        producer=C.ref(out/"candidate/work/numeric/RESULT.json");value=C.obj(producer)
        C.need(value["status"]=="ALL64_Q2Q4_COMPILED_READER_RAW_PENDING_INDEPENDENT"and value["primary"]is None,
          "actual complete reader outputs, independent reference pending")
        C.publish(out/"NUMERIC_REF.json",producer)
        ctl.cleanup();C.need(not ctl.secondary,"exact stopped/Pid0/noExec before long CPU reference")
        ctl=Controller(out);controllers.append(ctl);ctl.create("reader-independent",False,8*GIB)
        clis["independent"]=ctl.exec("reader-independent",args("independent",source,out,whole_file),cap=ctl.left(cap=TOTAL))
        independent=C.ref(out/"candidate/work/numeric/INDEPENDENT.json");value=C.obj(independent)
        C.need(value["status"]=="ALL64_Q2Q4_COMPILED_ATTENTION_CONSUMED"and value["actual_cases"]==128 and
          value["actual_output_elements"]==128*1536 and all(value[k]is False for k in C.scopes()),"all same-input independent equations")
        result=dict(cpu_ref=prior,canary_ref=canary,device_proof_ref=proof,producer_ref=producer,
          independent_ref=independent,actual_cli_refs=clis)
    except BaseException as e:ctl.primary=e
    finally:
        for one in controllers:
            try:one.cleanup()
            except BaseException as e:one.secondary.append("cleanup capture: "+repr(e))
        secondary=[e for one in controllers for e in one.secondary];first=next((repr(one.primary)for one in controllers if one.primary),None)
        snap=None
        try:snap=C.snapshot(out)
        except BaseException as e:secondary.append("output1GiB: "+repr(e))
        terminal=dict(schema="skvq.compiled-reader.host/v1",
          status="ACTUAL_READER_CONSUMED_PENDING_WHOLE"if result and not first and not secondary else"FAILED",
          source_ref=source,writer_whole_ref=whole,writer_whole_ref_file=C.ref(whole_file),result=result,primary=first,secondary=secondary,
          owned=[e for one in controllers for e in one.owned],capspent=[e for one in controllers for e in one.spend],
          elapsed_seconds=time.monotonic()-began,device_block_seconds=TOTAL,independent_cpu_block_seconds=TOTAL,
          total_seconds=2*TOTAL,cleanup_included_seconds=2*CLEANUP,
          actual_cleanup_seconds=sum(one.cleanup_spent for one in controllers),portfolio_cutoff_epoch=C.CUT,
          original_Control_source=Controller.donor_source,original_Control_AST=Controller.original_ast_sha256,
          adapted_Control_AST=Controller.adapted_ast_sha256,literal_delta=Controller.literal_delta,
          host_pid=os.getpid(),protected0_3=controllers[0].protected,actual_npu_observations=controllers[0].observations,
          output_budget_snapshot=snap,output_peak_not_measured=True,CPU_QUEUE_no_peer_admission=True,**C.scopes())
        row=C.publish(out/"HOST_RESULT.json",terminal);print(json.dumps(row,sort_keys=True),flush=True)
    C.need(terminal["primary"]is None and not terminal["secondary"],"original failure/cleanup cannot promote")
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--writer-whole-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.writer_whole_ref_json and a.output,"real writer whole/new unique root");execute(a)
if __name__=="__main__":main()
