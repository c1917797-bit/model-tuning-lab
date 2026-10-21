#!/usr/bin/env python3
import argparse,ast,copy,hashlib,json,re,stat
from pathlib import Path
BASE=(57773,'88453a988febf2d074ca4315a8e376faca6038ef0b54369deb0343034d2cfeef')
SOURCE13=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json',bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
HOST13=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/host_service.py',bytes=16157,sha256='62b963b1b96b37d4320bfae5757d7526628c8613e31f6c6a75b5d24687022c41')
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
MODEL_OUT=Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13')
CPU_Q=str(T/'G2_V13_CPU_READBACK.json');MODEL_Q=str(T/'G2_V13_MODEL_STAGE_READBACK.json');UNIT_PATH=str(T/'G2_V13_MODEL_SYSTEMD_TERMINAL.json')
STAGE_KEYS=('actual_software_child','CPU_child','CPU_report','CPU_release','handoff_saved_stage','handoff_cold_child','handoff_cold_report','handoff_cold_release')
MODEL_KEYS=('canary','MTP_load','MTP_load_receipts','stream_channel','metadata_handoff','stream_resource_profile','actual_client_terminal','worker_bindings','stream_consumer_terminal','model_release','independent','independent_release')
SUCCESS_KEYS=tuple(sorted(STAGE_KEYS+MODEL_KEYS))
MODIFIED={'execute','unit_gate','write_exclusive','main'}
ADDED={'model_summary','review'}
NEW_GLOBALS={'STAGE_SUMMARY_KEYS','MODEL_SUMMARY_KEYS','MODEL_CONTEXT_HOST_REF'}
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def file_ref(path):
    p=Path(path);need(p.is_absolute()and not p.is_symlink()and stat.S_ISREG(p.lstat().st_mode),'ordinary absolute actual evidence')
    b=p.stat();raw=p.read_bytes();a=p.stat();need((b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns)==(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns),'stable actual source bytes');return dict(path=str(p),bytes=len(raw),sha256=sha(raw))
def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'strict full Ref3');need(file_ref(r['path'])==r,'actual full Ref3 bytes/SHA');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def parse_ref(s):
    def pairs(rows):
        d={}
        for k,v in rows:need(k not in d,'duplicate Ref JSON key');d[k]=v
        return d
    r=json.loads(s,object_pairs_hook=pairs);checked(r);return r
def definitions(s):
    out={}
    for n in ast.parse(s).body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):need(n.name not in out,'unique top-level definition');out[n.name]=n
    return out
def segment(s,n):return ''.join(s.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def once(s,a,b):need(s.count(a)==1,'exact actual reader anchor '+repr(a));return s.replace(a,b)
def assignment_name(n):return n.targets[0].id if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)else None
def check_host_summary(host):
    tree=ast.parse(host);main=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main'];need(len(main)==1,'one exact source13 host main');main=main[0]
    keys=set();faults=[]
    for n in ast.walk(main):
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name)and t.id=='summary':need(isinstance(n.value,ast.Dict)and not n.value.keys,'only empty initial summary literal')
                elif isinstance(t,ast.Subscript)and isinstance(t.value,ast.Name)and t.value.id=='summary':
                    need(isinstance(t.slice,ast.Constant)and type(t.slice.value)is str,'only literal source-owned summary writes');keys.add(t.slice.value)
                    if t.slice.value=='first_host_fault':faults.append(n)
        if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='summary':need(n.func.attr in('get','items','values','keys','copy'),'no undeclared summary mutator; fixed host uses direct literal writes')
    need(keys==set(SUCCESS_KEYS)|{'first_host_fault'}and len(faults)==1 and faults[0].lineno==123,'fixed source13 twenty success roles plus declared single failure-only role')
    return dict(host_ref=HOST13,success_keys=list(SUCCESS_KEYS),failure_only_key='first_host_fault',failure_assignment_line=123,primaryNone_required=True,unknown_keys_rejected=True)
SUMMARY_FUNCTION='''def model_summary(summary):
    need(type(summary)is dict and all(type(k)is str for k in summary),'actual source-owned MODEL summary object')
    need(set(summary)==set(MODEL_SUMMARY_KEYS),'complete twenty successful source13 roles; no failure-only or unknown role')
    return sorted(set(summary)-set(STAGE_SUMMARY_KEYS))
'''
REVIEW_FUNCTION='''def review(sr,owner_ref):
    need(RESULT is not None and UNIT_REF is not None,'actual successful source13 MODEL/unit pins are pending')
    need(owner_ref==RESULT and owner_ref['path']==str(OUT/'RESULT.json'),'only fully pinned actual source13 MODEL owner')
    reader_before=ref(__file__);proof=execute(sr,owner_ref,UNIT_REF)
    need(proof['schema']=='bole.actual-G2-v13-MODEL-stage-independent-readback/v1'and proof['source']==SOURCE and proof['result_ref']==owner_ref and proof['numerical_model_qualification']is False,'MODEL-parent two-CPU-stage proof only')
    need(ref(__file__)==reader_before==proof['reader_ref'],'whole stage reader source remained unchanged')
    evidence={reader_before['path']:reader_before}
    for r in READS.values():need(r['path']not in evidence or evidence[r['path']]==r,'no conflicting actual stage evidence');evidence[r['path']]=r
    evidence_refs=list(evidence.values())
    for r in evidence_refs:checked(r)
    proof['reader_source_before_after_equal']=True;proof['full_evidence_refs']=evidence_refs
    return proof,evidence_refs
'''
MAIN_FUNCTION='''def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--result-ref');p.add_argument('--unit-terminal-ref');p.add_argument('--output');p.add_argument('--stdout-only',action='store_true');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(a.source_ref and a.result_ref and a.unit_terminal_ref and (a.stdout_only != bool(a.output)),'actual full source/MODEL/unit refs and exactly one output mode required')
    sr=parse(a.source_ref);owner_ref=parse(a.result_ref);unit_ref=parse(a.unit_terminal_ref);checked(sr);checked(owner_ref);checked(unit_ref)
    need(UNIT_REF is not None and unit_ref==UNIT_REF,'actual fully pinned MODEL unit terminal required')
    proof,evidence_refs=review(sr,owner_ref)
    if a.stdout_only:print(json.dumps(proof,sort_keys=True));return 0
    r=write_exclusive(a.output,proof);print(json.dumps(dict(schema='bole.actual-G2-v13-MODEL-stage-readback-execution/v1',qualification_ref=r,source=proof['source'],result_ref=owner_ref,finite_unit_ref=UNIT_REF,stage_only=True,numerical_model_qualification=False,model_ready=False,NPU=False)));return 0
'''
def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--base',type=Path);p.add_argument('--output',type=Path);p.add_argument('--inverse',type=Path);p.add_argument('--model-result-ref');p.add_argument('--unit-terminal-ref');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return
    need(a.base and a.output and a.inverse,'exact base, exclusive helper and inverse required');need(bool(a.model_result_ref)==bool(a.unit_terminal_ref),'actual MODEL/unit pins together or both pending')
    base_ref=file_ref(a.base);need((base_ref['bytes'],base_ref['sha256'])==BASE,'whole actual PASS CPU349 reader authority')
    old=checked(base_ref).read_text();ot=ast.parse(old);od=definitions(old)
    need(MODIFIED<=set(od)and not(ADDED&set(od)),'original functions and unique new interface names')
    m=obj(SOURCE13);need(m['files']['host_service.py']==HOST13 and m['output_root']==str(MODEL_OUT),'actual fixed source13 host/output')
    adapter=check_host_summary(checked(HOST13).read_text())
    model_ref=unit_ref=None
    if a.model_result_ref:
        model_ref=parse_ref(a.model_result_ref);unit_ref=parse_ref(a.unit_terminal_ref)
        need(model_ref['path']==str(MODEL_OUT/'RESULT.json')and unit_ref['path']==UNIT_PATH,'only actual new source13 MODEL result/unit paths')
        owner=obj(model_ref);u=obj(unit_ref)
        need(owner['source']==SOURCE13 and owner['cpu_only']is False and owner['primary']is None and owner['secondary']==[]and owner['source_before']and owner['source_before']==owner['source_after'],'only actual successful source13 MODEL owner; failed/cached CPU result forbidden')
        need(set(owner['summary'])==set(SUCCESS_KEYS),'actual complete twenty-success-role MODEL summary')
        need(u['schema']=='bole.actual-finite-unit-terminal/v1'and u['properties']==dict(Id='bole-g2-v13-model-20261020t154710z.service',Type='exec',Restart='no',MainPID='0',ControlPID='0',Result='success',ExecMainStatus='0',ActiveState='active',SubState='exited'),'actual closed successful MODEL unit before binding')
    current={}
    ex=segment(old,od['execute'])
    ex=once(ex,'actual source13 CPU349 result/unit pins pending; source-only reader never qualifies','actual successful source13 MODEL result/unit pins pending; stage-only reader never qualifies')
    ex=once(ex,'only exact actual future CPU349 result and unit','only exact actual fully pinned MODEL result and unit')
    ex=once(ex,"result['cpu_only']is True","result['cpu_only']is False")
    ex=once(ex,"result['actual_host_argv']==commands['CPU'][3:]","result['actual_host_argv']==commands['model'][3:]")
    ex=once(ex,'exact actual pinned CPU output RESULT, never model/previous/caller-rewritten result','exact actual pinned MODEL output RESULT, never CPU/previous/caller-rewritten result')
    ex=once(ex,'actual clean source-owned whole cold-phase CPU RESULT and exact command','actual clean source-owned MODEL owner and exact command; this proof consumes only its two CPU stages')
    original_summary="summary=result['summary'];need(set(summary)=={'actual_software_child','CPU_child','CPU_report','CPU_release','handoff_saved_stage','handoff_cold_child','handoff_cold_report','handoff_cold_release'},'complete actual two-helper CPU path, no skipped cold probe/model or caller result substitution')"
    ex=once(ex,original_summary,"summary=result['summary'];model_extra_roles=model_summary(summary)")
    ex=once(ex,"schema='bole.actual-G2-v13-CPU-independent-qualification/v1'","schema='bole.actual-G2-v13-MODEL-stage-independent-readback/v1'")
    ex=once(ex,'sameimage_349_parser_and_actual_cold_handoff_pass=True','sameimage_349_parser_and_actual_cold_handoff_stage_pass=True')
    ex=once(ex,'all_owned_stopped_retained=True','two_stage_CPU_helpers_stopped_retained=True')
    ex=once(ex,'CPU_owners=[first,second],','CPU_owners=[first,second],stage_only=True,unconsumed_model_summary_roles=model_extra_roles,model_summary_host_ref=MODEL_CONTEXT_HOST_REF,')
    current['execute']=ex
    unit=segment(old,od['unit_gate'])
    unit=once(unit,'bole-g2-v13-cpu-20261020t154710z.service','bole-g2-v13-model-20261020t154710z.service')
    unit=once(unit,'exact actual source13 CPU finite-unit terminal Ref; no caller boolean','exact actual source13 MODEL finite-unit terminal Ref; no caller boolean')
    unit=once(unit,'actual exact CPU349 unit success, no remaining Main/Control PID, no restart','actual exact MODEL unit success, no remaining Main/Control PID, no restart');current['unit_gate']=unit
    current['write_exclusive']=once(segment(old,od['write_exclusive']),CPU_Q,MODEL_Q)
    current['main']=SUMMARY_FUNCTION+'\n'+REVIEW_FUNCTION+'\n'+MAIN_FUNCTION
    values={'CPU_OUT':'OUT','RESULT':repr(model_ref),'UNIT_REF':repr(unit_ref)};effective={}
    for i,n in enumerate(ot.body):
        k=assignment_name(n)
        if k in values:effective[k]=i
    need(set(effective)==set(values),'last actual context assignments present')
    first=min(n.lineno-1 for n in od.values());edits=[];context={}
    for k,i in effective.items():
        n=ot.body[i];need(n.end_lineno<=first,'effective context assigned before all original definitions')
        before=segment(old,n);after=k+'='+values[k];context[k]=dict(module_index=i,before=before,after=after);edits.append((n.lineno-1,n.end_lineno,after+'\n'))
    globals_text='STAGE_SUMMARY_KEYS='+repr(tuple(STAGE_KEYS))+'\nMODEL_SUMMARY_KEYS='+repr(tuple(SUCCESS_KEYS))+'\nMODEL_CONTEXT_HOST_REF='+repr(HOST13)+'\n\n'
    edits.append((first,first,globals_text))
    for k,body in current.items():n=od[k];edits.append((n.lineno-1,n.end_lineno,body+'\n'))
    lines=old.splitlines(keepends=True)
    for lo,hi,value in sorted(edits,key=lambda e:(e[0],e[1]),reverse=True):lines[lo:hi]=[value]
    new=''.join(lines);nt=ast.parse(new);nd=definitions(new);need(set(nd)==set(od)|ADDED,'only explicit model_summary/review interfaces added')
    unchanged={}
    for k,n in od.items():
        if k not in MODIFIED:
            b=segment(old,n);need(b==segment(new,nd[k]),'whole original source_gate/software349/stage/ordered/owner/parser/cold predicate unchanged '+k);unchanged[k]=dict(bytes=len(b.encode()),sha256=sha(b.encode()))
    restored=copy.deepcopy(nt);restored.body=[n for n in restored.body if not(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))and n.name in ADDED)and assignment_name(n)not in NEW_GLOBALS]
    need(len(restored.body)==len(ot.body),'original module arity after declared interface/global removal')
    context_indices=set(effective.values())
    for i,n in enumerate(ot.body):
        if i in context_indices or isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))and n.name in MODIFIED:restored.body[i]=copy.deepcopy(n)
    need(ast.dump(restored,include_attributes=False)==ast.dump(ot,include_attributes=False),'whole executable module AST inverse; no hidden context/function changes')
    compile(new,str(a.output),'exec',dont_inherit=True)
    need(not a.output.exists()and not a.output.is_symlink()and not a.inverse.exists()and not a.inverse.is_symlink(),'exclusive new helper/inverse artifacts')
    with a.output.open('x',encoding='utf-8',newline='')as f:f.write(new)
    new_ref=file_ref(a.output)
    ledger=dict(schema='bole.exact-source13-CPU349-to-MODEL-stage-reader-inverse/v1',base_reader_ref=base_ref,stage_reader_ref=new_ref,source=SOURCE13,MODEL_result_ref=model_ref,MODEL_unit_ref=unit_ref,pins_pending=model_ref is None,context=context,model_summary_adapter=adapter,modified_functions={k:dict(before=segment(old,od[k]),after=segment(new,nd[k]))for k in MODIFIED},added_functions={k:segment(new,nd[k])for k in ADDED},added_globals=globals_text,whole_unchanged_original_definitions=unchanged,whole_file_inverse=dict(before=old,after=new),full_module_AST_inverse=True,actual_readback_executed=False,numerical_model_qualification=False,all_four_owners_qualified=False,NPU=False)
    with a.inverse.open('x',encoding='utf-8',newline='')as f:json.dump(ledger,f,sort_keys=True);f.write('\n')
    print(json.dumps(dict(reader_ref=new_ref,inverse_ref=file_ref(a.inverse),source=SOURCE13,pins_pending=model_ref is None,actual_readback_executed=False,numerical_model_qualification=False,NPU=False)))
if __name__=='__main__':main()
