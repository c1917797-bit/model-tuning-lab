"""Actual residual/update decomposition over successful124f Devices[] lifecycle."""
import ast,copy,hashlib,json,resource,sys,time,types
from pathlib import Path
HERE=Path(__file__).resolve().parent
PARENT={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_upstream_bridge_owned_prepare_v1_20261024/owner.py","bytes":8108,"sha256":"ea8e36c752f10c97868891e0edd4b897a8e4f2a52b476636de96b9541293d468"}
PLAN={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_upstream_bridge_owned_prepare_v1_20261024/INPUTS.json","bytes":8157,"sha256":"7357804ff9fc1162dfa15289ba3ebdc7f2eea26475337d23c3418b54bda9f424"}
OUT=Path("/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_RESIDUAL_UPDATE_DECOMPOSITION_CPU_20261024_V1")
OWNER='mxr-residual-update-decomposition-CPU-20261024-v1'
_O=None
def need(v,s):
    if not v:raise ValueError(s)
def checked(r):
    p=Path(r['path']);b=p.read_bytes()
    need(p.is_absolute()and not any(q.is_symlink()for q in(p,*p.parents))and len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'exact pinned original source');return b
def module(r,n):
    m=types.ModuleType(n);m.__file__=r['path'];exec(compile(checked(r),r['path'],'exec'),m.__dict__);return m
def execution_decision(O):
    # Derive actual original require_review literal; do not guess APPROVED/approve.
    tree=ast.parse(checked(module(PARENT,'_cast_review_parent').BASE).decode())
    f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='require_review')
    vals=[n.value.value for n in ast.walk(f)if isinstance(n,ast.Assign)and isinstance(n.value,ast.Constant)and any(isinstance(t,ast.Subscript)and isinstance(t.slice,ast.Constant)and t.slice.value=='decision'for t in n.targets)]
    need(vals==['approve'],'exact original explicit execution decision');return vals[0]
def configured():
    global _O
    if _O is not None:return _O
    B=module(PARENT,'_actual_cast_original124f');O=B.configured()
    old_review,old_derive=O.review_contract,O.derive_cpu
    old_algorithms=copy.deepcopy(O.ALGORITHM_REFS)
    Graw=O.checked(B.BASE_GUEST).read_text();original_algorithms=json.loads(json.loads(Graw.split('ALGORITHM_REFS=json.loads(',1)[1].split(')\nOUTROOT=',1)[0]))
    plan=json.loads(O.checked(PLAN).read_bytes());inputs=B.selected(plan)
    A=module(O.ref(HERE/'analysis.py'),'_actual_cast_source_contract')
    need(len(inputs)==17 and plan['cutoff_epoch']==O.CUT,'same original seventeen inputs and fixed deadline')
    original_source_inputs=O.source_inputs
    inputs=[*inputs,*A.RAW_REFS,A.CONSUMED]
    need(len(inputs)==21 and len({r['path']for r in inputs})==21,'original17 plus explicit3raw and CONSUMED control Ref')
    for r in [A.DIRECT,*A.RAW_REFS,A.CONSUMED]:O.checked(r)
    def source_inputs():
        H,old_inputs=original_source_inputs()
        need(old_inputs==inputs[:17],'unchanged original seventeen mount inputs')
        return H,inputs
    O.source_inputs=source_inputs
    O.HERE=HERE;O.OUT=OUT;O.OWNER=OWNER;O.ENTRY_FILE=HERE/'owner.py'
    O.ALGORITHM_REFS=[*old_algorithms,PARENT,PLAN,A.DIRECT,O.ref(HERE/'analysis.py'),O.ref(HERE/'guest_entry.py'),O.ref(__file__)]
    def review_contract():
        r=old_review();r.update(schema='mxr.MAIN-residual-update-decomposition-owned-CPU-review/v1',
            owner_program_ref=O.ref(__file__),guest_program_ref=O.ref(HERE/'guest_entry.py'),analysis_program_ref=O.ref(HERE/'analysis.py'),
            readonly_inputs=inputs,additional_reference_ref=A.DIRECT,output_root=str(OUT),sole_RW_leaf=str(OUT/'cpu'),
            output_identity_delta=dict(original=plan['output'],owned_leaf=str(OUT/'cpu/DECOMPOSITION.json')),
            native_execution=False,qualification=False,performance=False,prefill_state_causation_proven=False)
        return r
    def run_two(C,ctl,leaf):
        stages=[];script=O.GUEST_REF['path']
        cap=int(ctl.remaining(cap=60));need(cap>=10,'original software60 remaining')
        r,v=O.child(C,ctl,'software',[script,'--stage','software','--output',str(leaf/'SOFTWARE.json')],cap)
        sr=C.ref(leaf/'SOFTWARE.json');s=C.load(sr)
        need(s['schema']=='mxr.continuous-H-sameimage-software/v1'and s['algorithm_refs']==original_algorithms and s['tests']==10 and s['skipped']==0 and s['passed']is True and s['original_validate_frame_fixture_controls']==4 and s['real_retained_data_opened']is False and s['Devices']==[]and s['NPU']is s['qualification']is False,'unchanged original10+4 actual same-image gate')
        O.marker(C,v,'MAIN_MXR_RESIDUAL_UPDATE_SOFTWARE ',sr);stages.append(dict(stage='software',child=r,result=sr))
        cap=int(ctl.remaining(cap=300));need(cap>=10,'original analysis300 remaining')
        deadline=min(time.time()+cap-2,O.CUT-90)
        r,v=O.child(C,ctl,'analysis',[script,'--stage','analysis','--output',str(leaf/'DECOMPOSITION.json'),'--deadline-epoch',str(deadline)],cap)
        rr=C.ref(leaf/'DECOMPOSITION.json');need(rr['bytes']<=8*2**20,'original8MiB report cap')
        A.verify_report(C.load(rr),plan)
        O.marker(C,v,'MAIN_MXR_RESIDUAL_UPDATE_ANALYSIS ',rr);stages.append(dict(stage='analysis',child=r,result=rr,deadline_epoch=deadline,cap_seconds=cap))
        C.write(leaf/'TWO-STAGES.json',dict(schema='mxr.residual-update-decomposition-two-CPU-children/v1',stages=stages,Devices=[],NPU=False,qualification=False))
        return r,rr
    def derive_cpu(raw):
        body,pairs,original=old_derive(raw)
        edits=[('mxr.upstream-bridge-owned-CPU/v1','mxr.residual-update-decomposition-owned-CPU/v1'),('ACTUAL_UPSTREAM_BRIDGE_CPU_DIAGNOSTIC','ACTUAL_RESIDUAL_UPDATE_CPU_DIAGNOSTIC')]
        changed=body
        for a,b in edits:need(changed.count(a)==1,'one result identity delta');changed=changed.replace(a,b,1)
        back=changed
        for a,b in reversed(edits):back=back.replace(b,a,1)
        need(back==body,'complete original124f CPU lifecycle inverse');return changed,[*pairs,*edits],original
    O.review_contract=review_contract;O.run_two=run_two;O.derive_cpu=derive_cpu
    need(O.BUDGET==dict(guest_bytes=8*2**30,host_bytes=512*2**20,reserve_bytes=8*2**30,phase_seconds=600,software_seconds=60,analysis_seconds=300,cleanup_seconds=90,report_cap_bytes=8*2**20,Devices=[],NPU=False),'original resources unchanged')
    _O=O;return O
def main():
    O=configured()
    if sys.argv[1:]==['--plan']:
        body,pairs,_=O.derive_cpu(O.checked(O.PARENT_HOST).read_bytes())
        r=O.review_contract();decision=execution_decision(O)
        print(json.dumps(dict(required_review=r,required_execution_decision=decision,whole_original_cpu_function_inverse=True,delta_count=len(pairs),execution_ready=False,NPU=False),sort_keys=True));return
    if '--execute'in sys.argv[1:]and '--review-ref'in sys.argv[1:]:
        need(resource.getrlimit(resource.RLIMIT_AS)==(resource.RLIM_INFINITY,resource.RLIM_INFINITY),'actual Go/Docker owner must not inherit source-test AS512')
    return O.main()
if __name__=='__main__':main()
