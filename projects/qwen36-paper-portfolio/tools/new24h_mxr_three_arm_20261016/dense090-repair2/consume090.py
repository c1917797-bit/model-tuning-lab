"""Request-level C1 opportunity bounds, not kernel-sum or candidate speedup."""
import argparse,json,math,statistics,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import contract090 as C
def analyze(report,inputs,tokens):
 c=report['config'];s=report['summary'];rows=report['results'];warm=report['warmup_results']
 C.need(all(c[k]==v for k,v in dict(input_tokens=tokens,prefix_tokens=1024,output_tokens=1024,requests=C.MEASURED,concurrency=1,warmup_requests=C.WARMUPS,ignore_eos=True).items()),'actual frozen native profile, not32K/C16')
 C.need(inputs['input_tokens']==tokens and len(inputs['prompts'])==C.MEASURED+C.WARMUPS and all(len(v)==tokens for v in inputs['prompts']),'exact real tokenizer ID input counts')
 C.need(len(rows)==C.MEASURED and {r['index']for r in rows}==set(range(C.MEASURED)),'complete formal request indices')
 failures=[r for r in rows if not r['ok']or r.get('output_tokens')!=1024 or r.get('requested_output_tokens')!=1024]
 duration=s['benchmark_duration_s'];C.need(type(duration)in(int,float)and math.isfinite(duration)and duration>0,'whole measured wallclock')
 request_rows=[]
 for r in rows:
  row=dict(r);row['derived_TPOT_ms']=None
  if r['ok']and r.get('ttft_ms')is not None and r.get('output_tokens')==1024:
   C.need(all(type(r[k])in(int,float)and math.isfinite(r[k])for k in('ttft_ms','duration_s'))and 0<=r['ttft_ms']/1000<=r['duration_s'],'finite actual timing ordering')
   row['derived_TPOT_ms']=(r['duration_s']-r['ttft_ms']/1000)*1000/1023
  request_rows.append(row)
 good=not failures and len(warm)==C.WARMUPS and all(r['ok']and r['output_tokens']==r['requested_output_tokens']==1024 for r in warm)
 value=dict(input_tokens=tokens,output_tokens=1024,concurrency=1,warmup_results=warm,requests=request_rows,complete_fixed_output=good,failures=failures,benchmark_duration_s=duration,output_tokens_total=sum(r.get('output_tokens')or 0 for r in rows),candidate_gain_measured=False,qualification=False)
 if good:
  ttft=sum(r['ttft_ms']/1000 for r in rows);whole=sum(r['duration_s']for r in rows);C.need(whole<=duration+max(.01,duration*1e-4),'C1 serial request intervals cannot exceed whole benchmark')
  f=ttft/duration;decode=(whole-ttft)/duration
  value.update(output_tokens_per_second=C.MEASURED*1024/duration,TTFT_mean_ms=statistics.fmean(r['ttft_ms']for r in rows),TPOT_mean_ms=statistics.fmean(r['derived_TPOT_ms']for r in request_rows),sum_TTFT_s=ttft,sum_request_duration_s=whole,prefill_only_loose_fraction=f,post_first_token_loose_fraction=decode,unattributed_benchmark_overhead_s=duration-whole,prefill_only_zero_TTFT_conditional_max_throughput_gain=(f/(1-f)if f<1 else None),prefill_only_10percent_not_excluded_by_loose_bound=f>=1/11,post_first_token_zero_cost_conditional_max_throughput_gain=(decode/(1-decode)if decode<1 else None),bound_conditions='C1 only; all removed time is exposed and TPOT/other costs unchanged; TTFT includes more than solve, postfirst includes more than recurrent; not measured candidate gain')
 return value
def bindings(before,after,sr):
 C.need(len(before)==len(after)==4,'all4 actual native worker bindings');a={r['host']['pid']:r for r in after};C.need(len(a)==4 and {r['host']['physical']for r in before}=={4,5,6,7},'one actual worker percard')
 for x in before:
  y=a[x['host']['pid']]
  for k in('physical','start_ticks','cgroup'):C.need(x['host'][k]==y['host'][k],'same host lifetime '+k)
  for v in(x['guest'],y['guest']):C.need(v['schema']=='dense.native-worker-snapshot/v090'and v['source_ref']==sr and v['native_core']is v['native_inverse']is True and v['allow_hf32']is False and v['tensor_capture']is False,'actual native source/precision identity')
  C.need(x['guest']['pid']==y['guest']['pid']and x['guest']['framework_sources']==y['guest']['framework_sources']and y['guest']['ordinal']>x['guest']['ordinal'],'same actual native modules and new receipt')
 return True
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--dense-root',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 sr=json.loads(a.source_ref);C.source(sr,clock=False);results=[]
 for n in C.PROFILES:
  report=C.obj(C.ref(a.dense_root/('profile-%d.json'%n)));inputs=C.obj(C.ref(a.dense_root/('barriers-%d/INPUTS.json'%n)));b=C.obj(C.ref(a.dense_root/('BINDINGS-%d-BEFORE.json'%n)));d=C.obj(C.ref(a.dense_root/('BINDINGS-%d-AFTER.json'%n)));bindings(b,d,sr);results.append(analyze(report,inputs,n))
 C.write(a.output,dict(schema='dense.e2e-opportunity-consumption/v090',source=sr,profiles=results,scope='native-only current660 sync-eager2K+16K/C1 fixed1024 opportunity, no candidate gain',profile_order=list(C.PROFILES),formal_performance=False,task_accuracy=False,NPU_reexecuted=False));return 0
if __name__=='__main__':raise SystemExit(main())
