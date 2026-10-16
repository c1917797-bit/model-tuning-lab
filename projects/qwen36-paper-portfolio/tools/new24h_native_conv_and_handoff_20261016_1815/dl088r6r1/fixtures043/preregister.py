"""Single reviewed admission point: diagnostic160 only, never qualification."""
def need(x,m):
 if not x:raise ValueError(m)
def admit_smoke(owner,source,consumed):
 need(owner['schema']=='deltalog.diagnostic-owned-host/v035' and owner['target_source']==source,'exact same031 diagnostic source')
 need(owner['stage']=='numeric' and owner['steps']==16 and owner['stopped_retained']is True and owner['primary']is None and owner['secondary']==[],'actual complete16 owned release')
 need(owner['bridge_primitive_gate_pass']is False and owner['model_ready']is False,'no scope promotion')
 need(consumed['schema']=='deltalog.diagnostic-consumption/v035' and consumed['source']==source and consumed['actual_result']==owner['result'],'actual independent source/producer join')
 need(consumed['validation_contract']['schema']=='deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035','new preregistered reference domain only')
 need(consumed['diagnostic_capture_complete']is True and consumed['domain_checks_pass']is True and consumed['complete_proof']is False,'diagnostic smoke gate only')
 need(consumed['original_strict_result_preserved']['pass_gate']in(True,False),'original strict result retained, not relabelled')
 return dict(diagnostic160_admitted=True,model_ready=False,performance_ready=False,qualification=False)
