#!/usr/bin/env python3
import argparse,ast,hashlib,importlib.util,json
from pathlib import Path
BASE_EXPECTED=(46993,'4b9e65806aef2879d137d0dac34e9440c5c0edb401b91a526b942637b63e3618')
ACTUAL_RESULT=dict(path='/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v12-CPU/RESULT.json',bytes=1202315,sha256='d7f90208d7faf168fda68d61b08e15c066e00b0e37da54111445bd41b9b34cee')
ACTUAL_UNIT=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/G2_V12_CPU_SYSTEMD_TERMINAL.json',bytes=361,sha256='f98de0d3d059dd979f24ab662d50c8908d1be5caa604825372c3aeceb69341c3')
REPLACED={'source_modules','source_gate','software','execute','main'}
def need(ok,why):
    if not ok:raise ValueError(why)
def functions(s):
    t=ast.parse(s);v={}
    for n in t.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            need(n.name not in v,'unique original top-level definition');v[n.name]=n
    return v
def text(s,n):return ''.join(s.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def replace1(s,a,b):
    need(s.count(a)==1,'exact single original anchor '+repr(a));return s.replace(a,b)
def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--base',type=Path);p.add_argument('--parts',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return
    need(a.base and a.parts and a.output,'exact base, parts, new output required');raw=a.base.read_bytes();need((len(raw),hashlib.sha256(raw).hexdigest())==BASE_EXPECTED,'whole reviewed base-v2 reader')
    old=raw.decode('utf-8');nodes=functions(old);part=(a.parts/'source_gate_v12.py.txt').read_text();pn=functions(part)
    spec=importlib.util.spec_from_file_location('_g2_reader_transform',a.parts/'software_transform.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    current={k:text(part,pn[k])for k in('source_modules','source_gate')};current['software']=mod.software_v12(text(old,nodes['software']))
    ex=text(old,nodes['execute'])
    ex=replace1(ex,'def execute(sr,result_ref):','def execute(sr,result_ref,unit_ref):')
    ex=replace1(ex,"schema='bole.actual-G2-v11-CPU-independent-qualification/v2'","schema='bole.actual-G2-v12-CPU-independent-qualification/v1'")
    ex=replace1(ex,'sameimage_322_parser_and_actual_cold_handoff_pass=True','sameimage_341_parser_and_actual_cold_handoff_pass=True')
    ex=replace1(ex,'    cold=cold_gate(sr,m,mods,summary,c,second_owned,before)','    cold=cold_gate(sr,m,mods,summary,c,second_owned,before)\n    unit=unit_gate(unit_ref)')
    ex=replace1(ex,'cold_handoff=cold,CPU_owners=[first,second]','cold_handoff=cold,finite_unit_ref=unit_ref,finite_unit=unit,CPU_owners=[first,second]')
    current['execute']=ex
    unit='''def unit_gate(unit_ref):
    need(unit_ref==UNIT_REF,'exact actual source12 CPU finite-unit terminal Ref; no caller boolean')
    value=obj(unit_ref)
    need(set(value)=={'schema','observed_epoch','properties'} and value['schema']=='bole.actual-finite-unit-terminal/v1' and finite(value['observed_epoch']) and value['observed_epoch']>0,'actual full finite-unit terminal object')
    wanted=dict(Id='bole-g2-v12-cpu-20261020t154710z.service',Type='exec',Restart='no',MainPID='0',ControlPID='0',Result='success',ExecMainStatus='0',ActiveState='active',SubState='exited')
    need(value['properties']==wanted,'actual exact CPU341 unit success, no remaining Main/Control PID, no restart')
    return value
'''
    ma='''def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--source-ref');p.add_argument('--result-ref');p.add_argument('--unit-terminal-ref');p.add_argument('--output');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(a.source_ref and a.result_ref and a.unit_terminal_ref and a.output,'actual full source/result/unit-terminal Refs and new qualification path required')
    reader_before=ref(__file__);sr=parse(a.source_ref);result=parse(a.result_ref);unit_ref=parse(a.unit_terminal_ref);checked(sr);checked(result);checked(unit_ref)
    value=execute(sr,result,unit_ref);need(ref(__file__)==reader_before==value['reader_ref'],'independent reader source stayed unchanged');value['reader_source_before_after_equal']=True
    r=write_exclusive(a.output,value);print(json.dumps(dict(qualification_ref=r,source=sr,result_ref=result,finite_unit_ref=unit_ref,sameimage_341_parser_and_actual_cold_handoff_pass=True,all_owned_stopped_retained=True,model_ready=False,NPU=False)));return 0
'''
    current['main']=unit+'\n'+ma
    pnodes=ast.parse(part).body;consts=[]
    for n in pnodes:
        if isinstance(n,ast.Assign):consts.append(text(part,n))
    need(len(consts)==9,'exact nine v12 source-context assignments from part2')
    globals_block='import subprocess\n'+ '\n'.join(consts)+'\nRESULT='+repr(ACTUAL_RESULT)+'\nUNIT_REF='+repr(ACTUAL_UNIT)+'\n\n'
    sg=current['source_gate']
    sg=replace1(sg,"need((m['files']['prepare_g2_ack_v12.py']['bytes'],m['files']['prepare_g2_ack_v12.py']['sha256'])==ACK_PREPARER and proof['actual_preparer']==m['files']['prepare_g2_ack_v12.py'],'actual pinned v12 source preparer')", "need((m['files']['prepare_g2_ack_v12.py']['bytes'],m['files']['prepare_g2_ack_v12.py']['sha256'])==ACK_PREPARER and (proof['actual_preparer']['bytes'],proof['actual_preparer']['sha256'])==ACK_PREPARER and checked(proof['actual_preparer']).read_bytes()==checked(m['files']['prepare_g2_ack_v12.py']).read_bytes(),'actual pinned producer and byteequal source-owned preparer snapshot')")
    current['source_gate']=sg
    lines=old.splitlines(keepends=True);edits=[]
    for k,v in current.items():n=nodes[k];edits.append((n.lineno-1,n.end_lineno,v+'\n'))
    first=min(n.lineno-1 for n in nodes.values())
    for n in ast.parse(old).body:
        if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in('ROOT','OUT','CPU_OUT','SOURCE','RESULT')for t in n.targets):need(n.lineno-1<first,'original context before explicit override')
    edits.append((first,first,globals_block))
    for lo,hi,v in sorted(edits,key=lambda x:(x[0],x[1]),reverse=True):lines[lo:hi]=[v]
    new=''.join(lines);new_nodes=functions(new)
    for k,n in nodes.items():
        if k not in REPLACED:need(ast.dump(n,include_attributes=False)==ast.dump(new_nodes[k],include_attributes=False),'whole original read-only predicate/class AST unchanged '+k)
    need(set(new_nodes)==set(nodes)|{'unit_gate'},'only one explicit finite-unit predicate added')
    compile(new,str(a.output),'exec',dont_inherit=True)
    with a.output.open('x',encoding='utf-8',newline='')as f:f.write(new)
    out=a.output.read_bytes();print(json.dumps(dict(path=str(a.output),bytes=len(out),sha256=hashlib.sha256(out).hexdigest(),original_unchanged_definitions=sorted(set(nodes)-REPLACED),new_current_scope341=True,actual_readback_executed=False,NPU=False)))
if __name__=='__main__':main()
