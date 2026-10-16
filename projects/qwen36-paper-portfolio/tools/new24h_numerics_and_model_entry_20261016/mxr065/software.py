"""Actual six new source/ARM controls in owned Devices[]; not GDN numerics."""
import argparse,importlib.util,json,os,sys,unittest,unittest.mock
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from software_contract import SOFTWARE_CASES
def main():
 a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('--execute',action='store_true');a.add_argument('--source-ref');a.add_argument('--output',type=Path);v=a.parse_args()
 if not v.execute:print('{"enabled":false,"NPU":false}');return 0
 s=importlib.util.spec_from_file_location('_once007_entry',P/'entry.py');E=importlib.util.module_from_spec(s);s.loader.exec_module(E);sr=json.loads(v.source_ref);E.current(sr)
 if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci[0-9]*')):raise ValueError('actual Devices[] CPU only')
 s=importlib.util.spec_from_file_location('_once007_tests',P/'test_contract.py');T=importlib.util.module_from_spec(s);s.loader.exec_module(T)
 result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(T))
 if not(result.wasSuccessful()and result.testsRun==SOFTWARE_CASES and not result.skipped):raise ValueError('actual six new controls')
 if any(n=='torch'or n.startswith(('torch.','torch_npu','vllm'))for n in sys.modules):raise ValueError('cold suite must not import device/model')
 E.current(sr)
 from plugin_discovery import component,static_discovery
 component_root,_=component(E.current(sr)['plugin_source']);discovery=static_discovery(component_root)
 if not(v.output.is_absolute()and v.output.parent.is_dir()and not v.output.exists()):raise ValueError('new sole output')
 s=importlib.util.spec_from_file_location('_047_IPC',P/'ipc_controls.py');IPC=importlib.util.module_from_spec(s);s.loader.exec_module(IPC);ipc=IPC.run('/adakv-results')
 import errno,uuid
 try:fd=os.open('/.047-readonly-'+uuid.uuid4().hex,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 except OSError as error:
  if error.errno!=errno.EROFS:raise
 else:os.close(fd);raise ValueError('actual rootfs is writable')
 with(v.output.parent/'IPC_CONTROLS.json').open('x')as f:json.dump(ipc,f,sort_keys=True);f.write('\n')
 with v.output.open('x')as h:json.dump(dict(schema='mxr.observerless-once-cold-software/v1',source=sr,actual_cases=SOFTWARE_CASES,all_pass=True,Devices=[],NPU=False,actual044_static_discovery=discovery,actual_IPC_controls=ipc,actual_rootfs_write_errno=errno.EROFS,performance_ready=False,task_ready=False),h,sort_keys=True);h.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
