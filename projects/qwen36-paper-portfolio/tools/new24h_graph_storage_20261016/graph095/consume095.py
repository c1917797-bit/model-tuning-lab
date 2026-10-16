"""Devices[] independent retained-raw graph replay consumer."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import common095 as C
def consume(t,m,sr,stage_ref):
 import raw_codec as RC,graph094 as G,recipe094,oracle as R,precast as PRE
 RC.install(t);stage=C.obj(stage_ref);C.need(stage['schema']=='deltalog.graph-stage/v095'and stage['source']==sr and stage['primary']is None and stage['NPU']is True and stage['qualified']is False,'actual095 complete graph NPU stage');cases=stage['result']['cases'];C.need([c['batch']for c in cases]==[1,16],'B1/B16 exact order');reports=[]
 for case in cases:
  batch=case['batch'];initial,events=recipe094.recipe(t,batch,16);anchor=t.load(C.checked(case['initial']),map_location='cpu',weights_only=False);C.need(anchor['seed']==2610169401+batch and PRE.bits(t,anchor['initial'],initial),'independent initial recipe');ledger=initial.double().clone();previous=None
  C.need([r['step']for r in case['rows']]==list(range(16)),'16 exact real replay rows')
  for record,event in zip(case['rows'],events):
   raw=t.load(C.checked(record['raw']),map_location='cpu',weights_only=False);before,after=raw['before'],raw['after'];C.need(len(before)==len(after)==len(raw['debug_after'])==13,'13 actual full operands')
   C.need(set(raw['event'])==set(event)and set(raw['event']['resets'])==set(event['resets']),'exact event schema')
   C.need(set(raw['event']['inputs'])==set(G.INPUTS),'exact5input event ABI')
   for k in G.INPUTS:C.need(PRE.bits(t,before[G.INPUTS.index(k)],event['inputs'][k])and PRE.bits(t,raw['event']['inputs'][k],event['inputs'][k]),'independent changed input recipe '+k)
   C.need(PRE.bits(t,before[11],event['sequence'])and PRE.bits(t,before[12],event['ids'])and PRE.bits(t,raw['event']['sequence'],event['sequence'])and PRE.bits(t,raw['event']['ids'],event['ids']),'independent sequence/slot recipe')
   C.need(len(raw['pointer_before'])==13 and raw['pointer_before']==raw['pointer_after']and all(type(p)is int and p>0 for p in raw['pointer_before']),'actual fixed13pointer graph ABI')
   expected=[initial.clone(),t.zeros_like(before[6]),t.zeros_like(before[7]),t.zeros_like(before[8]),t.zeros_like(before[9]),t.zeros_like(before[10])]if previous is None else[x.clone()for x in previous]
   for slot,value in event['resets'].items():
    C.need(PRE.bits(t,raw['event']['resets'][slot],value),'actual reset recipe');expected[0][slot]=value;ledger[slot]=value.double().clone()
    for x in expected[1:]:x[slot].zero_()
   C.need(all(PRE.bits(t,x,y)for x,y in zip(expected,before[5:11])),'all6state byte continuity including capture/warmup restore and slot reset')
   metrics=G.inspect_step(t,R,PRE,before,after,raw['output'],raw['debug_after'],raw['debug_output'],raw['actual_precast_FP32'],ledger)
   C.need(metrics['passed'],'independent actual graph numeric/state predicate');previous=after[5:11];reports.append(dict(batch=batch,step=record['step'],raw=record['raw'],metrics=metrics))
 C.need(len(reports)==32,'all32 actual replays');return dict(schema='deltalog.graph-independent/v095',source=sr,actual_stage=stage_ref,rows=reports,pass_gate=True,qualified=False,full_mixed_graph_qualified=False,old_FAIL_unchanged=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--stage-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('disabled');return 0
 sr=json.loads(a.source_ref);m=C.source(sr);C.window(m)
 import torch as t
 t.set_num_threads(1);C.need('torch_npu'not in sys.modules,'no backend import')
 try:v=consume(t,m,sr,json.loads(a.stage_ref))
 except BaseException as e:
  import traceback
  C.write(a.output,dict(schema='deltalog.graph-independent/v095',source=sr,actual_stage=json.loads(a.stage_ref),pass_gate=False,qualified=False,full_mixed_graph_qualified=False,primary=repr(e),traceback=traceback.format_exc()));return 3
 C.write(a.output,v);return 0
if __name__=='__main__':raise SystemExit(main())
