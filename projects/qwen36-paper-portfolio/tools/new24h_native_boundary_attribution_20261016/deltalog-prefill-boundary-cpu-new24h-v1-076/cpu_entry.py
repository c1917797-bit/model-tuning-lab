"""Real same-image CPU frontdoor before any torch import; no NPU validation."""
import importlib.util,json,os,sys
from pathlib import Path
def main():
 if '--execute'not in sys.argv:print('{"enabled":false,"NPU":false}');return 0
 if sys.version_info[:2]!=(3,12)or os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci[0-9]*')):raise ValueError('actual guestPython3.12/Devices[]/autoload0')
 if len(os.sched_getaffinity(0))!=1:raise ValueError('actual one guestCPU')
 out=Path(sys.argv[sys.argv.index('--output')+1]);out.parent.is_dir()or(_ for _ in()).throw(ValueError('owned existing output parent'))
 import torch
 torch.set_num_threads(1)
 if torch.empty(1).device.type!='cpu':raise ValueError('actual CPU torch')
 proof=dict(schema='deltalog.actual-sameimage-CPU-runtime/v074',pid=os.getpid(),python=sys.version,executable=sys.executable,torch_version=str(torch.__version__),affinity=sorted(os.sched_getaffinity(0)),cgroup=Path('/proc/self/cgroup').read_text(),Devices=[],NPU=False)
 with(out.parent/'CPU_RUNTIME.json').open('x',encoding='utf8')as f:json.dump(proof,f,sort_keys=True);f.write('\n')
 p=Path(__file__).resolve().parent/'diagnose.py';s=importlib.util.spec_from_file_location('_actual074diagnosis',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m.main()
if __name__=='__main__':raise SystemExit(main())
