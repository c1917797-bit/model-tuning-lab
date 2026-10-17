"""Isolated no-backend source frontdoor, before full original heavy binder."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--template-sha256');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 raw=(P/'SOURCE_TEMPLATE.json').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=a.template_sha256:raise ValueError('exact reviewed template SHA before own reads')
 m=json.loads(raw);r=m['files']['prebind_static.py'];b=(P/'prebind_static.py').read_bytes()
 if r['path']!=m['root']+'/prebind_static.py'or(len(b),hashlib.sha256(b).hexdigest())!=(r['bytes'],r['sha256']):raise ValueError('exact own cheap helper before import')
 s=importlib.util.spec_from_file_location('_r21_checked_prebind',P/'prebind_static.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
 tr=dict(path=m['root']+'/SOURCE_TEMPLATE.json',bytes=len(raw),sha256=a.template_sha256)
 bound,report=g.prepare(m,tr,P,runtime=False)
 if any(n in sys.modules for n in('torch','torch_npu','vllm','vllm_ascend')):raise ValueError('stdlib-only cheap source check')
 print(json.dumps(report,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
