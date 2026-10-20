"""Prepare a fresh fixed1024 source after actual G2 full-stream qualification; default OFF."""
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
    need(ordinary_ref(r['path'])==r,'exact ordinary input Ref3');return json.loads(Path(r['path']).read_bytes())
def write(p,v):
    with p.open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
def replace(p,v):
    if p.exists():p.unlink()
    write(p,v)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v


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
         'exact reviewed G3 overlay bytes/SHA despite different advisory/remote paths '+name)
    return actual


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for key in('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','consumer-source-ref','executor-sources-json','advisory-manifest-ref','parent-source-audit-ref'):p.add_argument('--'+key)
    for key in('overlay','new-root','output-root'):p.add_argument('--'+key,type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all(vars(a).values()),'all exact actual qualified parent/reader/installed sources and fresh leaves required')
    advisory_ref=json.loads(a.advisory_manifest_ref)
    need(advisory_ref==ordinary_ref(a.overlay/'MANIFEST.json'),'exact externally reviewed G3 advisory MANIFEST Ref')
    manifest=obj(advisory_ref)
    for name in('sourceio.py','g2_contract.py','g2_host_adapter.py','g2_validate.py','g2_executor_proof.py','g3_parent.py','g3_budget.py','g3_readset.py'):
        portable_inventory(a.overlay,name,manifest['inventory'][name])
    sys.path.insert(0,str(a.overlay));import sourceio as C,g2_contract as G2,g2_host_adapter as HA,g2_validate as V,g2_executor_proof as EP,g3_parent as PARENT,g3_budget as BUDGET,g3_readset as READSET
    ps=json.loads(a.parent_source_ref);parent=obj(ps);po=json.loads(a.parent_owner_result_ref);pq=json.loads(a.parent_qualification_ref)
    pa=json.loads(a.parent_source_audit_ref)
    PARENT.qualified(ps,parent,po,pq,source_audit_ref=pa) # Fails before copying when actual model gate is pending.
    consumer=json.loads(a.consumer_source_ref);need(consumer==ref(a.overlay/'g2_consumer.py'),'explicit independently reviewed consumer source bytes')
    executors=json.loads(a.executor_sources_json)
    need(set(executors)=={'multiproc_executor','worker_base','ascend_worker','ompmultiprocessing','cpu_binding','ascend_config'},'exact complete native launcher source review operands')
    for r in executors.values():compile(Path(r['path']).read_bytes(),r['path'],'exec');need(ref(r['path'])==r,'actual native executor source')
    executor_proof=EP.consume(executors)
    old=Path(parent['root']);new,out=a.new_root,a.output_root
    need(new.parent==out.parent==Path('/opt/host/vnf/austinov')and new.name.startswith('bole-g3-fixed1024-')and
        out.name=='run-'+new.name and not new.exists()and not out.exists()and not Path(str(out)+'-CPU').exists(),
        'unique NEW G3 source/model/CPU output leaves; failed predecessors never overwritten')
    advisory_ref=json.loads(a.advisory_manifest_ref)
    need(advisory_ref==ordinary_ref(a.overlay/'MANIFEST.json'),'exact explicitly reviewed original G3 advisory MANIFEST Ref')
    parent_readset=READSET.collect(ps)['refs']
    manifest=obj(advisory_ref);names=manifest['overlay_files'];actual_overlay={}
    repair_builder_ref=ordinary_ref(Path(__file__).absolute())
    for name in names:
        if name!='MANIFEST.json':actual_overlay[name]=portable_inventory(a.overlay,name,manifest['inventory'][name])
        else:actual_overlay[name]=advisory_ref
        need(Path(name).name==name and(a.overlay/name).is_file(),'exact flat overlay file')
        if name.endswith('.py'):compile((a.overlay/name).read_bytes(),name,'exec')
    shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
    (new/'SOURCE_BOUND.json').rename(new/'PARENT_G2_SOURCE_BOUND.json')
    for name in('COMMANDS.json',parent['command_scope']['compatibility_file']):
        (new/name).rename(new/('PARENT_G2_'+name))
    for name in names:shutil.copyfile(a.overlay/name,new/name)
    contract=new/'contract090.py';text=contract.read_text();tree=ast.parse(text)
    for name,value in(('OUTPUT_POSIX',str(out)),('CPU_OUTPUT_POSIX',str(out)+'-CPU')):
        nodes=[n for n in tree.body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name]
        need(len(nodes)==1 and isinstance(nodes[0].value,ast.Constant)and type(nodes[0].value.value)is str,'exact output assignment')
        old_segment=ast.get_source_segment(text,nodes[0]);text=text.replace(old_segment,name+'='+repr(value),1)
        tree=ast.parse(text)
    contract.write_text(text)
    for name in V.MATH_UNCHANGED:need((new/name).read_bytes()==(old/name).read_bytes(),'unchanged original math/calibration '+name)
    # Preserve prior ledgers and add an exact separate G3 whole-file inverse.
    current={}
    for name,r in parent['files'].items():
        if(new/name).is_file()and Path(r['path']).is_relative_to(old):current[name]=ref(new/name)
    delta={name:dict(before=parent['files'][name],after=r,edits=[dict(before=Path(parent['files'][name]['path']).read_text(),after=Path(r['path']).read_text())])
        for name,r in current.items()if Path(parent['files'][name]['path']).read_bytes()!=Path(r['path']).read_bytes()}
    replace(new/'G3_LONG_EDITS_V1.json',dict(schema='bole.exact-G3-long-inverse-to-G2/v1',baseline=ps,files=delta,
        original_math_unchanged=True,original_G2_full_controls_rerun_separately=True))
    m=json.loads(json.dumps(parent));m.update(root=str(new),output_root=str(out),model_receipt_root=str(out/'dense/receipts'),
        prepared_only=True,default_enabled=False,service_experiment=G2.SCOPE)
    m.pop('prepared_template',None)
    def remap(r):return ref(new/Path(r['path']).relative_to(old))if Path(r['path']).is_relative_to(old)else r
    for name,r in list(m['files'].items()):m['files'][name]=remap(r)
    for name in (*names,'G3_LONG_EDITS_V1.json'):m['files'][name]=ref(new/name)
    for key in('service_runtime_source_snapshots','g1_overlay','g1_repair_v2_overlay','g2_overlay'):
        m[key]={k:remap(r)for k,r in m.get(key,{}).items()}
    # Historical ledgers keep exact predecessor refs. They are not current overlay claims.
    m['g3_predecessor']=dict(source=ps,owner_result=po,qualification=pq,source_audit=pa)
    m['g3_overlay']={name:ref(new/name)for name in names}
    m['profile']=dict(m['profile'],HTTP_output_tokens=1024,HTTP_tree_request_count=1)
    m['service_activation']=dict(m['service_activation'],enable_environment=G2.FLAG,
        request_count=1,monotonic_generations=[1],first_request_only=True,
        slot_reuse_must_be_observed=False,reuse_observation_required=False,
        capture_protocol=G2.SCOPE['capture_protocol'],model_ready=False,actual_scheduler_executed=False)
    m['stream_channel_root']=str(out/'dense/receipts/STREAM');m['stream_channel_contract_path']=str(out/'dense/receipts/STREAM/CHANNEL.json')
    m['stream_consumer_source']=ref(new/'g2_consumer.py');m['reviewed_stream_consumer']=consumer
    m['stream_executor_sources']=executors;m['stream_executor_proof']=executor_proof
    m['stream_runtime_sources']=EP.installed(executors);m['stream_resource_profile']=HA.CPU_PROFILE
    m['stream_CPU_binding_override']=dict(enable_cpu_binding=False,formal_timing=False)
    m['stream_metadata_reservation']=BUDGET.reservation()
    m['stream_long_time_budget']=dict(owner_phase=3600,shared_cleanup=180,client_cap=3000,HTTP_request_timeout=2400,formal_timing=False)
    m['stream_raw_success_replay_available']=False;m['stream_timing_is_formal']=False
    m['stream_capacity_scope']=dict(initial_physical_block_tokens=1536,real_sequence_growth=True,
        physical_allocation_growth_proven=False,task_total_capacity_required=5199,task_capacity_proven=False,
        normal_EOS_qualified=False,native_AR_token_identity_compared=False)
    original_count=parent['service_required_sameimage_software_cases']
    added=sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for name in names if name.startswith('test_g3')for n in ast.walk(ast.parse((new/name).read_bytes())))
    m['service_software_scope']=dict(schema='bole.G3-explicit-historical-plus-current-controls/v1',
        parent_source=ps,parent_exact_cases=original_count,new_current_cases=added,
        parent_suite_runs_in_separate_exact_source_process=True,current_pattern='test_g3*.py')
    m['service_required_sameimage_software_cases']=original_count+added
    parent_refs=[ps,po,pq,pa,*parent_readset,parent['prepared_template'],ref(old/'SOURCE.json'),ref(old/'COMMANDS.json'),ref(old/parent['command_scope']['compatibility_file']),
        *parent['files'].values(),*parent['dependencies'],*executors.values(),consumer]
    m['dependencies']=list({r['path']:r for r in[*[remap(r)for r in parent['dependencies']],*parent_refs,
        advisory_ref,repair_builder_ref,*actual_overlay.values()]}.values())
    m['g3_builder_portability']=dict(schema='bole.actual-remote-overlay-portability/v3',
        advisory_manifest=advisory_ref,
        actual_repair_builder=repair_builder_ref,original_advisory_paths_are_lineage_only=True,
        original_numerics_and_128_transaction_unchanged=True,
        inventory={name:dict(advisory=manifest['inventory'].get(name,advisory_ref),
            actual_overlay=actual_overlay[name],actual_bound=m['files'][name])for name in names})
    # New command closure remains generated after binding, never a manifest cycle.
    m['command_scope']=dict(parent['command_scope'],compatibility_file='COMMANDS_G3.json')
    for name in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(new/name,m)
    template=ref(new/'SOURCE_TEMPLATE.json')
    q=subprocess.run(['/usr/bin/python3','-I','-B',str(new/'bind_model.py'),'--execute',
        '--reviewed-template-ref',json.dumps(template),'--component-refs-json',json.dumps(parent['component_refs'])],capture_output=True,text=True,timeout=30)
    need(q.returncode==0,'actual G3 binding failed '+q.stdout+q.stderr)
    sr=ref(new/'SOURCE_BOUND.json');bound=obj(sr);cc=module('_g2_command_closure',new/'command_contract.py')
    historical=obj(m['command_scope']['historical_ref'])
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=template,bound_source=sr,
        **cc.expected(str(new),str(out),sr,template,parent['component_refs']),
        required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
        historical_required_sameimage_software_cases=historical['required_sameimage_software_cases'],
        legacy_entrypoints_retained_for_inverse_tests_only=True,actual_G1_execution_claimed=False,
        G3_stream_protocol=True,actual_G3_execution_claimed=False)
    replace(new/'COMMANDS.json',commands)
    replace(new/'COMMANDS_G3.json',dict(source=sr,template=template,commands=ref(new/'COMMANDS.json'),
        model=commands['model'],CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    cc.validate(cc.C,sr,bound)
    prerequisite_closure=READSET.audit(sr)
    for f in new.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    print(json.dumps(dict(source=sr,prerequisite_closure=prerequisite_closure,commands=ref(new/'COMMANDS.json'),new_software_cases=added,
        prospective_sameimage_cases=original_count+added,actual_sameimage_executed=False,
        actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
