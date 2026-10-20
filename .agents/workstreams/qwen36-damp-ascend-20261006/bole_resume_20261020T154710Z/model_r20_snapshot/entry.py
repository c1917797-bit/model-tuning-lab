"""Cold source/software entry, never a model or device launcher."""
import argparse,hashlib,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-audit',action='store_true');p.add_argument('--software',action='store_true');p.add_argument('--component-refs-json');a=p.parse_args()
 if not(a.source_audit or a.software or a.component_refs_json):print('{"enabled":false,"model_ready":false,"NPU":false}');return 0
 m=json.loads((P/'SOURCE.json').read_bytes())
 for n,r in m['files'].items():
  b=(P/n).read_bytes()
  if len(b)!=r['bytes']or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('source closure '+n)
 import root_repeat_witness as RW
 RW.cpu_preflight(__import__('sourceio'),m,P)
 if a.software:
  import unittest
  s=unittest.defaultTestLoader.discover(str(P),pattern='test*.py',top_level_dir=str(P))
  r=unittest.TextTestRunner().run(s);return 0 if r.wasSuccessful()and r.testsRun==150 else 3
 if a.component_refs_json:
  import sourceio as C,component_gate as G
  G.consume(C,json.loads(a.component_refs_json),gdn_math=C.ref(P/'core112.py'),paged_math=C.ref(P/'adapter.py'))
  print('{"actual_component_inputs_admitted":true,"model_ready":false,"NPU":false}');return 0
 print('{"source_audited":true,"model_ready":false,"NPU":false}');return 0
if __name__=='__main__':raise SystemExit(main())
