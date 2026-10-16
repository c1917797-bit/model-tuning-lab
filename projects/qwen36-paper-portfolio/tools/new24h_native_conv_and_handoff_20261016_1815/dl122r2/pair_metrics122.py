"""Real HTTP token counts AND runtime CPU-metadata steps determine hits."""
import math,statistics
from api122 import need
def arm(v,count):
 c=v['config'];s=v['summary'];rows=v['results'];expected=dict(input_tokens=2048,prefix_tokens=1024,output_tokens=1024,requests=count,concurrency=1,warmup_requests=2,ignore_eos=True)
 need(all(c[k]==x for k,x in expected.items()),'exact registered paired workload')
 need(len(rows)==count and {x['index']for x in rows}==set(range(count))and all(x['ok']is True and x['output_tokens']==x['requested_output_tokens']==1024 for x in rows),'all complete actual HTTP responses')
 duration=s['benchmark_duration_s'];need(type(duration)in(int,float)and math.isfinite(duration)and duration>0,'actual measured duration')
 throughput=sum(x['output_tokens']for x in rows)/duration
 need(s['failed']==0 and s['successful']==count and s['fixed_output_verified']is True and math.isclose(throughput,s['output_tokens_per_second'],rel_tol=1e-9),'HTTP exact reconstructed throughput')
 ttft=[x['ttft_ms']for x in rows];tpot=[(x['duration_s']-x['ttft_ms']/1000)*1000/1023 for x in rows]
 need(all(math.isfinite(x)and x>=0 for x in ttft+tpot),'finite per-request TTFT/TPOT')
 return dict(throughput=throughput,TTFT_mean_ms=statistics.fmean(ttft),TPOT_mean_ms=statistics.fmean(tpot)),sum(x['output_tokens']-1 for x in rows)
def metadata_delta(before,after,http_decode,requests):
 need(before['pid']==after['pid']and before['prefixes'].keys()==after['prefixes'].keys()and len(before['prefixes'])==48,'same actual48 worker')
 evidence={}
 for p,b in before['prefixes'].items():
  a=after['prefixes'][p];finished=a['finished_steps']-b['finished_steps'];prefills=a['materialized_slots']-b['materialized_slots'];candidate=a['candidate']-b['candidate'];native=a['native']-b['native']
  # C1 exact2048 and maxbatched2048 prohibit split prefill/mixed grouping.
  # These counters originate from actual CPU receipt/finish and prefill IDs,
  # not HTTP tokens multiplied by48 or a guessed model layer count.
  need(prefills==requests and finished-prefills==candidate==http_decode and native==0,'actual flat CPU-metadata steps, real prefill counts and HTTP decode count must agree')
  evidence[p]=dict(actual_finished=finished,actual_prefills=prefills,actual_decode=candidate)
 return evidence
