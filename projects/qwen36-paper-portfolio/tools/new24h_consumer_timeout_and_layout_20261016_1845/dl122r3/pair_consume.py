"""Independent one-pair statistics; same production library and actual calls."""
import argparse,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import api122 as A
from pair_metrics122 import arm,metadata_delta
def consume(d,c,di,ci,before,after,sr,count):
 m,_=A.qualify(sr);A.need(d['config']==c['config']and di==ci,'same exact run config and all actual token IDs')
 warmups=2;A.need(di['measured']==count and di['warmups']==warmups and len(di['prompts'])==count+warmups and all(len(x)==2048 and all(type(t)is int for t in x)for x in di['prompts'])and di['shared_prefix_tokens']==1024,'actual frozen 2K/C1 input arrays')
 dm,dc=arm(d,count);cm,cc=arm(c,count);A.need(dc==cc,'same actual HTTP completed decode count')
 A.need(len(before)==len(after)==4 and len({r['pid']for r in before})==4 and {r['pid']for r in before}=={r['pid']for r in after},'all four same actual worker lifetimes')
 old={r['pid']:r for r in before};hits=[]
 with A.context(m)as(v,pm):
  for row in after:
   prior=old[row['pid']];proof=metadata_delta(prior,row,cc,count)
   live=v['live106'].validate_delta(prior,row,m['production_source_ref'],m['production_qualification_ref'],expected_decode_calls=cc)
   A.need(row['proc_stat'].split(')')[-1].split()[19]==prior['proc_stat'].split(')')[-1].split()[19]and row['cgroup']==prior['cgroup'],'same start/cgroup throughout actual measurement')
   hits.append(dict(pid=row['pid'],cpu_metadata=proof,live=live))
 gain=cm['throughput']/dm['throughput']-1
 return dict(schema='deltalog.actual-single-pair-independent/v122',source=sr,production_source=m['production_source_ref'],qualification=m['production_qualification_ref'],dense=dm,candidate=cm,throughput_gain=gain,observed_worker_delta=hits,HTTP_decode_calls_per_layer=cc,screen_gain_at_least10percent=gain>=.1,smoke_pair=count==2,formal_three_rounds=False,task_accuracy=False,acceptance=False,scope='2K C1 sync eager HF32OFF PDCoff only')
def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 for k in('dense','candidate','dense-inputs','candidate-inputs','workers-before','workers-after','output'):p.add_argument('--'+k,required=True,type=Path)
 p.add_argument('--source-ref',required=True);p.add_argument('--requests',required=True,type=int,choices=(2,40));a=p.parse_args();get=lambda p:json.loads(p.read_bytes())
 A.write(a.output,consume(get(a.dense),get(a.candidate),get(a.dense_inputs),get(a.candidate_inputs),get(a.workers_before),get(a.workers_after),json.loads(a.source_ref),a.requests));return 0
if __name__=='__main__':raise SystemExit(main())
