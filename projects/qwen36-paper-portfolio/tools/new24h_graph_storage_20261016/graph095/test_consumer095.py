"""Actual retained-raw consumer ABI, CPU reference-generated test data only."""
import copy,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import torch as t,common095 as C,consume095 as S,recipe094,oracle as R,precast as PRE,direct_round,raw_codec as RC
t.set_num_threads(1)
class Test(unittest.TestCase):
 def test_real_store_decode_consumer32_and_wrongscale_negative(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td);store=RC.Store(t,p,768*2**20);source=p/'software-source';source.write_text('software fixture, NOT hardware');sr=C.ref(source);cases=[]
   for batch in(1,16):
    initial,events=recipe094.recipe(t,batch,16);slots=initial.shape[0];state=dict(base=initial.clone(),k_log=t.zeros((slots,4,7,128),dtype=t.bfloat16),u_log=t.zeros((slots,12,7,128)),lambda_log=t.zeros((slots,12,16)),decay=t.zeros((slots,12,16)),length=t.zeros((slots,12,16),dtype=t.int32));ledger=initial.double().clone();rows=[];anchor=store.write(p/('initial-%d.pt'%batch),dict(seed=2610169401+batch,initial=initial))
    for step,e in enumerate(events):
     for slot,value in e['resets'].items():
      state['base'][slot]=value;ledger[slot]=value.double().clone()
      for name in('k_log','u_log','lambda_log','decay','length'):state[name][slot].zero_()
     before=[e['inputs'][k].clone()for k in('query','key','value','g','beta')]+[state[k].clone()for k in('base','k_log','u_log','lambda_log','decay','length')]+[e['sequence'].clone(),e['ids'].clone()];after=[x.clone()for x in before];truth=[]
     for j,slot in enumerate(e['ids'].tolist()):
      previous=ledger[slot];current,y=R.advance(t,previous,e['inputs'],j);truth.append(y);n=int(state['length'][slot,0,0])
      if n==7:
       after[5][slot]=current.float()
       for x in after[6:11]:x[slot].zero_()
      else:
       d=state['decay'][slot,:,0]+e['inputs']['g'][j];after[9][slot,:,0]=d;after[10][slot,:,0]=n+1;after[6][slot,:,n]=e['inputs']['key'][j];after[8][slot,:,n]=d
       for head in range(12):
        decayed=previous[head]*__import__('math').exp(float(e['inputs']['g'][j,head]));u=float(e['inputs']['beta'][j,head])*(e['inputs']['value'][j,head].double()-decayed@e['inputs']['key'][j,head//3].double());after[7][slot,head,n]=u.float()
      ledger[slot]=current
     truth=t.stack(truth);pre=truth.float();out=direct_round.round_bf16(t,pre.double());state=dict(zip(('base','k_log','u_log','lambda_log','decay','length'),after[5:11]));raw=dict(event=e,before=before,after=after,output=out,debug_after=[x.clone()for x in after],debug_output=out.clone(),actual_precast_FP32=pre,pointer_before=list(range(100,113)),pointer_after=list(range(100,113)),graph_type='software-only-not-an-NPUGraph')
     rr=store.write(p/('B%d-%02d.pt'%(batch,step)),raw);rows.append(dict(step=step,raw=rr))
    cases.append(dict(batch=batch,initial=anchor,rows=rows))
   stage=p/'STAGE.json';C.write(stage,dict(schema='deltalog.graph-stage/v095',source=sr,primary=None,NPU=True,qualified=False,result=dict(cases=cases)))
   result=S.consume(t,{},sr,C.ref(stage));self.assertEqual(len(result['rows']),32);self.assertTrue(result['pass_gate']);self.assertFalse(result['qualified'])
   # Actual saved-raw reader is re-used; alter one independently read frame.
   r=cases[0]['rows'][0]['raw'];raw=t.load(C.checked(r),map_location='cpu',weights_only=False);raw['actual_precast_FP32']*=2;raw['output']=direct_round.round_bf16(t,raw['actual_precast_FP32'].double());raw['debug_output']=raw['output'].clone();bad=store.write(p/'wrong-scale.pt',raw);cases[0]['rows'][0]['raw']=bad;badstage=p/'BAD.json';C.write(badstage,dict(schema='deltalog.graph-stage/v095',source=sr,primary=None,NPU=True,qualified=False,result=dict(cases=cases)))
   with self.assertRaisesRegex(ValueError,'numeric/state predicate'):S.consume(t,{},sr,C.ref(badstage))
if __name__=='__main__':unittest.main()
