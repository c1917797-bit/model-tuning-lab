"""Source closure for new fixed1024 domain; no device or timing qualification."""
import ast
from pathlib import Path
import sourceio as C
import g2_contract as G
import g3_parent as PARENT
import g3_budget as B
import g2_executor_proof as EP
MATH_UNCHANGED=('core112.py','adapter.py','oracle112.py','native_seams.py','treeconv118.py',
    'independent_model.py','model_entry.py','service_bridge.py','model_process_calibration.py',
    'model_calibration131r12.py','calibrate_conv118.py','transaction.py','eligibility.py')


def validate(sr):
 m=C.obj(sr);root=Path(m['root']);p=m['g3_predecessor'];parent=C.obj(p['source'])
 C.need(root==Path(__file__).resolve().parent and m['service_experiment']==G.SCOPE and
    G.SCOPE['profile']=='fixed1024'and m['default_enabled']is False,'new exact defaultOFF long-output profile')
 C.need(m['profile']['HTTP_output_tokens']==1024 and m['profile']['HTTP_tree_request_count']==1 and
    m['service_activation']['request_count']==1 and m['service_activation']['monotonic_generations']==[1]and
    m['service_activation']['first_request_only']is True and m['service_activation']['reuse_observation_required']is False and
    m['service_activation']['slot_reuse_must_be_observed']is False,
    'one long BOLE request only; native barrier and no allocator-reuse claim')
 C.need(m['stream_long_time_budget']==dict(owner_phase=3600,shared_cleanup=180,client_cap=3000,HTTP_request_timeout=2400,formal_timing=False),
    'explicit unchanged finite owner/cleanup envelope; no silent timing-budget extension')
 PARENT.qualified(p['source'],parent,p['owner_result'],p['qualification'],source_audit_ref=p['source_audit'])
 for ref in(*m['files'].values(),*m['runtime_sources'].values(),*m['dependencies']):C.checked(ref)
 for name in MATH_UNCHANGED:C.need(C.checked(m['files'][name]).read_bytes()==C.checked(parent['files'][name]).read_bytes(),'byteexact original numerical/transaction reference '+name)
 current=C.checked(m['files']['service_fia.py']).read_text();before=C.checked(parent['files']['service_fia.py']).read_text()
 marker='  converted=dict(kwargs);before={}'
 C.need(current[current.index(marker):]==before[before.index(marker):],'exact original conversion/delegate/result numerical body')
 C.need(m['stream_metadata_reservation']==B.reservation(),'explicit full1024 retained-evidence resource proof')
 C.need(m['stream_executor_proof']==EP.consume(m['stream_executor_sources'])and m['stream_runtime_sources']==EP.installed(m['stream_executor_sources']),'actual same-image native CPU3 source proof inherited explicitly')
 proof=C.obj(m['files']['G3_LONG_EDITS_V1.json']);C.need(proof['baseline']==p['source'],'exact G3 source inverse ledger')
 for name,row in proof['files'].items():
  C.need(row['before']==parent['files'][name]and row['after']==m['files'][name]and row['edits']==[
    dict(before=C.checked(row['before']).read_text(),after=C.checked(row['after']).read_text())],
    'complete exact G3 source delta '+name)
 import command_contract,g3_readset
 C.need(C.ref(g3_readset.__file__)==m['files']['g3_readset.py'],'exact original-function readset collector')
 commands=command_contract.validate(C,sr,m)
 return dict(source_validated=True,NPU=False,actual_scheduler_executed=False,model_ready=False,
    scope=G.SCOPE,parent_source=p['source'],commands=commands,physical_allocation_growth_proven=False)
