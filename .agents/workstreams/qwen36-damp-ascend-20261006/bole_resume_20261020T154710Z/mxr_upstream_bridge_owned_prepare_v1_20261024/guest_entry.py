"""Original software controls then reviewed upstream bridge; Devices[] only."""
import argparse,hashlib,json,os,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE_GUEST={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_continuous_h_counterfactual_owner_prepare_v1/guest_entry.py","bytes":6112,"sha256":"859ff6c18e8bbe4af62988b262e7eb0028d7042ba5fb3c2abec9984132d73948"}
ANALYSIS={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_upstream_bridge_owned_prepare_v1_20261024/analyze_bridge.py","bytes":17457,"sha256":"b0868ef2867c04a99decf6071ad2bfe83d43849531bb7bd1888b7c4b8f9769e3"}
PLAN={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_upstream_bridge_owned_prepare_v1_20261024/INPUTS.json","bytes":8157,"sha256":"7357804ff9fc1162dfa15289ba3ebdc7f2eea26475337d23c3418b54bda9f424"}
LEAF=Path("/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_UPSTREAM_BRIDGE_CPU_20261024_V1/cpu")
def need(v,s):
    if not v:raise ValueError(s)
def checked(r):
    p=Path(r['path']);b=p.read_bytes()
    need(p.is_absolute()and not any(q.is_symlink()for q in(p,*p.parents))and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact reviewed guest/program/plan')
    return b
def load(r,n):
    m=types.ModuleType(n);m.__file__=r['path'];exec(compile(checked(r),r['path'],'exec'),m.__dict__);return m
def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--stage',choices=('software','analysis'));p.add_argument('--output',type=Path);p.add_argument('--deadline-epoch',type=float);a=p.parse_args()
    if a.stage is None:
        need(a.output is a.deadline_epoch is None,'no ignored guest arguments');print('{"enabled":false,"NPU":false}');return
    need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8)),'original Devices[] no-autoload environment')
    need(a.output==LEAF/('SOFTWARE.json'if a.stage=='software'else'BRIDGE.json')and a.output.parent.is_dir()and not a.output.exists(),'same-absolute sole owned RW leaf')
    B=load(ANALYSIS,'_reviewed_cpu_upstream_bridge');plan=json.loads(checked(PLAN));B.no_device()
    if a.stage=='software':
        need(a.deadline_epoch is None,'software has original child cap')
        B.source_contract(plan) # pinned small source AST only; no retained tensor read
        G=load(BASE_GUEST,'_unchanged_retained_software_guest')
        r=G.software(a.output)
    else:
        need(a.deadline_epoch is not None,'actual original remaining-derived CPU deadline')
        before=sys.argv[:]
        try:
            sys.argv=[B.__file__,'--execute','--inputs',PLAN['path'],'--output',str(a.output),'--deadline-epoch',str(a.deadline_epoch)]
            B.main()
        finally:sys.argv[:]=before
        r=ref(a.output)
    print('MAIN_MXR_UPSTREAM_BRIDGE_'+a.stage.upper()+' '+json.dumps(r,sort_keys=True),flush=True)
if __name__=='__main__':main()
