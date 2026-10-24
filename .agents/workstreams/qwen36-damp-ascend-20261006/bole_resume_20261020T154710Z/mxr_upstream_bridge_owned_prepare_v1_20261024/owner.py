"""Exact original Devices[] owner adaptation for retained upstream CPU bridge."""
import argparse,ast,copy,json,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_continuous_h_counterfactual_owner_prepare_v1/owner.py","bytes":12810,"sha256":"15c0cb2eec448e749988eef52d5fa194525ae8f58a4007daac7b4ace93ae5022"}
BASE_GUEST={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_continuous_h_counterfactual_owner_prepare_v1/guest_entry.py","bytes":6112,"sha256":"859ff6c18e8bbe4af62988b262e7eb0028d7042ba5fb3c2abec9984132d73948"}
ANALYSIS={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_upstream_bridge_owned_prepare_v1_20261024/analyze_bridge.py","bytes":17457,"sha256":"b0868ef2867c04a99decf6071ad2bfe83d43849531bb7bd1888b7c4b8f9769e3"}
PLAN={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_upstream_bridge_owned_prepare_v1_20261024/INPUTS.json","bytes":8157,"sha256":"7357804ff9fc1162dfa15289ba3ebdc7f2eea26475337d23c3418b54bda9f424"}
OUT=Path("/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_UPSTREAM_BRIDGE_CPU_20261024_V1")
OWNER='mxr-upstream-bridge-CPU-20261024-v1'
O=None
def need(v,s):
    if not v:raise ValueError(s)
def load_base():
    import hashlib
    b=Path(BASE['path']).read_bytes()
    need((len(b),hashlib.sha256(b).hexdigest())==(BASE['bytes'],BASE['sha256']),'exact retained Devices[] owner')
    m=types.ModuleType('_unchanged_continuous_CPU_owner');m.__file__=BASE['path'];exec(compile(b,BASE['path'],'exec'),m.__dict__);return m,b
def selected(plan):
    expected=['continuous_source','existing_attribution','actual_probe','actual_source','actual_reference_source','wy_source',
        'g_producer_sources[0]','g_producer_sources[1]','fixed_inputs.donor','fixed_inputs.canonical','fixed_inputs.codec','fixed_inputs.metrics',
        'fixed_inputs.arms[0]','fixed_inputs.arms[1]','fixed_inputs.arms[2]','fixed_inputs.case.raw','fixed_inputs.case.raw_sidecar']
    need(plan['minimum_read_only_mount_keys']==expected,'exact seventeen reviewed read paths')
    values=[plan[k]for k in expected[:6]]+plan['g_producer_sources']+[plan['fixed_inputs'][k]for k in('donor','canonical','codec','metrics')]+plan['fixed_inputs']['arms']+[plan['fixed_inputs']['case'][k]for k in('raw','raw_sidecar')]
    seen={}
    for r in values:
        need(type(r)is dict and set(r)=={'path','bytes','sha256'}and Path(r['path']).is_absolute(),'actual exact Ref3 readset')
        need(r['path']not in seen,'unique seventeen input paths');seen[r['path']]=r
    need(len(values)==17,'all seventeen inputs')
    return values
def configured():
    global O
    if O is not None:return O
    O,raw=load_base();old_review=O.review_contract;old_derive=O.derive_cpu
    original_algorithms=copy.deepcopy(O.ALGORITHM_REFS)
    plan=json.loads(O.checked(PLAN).read_bytes());inputs=selected(plan)
    need(plan['output']==str(OUT/'cpu/BRIDGE.json')and plan['cutoff_epoch']==O.CUT and plan['qualification']is False and plan['new_NPU_execution']is False,'one reviewed CPU output/window; no borrowed qualification')
    O.HERE=HERE;O.OUT=OUT;O.OWNER=OWNER;O.ENTRY_FILE=HERE/'owner.py'
    O.ALGORITHM_REFS=[*original_algorithms,BASE,BASE_GUEST,ANALYSIS,PLAN,O.ref(__file__)]
    def source_inputs():
        C=O.load(plan['continuous_source'],'_exact_retained_bridge_constants')
        need(C.FIXED==plan['fixed_inputs'],'actual source-defined fixed inputs')
        return C,inputs
    def review_contract():
        r=old_review();r.update(schema='mxr.MAIN-upstream-bridge-owned-CPU-review/v1',owner_program_ref=O.ref(__file__),
            original_owned_adapter_ref=BASE,original_guest_adapter_ref=BASE_GUEST,input_plan_ref=PLAN,readonly_inputs=inputs,
            output_identity_delta=dict(original="/opt/host/vnf/austinov/run-mxr-upstream-bridge-L21-CPU-20261024-v1/BRIDGE.json",owned_leaf=str(OUT/'cpu/BRIDGE.json')),
            native_execution=False,qualification=False,performance=False)
        return r
    def derive_cpu(raw):
        body,pairs,original=old_derive(raw)
        edits=[("schema='mxr.continuous-H-owned-CPU/v1'","schema='mxr.upstream-bridge-owned-CPU/v1'"),
               ("ACTUAL_CONTINUOUS_H_CPU_DIAGNOSTIC","ACTUAL_UPSTREAM_BRIDGE_CPU_DIAGNOSTIC")]
        changed=body
        for a,b in edits:need(changed.count(a)==1,'one result-only identity seam');changed=changed.replace(a,b)
        restored=changed
        for a,b in reversed(edits):restored=restored.replace(b,a)
        need(restored==body,'complete original CPU function after result-identity inverse')
        return changed,[*pairs,*edits],original
    def run_two(C,ctl,leaf):
        stages=[];script=O.GUEST_REF['path']
        cap=int(ctl.remaining(cap=60));need(cap>=10,'original software remaining60 budget')
        r,v=O.child(C,ctl,'software',[script,'--stage','software','--output',str(leaf/'SOFTWARE.json')],cap)
        sr=C.ref(leaf/'SOFTWARE.json');s=C.load(sr)
        need(s['schema']=='mxr.continuous-H-sameimage-software/v1'and s['algorithm_refs']==original_algorithms and s['tests']==10
            and s['skipped']==0 and s['passed']is True and s['original_validate_frame_fixture_controls']==4
            and s['real_retained_data_opened']is False and s['Devices']==[]and s['NPU']is s['qualification']is False,'unchanged real software10 plus validator4 before retained raw')
        O.marker(C,v,'MAIN_MXR_UPSTREAM_BRIDGE_SOFTWARE ',sr);stages.append(dict(stage='software',child=r,result=sr))
        cap=int(ctl.remaining(cap=300));need(cap>=10,'original analysis remaining300 budget including cleanup')
        deadline=min(time.time()+cap-2,O.CUT-90)
        r,v=O.child(C,ctl,'analysis',[script,'--stage','analysis','--output',str(leaf/'BRIDGE.json'),'--deadline-epoch',str(deadline)],cap)
        rr=C.ref(leaf/'BRIDGE.json');need(rr['bytes']<=8*2**20,'complete report cap8MiB');x=C.load(rr)
        need(x['schema']=='mxr.existing-raw-upstream-baseline-bridge/v1'and x['source_refs']==plan and x['case']==plan['fixed_inputs']['case']
            and x['actual_source']==plan['actual_source']and x['actual_reference_source']==plan['actual_reference_source']
            and x['diagnostic_complete']is True and all(x[k]is False for k in('qualification','performance','task_accuracy','new_NPU_execution','candidate_patch','native_floor_grants_relaxation')),'strict CPU-only actual diagnostic report')
        need(len(x['chunk_head_rows'])==384 and {(a['chunk'],a['head'])for a in x['chunk_head_rows']}=={(c,h)for c in range(32)for h in range(12)},'complete32chunks x12heads')
        need(x['precision_contract']['oracle_and_thresholds_changed']is False,'original metrics/oracle unchanged')
        O.marker(C,v,'MAIN_MXR_UPSTREAM_BRIDGE_ANALYSIS ',rr);stages.append(dict(stage='analysis',child=r,result=rr,deadline_epoch=deadline,cap_seconds=cap))
        C.write(leaf/'TWO-STAGES.json',dict(schema='mxr.upstream-bridge-actual-two-CPU-children/v1',stages=stages,Devices=[],NPU=False,qualification=False))
        return r,rr
    O.source_inputs=source_inputs;O.review_contract=review_contract;O.derive_cpu=derive_cpu;O.run_two=run_two
    # Original whole main remains exact except truthful entry-program receipt.
    a=ast.parse(raw);node=next(n for n in a.body if isinstance(n,ast.FunctionDef)and n.name=='main');body=ast.get_source_segment(raw.decode(),node)
    old='MAIN_PROGRAM_REF=ref(__file__)';new='MAIN_PROGRAM_REF=ref(ENTRY_FILE)'
    need(body.count(old)==1,'single owner entry receipt seam');changed=body.replace(old,new);need(changed.replace(new,old)==body,'complete original main inverse')
    exec(compile(changed,BASE['path']+'#upstream-entry-program-receipt','exec'),O.__dict__)
    return O
def main():
    return configured().main()
if __name__=='__main__':main()
