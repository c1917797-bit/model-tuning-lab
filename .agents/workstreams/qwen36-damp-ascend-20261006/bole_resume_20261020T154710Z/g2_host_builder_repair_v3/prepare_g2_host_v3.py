"""Portable host preparer for the byteexact frozen G2 overlay; default OFF."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys


def need(v,s):
    if not v:raise ValueError(s)
def ref(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def obj(r):
    need(ref(r['path'])==r,'exact input Ref3');return json.loads(Path(r['path']).read_bytes())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def replace(p,v):
    if p.exists():p.unlink()
    write(p,v)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

ADVISORY_MANIFEST=dict(bytes=15972,sha256='34119feffb6b8b910177731575a63181b02ef46b1670e2844f0813456a9c6f0d')
ORIGINAL_BUILDER=dict(bytes=10075,sha256='f2cd77167dda0ce876d91065c0e096ee0a597aff7e66e1382526b578d4b463db')


def ordinary_ref(path):
    path=Path(path)
    need(path.is_absolute()and path.is_file()and not any(p.is_symlink()for p in(path,*path.parents)),
         'actual ordinary file/full path without symlink')
    return ref(path)


def portable_inventory(overlay,name,advisory):
    need(type(name)is str and Path(name).name==name and name not in('.','..'),
         'exact flat overlay filename')
    need(type(advisory)is dict and set(advisory)=={'path','bytes','sha256'}and
         Path(advisory['path']).is_absolute()and Path(advisory['path']).name==name,
         'original advisory Ref3 path is lineage only, never a remote read target')
    actual=ordinary_ref(Path(overlay)/name)
    need(all(actual[k]==advisory[k]for k in('bytes','sha256')),
         'exact reviewed overlay bytes/SHA despite different advisory/remote paths '+name)
    return actual


def parent_rank_reports(parent_source,qualification_ref):
    qualification=obj(qualification_ref);references=qualification['ranks']
    need(type(references)is list and len(references)==4 and len({r['path']for r in references})==4,
         'four distinct actual independent parent rank report Refs')
    requests=None
    for rank,reference in enumerate(references):
        need(ordinary_ref(reference['path'])==reference and
             Path(reference['path'])==Path(qualification_ref['path']).parent/('RANK-%d.json'%rank),
             'exact ordinary parent qualification sibling rank report')
        row=obj(reference);items=row['requests']
        need(row['source']==parent_source and len(items)==2 and
             [v['generation']for v in items]==[1,2] and
             all(v['rank']==rank and v['actual_final_retirement_observed']is True and
                 v['component_checks_pass']is True and v['actual_next_counter_acknowledgements']==0 and
                 len(v['output_token_ids'])==2 and v['model_ready']is False
                 for v in items),
             'actual both G1-v2 generations retired with original component gates on this source/rank')
        identities=[(v['request'],v['output_token_ids'])for v in items]
        need(len({v['request']for v in items})==2 and(requests is None or identities==requests),
             'same two distinct actual request/output identities across all four parent reports')
        requests=identities
    return references


READSET_PROGRAM = """import hashlib,json,sys
from pathlib import Path
sr=json.loads(sys.argv[1]);raw=Path(sr['path']).read_bytes()
assert len(raw)==sr['bytes']and hashlib.sha256(raw).hexdigest()==sr['sha256']
m=json.loads(raw);sys.path.insert(0,m['root'])
import sourceio as C,bind_model as B,command_contract as CC
assert C.ref(B.__file__)==m['files']['bind_model.py']
assert C.ref(CC.__file__)==m['files']['command_contract.py']
refs=[*B.readset(sr),*m['dependencies'],*CC.validate(C,sr,m)]
for ref in refs:C.checked(ref)
print(json.dumps(list({r['path']:r for r in refs}.values())))
"""


def source_readset(source_ref):
    result=subprocess.run(['/usr/bin/python3','-I','-B','-c',READSET_PROGRAM,json.dumps(source_ref)],
        capture_output=True,text=True,timeout=90)
    need(result.returncode==0,'exact source-owned readset collection '+result.stderr[-3000:])
    return json.loads(result.stdout)


def audit_prerequisite_closure(source_ref):
    current=obj(source_ref);p=current['g2_predecessor'];parent=obj(p['source'])
    ranks=parent_rank_reports(p['source'],p['qualification'])
    historical=source_readset(p['source']);actual=source_readset(source_ref)
    required=[*historical,p['source'],p['owner_result'],p['qualification'],*ranks]
    by_path={r['path']:r for r in actual}
    missing=[r for r in required if by_path.get(r['path'])!=r]
    need(not missing,'historical software/validation exact prerequisite closure missing '+json.dumps(missing))
    digest=hashlib.sha256(json.dumps(sorted(required,key=lambda r:r['path']),sort_keys=True).encode()).hexdigest()
    return dict(schema='bole.G2-parent-validation-and-software-readset-closure/v3',
        current_readset_count=len(actual),historical_readset_count=len(historical),
        independently_validated_parent_rank_reports=ranks,missing=[],required_refs_sha256=digest,
        directory_mounts_added=False,NPU=False)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for key in('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','consumer-source-ref','executor-sources-json','advisory-manifest-ref','original-builder-ref'):p.add_argument('--'+key)
    for key in('overlay','new-root','output-root'):p.add_argument('--'+key,type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all(vars(a).values()),'all exact actual qualified parent/reader/installed sources and fresh leaves required')
    sys.path.insert(0,str(a.overlay));import sourceio as C,g2_contract as G2,g2_host_adapter as HA,g2_validate as V,g2_executor_proof as EP
    ps=json.loads(a.parent_source_ref);parent=obj(ps);po=json.loads(a.parent_owner_result_ref);pq=json.loads(a.parent_qualification_ref)
    V.parent_qualified(ps,parent,po,pq)
    actual_parent_rank_reports=parent_rank_reports(ps,pq)
    # Fails before copying when actual model gate is pending.
    consumer=json.loads(a.consumer_source_ref);need(consumer==ref(a.overlay/'g2_consumer.py'),'explicit independently reviewed consumer source bytes')
    executors=json.loads(a.executor_sources_json)
    need(set(executors)=={'multiproc_executor','worker_base','ascend_worker','ompmultiprocessing','cpu_binding','ascend_config'},'exact complete native launcher source review operands')
    for r in executors.values():compile(Path(r['path']).read_bytes(),r['path'],'exec');need(ref(r['path'])==r,'actual native executor source')
    executor_proof=EP.consume(executors)
    old=Path(parent['root']);new,out=a.new_root,a.output_root
    need(new.parent==out.parent==Path('/opt/host/vnf/austinov')and new.name.startswith('bole-g2-stream-smoke4-')and
        out.name=='run-'+new.name and not new.exists()and not out.exists()and not Path(str(out)+'-CPU').exists(),
        'unique NEW G2 source/model/CPU output leaves; failed predecessors never overwritten')
    advisory_ref=json.loads(a.advisory_manifest_ref);original_builder_ref=json.loads(a.original_builder_ref)
    need(advisory_ref==ordinary_ref(a.overlay/'MANIFEST.json')and
        all(advisory_ref[k]==v for k,v in ADVISORY_MANIFEST.items()),'exact byteoriginal frozen advisory MANIFEST Ref')
    need(original_builder_ref==ordinary_ref(a.overlay/'prepare_g2.py')and
        all(original_builder_ref[k]==v for k,v in ORIGINAL_BUILDER.items()),'exact byteoriginal frozen G2 builder Ref')
    manifest=obj(advisory_ref);names=manifest['overlay_files'];actual_overlay={}
    repair_builder_ref=ordinary_ref(Path(__file__).absolute())
    for name in names:
        if name!='MANIFEST.json':actual_overlay[name]=portable_inventory(a.overlay,name,manifest['inventory'][name])
        else:actual_overlay[name]=advisory_ref
        need(Path(name).name==name and(a.overlay/name).is_file(),'exact flat overlay file')
        if name.endswith('.py'):compile((a.overlay/name).read_bytes(),name,'exec')
    shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
    (new/'SOURCE_BOUND.json').rename(new/'PARENT_G1_V2_SOURCE_BOUND.json')
    for name in('COMMANDS.json','COMMANDS_G1.json'):
        (new/name).rename(new/('PARENT_G1_V2_'+name))
    for name in names:shutil.copyfile(a.overlay/name,new/name)
    contract=new/'contract090.py';text=contract.read_text();tree=ast.parse(text)
    for name,value in(('OUTPUT_POSIX',str(out)),('CPU_OUTPUT_POSIX',str(out)+'-CPU')):
        nodes=[n for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name]
        need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant)and type(nodes[0].value.value)is str,'exact output assignment')
        old_segment=ast.get_source_segment(text,nodes[0]);text=text.replace(old_segment,name+'='+repr(value),1)
        tree=ast.parse(text)
    contract.write_text(text)
    for name in V.MATH_UNCHANGED:need((new/name).read_bytes()==(old/name).read_bytes(),'unchanged original math/calibration '+name)
    # Keep the exact G1-v2 metadata/registry inverses, then add a separate G2 layer.
    current={}
    for name,r in parent['files'].items():
        if(new/name).is_file()and Path(r['path']).is_relative_to(old):current[name]=ref(new/name)
    delta={name:dict(before=parent['files'][name],after=r,edits=[dict(before=Path(parent['files'][name]['path']).read_text(),after=Path(r['path']).read_text())])
        for name,r in current.items()if Path(parent['files'][name]['path']).read_bytes()!=Path(r['path']).read_bytes()}
    replace(new/'G2_STREAM_EDITS_V1.json',dict(schema='bole.exact-G2-stream-inverse-to-G1v2/v1',baseline=ps,files=delta,
        original_math_unchanged=True,original_G1v2_full_controls_rerun_separately=True))
    m=json.loads(json.dumps(parent));m.update(root=str(new),output_root=str(out),model_receipt_root=str(out/'dense/receipts'),
        prepared_only=True,default_enabled=False,service_experiment=G2.SCOPE)
    m.pop('prepared_template',None)
    def remap(r):return ref(new/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
    for name,r in list(m['files'].items()):m['files'][name]=remap(r)
    for name in (*names,'G2_STREAM_EDITS_V1.json'):m['files'][name]=ref(new/name)
    for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay'):
        m[key]={k:remap(r)for k,r in m.get(key,{}).items()}
    # Historical ledgers keep exact predecessor refs. They are not current overlay claims.
    m['g2_predecessor']=dict(source=ps,owner_result=po,qualification=pq)
    m['g2_overlay']={name:ref(new/name)for name in names}
    m['profile']=dict(m['profile'],HTTP_output_tokens=4,HTTP_tree_request_count=2)
    m['service_activation']=dict(m['service_activation'],enable_environment=G2.FLAG,
        request_count=2,monotonic_generations=[1,2],first_request_only=False,
        slot_reuse_must_be_observed=False,reuse_observation_required=True,
        capture_protocol=G2.SCOPE['capture_protocol'],model_ready=False,actual_scheduler_executed=False)
    m['stream_channel_root']=str(out/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(out/'dense/receipts/STREAM/CHANNEL.json')
    m['stream_consumer_source']=ref(new/'g2_consumer.py');m['reviewed_stream_consumer']=consumer
    m['stream_executor_sources']=executors;m['stream_executor_proof']=executor_proof
    m['stream_runtime_sources']=EP.installed(executors);m['stream_resource_profile']=HA.CPU_PROFILE
    m['stream_CPU_binding_override']=dict(enable_cpu_binding=False,formal_timing=False)
    m['stream_raw_success_replay_available']=False;m['stream_timing_is_formal']=False
    m['stream_capacity_scope']=dict(initial_physical_block_tokens=1536,real_sequence_growth=True,
        physical_allocation_growth_proven=False,task_total_capacity_required=5199,task_capacity_proven=False,
        normal_EOS_qualified=False,native_AR_token_identity_compared=False)
    original_count=parent['service_required_sameimage_software_cases']
    added=sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for name in names if name.startswith('test_g2')for n in ast.walk(ast.parse((new/name).read_bytes())))
    m['service_software_scope']=dict(schema='bole.G2-explicit-historical-plus-current-controls/v1',
        parent_source=ps,parent_exact_cases=original_count,new_current_cases=added,
        parent_suite_runs_in_separate_exact_source_process=True,current_pattern='test_g2*.py')
    m['service_required_sameimage_software_cases']=original_count+added
    parent_refs=[ps,po,pq,parent['prepared_template'],ref(old/'SOURCE.json'),ref(old/'COMMANDS.json'),ref(old/'COMMANDS_G1.json'),
        *parent['files'].values(),*parent['dependencies'],*executors.values(),consumer]
    m['dependencies']=list({r['path']:r for r in[*[remap(r)for r in parent['dependencies']],*parent_refs,
        advisory_ref,original_builder_ref,repair_builder_ref,*actual_overlay.values(),*actual_parent_rank_reports]}.values())
    m['g2_builder_portability_v2']=dict(schema='bole.actual-remote-overlay-portability/v2',
        advisory_manifest=advisory_ref,original_frozen_builder=original_builder_ref,
        actual_repair_builder=repair_builder_ref,original_advisory_paths_are_lineage_only=True,
        runtime_and_28_controls_unchanged=True,
        inventory={name:dict(advisory=manifest['inventory'].get(name,advisory_ref),
            actual_overlay=actual_overlay[name],actual_bound=m['files'][name])for name in names})
    m['g2_parent_prerequisites_v3']=dict(parent_source=ps,qualification=pq,
        actual_rank_reports=actual_parent_rank_reports,actual_preparer=repair_builder_ref,
        exact_file_mounts_only=True,runtime_and_28_controls_unchanged=True)
    # New command closure remains generated after binding, never a manifest cycle.
    m['command_scope']=dict(parent['command_scope'],compatibility_file='COMMANDS_G2.json')
    for name in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(new/name,m)
    template=ref(new/'SOURCE_TEMPLATE.json')
    q=subprocess.run(['/usr/bin/python3','-I','-B',str(new/'bind_model.py'),'--execute',
        '--reviewed-template-ref',json.dumps(template),'--component-refs-json',json.dumps(parent['component_refs'])],capture_output=True,text=True,timeout=30)
    need(q.returncode==0,'actual G2 binding failed '+q.stdout+q.stderr)
    sr=ref(new/'SOURCE_BOUND.json');bound=obj(sr);cc=module('_g2_command_closure',new/'command_contract.py')
    historical=obj(m['command_scope']['historical_ref'])
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=template,bound_source=sr,
        **cc.expected(str(new),str(out),sr,template,parent['component_refs']),
        required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
        historical_required_sameimage_software_cases=historical['required_sameimage_software_cases'],
        legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,
        G2_stream_protocol=True,actual_G2_execution_claimed=False)
    replace(new/'COMMANDS.json',commands)
    replace(new/'COMMANDS_G2.json',dict(source=sr,template=template,commands=ref(new/'COMMANDS.json'),
        model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    cc.validate(cc.C,sr,bound)
    prerequisite_closure=audit_prerequisite_closure(sr)
    for f in new.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    print(json.dumps(dict(prerequisite_closure=prerequisite_closure,source=sr,commands=ref(new/'COMMANDS.json'),new_software_cases=added,
        prospective_sameimage_cases=original_count+added,actual_sameimage_executed=False,
        actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
