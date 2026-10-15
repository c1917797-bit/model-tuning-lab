"""Devices[] actual044 independent receiver; failed metrics remain failed."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common as C
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for key in('source-ref','probe-ref','output'):p.add_argument('--'+key)
 a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr,pr=map(json.loads,(a.source_ref,a.probe_ref));m=C.source(sr);v=C.obj(pr);G=C.load(m['files']['probe_contract.py'],'_owned044_CPU_contract');C.need(G.ready(v,sr),'complete actual044 callback')
 component=C.obj(m['component044_source']);Q=C.load(component['files']['qualification_probe.py'],'_owned044_independent');target=Path(a.output);ir=target.with_name('INDEPENDENT044.json');C.need(not target.exists()and not ir.exists(),'exclusive result paths')
 code=Q.consume(m['component044_source'],v['actual_result'],str(ir));report=C.obj(C.ref(ir));C.need(code in(0,3)and report['source']==m['component044_source']and report['actual_result']==v['actual_result']and report['complete']is True and len(report['rows'])==9,'exact real independent nine-case result, no relabeling failure')
 raw=C.obj(v['actual_result']);C.need(raw['source']==m['component044_source']and raw['raws']==v['raws']and len(raw['raws'])==9 and len({r['path']for r in raw['raws']})==9,'same complete actual nine-case ledger');counts=[]
 import torch
 for rr in raw['raws']:
  row=torch.load(C.checked(rr),map_location='cpu',weights_only=True);C.need(len(row['outputs'])==3 and row['operator']==v['actual_algorithm_identity'],'each actual three outputs and actual037 operator identity retained');counts.append(len(row['outputs']))
 C.write(target,dict(schema='mxr.block-refinement-owned-consumer/v044',source=sr,component_source=m['component044_source'],actual_probe=pr,independent=C.ref(ir),rows=report['rows'],case_outputs=counts,complete=True,pass_gate=report['pass_gate'],independent_exit=code,numerical_qualification_granted=False,model_ready=False,performance_ready=False,task_ready=False,NPU=False))
 return 0
if __name__=='__main__':raise SystemExit(main())
