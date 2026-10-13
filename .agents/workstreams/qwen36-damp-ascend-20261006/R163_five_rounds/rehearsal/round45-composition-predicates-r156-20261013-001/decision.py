"""Pure planning classification. Never numerical/performance/run acceptance.

Caller must first consume original source-qualified numerical and paired model
evidence using its existing strict consumers. These booleans are explicit inputs
to a planning function, NOT substitute receipts or authority to run hardware.
"""
import math
def need(v,m):
 if not v:raise ValueError(m)
def positive(x):return type(x)in(int,float)and math.isfinite(x)and x>0
def retain_component(rounds,*,correctness_consumed=False,same_configuration=False):
 need(type(rounds)is list and type(correctness_consumed)is bool and type(same_configuration)is bool,'explicit consumed-input planning scope')
 need(all(type(r)is dict and set(r)=={'dense','candidate'}and positive(r['dense'])and positive(r['candidate'])for r in rounds),'actual positive finite throughput pairs')
 ratios=[r['candidate']/r['dense']for r in rounds]
 complete=correctness_consumed and same_configuration and len(rounds)>=3
 repeated_positive=complete and all(r>1 for r in ratios)
 return dict(schema='ascend.component-composition-planning/v1',retain_for_composition=repeated_positive,
  repeatable_positive_observed=repeated_positive,ratios=ratios,rounds=len(rounds),
  standalone_10percent_observed=complete and all(r>=1.10 for r in ratios),
  insufficient=not complete,final_accepted=False,run_authority=False,task_accuracy_accepted=False,
  reason='repeatable correct positive component may be combined; not acceptance'if repeated_positive else'no retention by this predicate without complete correctness/same-config/three positive pairs')
def final_measurement(rounds,*,correctness_consumed=False,same_configuration=False,all_three_tasks_consumed=False):
 value=retain_component(rounds,correctness_consumed=correctness_consumed,same_configuration=same_configuration)
 need(type(all_three_tasks_consumed)is bool,'actual complete task consumer input')
 value.update(final_measurement_requirements_observed=value['standalone_10percent_observed']and all_three_tasks_consumed,
  final_accepted=False,reason='Actual D/A/B/A+B new paired results required; percent gains never add; independent canonical acceptance consumer remains mandatory')
 return value
def deadline_budget(*,cutoff,now,stages,cleanup_seconds,safety_seconds):
 need(type(stages)is dict and stages and positive(cutoff)and positive(now),'named actual critical path')
 need(type(cleanup_seconds)in(int,float)and math.isfinite(cleanup_seconds)and cleanup_seconds>=0 and type(safety_seconds)in(int,float)and math.isfinite(safety_seconds)and safety_seconds>=0,'finite explicit cleanup/safety')
 known=all(positive(v)for v in stages.values())
 if not known:return dict(status='no_finite_eta',ready=False,latest_start=None,unknown_stages=[k for k,v in stages.items()if not positive(v)],full_start_admitted=False)
 total=sum(stages.values())+cleanup_seconds+safety_seconds;latest=cutoff-total
 return dict(status='budget_fit'if now<=latest else'budget_expired',ready=False,latest_start=latest,total_seconds=total,start_slack_seconds=latest-now,full_start_admitted=False)
