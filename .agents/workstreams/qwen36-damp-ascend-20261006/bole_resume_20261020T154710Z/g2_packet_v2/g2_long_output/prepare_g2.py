"""Prepare one NEW smoke4 stream source; default OFF and no host/device execution."""
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

def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for key in('parent-source-ref','parent-owner-result-ref','parent-qualification-ref','consumer-source-ref','executor-sources-json'):p.add_argument('--'+key)
    for key in('overlay','new-root','output-root'):p.add_argument('--'+key,type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    need(all(vars(a).values()),'all exact actual qualified parent/reader/installed sources and fresh leaves required')
    sys.path.insert(0,str(a.overlay));import sourceio as C,g2_contract as G2,g2_host_adapter as HA,g2_validate as V,g2_executor_proof as EP
    ps=json.loads(a.parent_source_ref);parent=obj(ps);po=json.loads(a.parent_owner_result_ref);pq=json.loads(a.parent_qualification_ref)
    V.parent_qualified(ps,parent,po,pq) # Fails before copying when actual model gate is pending.
    consumer=json.loads(a.consumer_source_ref);need(consumer==ref(a.overlay/'g2_consumer.py'),'explicit independently reviewed consumer source bytes')
    executors=json.loads(a.executor_sources_json)
    need(set(executors)=={'multiproc_executor','worker_base','ascend_worker','ompmultiprocessing','cpu_binding','ascend_config'},'exact complete native launcher source review operands')
    for r in executors.values():compile(Path(r['path']).read_bytes(),r['path'],'exec');need(ref(r['path'])==r,'actual native executor source')
    executor_proof=EP.consume(executors)
    old=Path(parent['root']);new,out=a.new_root,a.output_root
    need(new.parent==out.parent==Path('/opt/host/vnf/austinov')and new.name.startswith('bole-g2-stream-smoke4-')and
        out.name=='run-'+new.name and not new.exists()and not out.exists()and not Path(str(out)+'-CPU').exists(),
        'unique NEW G2 source/model/CPU output leaves; failed predecessors never overwritten')
    manifest=obj(ref(a.overlay/'MANIFEST.json'));names=manifest['overlay_files']
    for name in names:
        if name!='MANIFEST.json':need(ref(a.overlay/name)==manifest['inventory'][name],'exact reviewed overlay inventory '+name)
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
    m['dependencies']=list({r['path']:r for r in[*[remap(r)for r in parent['dependencies']],*parent_refs]}.values())
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
    for f in new.rglob('*.py'):compile(f.read_bytes(),str(f),'exec')
    print(json.dumps(dict(source=sr,commands=ref(new/'COMMANDS.json'),new_software_cases=added,
        prospective_sameimage_cases=original_count+added,actual_sameimage_executed=False,
        actual_scheduler_executed=False,model_ready=False,timing_is_formal=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
