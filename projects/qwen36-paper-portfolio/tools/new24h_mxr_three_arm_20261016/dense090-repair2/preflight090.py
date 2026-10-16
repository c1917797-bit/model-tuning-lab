"""Devices[] exact source/argv/frontend checks before model allocation."""
import argparse,ast,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','actual Devices[] CPU environment')
 for n,r in m['files'].items():
  if n.endswith('.py'):ast.parse(C.checked(r).read_bytes())
 from client090 import warmup_transform
 fn=warmup_transform(C.checked(C.DRIVER).read_bytes());args=C.server_command();C.need('--enforce-eager'in args and '--no-enable-prefix-caching'in args and '--no-async-scheduling'in args and args[args.index('--max-model-len')+1]=='17408','actual original005-derived argv')
 import unittest
 result=unittest.TextTestRunner(stream=sys.stderr).run(unittest.defaultTestLoader.discover(str(P),pattern='test_090.py'));C.need(result.wasSuccessful()and result.testsRun==6 and not result.skipped,'exact actual source controls')
 C.need('torch'not in sys.modules and 'torch_npu'not in sys.modules,'stdonly no fake platform parser')
 C.write(a.output,dict(schema='dense.sameimage-source-preflight/v090',source=sr,Devices=[],NPU=False,tests=6,pass_software=True,native_runtime_parser_checked=False,argv=args));return 0
if __name__=='__main__':raise SystemExit(main())
