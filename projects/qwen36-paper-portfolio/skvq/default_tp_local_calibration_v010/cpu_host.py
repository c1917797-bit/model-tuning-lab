"""DEFAULT OFF MAIN-owned Devices[] calibration. Reuse exact reviewed Control body.
CPU_QUEUE: no peer lease or accelerator reservation; no observe()/npu-smi.
"""
import argparse,ast,json,os,re,shutil,stat,subprocess,sys,time,traceback,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import common as C
TOTAL=600;CLEANUP=90;GIB=2**30;OUTCAP=32*2**20
OWNER="skvq-default-tp-local-calibration-v1-010"
IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1"
PY="/usr/local/python3.12.13/bin/python3";DOCKER="/usr/bin/docker";PRLIMIT="/usr/bin/prlimit"
def newroot(path):
    p=Path(path);C.need(p.is_absolute()and".."not in p.parts and p.parent==C.ROOT.parent and
      p.parent.resolve()==p.parent and re.fullmatch("run-skvq-default-tp-local-010-[a-zA-Z0-9-]+",p.name)and
      not p.exists()and not p.is_symlink(),"exact absent CPU hostroot")
    p.mkdir(mode=0o700);return p
def environment():
    return dict(TORCH_DEVICE_BACKEND_AUTOLOAD="0",ASCEND_RT_VISIBLE_DEVICES="",
      PYTHONDONTWRITEBYTECODE="1",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",
      OPENBLAS_NUM_THREADS="1",NUMEXPR_NUM_THREADS="1")
def guest_args(source,whole_file,root,mode):
    return [str(C.ROOT/"cpu_entry.py"),"--execute","--source-manifest-sha256",source["sha256"],
      "--whole-ref-json",str(whole_file),"--output",str(root/"work"),"--feature-mode",mode]
def mounted(mounts,path):
    p=Path(path);return any(p==Path(dst)or Path(dst)in p.parents for dst in mounts)
def mount_set(out,whole_file,whole_ref):
    manifest=C.bound(C.reference(HERE/"SOURCE_MANIFEST.json"));whole=C.bound(whole_ref)
    from whole_precheck import envelope
    envelope(whole)
    captured=Path(whole["original_capture_host_result_ref"]["path"]).parent
    derived=Path(whole["host_result_ref"]["path"]).parent
    C.need(captured.parent==C.ROOT.parent and
      re.fullmatch("run-skvq-current72h-projection-014-[a-zA-Z0-9-]+",captured.name)and
      derived.parent==C.ROOT.parent and re.fullmatch("run-skvq-capture014-offline-004-[a-zA-Z0-9-]+",derived.name),
      "exact original014 and distinct derived CPU experiment trees, not broad lowbit")
    prior=C.bound(whole["host_result_ref"],limit=64*2**20)
    C.need(len(prior["owned"])==1 and prior["owned"][0]["npu"]is False and
      prior["owned"][0]["released"]is True,"actual derived sole released CPU owner")
    # The fresh child independently verified these full original mounts. All now RO.
    mounts={d:(s,False)for d,(s,rw)in prior["owned"][0]["mounts"].items()}
    mounts.update({str(C.ROOT):(str(C.ROOT),False),str(captured):(str(captured),False),
      str(derived):(str(derived),False)})
    for ref in [whole_ref,whole["original_ref"],C.reference(whole_file),*manifest["dependencies"]]:
        p=Path(ref["path"])
        if not mounted(mounts,p):mounts[str(p)]=(str(p),False)
    index="/cache/efim/Qwen3.6-27B/model.safetensors.index.json"
    if not mounted(mounts,index):mounts[index]=(index,False)
    mounts[str(out)]=(str(out),True)
    C.need([dst for dst,(_,rw)in mounts.items()if rw]==[str(out)],"one exact experiment RW")
    for dst,(src,rw)in mounts.items():
        C.need((dst==src or (dst,src)==("/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v1",
          "/cache/cch/qwen36-damp-20261006/calibration-inputs/source-v2"))and Path(src).is_absolute()and
          Path(dst).is_absolute()and","not in src+dst and".."not in Path(src).parts and".."not in Path(dst).parts,
          "identity same-absolute mount; no guest alias guess")
        if not rw:C.need(not(Path(dst)==out or Path(dst)in out.parents or out in Path(dst).parents),
          "no read-only source/evidence overlap with writer tree")
    return mounts
def mount_adapter():
    row=C.CAPTURE_BINDINGS["mount_preflight.py"]
    module=C.donor("_skvq_cal010_mount_primitives",row["path"],row["sha256"])
    def observe(mounts,phase,source):
        rows,errors=module.inspect_mounts(mounts)
        return dict(schema="skvq.default-tp-local.mount-preflight/v1",phase=phase,source_ref=source,
          mounts=rows,errors=errors,passed=not errors,Devices_empty=True,no_NPU_access=True)
    return types.SimpleNamespace(observe=observe)
def control_class(source,resources,mounts,preflight):
    """Compile EXACT original Control AST in a NEW explicitly scoped namespace.
    No donor import, globals mutation, body rewrite or inherited capture identity.
    Four CPU-only adapters override devices/env/mounts/create/exec; observe refuses.
    """
    row=C.CAPTURE_BINDINGS["MAIN_HOST.py"]
    C.need(C.reference(row["path"])==row,"exact reviewed Control donor bytes")
    tree=ast.parse(Path(row["path"]).read_bytes(),filename=row["path"])
    nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Control"]
    C.need(len(nodes)==1,"one exact original Control")
    scope=dict(__name__="_skvq_cal010_exact_control",Path=Path,os=os,json=json,re=re,
      subprocess=subprocess,time=time,traceback=traceback,shutil=shutil,
      TOTAL=TOTAL,CLEANUP=CLEANUP,DEADLINE=C.CUT,OWNER=OWNER,HERE=C.ROOT,IMAGE=IMAGE,
      PY=PY,DOCKER=DOCKER,PRLIMIT=PRLIMIT,SMI="/usr/local/sbin/npu-smi",GIB=GIB,
      R=resources,M=preflight,closure=lambda:source,reference=C.reference,
      publish_json=C.publish,require=C.need)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),row["path"],"exec"),scope)
    original=scope["Control"]
    class CPUControl(original):
        def __init__(self,out,limit=TOTAL):
            C.need(limit==TOTAL,"unique fixed600 includes90")
            super().__init__(out,limit)
        def observe(self,*args,**kwargs):raise ValueError("CPU-only no accelerator observation/lease")
        def devices(self,npu):
            C.need(npu is False,"CPU-only Devices[]");return {}
        def env(self,npu):
            C.need(npu is False,"CPU-only environment");return environment()
        def mounts(self,npu,inputs=None):
            C.need(npu is False and inputs is None,"CPU-only prebound RO inputs");return mounts
        def create(self,phase,npu,mem,inputs=None):
            C.need(phase=="calibration"and npu is False and mem==8*GIB and inputs is None,
              "sole real Devices[] CPU8 stage, no NPU path")
            return super().create(phase,npu,mem,inputs)
        def exec(self,label,args,npu=False,cap=510,env=None):
            C.need(npu is False and env is None and label=="calibration128",
              "one fresh actual CPU child, immutable environment")
            return super().exec(label,args,False,min(cap,510),None)
    CPUControl.donor_source_ref=row
    CPUControl.donor_class_ast_sha256=__import__("hashlib").sha256(
      ast.dump(nodes[0],include_attributes=False).encode()).hexdigest()
    return CPUControl
def output_bytes(root):
    total=0
    for parent,dirs,files in os.walk(root,followlinks=False):
        C.need(all(not Path(parent,n).is_symlink()for n in dirs+files),"no output symlink")
        for name in files:
            p=Path(parent,name);s=p.stat();C.need(stat.S_ISREG(s.st_mode),"ordinary CPU output")
            total+=s.st_size;C.need(total<=OUTCAP,"32MiB complete output cap")
    return total
def execute(args):
    stage_start=time.monotonic()
    C.need(os.environ.get("MAIN_SKVQ_CALIBRATION_CPU_ENABLE")=="1","MAIN-only explicit CPU admission")
    C.need(time.time()+TOTAL<=C.CUT,"fixed portfolio clock,600incl90 fit")
    source=C.source(args.source_manifest_sha256)
    whole_file=Path(args.whole_ref_json);whole_ref=json.loads(whole_file.read_bytes())
    from calibration_inputs import inputs
    inputs(whole_ref) # actual new derived whole; old05a7 failed remains failed
    row=C.CAPTURE_BINDINGS["resources.py"];R=C.donor("_skvq_cal010_cpu_resources",row["path"],row["sha256"])
    R.helper();view=R.helper().cpu_view(os.getpid());os.sched_setaffinity(0,{min(view["effective_cpus"])})
    import resource
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    C.need(hard==resource.RLIM_INFINITY,"Docker CLI child only needs original unlimited hardAS")
    resource.setrlimit(resource.RLIMIT_AS,(R.HOST,hard))
    out=newroot(args.output);(out/"work").mkdir(mode=0o700)
    mounts=mount_set(out,whole_file,whole_ref);Controller=control_class(source,R,mounts,mount_adapter())
    ctl=Controller(out);result=None;cli=None
    ctl.start=stage_start;ctl.end=min(ctl.end,stage_start+TOTAL)
    ctl.left() # prior/source/all16384 precheck charged to the same600incl90
    try:
        ctl.create("calibration",False,8*GIB)
        cli=ctl.exec("calibration128",guest_args(source,whole_file,out,args.feature_mode))
        result_ref=C.reference(out/"work"/"CPU_WORKLOAD_RESULT.json");value=C.bound(result_ref)
        C.need(value["status"]=="CALIBRATION_CPU_WORKLOAD_CONSUMED_HOST_AUTHORITY_PENDING"and
          value["source_ref"]==source and value["capture_whole_ref"]==whole_ref and value["primary"]is None,
          "actual current CPU workload terminal, not source/library-only")
        result=dict(workload_ref=result_ref,actual_child_cli_ref=cli)
    except BaseException as e:ctl.primary=e
    finally:
        try:ctl.cleanup()
        except BaseException as e:ctl.secondary.append("cleanup persistence: "+repr(e))
        cap=None
        try:cap=output_bytes(out)
        except BaseException as e:ctl.secondary.append("complete output budget: "+repr(e))
        value=dict(schema="skvq.default-tp-local.owned-host/v1",
          status="CPU_CALIBRATION_WORKLOAD_COMPLETE_PENDING_WHOLE"if result and not ctl.primary and not ctl.secondary else"FAILED",
          source_ref=source,capture_whole_ref=whole_ref,capture_whole_ref_file=C.reference(whole_file),
          feature_mode=args.feature_mode,result=result,owned=ctl.owned,capspent=ctl.spend,
          primary=repr(ctl.primary)if ctl.primary else None,secondary=ctl.secondary,
          elapsed_seconds=time.monotonic()-ctl.start,total_seconds=TOTAL,cleanup_included_seconds=CLEANUP,
          actual_cleanup_seconds=ctl.cleanup_spent,portfolio_cutoff_epoch=C.CUT,
          donor_control_source_ref=Controller.donor_source_ref,
          exact_original_control_class_ast_sha256=Controller.donor_class_ast_sha256,
          CPU_QUEUE_no_peer_admission=True,Devices_empty=True,no_NPU_observation=True,
          output_bytes_snapshot=cap,output_peak_not_measured=True,
          native_ready=False,model_ready=False,performance_ready=False,task_ready=False)
        ref=C.publish(out/"HOST_RESULT.json",value);print(json.dumps(ref,sort_keys=True),flush=True)
    if ctl.primary:raise ctl.primary
    C.need(not ctl.secondary,"cleanup/output failure cannot pass")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--execute",action="store_true")
    ap.add_argument("--source-manifest-sha256");ap.add_argument("--whole-ref-json");ap.add_argument("--output")
    ap.add_argument("--feature-mode",choices=("original","bf16-exact-cpu32"));a=ap.parse_args()
    if not a.execute:print(json.dumps(dict(default_enabled=False,Devices_empty=True,model_ready=False)));return
    C.need(a.whole_ref_json and a.output and a.feature_mode,"explicit actual capture/CPU leaf/precision")
    execute(a)
if __name__=="__main__":main()
