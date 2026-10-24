"""Original software then actual same-A cast comparison; no NPU visibility."""
import argparse,json,os,sys,time,types,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
LEAF=Path("/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_ACTUAL_INVERSE_ROUNDING_CPU_20261024_V2")/'cpu'
BASE_GUEST={'path':"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_continuous_h_counterfactual_owner_prepare_v1/guest_entry.py",'bytes':6112,'sha256':'859ff6c18e8bbe4af62988b262e7eb0028d7042ba5fb3c2abec9984132d73948'}
PLAN={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_upstream_bridge_owned_prepare_v1_20261024/INPUTS.json","bytes":8157,"sha256":"7357804ff9fc1162dfa15289ba3ebdc7f2eea26475337d23c3418b54bda9f424"}
def need(v,s):
    if not v:raise ValueError(s)
def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(r,n):
    p=Path(r['path']);need(ref(p)==r and not any(q.is_symlink()for q in(p,*p.parents)),'pinned mounted source')
    m=types.ModuleType(n);m.__file__=r['path'];exec(compile(p.read_bytes(),r['path'],'exec'),m.__dict__);return m
def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--stage',choices=('software','analysis'));p.add_argument('--output',type=Path);p.add_argument('--deadline-epoch',type=float);a=p.parse_args()
    if a.stage is None:
        need(a.output is a.deadline_epoch is None,'no ignored arguments');print('{"enabled":false,"NPU":false}');return
    need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not any(Path('/dev/davinci'+str(i)).exists()for i in range(8))and 'torch_npu'not in sys.modules,'original Devices[] environment')
    wanted=LEAF/('SOFTWARE.json'if a.stage=='software'else'ACTUAL_CAST.json')
    need(a.output==wanted and wanted.parent.is_dir()and not wanted.exists()and not any(q.is_symlink()for q in(wanted,*wanted.parents)),'only new registered exclusive RW output')
    if a.stage=='software':
        need(a.deadline_epoch is None,'original software60 cap')
        load(BASE_GUEST,'_actual_cast_original_software').software(wanted)
    else:
        need(a.deadline_epoch is not None and time.time()<a.deadline_epoch and len(os.sched_getaffinity(0))==1,'actual oneCPU remaining deadline')
        import signal
        def timeout(*unused):raise TimeoutError('original remaining-derived analysis deadline')
        signal.signal(signal.SIGALRM,timeout);signal.setitimer(signal.ITIMER_REAL,a.deadline_epoch-time.time())
        A=load(ref(HERE/'analysis.py'),'_actual_cast_analysis')
        plan=json.loads(A.checked(PLAN).read_bytes())
        import torch
        torch.set_num_threads(1)
        need('torch_npu'not in sys.modules and not any('ascend'in os.readlink('/proc/self/fd/'+n).lower()or'davinci'in os.readlink('/proc/self/fd/'+n).lower()for n in os.listdir('/proc/self/fd') if Path('/proc/self/fd/'+n).exists()),'no Ascend device descriptors')
        result=A.analyze(torch,plan)
        raw=(json.dumps(result,sort_keys=True)+'\n').encode();need(len(raw)<=8*2**20 and time.time()<a.deadline_epoch,'original report/deadline cap')
        with wanted.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
        signal.setitimer(signal.ITIMER_REAL,0)
    print('MAIN_MXR_ACTUAL_CAST_'+a.stage.upper()+' '+json.dumps(ref(wanted),sort_keys=True),flush=True)
if __name__=='__main__':main()
