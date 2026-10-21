"""Default-OFF fresh source builder for actual G1 service GDN numerical probe.

No Docker/device/Git admission. MAIN executes this against real pinned parent
evidence and then independently owns the original finite same-image workflow.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

P=Path(__file__).resolve().parent
EXT=('gdn_service_gate.py','gdn_service_seam.py','consume_gdn_service.py','gdn_probe_contract.py','gdn_probe_runtime.py')
ADDED=(*EXT,'test_gdn_service_pure.py','test_gdn_probe_pure.py','prepare_gdn_probe.py','gdn_probe_clock.py','test_gdn_probe_clock.py','CLOCK_INVERSE_AUTHORITY.json')


def need(v,s):
    if not v:raise ValueError(s)
def ref(p):
    p=Path(p);b=p.read_bytes();need(p.is_absolute()and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary absolute source')
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def checked(r):
    need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r,'exact Ref3');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def write(p,v):
    with Path(p).open('x')as f:json.dump(v,f,sort_keys=True,allow_nan=False);f.write('\n')
    return ref(p)
def replace(p,v):
    if Path(p).exists():Path(p).unlink()
    return write(p,v)
def load(name,p):
    s=importlib.util.spec_from_file_location(name,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def change(text,before,after):
    need(text.count(before)==1,'one exact source seam operand '+before[:70]);return text.replace(before,after)


def overlays(parent,out):
    """Only exact reviewed G1 byte operands; no mathematical bodies rewritten."""
    files={name:checked(parent['files'][name]).read_text()for name in
           ('service_bridge.py','host_service.py','server090.py','command_contract.py','contract090.py')}
    s=files['service_bridge.py']
    s=change(s," return bridge\n"," if m.get('gdn_service_extension')is not None:\n  import gdn_probe_runtime\n  gdn_probe_runtime.install(bridge,live,C,m)\n return bridge\n")
    s=change(s,"  except BaseException as secondary:ctx.secondary_faults=(repr(secondary),)\n  raise\n",
        "  except BaseException as secondary:ctx.secondary_faults=(repr(secondary),)\n  if hasattr(bridge,'_bole_gdn_extension'):\n   import gdn_probe_runtime\n   gdn_probe_runtime.abort(bridge,ctx,error)\n  raise\n")
    files['service_bridge.py']=s
    s=files['host_service.py']
    s=change(s,"readset=bind_model.readset(sr)+m['dependencies']+command_contract.validate(C,sr,m)",
        "readset=bind_model.readset(sr)+m['dependencies']+command_contract.validate(C,sr,m);import gdn_probe_runtime as GP;readset+=GP.host_readset(C,sr,m)")
    s=change(s," a.output=C.output_argument(a.output);C.need(",
        " C.need(os.environ.get('BOLE_GDN_PROBE_MAIN_ENABLE')=='1','explicit MAIN GDN service numerical probe opt-in')\n a.output=C.output_argument(a.output);C.need(")
    s=change(s,"summary['CPU_report']=owned_ref.file_ref(C,c,cpu.out/'CPU.json');summary['CPU_release']=close(cpu)\n",
        "summary['CPU_report']=owned_ref.file_ref(C,c,cpu.out/'CPU.json');summary['CPU_release']=close(cpu)\n  Q=GP.helper(C,m);summary['GDN_software']=Q.materialize_software(C,cpu.out,summary['actual_software_child'],summary['CPU_release'],sr,m);readset+=GP.handoff_readset(C,sr,m,summary['GDN_software']);[C.checked(r)for r in readset];before.update({r['path']:r['sha256']for r in readset})\n")
    s=change(s,"'--receipt-root',str(ctl.out/'receipts')],'server')",
        "'--receipt-root',str(ctl.out/'receipts'),'--gdn-software-gate-ref',json.dumps(summary['GDN_software'])],'server')")
    s=change(s,"summary['independent_release']=close(consumer)",
        "gdn_out=consumer.out/'gdn';gdn_out.mkdir();summary['GDN_independent_child']=child(consumer,'GDN-INDEPENDENT',[str(P/'consume_gdn_service.py'),'--execute','--source-ref',json.dumps(sr),'--extension-ref',json.dumps(m['gdn_service_extension']['source']),'--software-gate-ref',json.dumps(summary['GDN_software']),'--base-report-ref',json.dumps(summary['independent']),'--output',str(gdn_out)],900);summary['GDN_independent']=C.ref(gdn_out/'GDN-INDEPENDENT.json');gdn_value=C.obj(summary['GDN_independent']);C.need(gdn_value['new_service_prefixes_pass']is True and gdn_value['actual_GDN_frames']==384,'actual full GDN supplement after original complete G1 consumer');summary['independent_release']=close(consumer)")
    # The consumer is a fresh Devices[] Docker exec. Explicit opt-in is passed
    # in the child CLI, never inferred from parent os.environ.
    s=change(s,"str(P/'consume_gdn_service.py'),'--execute'","str(P/'consume_gdn_service.py'),'--execute','--owned-probe-consumer'")
    # Whole entry clock covers C.source, inherited MAIN observation and replay
    # readset hashing. The original shared Joint/controller get this same clock.
    s=change(s,'def main():\n','def main():\n entry_start=time.monotonic()\n')
    s=change(s,' sr=json.loads(a.source_ref);m=C.source(sr);',
        " from gdn_probe_clock import held_main_lock,phase_admission,controller_admission\n main_lock=held_main_lock(C)if a.execute else None\n sr=json.loads(a.source_ref);m=C.source(sr);")
    s=change(s," C.need(os.environ.get('BOLE_GDN_PROBE_MAIN_ENABLE')=='1'", 
        " phase_admission(C,entry_start)\n C.need(os.environ.get('BOLE_GDN_PROBE_MAIN_ENABLE')=='1'")
    s=change(s,' start=time.monotonic();c,S,H,pairs=load(a.output);',' start=entry_start;c,S,H,pairs=load(a.output);')
    s=change(s,"ctl.observe(role+'-admission',initial=True);mark(role,'create-start-inspect');",
        "ctl.observe(role+'-admission',initial=True);controller_admission(C,c,S,ctl,entry_start);mark(role,'create-start-inspect');")
    s=change(s,"host_pid=os.getpid(),candidate_qualification=False", 
        "host_pid=os.getpid(),MAIN_lock=main_lock,entry_clock_before_source_replay=True,deadline_renewed=False,candidate_qualification=False")
    clock=load('_gdn_builder_cold_source',P/'gdn_probe_clock.py');clock.validate(s)
    files['host_service.py']=s
    s=files['server090.py']
    s=change(s,"p.add_argument('--receipt-root',type=Path);a=p.parse_args()",
        "p.add_argument('--receipt-root',type=Path);p.add_argument('--gdn-software-gate-ref');a=p.parse_args()")
    s=change(s," os.environ.update(environment(os.environ,sr,a.receipt_root))",
        " env=environment(os.environ,sr,a.receipt_root)\n if a.gdn_software_gate_ref is not None:\n  import gdn_probe_runtime\n  env=gdn_probe_runtime.server_environment(C,m,sr,env,json.loads(a.gdn_software_gate_ref))\n os.environ.update(env)")
    files['server090.py']=s
    s=files['command_contract.py']
    s=change(s,"'/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1',",
        "'/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1','DENSE090_EXTERNAL_OUTPUT_ENABLE=1','BOLE_GDN_PROBE_MAIN_ENABLE=1',")
    s=change(s,"return ['/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1'",
        "return ['/usr/bin/flock','--nonblock','--no-fork','/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock','/usr/bin/env','BOLE_MODEL131_MAIN_ENABLE=1'")
    files['command_contract.py']=s
    s=files['contract090.py'];need(s.count(parent['output_root'])==2,'exact existing model/CPU output operands')
    files['contract090.py']=s.replace(parent['output_root'],str(out))
    for name,s in files.items():compile(ast.parse(s),name,'exec')
    return files


def main():
    p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);p.add_argument('--execute',action='store_true')
    for n in('prior-G1-refs-json','replay-refs-json'):p.add_argument('--'+n)
    p.add_argument('--mode',choices=('matched_original','candidate'));p.add_argument('--new-root',type=Path);p.add_argument('--output-root',type=Path)
    a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false,"prepared_only":true}');return 0
    need(all(vars(a).values()),'exact actual G1/replay chains, matched mode and new absent source/output leaves')
    C=sys.modules[__name__];Q=load('_gdn_builder_contract',P/'gdn_probe_contract.py')
    prior=json.loads(a.prior_G1_refs_json);on,own,b,v=Q.prior(C,prior);old=Path(on['root'])
    replay=json.loads(a.replay_refs_json)
    need(set(replay)=={'replay_manifest','replay_result','replay_independent','replay_release'},'exact successful replay chain fields')
    G=load('_gdn_builder_replay_gate',P/'gdn_service_gate.py');G.replay_contract(C,replay)
    new,out=a.new_root,a.output_root
    need(new.parent==out.parent==Path('/opt/host/vnf/austinov')and new.name.startswith('bole-gdn-g1-probe-')and
        out.name=='run-'+new.name and not new.exists()and not out.exists()and not Path(str(out)+'-CPU').exists(),
        'unique registered MAIN-only source/model/CPU leaves')
    changes=overlays(on,out)
    # Donor closure was fully checked by prior(); only a fresh private copy is mutated.
    shutil.copytree(old,new,ignore=shutil.ignore_patterns('__pycache__'))
    (new/'SOURCE_BOUND.json').rename(new/'PARENT_G1_SOURCE_BOUND.json')
    for name,text in changes.items():(new/name).write_text(text)
    for name in ADDED:
        need(not(new/name).exists(),'no source/helper shadowing '+name);shutil.copyfile(P/name,new/name)
    v6=obj(on['g1_inverse']['baseline_v6']);original=obj(on['g1_predecessor']['inverse_original'])
    def ledger(donor):
        rows={}
        for name,r in donor['files'].items():
            target=new/name
            if target.is_file()and Path(r['path']).is_relative_to(Path(donor['root'])):
                before=checked(r).read_text();after=target.read_text()
                if before!=after:rows[name]=dict(before=r,after=ref(target),edits=[dict(before=before,after=after)])
        return rows
    replace(new/'FA_BOUNDARY_EDITS_R14.json',ledger(original))
    replace(new/'G1_LIFECYCLE_EDITS_V1.json',dict(schema='bole.exact-G1-lifecycle-inverse-to-passed-V6/v1',
        baseline_v6=on['g1_inverse']['baseline_v6'],failed_g1_v1=on['g1_inverse']['failed_g1_v1'],
        files=ledger(v6),original_math_unchanged=True))
    for name in('model_entry.py','service_runner.py','consume_service.py','core112.py','oracle112.py','independent_model.py',
                'native_seams.py','treeconv118.py','adapter.py','transaction.py','live_owner.py'):
        need((new/name).read_bytes()==checked(on['files'][name]).read_bytes(),'byteexact original G1 math/runner/owner/complete consumer '+name)
    m=json.loads(json.dumps(on));m.pop('prepared_template',None)
    def rebase(value):
        if type(value)is dict:
            if set(value)=={'path','bytes','sha256'}and Path(value['path']).is_relative_to(old):
                target=new/Path(value['path']).relative_to(old)
                if target.is_file():return ref(target)
            return {k:rebase(v)for k,v in value.items()}
        if type(value)is list:return [rebase(v)for v in value]
        return value
    m=rebase(m);m.update(root=str(new),output_root=str(out),model_receipt_root=str(out/'dense/receipts'),
        prepared_only=True,default_enabled=False)
    m['files'].update({name:ref(new/name)for name in ADDED})
    m['files']['G1_LIFECYCLE_EDITS_V1.json']=ref(new/'G1_LIFECYCLE_EDITS_V1.json')
    m['files']['FA_BOUNDARY_EDITS_R14.json']=ref(new/'FA_BOUNDARY_EDITS_R14.json')
    extra_count=sum(isinstance(n,ast.FunctionDef)and n.name.startswith('test_')for name in ADDED if name.startswith('test')for n in ast.walk(ast.parse((new/name).read_bytes())))
    m['service_required_sameimage_software_cases']=on['service_required_sameimage_software_cases']+extra_count
    extension=dict(schema='bole.gdn3-service-extension/v1',files={n:ref(new/n)for n in EXT},
        service_files={n:m['files'][n]for n in G.SERVICE_FILES},prior_G1=prior,**replay,
        timing_manifest=None,timing_result=None,timing_release=None,
        purpose='service_numerical_only',whole_model_qualified=False,formal_success=False)
    xr=write(new/'GDN_EXTENSION.json',extension)
    m['gdn_service_extension']=dict(source=xr,mode=a.mode,purpose='service_numerical_only',formal_performance=False,model_ready=False)
    m['dependencies'] += [*prior.values(),*replay.values(),xr,ref(__file__)]
    m['gdn_probe']=dict(prior=prior,original_software_cases=214,added_software_cases=extra_count,
        matched_O_P_U_plus_one_selected_state=True,matched_unused_three_state_removal=True,
        capture=True,performance_candidate=False,new_service_execution_claimed=False,formal_success=False)
    clock=load('_gdn_fresh_cold_source',new/'gdn_probe_clock.py');clockproof=clock.validate((new/'host_service.py').read_text())
    m['gdn_probe_cold_clock_v3']=dict(clockproof,first_entry_before_source_hashes=True,inherited_MAIN_flock_required=True,
        shared_original_Joint_and_controller=True,prior_v2_actual_CPU232_executed=False,prior_v2_actual_model_executed=False,
        prospective_sameimage_cases=m['service_required_sameimage_software_cases'])
    for path in new.rglob('*.py'):compile(path.read_bytes(),str(path),'exec')
    for name in('SOURCE_TEMPLATE.json','SOURCE.json'):replace(new/name,m)
    tr=ref(new/'SOURCE_TEMPLATE.json')
    run=subprocess.run([sys.executable,'-I','-B',str(new/'bind_model.py'),'--execute','--reviewed-template-ref',json.dumps(tr),
        '--component-refs-json',json.dumps(m['component_refs'])],capture_output=True,text=True,timeout=40)
    need(run.returncode==0,'actual fresh source bind failed '+run.stdout+run.stderr)
    sr=ref(new/'SOURCE_BOUND.json');bound=obj(sr)
    sys.path.insert(0,str(new))
    CC=load('_gdn_bound_commands',new/'command_contract.py')
    history=obj(m['command_scope']['historical_ref'])
    commands=dict(schema='bole.G1-actual-bound-commands/v2',source=tr,bound_source=sr,
        **CC.expected(str(new),str(out),sr,tr,m['component_refs']),required_sameimage_software_cases=m['service_required_sameimage_software_cases'],
        historical_required_sameimage_software_cases=history['required_sameimage_software_cases'],
        actual_G1_execution_claimed=False,legacy_entrypoints_retained_for_inverse_tests_only=True)
    replace(new/'COMMANDS.json',commands)
    replace(new/'COMMANDS_G1.json',dict(source=sr,template=tr,commands=ref(new/'COMMANDS.json'),model=commands['model'],
        CPU=commands['CPU'],required_sameimage_software_cases=m['service_required_sameimage_software_cases']))
    CC.validate(CC.C,sr,bound)
    # Audits replay/parent closure now; no resource/device admission takes place.
    sys.path.insert(0,str(new));R=load('_gdn_bound_host_runtime',new/'gdn_probe_runtime.py');R.host_readset(CC.C,sr,bound)
    print(json.dumps(dict(source=sr,extension=xr,commands=ref(new/'COMMANDS.json'),mode=a.mode,
        required_sameimage_cases=m['service_required_sameimage_software_cases'],NPU=False,
        actual_sameimage_executed=False,actual_service_executed=False,model_ready=False,formal_success=False)))
    return 0


if __name__=='__main__':raise SystemExit(main())
