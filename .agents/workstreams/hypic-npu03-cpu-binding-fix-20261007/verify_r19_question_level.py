#!/usr/bin/env python3
"""Post-hoc question-level r19 replay; no device run or acceptance change."""
from pathlib import Path
import hashlib
assert hashlib.sha256(Path(__file__).with_name('r19_repaired_c32_longbench_audit.py').read_bytes()).hexdigest()=='4bcb73eba4bb825d3f39cfa98875a631f7cf5dad6c590927ac127b88034e6832'
import r19_repaired_c32_longbench_audit as a,json
from collections import Counter
cases,e=a.frozen_cases()
b=a.audit_arm(a.BASE,'no-cache',cases,e,require_source_attestation=True)
c=a.audit_arm(a.CAND,'hypic-only',cases,e,allow_hot_shortfall=True,require_source_attestation=True)
f=json.loads(a.OUT.read_text());assert a.quality.sha256(a.OUT)=='40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b'
for key,val in a.decide(b,c).items():assert f['quality'][key]==val
B={(r['index'],r['repetition']):r for r in b['rows']};C={(r['index'],r['repetition']):r for r in c['rows']}
per=[];cross=Counter();finish=Counter()
for i in range(127):
 br=[B[(i,r)] for r in (1,2,3)];cr=[C[(i,r)] for r in (1,2,3)]
 bs=sum(x['correct'] for x in br);cs=sum(x['correct'] for x in cr)
 per.append({'index':i,'baseline_correct':bs,'candidate_correct':cs,'delta':cs-bs,'baseline_length':sum(x['finish_reason']=='length' for x in br),'candidate_length':sum(x['finish_reason']=='length' for x in cr)})
 cross[f'{bs}->{cs}']+=1
 for x,y in zip(br,cr):
  outcome='regressed' if x['correct'] and not y['correct'] else 'improved' if not x['correct'] and y['correct'] else 'unchanged'
  finish[f"{outcome}:{x['finish_reason']}->{y['finish_reason']}"]+=1
summary=({'sample_count':127,'scored_pairs':381,'same_question_score_transition':dict(cross),'improved_questions':sum(x['delta']>0 for x in per),'regressed_questions':sum(x['delta']<0 for x in per),'unchanged_questions':sum(x['delta']==0 for x in per),'baseline_unstable_questions':sum(0<x['baseline_correct']<3 for x in per),'candidate_unstable_questions':sum(0<x['candidate_correct']<3 for x in per),'stable_regression_3_to_0':[x['index'] for x in per if x['baseline_correct']==3 and x['candidate_correct']==0],'stable_improvement_0_to_3':[x['index'] for x in per if x['baseline_correct']==0 and x['candidate_correct']==3],'finish_transitions':dict(finish),'changed_question_details':[x for x in per if x['delta']]})
assert summary['sample_count']==127 and summary['scored_pairs']==381
assert (summary['improved_questions'],summary['regressed_questions'],summary['unchanged_questions'])==(8,13,106)
assert (summary['baseline_unstable_questions'],summary['candidate_unstable_questions'])==(13,22)
assert summary['stable_regression_3_to_0']==[59] and not summary['stable_improvement_0_to_3']
assert sum(x['delta'] for x in per)==-8
assert finish['regressed:stop->length']==15 and finish['regressed:stop->stop']==6
print(json.dumps(summary,sort_keys=True))
