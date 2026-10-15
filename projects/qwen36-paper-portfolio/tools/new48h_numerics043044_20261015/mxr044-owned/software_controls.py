"""Explicit sameimage CPU geometry and actual wrapper CLI/contract controls."""
import argparse,json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common as C
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--output');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);component=C.obj(m['component044_source'])
 import torch
 torch.set_num_threads(1);B=C.load(component['files']['block_refine.py'],'_owned044_meta_block');Q=C.load(component['files']['qualification_probe.py'],'_owned044_recipe');rows=[]
 for name,cu in Q.recipes():
  A=torch.empty((1,cu[-1],12,64),dtype=torch.float32,device='meta');X=torch.empty_like(A);out=torch.empty_like(A,dtype=torch.bfloat16);tiles,groups=B.plan(cu,cu[-1]);value=B._correct_blocks(torch,A,X,groups,out,B.allocate(torch,A));budget=B.budget(cu,cu[-1]);C.need(value.shape==A.shape and value.dtype==torch.bfloat16 and value.device.type=='meta'and budget['formal_one_live_fit'],'actual Torch Meta shape/layout and original512MiB bound');rows.append(dict(name=name,cu=cu,chunks=len(tiles),budget=budget,shape=list(value.shape),outputs_required=3,Meta=True,numeric_qualified=False))
 results=[]
 for name in('mainhost.py','replay.py','consume.py','cpu_preflight.py'):
  argv=[sys.executable,'-I','-B',str(P/name)];r=subprocess.run(argv,capture_output=True,text=True,timeout=10);C.need(r.returncode==0 and json.loads(r.stdout)==dict(enabled=False,NPU=False),'real isolated defaultOFF '+name);results.append(dict(argv=argv,returncode=r.returncode))
 tests=subprocess.run([sys.executable,'-I','-B','-m','unittest','discover','-s',str(P),'-p','test_*.py','-v'],capture_output=True,text=True,timeout=45);C.need(tests.returncode==0,'actual own report/entry controls: '+tests.stderr)
 C.write(a.output,dict(source=sr,pass_software=True,ninecases=rows,defaultOFF=results,actual_controls=dict(returncode=tests.returncode,stdout=tests.stdout,stderr=tests.stderr),NPU=False,DSO_Meta=False,model_ready=False))
 return 0
if __name__=='__main__':raise SystemExit(main())
