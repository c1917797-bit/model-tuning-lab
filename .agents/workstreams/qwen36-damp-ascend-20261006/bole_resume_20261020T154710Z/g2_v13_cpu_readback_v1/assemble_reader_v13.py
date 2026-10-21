#!/usr/bin/env python3
import argparse,ast,copy,hashlib,importlib.util,json,re,stat
from pathlib import Path
BASE=(51180,'bbd3f5502ab28f9fe5957c678114faaf34a9a5b70419c97c8681f22f83e18c33')
SOURCE13=dict(path='/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v13/SOURCE_BOUND.json',bytes=994678,sha256='545e09b8bd8e598830cd81ab2ba3be6c5a6b775d1d35f263ed6d3519a4145345')
T=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z')
OUT=Path('/opt/host/vnf/austinov/run-bole-g2-stream-smoke4-20261020T154710Z-v13-CPU')
OLD_Q=str(T/'G2_V12_CPU_READBACK.json');NEW_Q=str(T/'G2_V13_CPU_READBACK.json')
UNIT_PATH=str(T/'G2_V13_CPU_SYSTEMD_TERMINAL.json')
CHANGED={'source_modules','source_gate','software','execute','unit_gate','write_exclusive','main'}
CONSTANTS={'SOURCE12','ROOT','OUT','CPU_OUT','SOURCE','RESULT','UNIT_REF','HTTP_MANIFEST','HTTP_FILES','SAVED_CPU341','CPU341_READER','CPU341_RESULT','FAILED_MODEL12'}
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def file_ref(path):
    p=Path(path);need(p.is_absolute()and not p.is_symlink()and stat.S_ISREG(p.lstat().st_mode),'ordinary absolute exact evidence');s=p.stat();raw=p.read_bytes();a=p.stat();need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns),'stable actual evidence');return dict(path=str(p),bytes=len(raw),sha256=sha(raw))
def parse_ref(s):
    def pairs(rows):
        d={}
        for k,v in rows:need(k not in d,'duplicate Ref JSON key');d[k]=v
        return d
    r=json.loads(s,object_pairs_hook=pairs)
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['path'])is str and type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and re.fullmatch('[0-9a-f]{64}',r['sha256']),'strict actual Ref3');need(file_ref(r['path'])==r,'actual complete Ref3 bytes/SHA');return r
def nodes(src):
    d={}
    for n in ast.parse(src).body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):need(n.name not in d,'unique original definition');d[n.name]=n
    return d
def text(src,n):return ''.join(src.splitlines(keepends=True)[n.lineno-1:n.end_lineno])
def once(s,a,b):need(s.count(a)==1,'exact original anchor '+repr(a));return s.replace(a,b)
def target(n):return n.targets[0].id if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)else None
def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--base',type=Path);p.add_argument('--parts',type=Path);p.add_argument('--output',type=Path);p.add_argument('--inverse',type=Path);p.add_argument('--result-ref');p.add_argument('--unit-terminal-ref');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return
    need(a.base and a.parts and a.output and a.inverse,'actual base, new parts, exclusive output and inverse required');need(bool(a.result_ref)==bool(a.unit_terminal_ref),'actual future RESULT/unit pins supplied together or both pending')
    base_ref=file_ref(a.base);need((base_ref['bytes'],base_ref['sha256'])==BASE,'whole actual source12 CPU reader-v2 authority')
    old=a.base.read_text();od=nodes(old);ot=ast.parse(old);first=min(n.lineno-1 for n in od.values())
    for n in ot.body:
        if target(n)in('ROOT','OUT','CPU_OUT','SOURCE','RESULT','UNIT_REF'):need(n.end_lineno<=first,'no old effective context override after inserted new globals')
    part=(a.parts/'source_gate_v13.py.txt').read_text();pd=nodes(part);pt=ast.parse(part)
    assignments=[n for n in pt.body if isinstance(n,ast.Assign)];need({target(n)for n in assignments}==CONSTANTS and len(assignments)==len(CONSTANTS),'all thirteen declared source13 context assignments')
    current={k:text(part,pd[k])for k in('source_modules','source_gate')}
    sg=current['source_gate'];sg=once(sg,"proof['phase_seconds']==3600","proof['original_phase_seconds']==3600")
    old_collect="    oldcanonical=C.ref(SOURCE12['path']);need(oldcanonical==SOURCE12,'canonical exact source12 Ref')\n    oldrefs=[*mods.bind_model.readset(oldcanonical),*parent['dependencies'],*mods.command_contract.validate(C,oldcanonical,parent)];oldcomplete={}"
    new_collect="""    collector_ref=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/g2_control_ref_repair_v5/prepare_g2_control_v5.py',bytes=16604,sha256='ce4f5c41be679f0f969b7178e02667461a7f2f601d7c5c8f19c04dabb8f23dd3')
    collector_rows=[r for r in parent['dependencies']if r==collector_ref]
    need(len(collector_rows)==1,'one exact canonical original collector Ref; other historical same-byte paths are separate evidence')
    checked(collector_ref)
    collector=mods.prepare_g2_http_v13.collector(parent);need(ref(collector.__file__)==collector_ref,'exact source-owned original collector, never current-root binder for old namespace')
    baseline=collector.collect(SOURCE12);oldrefs=baseline['refs'];oldcomplete={}
    need(baseline['commands']==ref(Path(parent['root'])/'COMMANDS.json')and obj(baseline['commands'])['required_sameimage_software_cases']==341,'actual original COMMANDS and literal argv checked in fresh exactsource12 subprocess')"""
    sg=once(sg,old_collect,new_collect)
    sg=once(sg,'snapshot=mods.g2_callee_proof.verify_snapshot(parent);','snapshot=mods.g2_callee_proof.verify_snapshot(m);')
    sg=once(sg,"source12_readset_count=len(oldcomplete),all_retained_authority_refs_reopened=True","source12_readset_count=len(oldcomplete),source12_collector_ref=collector_ref,source12_commands_ref=baseline['commands'],all_retained_authority_refs_reopened=True")
    current['source_gate']=sg
    spec=importlib.util.spec_from_file_location('_g2_http13_reader_software_transform',a.parts/'software_transform_v13.py');tr=importlib.util.module_from_spec(spec);spec.loader.exec_module(tr)
    current['software']=tr.software_v13(text(old,od['software']))
    ex=text(old,od['execute'])
    ex=once(ex,'def execute(sr,result_ref,unit_ref):\n','def execute(sr,result_ref,unit_ref):\n    need(RESULT is not None and UNIT_REF is not None,"actual source13 CPU349 result/unit pins pending; source-only reader never qualifies")\n    need(result_ref==RESULT and unit_ref==UNIT_REF,"only exact actual future CPU349 result and unit")\n')
    ex=once(ex,"schema='bole.actual-G2-v12-CPU-independent-qualification/v1'","schema='bole.actual-G2-v13-CPU-independent-qualification/v1'")
    ex=once(ex,'sameimage_341_parser_and_actual_cold_handoff_pass=True','sameimage_349_parser_and_actual_cold_handoff_pass=True');current['execute']=ex
    unit=text(old,od['unit_gate']);unit=once(unit,'need(unit_ref==UNIT_REF,','need(UNIT_REF is not None and unit_ref==UNIT_REF,')
    unit=once(unit,'bole-g2-v12-cpu-20261020t154710z.service','bole-g2-v13-cpu-20261020t154710z.service')
    unit=once(unit,'exact actual source12 CPU finite-unit terminal Ref; no caller boolean','exact actual source13 CPU finite-unit terminal Ref; no caller boolean')
    unit=once(unit,'actual exact CPU341 unit success, no remaining Main/Control PID, no restart','actual exact CPU349 unit success, no remaining Main/Control PID, no restart');current['unit_gate']=unit
    current['write_exclusive']=once(text(old,od['write_exclusive']),OLD_Q,NEW_Q)
    ma=text(old,od['main']);ma=once(ma,'sameimage_341_parser_and_actual_cold_handoff_pass=True','sameimage_349_parser_and_actual_cold_handoff_pass=True');current['main']=ma
    result_ref=unit_ref=None
    if a.result_ref:
        result_ref=parse_ref(a.result_ref);unit_ref=parse_ref(a.unit_terminal_ref)
        need(result_ref['path']==str(OUT/'RESULT.json')and unit_ref['path']==UNIT_PATH,'only new actual source13 CPU paths')
        r=json.loads(Path(result_ref['path']).read_bytes());u=json.loads(Path(unit_ref['path']).read_bytes())
        need(r['source']==SOURCE13 and r['cpu_only']is True and r['primary']is None and r['secondary']==[]and r['source_before']and r['source_before']==r['source_after'],'actual clean CPU349 owner required for freeze')
        need(u['schema']=='bole.actual-finite-unit-terminal/v1'and u['properties']==dict(Id='bole-g2-v13-cpu-20261020t154710z.service',Type='exec',Restart='no',MainPID='0',ControlPID='0',Result='success',ExecMainStatus='0',ActiveState='active',SubState='exited'),'actual terminal clean finite CPU349 unit required for freeze')
    block='import ast\n'+'\n'.join(text(part,n)for n in assignments)+'\nRESULT='+repr(result_ref)+'\nUNIT_REF='+repr(unit_ref)+'\n\n'
    block_nodes=ast.parse(block).body;first_index=min(i for i,n in enumerate(ot.body)if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)))
    edits=[(first,first,block)]
    for k,v in current.items():n=od[k];edits.append((n.lineno-1,n.end_lineno,v+'\n'))
    lines=old.splitlines(keepends=True)
    for lo,hi,value in sorted(edits,key=lambda e:(e[0],e[1]),reverse=True):lines[lo:hi]=[value]
    new=''.join(lines);nd=nodes(new);nt=ast.parse(new);need(set(nd)==set(od),'no undeclared new top-level execution functions')
    unchanged={}
    for k,n in od.items():
        if k not in CHANGED:
            before=text(old,n);need(before==text(new,nd[k]),'whole original raw/stage/ordered-create/owner/parser/cold predicate unchanged '+k);unchanged[k]=dict(bytes=len(before.encode()),sha256=sha(before.encode()))
    restored=copy.deepcopy(nt);need(ast.dump(ast.Module(body=restored.body[first_index:first_index+len(block_nodes)],type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=block_nodes,type_ignores=[]),include_attributes=False),'only declared new source13 global context block inserted')
    del restored.body[first_index:first_index+len(block_nodes)];need(len(restored.body)==len(ot.body),'original module arity after context removal')
    for i,n in enumerate(ot.body):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))and n.name in CHANGED:restored.body[i]=copy.deepcopy(n)
    need(ast.dump(restored,include_attributes=False)==ast.dump(ot,include_attributes=False),'complete executable module AST inverse, no hidden changes')
    compile(new,str(a.output),'exec',dont_inherit=True)
    need(not a.output.exists()and not a.output.is_symlink()and not a.inverse.exists()and not a.inverse.is_symlink(),'exclusive new reader/inverse artifacts')
    with a.output.open('x',encoding='utf-8',newline='')as f:f.write(new)
    reader_ref=file_ref(a.output)
    inverse=dict(schema='bole.exact-source12-CPU341-to-source13-CPU349-reader-inverse/v1',base_reader_ref=base_ref,reader_ref=reader_ref,source=SOURCE13,actual_CPU349_result_ref=result_ref,actual_CPU349_unit_ref=unit_ref,pins_pending=result_ref is None,declared_context=block,modified_functions={k:dict(before=text(old,od[k]),after=text(new,nd[k]))for k in CHANGED},whole_unchanged_definitions=unchanged,whole_file_inverse=dict(before=old,after=new),full_module_AST_inverse=True,source12_CPU341_authority_not_reused_as_current_PASS=True,actual_readback_executed=False,numerical_model_qualification=False,NPU=False)
    with a.inverse.open('x',encoding='utf-8',newline='')as f:json.dump(inverse,f,sort_keys=True);f.write('\n')
    print(json.dumps(dict(reader_ref=reader_ref,inverse_ref=file_ref(a.inverse),source=SOURCE13,pins_pending=result_ref is None,actual_readback_executed=False,numerical_model_qualification=False,NPU=False)))
if __name__=='__main__':main()
