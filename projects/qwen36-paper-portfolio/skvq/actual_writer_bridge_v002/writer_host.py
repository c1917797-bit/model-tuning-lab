"""MAIN-only single physical4 writer; exact reviewed Control lifecycle, no model.
Device block1800incl90 stops before independent Devices[]1800incl90.
"""
import argparse,ast,hashlib,json,os,re,shutil,subprocess,sys,time,traceback,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import writer_contract as C
import writer_resources as R
TOTAL=1800;CLEANUP=90;GIB=2**30;OWNER="skvq-actual-writer-bridge-v1-002"
IMAGE=C.IMAGE;PY="/usr/local/python3.12.13/bin/python3";DOCKER="/usr/bin/docker";PRLIMIT="/usr/bin/prlimit";SMI="/usr/local/sbin/npu-smi"
def newroot(value):
    p=Path(value);C.need(p.is_absolute()and".."not in p.parts and p.parent==C.ROOT.parent and
      p.parent.resolve()==p.parent and re.fullmatch("run-skvq-actual-writer-bridge-002-[a-zA-Z0-9-]+",p.name)and
      not p.exists()and not p.is_symlink(),"exact absent new writer hostroot")
    p.mkdir(mode=0o700);return p
def environment(npu):
    return dict(ASCEND_RT_VISIBLE_DEVICES="0"if npu else"",TORCH_DEVICE_BACKEND_AUTOLOAD="0",
      MAIN_SKVQ_WRITER_NUMERIC_ENABLE="1"if npu else"0",PYTHONDONTWRITEBYTECODE="1",
      OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1")
def descriptor(path,row):return C.publish(path,row)
def args(stage,source,out,whole_file):
    base=["--execute","--source-manifest-sha256",source["sha256"]]
    if stage=="input-plan":return [str(C.ROOT/"writer_cpu.py"),*base,"--calibration-whole-ref-json",str(whole_file),"--output",str(out/"input-plan/work")]
    if stage=="canary":return [str(C.ROOT/"writer_canary.py"),*base,"--input-plan-ref-json",str(out/"INPUT_PLAN_REF.json"),
      "--prior-numpy-ref-json",str(out/"NUMPY_REF.json"),"--output",str(out/"candidate/work/CANARY.json")]
    if stage=="numeric":return [str(C.ROOT/"writer_numeric.py"),*base,"--input-plan-ref-json",str(out/"INPUT_PLAN_REF.json"),
      "--device-proof-ref-json",str(out/"candidate/work/DEVICE_PROOF_REF.json"),"--output",str(out/"candidate/work/numeric")]
    if stage=="independent":return [str(C.ROOT/"writer_consume.py"),*base,"--producer-ref-json",str(out/"NUMERIC_REF.json"),
      "--output",str(out/"candidate/work/numeric/WRITER_INDEPENDENT.json")]
    raise ValueError("unique four actual stages")
def mount_set(out,whole_file,whole_ref):
    manifest=C.obj(C.ref(HERE/"SOURCE_MANIFEST.json"));whole=C.obj(whole_ref)
    calroot=Path(whole["host_result_ref"]["path"]).parent;capture=C.obj(whole["capture_whole_ref"])
    caproot=Path(capture["host_result_ref"]["path"]).parent
    C.need(calroot.parent==caproot.parent==C.ROOT.parent and
      re.fullmatch("run-skvq-default-tp-local-006-[a-zA-Z0-9-]+",calroot.name)and
      re.fullmatch("run-skvq-current72h-projection-014-[a-zA-Z0-9-]+",caproot.name),"exact current whole experiment roots")
    mounts={str(C.ROOT):(str(C.ROOT),False),str(calroot):(str(calroot),False),str(caproot):(str(caproot),False)}
    for row in [whole_ref,C.ref(whole_file),*manifest["dependencies"]]:
        p=Path(row["path"])
        if not any(p==Path(q)or Path(q)in p.parents for q in mounts):mounts[str(p)]=(str(p),False)
    index="/cache/efim/Qwen3.6-27B/model.safetensors.index.json";mounts[index]=(index,False)
    mounts[str(out)]=(str(out),True)
    return mounts
def preflight_module():
    original=C.module("_skvq_writer_mount_primitives",C.HOST_BINDINGS["mount_preflight.py"])
    def observe(mounts,phase,source):
        rows,errors=original.inspect_mounts(mounts)
        return dict(schema="skvq.actual-writer.mounts/v1",source_ref=source,phase=phase,mounts=rows,errors=errors,passed=not errors)
    return types.SimpleNamespace(observe=observe)
def control_hbm(text,card):
    return C.module("_skvq_writer_hbm",C.HOST_BINDINGS["physical_hbm.py"]).actual_hbm(text,card)
def control_class(source,mounts,preflight):
    # Exact source14 proc-byte helper preserves original Owned gate and padding.
    C.module("current_contract",C.HOST_BINDINGS["current_contract.py"])
    C.module("process_cmdline",C.HOST_BINDINGS["process_cmdline.py"])
    row=C.HOST_BINDINGS["MAIN_HOST.py"];tree=ast.parse(C.checked(row),filename=row["path"])
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
    scope=dict(__name__="_skvq_writer_exact_owned_control",Path=Path,os=os,json=json,re=re,subprocess=subprocess,
      time=time,traceback=traceback,shutil=shutil,TOTAL=TOTAL,CLEANUP=CLEANUP,DEADLINE=C.CUT,OWNER=OWNER,HERE=C.ROOT,
      IMAGE=IMAGE,PY=PY,DOCKER=DOCKER,PRLIMIT=PRLIMIT,SMI=SMI,GIB=GIB,R=R,M=preflight,C=C,
      closure=lambda:source,reference=C.ref,publish_json=C.publish,require=C.need,
      actual_hbm=C.module("_skvq_writer_hbm",C.HOST_BINDINGS["physical_hbm.py"]).actual_hbm)
    exec(compile(ast.Module(body=[adapted],type_ignores=[]),row["path"],"exec"),scope)
    original_class=scope["Control"]
    class WriterControl(original_class):
        def devices(self,npu):
            return {"/dev/davinci4":"/dev/davinci0",**{"/dev/"+k:"/dev/"+k for k in("davinci_manager","devmm_svm","hisi_hdc")}}if npu else{}
        def env(self,npu):return environment(npu)
        def mounts(self,npu,inputs=None):
            C.need(inputs is None,"prebound exact calibration evidence only")
            value=dict(mounts)
            if npu:value["/usr/local/Ascend/driver"]=("/usr/local/Ascend/driver",False)
            return value
        def guard(self):
            value=super().guard()
            raw=C.snapshot(self.out);self.save("OUTPUT1GIB_SNAPSHOT",raw)
            return value
    WriterControl.donor_source=row
    WriterControl.original_ast_sha256=hashlib.sha256(ast.dump(original[0],include_attributes=False).encode()).hexdigest()
    WriterControl.adapted_ast_sha256=hashlib.sha256(ast.dump(adapted,include_attributes=False).encode()).hexdigest()
    WriterControl.literal_delta=applied
    return WriterControl
def consume_canary(value,source,plan,prior):
    C.need(value["schema"]=="skvq.actual-writer.canary/v1"and value["status"]=="ACTUAL_SINGLE4_TINY_CHECKED"and
      value["source_ref"]==source and value["input_plan_ref"]==plan and value["prior_numpy_ref"]==prior and
      value["primary"]is None and value["physical_card"]==4 and value["logical_device"]==0 and
      value["identity"]==value["after_identity"]and all(value[k]is False for k in C.scopes()),"actual current tiny source/map/identity")
    F=C.module("_skvq_writer_actual_format",C.HOST_BINDINGS["n1_format.py"])
    F.consume_raw(C.obj(value["original_observation_ref"]),value["actual_format"],rank=0,source=source,
      identity=value["identity"],after_identity=value["after_identity"])
    C.need(value["input"]==[1.,2.]and value["output"]==[4.,5.]and type(value["format"])is int and value["format"]==2,
      "actual tiny output/ND; no enum coercion")
    return value
def device_proof(ctl,source,plan,prior,canary,out):
    value=consume_canary(C.obj(canary),source,plan,prior);C.need(value["owned_cid"]==ctl.current["cid"],"same exact owned canary")
    observed=[C.obj(r)for r in ctl.observations]
    proofs=[p for v in observed for p in v["proofs"]if p["namespace_pids"][-1]==value["identity"]["pid"]and
      p["start_ticks"]==value["identity"]["start_ticks"]and p["physical"]==4]
    C.need(proofs,"actual SMI/proc canary mapping observation, not guest declaration")
    clock=C.obj(C.CLOCK);cr=ctl.save("FIXED_CLOCK",dict(source_ref=source,protocol_ref=C.CLOCK,portfolio_cutoff_epoch=C.CUT,
      observed_epoch=time.time(),device_total_seconds=TOTAL,cleanup_included_seconds=CLEANUP))
    sg=ctl.save("ACTUAL_SOURCE_GATE",dict(source_ref=source,capture_source=C.CAPTURE,calibration_source=C.CALIBRATION,
      entire_closure_bytes_checked=True,calibration_whole_ref=C.obj(plan)["calibration_whole_ref"]))
    mr=ctl.save("ACTUAL_SINGLE4_MAPPING",dict(source_ref=source,cid=ctl.current["cid"],physical_card=4,logical_device=0,
      devices=ctl.current["devices"],canary_ref=canary,actual_mapping_proofs=proofs,observations=ctl.observations))
    owned=ctl.save("ACTUAL_CURRENT_OWNED",ctl.current)
    p=dict(schema="skvq.actual-writer.owned-device-proof/v1",source_ref=source,input_plan_ref=plan,prior_numpy_ref=prior,
      image=IMAGE,physical_card=4,logical_device=0,cid=ctl.current["cid"],source_gate_ref=sg,mapping_ref=mr,
      resource_ref=ctl.current["resource_ref"],clock_ref=cr,owned_ref=owned,fresh_canary_ref=canary,
      host_owned_semantic_consumer_required=True)
    row=C.publish(out/"candidate/work/DEVICE_PROOF.json",p);descriptor(out/"candidate/work/DEVICE_PROOF_REF.json",row)
    return row
def execute(a):
    import resource
    C.need(os.environ.get("MAIN_SKVQ_WRITER_HOST_ENABLE")=="1"and time.time()+2*TOTAL<=C.CUT,
      "MAIN-only fixed 3600 wall includes180 cleanup before immutable cutoff")
    source=C.source(a.source_manifest_sha256);whole_file=Path(a.calibration_whole_ref_json);whole=json.loads(whole_file.read_bytes())
    from writer_inputs import verify_whole
    verify_whole(whole) # real complete013 capture/cal006 fit before any container
    view=R.helper().cpu_view(os.getpid());os.sched_setaffinity(0,{min(view["effective_cpus"])})
    soft,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,"exact DockerCLI hardAS")
    resource.setrlimit(resource.RLIMIT_AS,(R.HOST,hard));out=newroot(a.output)
    for stage in("input-plan","candidate","independent"):(out/stage/"work").mkdir(parents=True,mode=0o700)
    mounts=mount_set(out,whole_file,whole);Controller=control_class(source,mounts,preflight_module())
    ctl=Controller(out);controllers=[ctl];began=time.monotonic();result=None;plan=prior=canary=numeric=independent=proof=None;clis={}
    try:
        ctl.create("input-plan",False,8*GIB)
        clis["input-plan"]=ctl.exec("input-plan",args("input-plan",source,out,whole_file),cap=600)
        cpu=C.obj(C.ref(out/"input-plan/work/CPU_RESULT.json"))
        C.need(cpu["status"]=="ACTUAL_INPUT_PLAN_NUMPY24_COMPLETE"and cpu["source_ref"]==source,"actual CPU plan+parity")
        plan=cpu["input_plan_ref"];prior=cpu["numpy_ref"]
        descriptor(out/"INPUT_PLAN_REF.json",plan);descriptor(out/"NUMPY_REF.json",prior)
        ctl.cleanup();C.need(not ctl.secondary,"exact CPU stop-retain before own NPU")
        ctl.create("single4-writer",True,8*GIB)
        env={"MAIN_OWNED_CID":ctl.current["cid"]}
        clis["canary"]=ctl.exec("canary",args("canary",source,out,whole_file),True,180,env)
        canary=C.ref(out/"candidate/work/CANARY.json")
        proof=device_proof(ctl,source,plan,prior,canary,out)
        clis["numeric"]=ctl.exec("numeric",args("numeric",source,out,whole_file),True,ctl.left(cap=TOTAL),env)
        numeric=C.ref(out/"candidate/work/numeric/PRODUCER_RESULT.json");v=C.obj(numeric)
        C.need(v["status"]=="ACTUAL_ALL64_Q2Q4_WRITER_RETURNED_RAW_PENDING_INDEPENDENT"and v["primary"]is None,
          "complete actual writer returned, raw reference still pending")
        descriptor(out/"NUMERIC_REF.json",numeric)
        ctl.cleanup();C.need(not ctl.secondary,"exact owned single4 stopped/Pid0/noExec before long independent CPU")
        cpu_ctl=Controller(out);controllers.append(cpu_ctl);ctl=cpu_ctl
        ctl.create("independent",False,8*GIB)
        clis["independent"]=ctl.exec("independent",args("independent",source,out,whole_file),cap=ctl.left(cap=TOTAL))
        independent=C.ref(out/"candidate/work/numeric/WRITER_INDEPENDENT.json");v=C.obj(independent)
        C.need(v["status"]=="ACTUAL_ALL64_Q2Q4_WRITER_BYTES_CONSUMED"and v["actual_cases"]==128 and
          v["actual_axis_writer_calls"]==256 and all(v[k]is False for k in C.scopes()),"real complete independent raw scope")
        result=dict(input_plan_ref=plan,numpy_ref=prior,canary_ref=canary,device_proof_ref=proof,
          numeric_ref=numeric,independent_ref=independent,actual_cli_refs=clis)
    except BaseException as e:ctl.primary=e
    finally:
        for one in controllers:
            try:one.cleanup()
            except BaseException as e:one.secondary.append("cleanup capture: "+repr(e))
        secondary=[e for one in controllers for e in one.secondary];first=next((repr(one.primary)for one in controllers if one.primary),None)
        snapshot=None
        try:snapshot=C.snapshot(out)
        except BaseException as e:secondary.append("output1GiB: "+repr(e))
        terminal=dict(schema="skvq.actual-writer.owned-host/v1",status="ACTUAL_WRITER_RAW_CONSUMED_PENDING_WHOLE"if result and not first and not secondary else"FAILED",
          source_ref=source,calibration_whole_ref=whole,calibration_whole_ref_file=C.ref(whole_file),result=result,
          owned=[e for one in controllers for e in one.owned],capspent=[e for one in controllers for e in one.spend],
          primary=first,secondary=secondary,elapsed_seconds=time.monotonic()-began,device_block_seconds=TOTAL,
          independent_cpu_block_seconds=TOTAL,total_seconds=2*TOTAL,cleanup_included_seconds=2*CLEANUP,
          actual_cleanup_seconds=sum(one.cleanup_spent for one in controllers),portfolio_cutoff_epoch=C.CUT,
          original_Control_source=Controller.donor_source,original_Control_AST=Controller.original_ast_sha256,
          adapted_Control_AST=Controller.adapted_ast_sha256,literal_delta=Controller.literal_delta,
          host_pid=os.getpid(),protected0_3=controllers[0].protected,actual_npu_observations=controllers[0].observations,
          output_budget_snapshot=snapshot,output_peak_not_measured=True,CPU_QUEUE_no_peer_admission=True,**C.scopes())
        ref=C.publish(out/"HOST_RESULT.json",terminal);print(json.dumps(ref,sort_keys=True),flush=True)
    if terminal["primary"]:raise ValueError(terminal["primary"])
    C.need(not terminal["secondary"],"cleanup/output cannot promote")
def main():
    p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true");p.add_argument("--source-manifest-sha256")
    p.add_argument("--calibration-whole-ref-json");p.add_argument("--output");a=p.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,**C.scopes())));return
    C.need(a.calibration_whole_ref_json and a.output,"strict current real whole/newroot");execute(a)
if __name__=="__main__":main()
