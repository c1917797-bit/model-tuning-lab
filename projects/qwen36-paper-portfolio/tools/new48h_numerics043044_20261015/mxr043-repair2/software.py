"""Actual six new source/ARM controls in owned Devices[]; not GDN numerics."""
import argparse,importlib.util,json,os,sys,unittest,unittest.mock
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
 a=argparse.ArgumentParser(allow_abbrev=False);a.add_argument('--execute',action='store_true');a.add_argument('--source-ref');a.add_argument('--output',type=Path);v=a.parse_args()
 if not v.execute:print('{"enabled":false,"NPU":false}');return 0
 s=importlib.util.spec_from_file_location('_once007_entry',P/'entry.py');E=importlib.util.module_from_spec(s);s.loader.exec_module(E);sr=json.loads(v.source_ref);E.current(sr)
 if os.environ.get('ASCEND_RT_VISIBLE_DEVICES')!=''or os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')!='0'or list(Path('/dev').glob('davinci[0-9]*')):raise ValueError('actual Devices[] CPU only')
 s=importlib.util.spec_from_file_location('_once007_tests',P/'test_contract.py');T=importlib.util.module_from_spec(s);s.loader.exec_module(T)
 suite=unittest.defaultTestLoader.loadTestsFromModule(T)
 s=importlib.util.spec_from_file_location('_cap009_tests',P/'test_source_cap48.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C);suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(C))
 s=importlib.util.spec_from_file_location('_binding010_suite',P/'test_prefix_binding.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C);suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(C))
 s=importlib.util.spec_from_file_location('_ownership013_suite',P/'test_ownership_order.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C);suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(C));expected=C.O.SOFTWARE_CASES
 result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
 if not(result.wasSuccessful()and result.testsRun==expected and not result.skipped):raise ValueError('actual shared source/cap48/binding controls')
 s=importlib.util.spec_from_file_location('_043_new_tests',P/'test_043.py');N=importlib.util.module_from_spec(s);s.loader.exec_module(N);extra=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(N))
 if not(extra.wasSuccessful()and extra.testsRun==4 and not extra.skipped):raise ValueError('actual043 admission/consumer controls')
 external_suite=unittest.TestSuite()
 for name in('test_disk_relocation.py','test_external_output.py'):
  s=importlib.util.spec_from_file_location('_043_external_'+name[:-3],P/name);X=importlib.util.module_from_spec(s);s.loader.exec_module(X);external_suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(X))
 external=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(external_suite)
 if not(external.wasSuccessful()and external.testsRun==8 and not external.skipped):raise ValueError('actual external-output source/create/inspect/resource controls')
 s=importlib.util.spec_from_file_location('_043R2_actual_IPC',P/'ipc_controls.py');IPC=importlib.util.module_from_spec(s);s.loader.exec_module(IPC)
 actual_ipc=IPC.run('/adakv-results')
 if not(actual_ipc['actual_Linux_AF_UNIX']and actual_ipc['direct_UUID4_scan_consume_pass']and actual_ipc['nested_original_rejection_pass']and actual_ipc['bad_basename_original_rejection_pass']):raise ValueError('actual Linux IPC original-scan controls mandatory')
 with(v.output.parent/'IPC_CONTROLS.json').open('x')as receipt:json.dump(actual_ipc,receipt,sort_keys=True);receipt.write('\n')
 import errno,uuid
 try:
  fd=os.open('/.external-output-readonly-proof-'+uuid.uuid4().hex,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 except OSError as error:
  if error.errno!=errno.EROFS:raise ValueError('actual rootfs readonly proof requires EROFS')from error
 else:
  os.close(fd);raise ValueError('root filesystem unexpectedly writable; failed proof file retained')
 if any(n=='torch'or n.startswith(('torch.','torch_npu','vllm'))for n in sys.modules):raise ValueError('cold suite must not import device/model')
 E.current(sr)
 if not(v.output.is_absolute()and v.output.parent.is_dir()and not v.output.exists()):raise ValueError('new sole output')
 with v.output.open('x')as h:json.dump(dict(schema='mxr.observerless-once-cold-software/v1',source=sr,actual_cases=expected,actual043_cases=extra.testsRun,actual043_all_pass=True,actual_IPC_controls=actual_ipc,external_output_cases=external.testsRun,external_output_all_pass=True,actual_rootfs_write_errno=errno.EROFS,all_pass=True,Devices=[],NPU=False,performance_ready=False,task_ready=False),h,sort_keys=True);h.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
