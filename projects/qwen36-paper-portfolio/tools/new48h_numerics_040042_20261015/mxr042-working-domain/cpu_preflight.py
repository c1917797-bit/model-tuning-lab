"""Actual Devices[] -I CLI/source/real saved selection preflight; no torch import."""
import argparse,hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def ref(p):
 b=Path(p).read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
 need(ref(r['path'])==r,'exact source/input');return Path(r['path']).read_bytes()
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=json.loads(checked(sr));need(m['schema']=='mxr.saved-frame-attribution-source/v042'and m['default_enabled']is False,'actual019 source')
 need(not any(Path('/dev/davinci'+str(i)).exists()for i in range(8))and not Path('/dev/davinci_manager').exists(),'actual Devices[]')
 for r in m['files'].values():checked(r)
 def load(name,r):
  need(name not in sys.modules,'no foreign cold-test module');s=importlib.util.spec_from_file_location(name,r['path']);v=importlib.util.module_from_spec(s);sys.modules[name]=v;exec(compile(checked(r),r['path'],'exec'),v.__dict__);return v
 load('once_contract',m['original_contract']);L=load('_actual020_lifecycle',m['original_lifecycle']);T=load('_actual020_integration',m['files']['lifecycle_integration.py']);integration=T.check(L)
 environment=load('_actual025_environment',m['files']['physical_environment.py']).check(m['original_contract'])
 rows=[]
 # Same-image actual Torch CPU controls and HF32-property availability, no device operations.
 proof=load('_actual042_sourceproof',m['files']['source_proof.py']).check(m['native_source_refs'])
 for args in([sys.executable,'-I','-B','-m','unittest','discover','-s',str(Path(__file__).resolve().parent),'-p','test_*.py','-v'],[sys.executable,'-I','-B',m['files']['precision_probe.py']['path'],'--execute']):
  test=subprocess.run(args,capture_output=True,text=True,timeout=60);need(test.returncode==0,'new027 CPU math/precision API preflight: '+test.stderr);rows.append(dict(argv=args,returncode=test.returncode,stdout=test.stdout,stderr=test.stderr))
 for name in('select_frames.py','closure.py','replay.py','consume.py','mainhost.py'):
  argv=[sys.executable,'-I','-B',m['files'][name]['path']];v=subprocess.run(argv,capture_output=True,text=True,timeout=20);need(v.returncode==0 and json.loads(v.stdout)==dict(enabled=False,NPU=False),'actual isolated defaultOFF CLI '+name);rows.append(dict(argv=argv,returncode=v.returncode,stdout=v.stdout,stderr=v.stderr))
 r=m['files']['select_frames.py'];s=importlib.util.spec_from_file_location('_actual019_select',r['path']);S=importlib.util.module_from_spec(s);exec(compile(checked(r),r['path'],'exec'),S.__dict__);selection=S.select(m['original_report']);target=a.output.parent/'SELECTION.json'
 need(not target.exists()and not a.output.exists(),'new CPU evidence')
 with target.open('x')as f:json.dump(selection,f,sort_keys=True);f.write('\n')
 need(not any(n=='torch'or n.startswith(('torch.','torch_npu','vllm'))for n in sys.modules),'CPU source/IO did not import platform')
 with a.output.open('x')as f:json.dump(dict(schema='mxr.saved-frame-devicefree/v042',source=sr,pass_software=True,Devices=[],NPU=False,selection=ref(target),actual_default_OFF_CLIs=rows,actual_native_source_proof=proof,actual_lifecycle_integration=integration,actual_create_inspect_environment=environment,source_closure_checked=True),f,sort_keys=True);f.write('\n')
 return 0
if __name__=='__main__':raise SystemExit(main())
