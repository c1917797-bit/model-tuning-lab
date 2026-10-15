"""Independent stdlib complete paired-report and real worker-hit consumer."""
import argparse,json,math,statistics
from pathlib import Path
def need(v,m):
 if not v:raise ValueError(m)
def arm(v):
 c=v['config'];s=v['summary'];rows=v['results']
 frozen=dict(input_tokens=32768,prefix_tokens=16384,output_tokens=1024,requests=40,concurrency=16,warmup_requests=2,ignore_eos=True)
 need(all(c[k]==x for k,x in frozen.items()),'exact performance input/protocol')
 need(len(rows)==40 and {x['index']for x in rows}==set(range(40)) and all(x['ok']is True and x['output_tokens']==x['requested_output_tokens']==1024 for x in rows),'whole forty fixed-output successes')
 duration=s['benchmark_duration_s'];need(type(duration)in(int,float)and math.isfinite(duration)and duration>0,'positive whole benchmark duration')
 ttft=[x['ttft_ms']for x in rows];tpot=[(x['duration_s']-x['ttft_ms']/1000)*1000/1023 for x in rows]
 need(all(math.isfinite(x)and x>=0 for x in ttft+tpot),'complete perrequestTTFT/TPOT')
 throughput=40960/duration
 need(s['failed']==0 and s['successful']==40 and s['fixed_output_verified']is True and math.isclose(throughput,s['output_tokens_per_second'],rel_tol=1e-9),'summary reconstructed from whole rawrequests')
 return dict(throughput=throughput,TTFT_mean_ms=statistics.fmean(ttft),TPOT_mean_ms=statistics.fmean(tpot))
def hits(before,after):
 from screen_binding import startup_gate
 need(len(before)==len(after)==4 and {x['pid']for x in before}=={x['pid']for x in after},'same four actual DL workers')
 startup_gate(before,before[0]['source_ref'],before[0]['qualification_ref']);startup_gate(after,before[0]['source_ref'],before[0]['qualification_ref'])
 old={x['pid']:x for x in before};rows=[]
 for a in after:
  b=old[a['pid']]
  need(a['source_ref']==b['source_ref'] and a['qualification_ref']==b['qualification_ref'] and a['library']==b['library'] and a['framework_sources']==b['framework_sources'] and a['ordinal']==b['ordinal']+1 and a['proc_stat'].split(')')[-1].split()[19]==b['proc_stat'].split(')')[-1].split()[19],'exact actual worker/source/start; no extra timed health snapshot')
  need(set(a['prefixes'])==set(b['prefixes']) and len(a['prefixes'])==48,'same actual48 DL prefixes')
  deltas={}
  for prefix,v in a['prefixes'].items():
   p=b['prefixes'][prefix]
   need(v['self_id']==p['self_id'] and v['core_id']==p['core_id'] and v['arena']==p['arena'],'same actual instance/arena/core')
   need(v['candidate']>p['candidate'] and v['native']==p['native'] and v['finished_steps']>p['finished_steps'],'measured actual DL each48; no native fallback or warmup-only credit')
   deltas[prefix]=dict(candidate=v['candidate']-p['candidate'],materialized_slots=v['materialized_slots']-p['materialized_slots'])
  need(set(a['health']['rows'])==set(b['health']['rows']) and all(x['observations']>b['health']['rows'][d]['observations'] for d,x in a['health']['rows'].items()),'actual measured device health updates')
  rows.append(dict(pid=a['pid'],prefixes=deltas,finite=True))
 return rows
def main():
 p=argparse.ArgumentParser(allow_abbrev=False)
 for k in('dense','candidate','dense-inputs','candidate-inputs','workers-before','workers-after','output'):p.add_argument('--'+k,required=True,type=Path)
 a=p.parse_args();d,c=json.loads(a.dense.read_text()),json.loads(a.candidate.read_text())
 need(d['config']==c['config'],'same exact driver run config')
 di,ci=json.loads(a.dense_inputs.read_text()),json.loads(a.candidate_inputs.read_text())
 need(di==ci and len(di['prompts'])==42 and all(len(v)==32768 for v in di['prompts'])and di['shared_prefix_tokens']==16384 and di['warmups']==2 and di['measured']==40,'actual all42 input-token-ID arrays exactly paired')
 dm,cm=arm(d),arm(c);workers=hits(json.loads(a.workers_before.read_text()),json.loads(a.workers_after.read_text()))
 gain=cm['throughput']/dm['throughput']-1
 value=dict(schema='deltalog.production-screen-pair-independent/v033',dense=dm,candidate=cm,throughput_gain=gain,workers=workers,screen_gain_at_least10percent=gain>=.1,scope='sync-eager-PDCoff-only',deployment_async_control_pending=True,formal_three_rounds=False,task_accuracy=False,acceptance=False)
 with a.output.open('x',encoding='utf8')as f:json.dump(value,f,sort_keys=True);f.write('\n')
if __name__=='__main__':main()


