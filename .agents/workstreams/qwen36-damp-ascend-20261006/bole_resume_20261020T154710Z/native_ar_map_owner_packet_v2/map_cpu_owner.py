#!/usr/bin/env python3
"""Default-OFF finite original025 CPU-only map identity diagnostic owner."""
import argparse,hashlib,importlib.util,json,os,resource,sys,time,traceback
from pathlib import Path
SCHEMA='bole.native-ar-map-diagnostic-owner-inputs/v1'
FILES={'map_cpu_owner.py','map_diagnostic_entry.py','map_identity_diagnostic.py','prepare_map_owner.py'}
OLD_OWNER_SHA='57ccd1de84de0132a2cacf5c18fcf0d56ca6eec5b09926333c9a006a7c1d7732'
TORCH_REF=dict(path='/usr/local/python3.12.13/lib/python3.12/site-packages/torch/__init__.py',bytes=106868,sha256='51c90fe34a7cf869517d1bab4cd114498790e169ec668f1a154c35ec64117a5e')
DIAG_SHA='1b96f3bac601e491f42481a0a479f53f573ac8d27dc605f0cd0abf810bb205e8'
def fail(ok,message):
    if not ok:raise ValueError(message)
def isref(v):return type(v)is dict and set(v)=={'path','bytes','sha256'}
def rkey(r):return r['path'],r['bytes'],r['sha256']
def walkrefs(v):
    if isref(v):yield v
    elif type(v)is dict:
        for q in v.values():yield from walkrefs(q)
    elif type(v)in(list,tuple):
        for q in v:yield from walkrefs(q)
def bootstrap_ref(r):
    fail(isref(r)and type(r['path'])is str and Path(r['path']).is_absolute(),'exact bootstrap Ref3')
    fail(type(r['bytes'])is int and r['bytes']>=0 and type(r['sha256'])is str and len(r['sha256'])==64,'bootstrap Ref3 fields')
    p=Path(r['path']);s=p.stat();h=hashlib.sha256();n=0;fail(p.is_file(),'ordinary bootstrap file')
    with p.open('rb')as f:
        z=os.fstat(f.fileno());fail((z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)==(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns),'bootstrap opened identity')
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b);n+=len(b)
        q=os.fstat(f.fileno())
    a=p.stat();fail((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns)==(a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns),'bootstrap stable source')
    fail(n==r['bytes']and h.hexdigest()==r['sha256'],'bootstrap complete source bytes/SHA');return r
def read_boot(r):
    bootstrap_ref(r);fail(r['bytes']<=4*2**20,'bounded owner ticket');b=Path(r['path']).read_bytes()
    fail(len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'],'ticket exact reopen');return json.loads(b)
def remaining_phase(C,start,cutoff):
    elapsed=time.monotonic()-start;remaining=3600-elapsed
    C.need(elapsed>=0 and remaining>=2580,'cold source/predecessor hashing leaves metadata600+replay900+consumer900+cleanup180')
    C.need(time.time()+remaining<=cutoff,'same original phase3600 fits fixed cutoff; never renew clock');return remaining
def full_generated_ref(C,r):
    C.need(type(r)is dict and set(r)in({'path','sha256'},{'path','bytes','sha256'}),'original generated receipt Ref2 or Ref3 only')
    C.checked(r);observed=C.ref(r['path'])
    C.need(observed['sha256']==r['sha256']and('bytes'not in r or observed['bytes']==r['bytes']),'upgrade generated Ref2 only after exact complete bytes/SHA')
    return observed
def generated_receipt_refs(C,v):
    if type(v)is dict and set(v)in({'path','sha256'},{'path','bytes','sha256'}):yield full_generated_ref(C,v)
    elif type(v)is dict:
        for q in v.values():yield from generated_receipt_refs(C,q)
    elif type(v)in(list,tuple):
        for q in v:yield from generated_receipt_refs(C,q)
def source_bundle(ticket_ref,execute=False):
    t=read_boot(ticket_ref)
    required={'schema','default_enabled','source_root','output_root','original_fia_inputs_ref','diagnostic_inputs_ref',
              'original_owner_ref','original_replay_common_ref','files','installed_host_projection',
              'torch_host_copy_ref','torch_copy_receipt_ref','v2_result_ref','predecessor_refs','preparer_execution_ref'}
    fail(type(t)is dict and set(t)==required and t['schema']==SCHEMA and t['default_enabled']is False,'exact default-OFF new owner ticket')
    fail(type(t['files'])is dict and set(t['files'])==FILES,'four new exact sources')
    for name,r in t['files'].items():
        bootstrap_ref(r);fail(str(Path(r['path']).parent)==t['source_root']and Path(r['path']).name==name,'new control source full path')
    fail(t['files']['map_cpu_owner.py']['path']==str(Path(__file__).absolute()),'prepared new owner module path identity')
    bootstrap_ref(t['original_replay_common_ref'])
    s=importlib.util.spec_from_file_location('_fia_owner_common',t['original_replay_common_ref']['path'])
    R=importlib.util.module_from_spec(s);s.loader.exec_module(R);C=R.common()
    ir=t['original_fia_inputs_ref'];y=R.source(C,ir)
    C.need(C.ref(R.__file__)==t['original_replay_common_ref']==y['files']['replay_common.py'],'original R whole source/path unchanged')
    C.need(t['original_owner_ref']==y['files']['replay_cpu_owner.py']and t['original_owner_ref']['bytes']==13176
           and t['original_owner_ref']['sha256']==OLD_OWNER_SHA,'actual full original owner, not message excerpt')
    C.checked(t['original_owner_ref']);C.checked(ticket_ref);lock=R.held_main_lock(C)if execute else None
    x,m,on,refs,mapping=R.readset(C,y);C.checked(ir);refs=list(refs)+[ir];existing={r['path']:r for r in refs}
    def add(r):
        C.checked(r);C.need(r['path']not in existing or existing[r['path']]==r,'one exact immutable source Ref3');existing[r['path']]=r
    p=C.obj(t['v2_result_ref']);add(t['v2_result_ref'])
    C.need(p['inputs']==ir and p['primary']is not None and p['secondary']==[]and p['source_before']and p['source_before']==p['source_after']
           and p['private_namespace_restored_by_identity']is True and p['singleton_profile_restored_by_identity']is True,
           'actual failed v2 immutable source/restoration chain')
    for path,digest in p['source_before'].items():
        r=existing.get(path)
        if r is None:r=C.ref(path);add(r)
        C.need(r['sha256']==digest,'actual v2 full immutable source closure: '+path)
    old_release=full_generated_ref(C,p['summary']['failure_release']);v=C.obj(old_release);add(old_release)
    C.need(v['stopped']is True and v['retained']is True and v['deleted']is False and v['errors']==[],
           'failed v2 original CPU helper stopped-retained; no failed producer promotion')
    allowed={rkey(r)for r in walkrefs(mapping)};projection={};projected=[]
    C.need(type(t['installed_host_projection'])is list,'explicit exact installed-to-host projection')
    th=t['torch_host_copy_ref'];C.need(th['bytes']==TORCH_REF['bytes']and th['sha256']==TORCH_REF['sha256'],'exact new Torch copy content')
    add(th);add(t['torch_copy_receipt_ref'])
    for row in t['installed_host_projection']:
        C.need(type(row)is dict and set(row)=={'installed_ref','host_ref'},'exact projection pair');a,b=row['installed_ref'],row['host_ref']
        C.need(isref(a)and isref(b)and(a['bytes'],a['sha256'])==(b['bytes'],b['sha256']),'same complete bytes/SHA explicit projection')
        old=rkey(a)in allowed and rkey(b)in allowed
        C.need(old or(a==TORCH_REF and b==th),'projection originates exact old mapping or pinned Torch copy')
        C.need(rkey(a)not in projection,'one host copy per exact installed Ref3');add(b);projection[rkey(a)]=b;projected.append(row)
    def host_ref(r):
        if rkey(r)in projection:add(projection[rkey(r)]);return
        add(r)
    d=C.obj(t['diagnostic_inputs_ref'])
    C.need(d['schema']=='bole.native-ar-map-identity-diagnostic-inputs/v1'and d['default_enabled']is False and d['diagnostic_seconds']==600,'exact diagnostic schema/default-OFF/cap')
    C.need(d['files']['diagnostic']==t['files']['map_identity_diagnostic.py']and d['files']['diagnostic']['bytes']==19468
           and d['files']['diagnostic']['sha256']==DIAG_SHA,'frozen actual diagnostic bytes with new full path')
    C.need(d['files']['library_maps']==y['files']['library_maps.py']and d['files']['metadata_cpu']==y['files']['metadata_cpu.py'],'original L/metadata source identities')
    C.need(d['library_name']=='_fia_metadata_maps'and d['sys_path']==[m['root']],'actual original metadata namespace root')
    original,num=R.math_sources(C,y)
    npuref=dict(path='/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/__init__.py',bytes=2435,sha256='a21f553fb9ac12f087cfdf0fb61a583be3c864d3785cff9920ec862f565d6072')
    expected_imports=[dict(kind='module',name='torch',ref=TORCH_REF),dict(kind='module',name='torch_npu',ref=npuref),
        dict(kind='file',name='pair_contract',ref=m['files']['pair_contract.py']),
        dict(kind='file',name='_fia_metadata_frozen_math',ref=original['files']['derived_math_consumer.py']),
        dict(kind='file',name='_fia_metadata_frozen_diagnostic',ref=num['files']['numeric_diagnostic.py']),
        dict(kind='file',name='_fia_metadata_arena',ref=y['files']['arena_layout.py']),
        dict(kind='file',name='_fia_metadata_maps',ref=y['files']['library_maps.py'])]
    C.need(d['imports']==expected_imports,'all actual metadata import source paths/bytes/SHA and order')
    names=[item['name']for item in d['imports']]
    C.need(names==['torch','torch_npu','pair_contract','_fia_metadata_frozen_math','_fia_metadata_frozen_diagnostic','_fia_metadata_arena','_fia_metadata_maps'],'actual original metadata import sequence')
    C.need(d['imports'][0]['ref']==TORCH_REF and d['imports'][-1]['ref']==y['files']['library_maps.py'],'actual Torch/L source joins')
    C.need(d['output_dir']==str(Path(t['output_root'])/'cpu-preflight'/'map-identity'),'new single-RW child output')
    C.need(t['files']['map_diagnostic_entry.py']in d['source_refs'],'source-bound child opt-in entry')
    for r in walkrefs(t):host_ref(r)
    for r in walkrefs(d):host_ref(r)
    for r in t['predecessor_refs']:host_ref(r)
    C.need(t['preparer_execution_ref']['bytes']==t['files']['prepare_map_owner.py']['bytes']
           and t['preparer_execution_ref']['sha256']==t['files']['prepare_map_owner.py']['sha256'],'actual preparer execution bytes, separate full path')
    C.need(Path(t['source_root']).is_absolute()and Path(t['output_root']).is_absolute()and not Path(t['output_root']).exists(),'new ordinary owner output absent')
    return C,R,t,y,x,m,on,list(existing.values()),mapping,lock,projected

def main():
    entry_start=time.monotonic();p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    g=p.add_mutually_exclusive_group();g.add_argument('--execute',action='store_true');g.add_argument('--source-audit',action='store_true')
    p.add_argument('--inputs-ref');a=p.parse_args()
    if not(a.execute or a.source_audit):print('{"enabled":false,"NPU":false,"formal_success":false}');return 0
    if not a.inputs_ref:p.error('new exact map diagnostic owner ticket Ref3 required')
    sys.dont_write_bytecode=True;tr=json.loads(a.inputs_ref)
    C,R,t,y,x,m,on,refs,mapping,lock,projected=source_bundle(tr,execute=a.execute);ir=t['original_fia_inputs_ref'];dr=t['diagnostic_inputs_ref']
    if a.source_audit:
        print(json.dumps(dict(owner_inputs=tr,original_inputs=ir,diagnostic_inputs=dr,readset_count=len(refs),
            NPU=False,resources_admitted=False,diagnostic_only=True,original_native_numerical_pass=False,formal_success=False)));return 0
    C.need(os.environ.get('BOLE_NATIVE_AR_MAP_MAIN_ENABLE')=='1','MAIN explicit new finite CPU map diagnostic opt-in')
    argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v]
    C.need(argv[1:3]==['-I','-B']and Path(argv[3]).resolve()==Path(__file__).resolve(),'actual inherited-flock private host -I/-B argv')
    remaining=remaining_phase(C,entry_start,C.obj(y['authority'])['cutoff_epoch'])
    NS=C.load(y['files']['ar_saved_namespace.py'],'_fia_private_original_namespace');SP=C.load(y['files']['singleton_profile.py'],'_fia_private_singleton_profile')
    root=Path(t['output_root']);joint=None;primary=None;summary={};namespace_restored=False;profile_restored=False
    before={r['path']:r['sha256']for r in refs};after={};all_refs={r['path']:r for r in refs};ctl=None
    def add(values):
        for r in values:
            C.checked(r);C.need(r['path']not in all_refs or all_refs[r['path']]==r,'one immutable stage input identity')
            all_refs[r['path']]=r;before[r['path']]=r['sha256']
    try:
        with NS.open_namespace(C,dict(x,output_root=t['output_root']),on)as(c,S,H,namespace):
            import owned_create
            C.need(166 in os.sched_getaffinity(0),'original host CPU166 available');os.sched_setaffinity(0,{166})
            _,hard=resource.getrlimit(resource.RLIMIT_AS);C.need(hard==resource.RLIM_INFINITY,'original Go-child AS wrapper')
            resource.setrlimit(resource.RLIMIT_AS,(512*2**20,hard));root.mkdir(mode=0o700);joint=H.Joint(entry_start)
            C.write(root/'MAIN-LOCK.json',lock);C.write(root/'PRIVATE_NAMESPACE.json',namespace);C.write(root/'SOURCE-MAPPING.json',mapping)
            pr=C.write(root/'MAP-DIAGNOSTIC-PROJECTION.json',dict(schema='bole.native-ar-map-diagnostic-host-projection/v1',
                owner_inputs=tr,original_fia_inputs=ir,installed_host_projection=projected,host_only_source_enumeration=True,
                actual_mapping_identity_qualified=False,formal_success=False));add([pr])
            with SP.install(C,c,S,H,on)as profile:
                profile_ref=C.write(root/'SINGLETON-PROFILE.json',profile);add([profile_ref])
                def open_owner(leaf,role,readset):
                    nonlocal ctl
                    leaf=H.fresh_leaf(root/leaf);H.outputs(leaf);(leaf/'receipts').mkdir()
                    ctl=H.controller(S,joint)(argparse.Namespace(output_dir=leaf),entry_start)
                    C.need(ctl.name.islower()and len(ctl.name)<80,'bounded lowercase actual owner name')
                    ctl.observe('native-fia-'+role+'-admission',initial=True)
                    C.need(ctl.cpu is not None and ctl.cpu['guest_cpus'][:1]==[0],'original CPU0 allocation AFTER observe before create')
                    ctl.remaining(cap=60)
                    live_ref=owned_create.create(c,S,ctl,ir,readset,role,Path(t['original_owner_ref']['path']).parent)
                    live,inspection=ctl.inspect();inspection=full_generated_ref(C,inspection)
                    C.need(live['State']['Running']is True and live['State']['Pid']>0,'actual source-bound live init')
                    if role=='cpu-preflight':C.need(not(live['HostConfig'].get('Devices')or[])and live['HostConfig']['Memory']==8*2**30,'original Devices[]CPU0/8GiB helper')
                    else:C.need(len(live['HostConfig'].get('Devices')or[])==4,'only singleton4→0 plus3aux')
                    return leaf,inspection
                def release(label):
                    nonlocal ctl
                    release_ref=full_generated_ref(C,ctl.cleanup());ctl._fia_closed=True;v=C.obj(release_ref)
                    C.need(v['stopped']is True and v['retained']is True and v['deleted']is False and v['errors']==[],'actual exact owned '+label+' stopped-retained clean')
                    joint.secondary.extend(ctl.secondary);ctl=None;return release_ref
                try:
                    leaf,inspection=open_owner('cpu-preflight','cpu-preflight',list(all_refs.values()));summary['diagnostic_live_inspect']=inspection
                    summary['diagnostic_child']=H.child(ctl,'MAP-IDENTITY-DIAGNOSTIC',[t['files']['map_diagnostic_entry.py']['path'],'--execute','--inputs-ref',json.dumps(dr)],600,observe=False)
                    out=leaf/'map-identity';report_ref=C.ref(out/'MAP-IDENTITY-DIAGNOSTIC.json');owned=C.ref(leaf/'OWNED.json')
                    summary['diagnostic_report']=report_ref;summary['diagnostic_owned']=owned;summary['diagnostic_release']=release('map-diagnostic');report=C.obj(report_ref)
                    C.need(report['schema']=='bole.native-ar-map-identity-diagnostic/v1'and report['inputs_ref']==dr and report['diagnostic_completed']is True and report['complete_requested_mapping_observation_attempts']is True,'actual complete CPU map observation report')
                    C.need(type(report['executable_rows_observed'])is int and 0<report['executable_rows_observed']<=1024 and report['executable_rows_processed']==report['executable_rows_observed'],'all X mappings, no selection')
                    C.need(report['source_before']and report['source_before']==report['source_after']and report['source_unchanged']is True and report['original_function_objects_unchanged']is True,'child source/function identity unchanged')
                    for flag in ('original_owner_admission_replaced','original_metadata_run_replayed','original_128_math_replayed','actual_npu_operator_called','mapped_file_identity_qualified','native_FA_math_pass','model_qualified','common_plugin_effects_pass','formal_performance_pass','atomic_proc_snapshot_claim','sampled_or_filtered_mapping_set','old_failure_reclassified_as_numerical'):
                        C.need(report[flag]is False,'diagnostic never promotes '+flag)
                    expected={'IMPORT-CONTEXT.json','PROCESS.json','PROC-VERSION.txt','PROC-STATUS.txt','PROC-CGROUP.txt','PROC-MAPS-BEFORE.txt','PROC-MOUNTINFO-BEFORE.txt','ORIGINAL-EXECUTABLE-PATHS.json','ORIGINAL-INVENTORY.json','MALFORMED-ROWS.json','EXECUTABLE-MAPPINGS.jsonl','KNOWN-SOURCE-CANONICAL-JOIN.json','PROC-MAPS-AFTER.txt','PROC-MOUNTINFO-AFTER.txt'}
                    C.need(set(report['artifacts'])==expected,'all raw/full error artifacts retained');artifacts=[]
                    for name,r in report['artifacts'].items():
                        C.need(r['path']==str(out/name),'exact private diagnostic artifact path');C.checked(r);artifacts.append(r)
                    C.need(sum(r['bytes']for r in artifacts)+report_ref['bytes']<=64*2**20,'actual complete export <=64MiB')
                    add([report_ref,owned,summary['diagnostic_release']]+artifacts+list(generated_receipt_refs(C,summary['diagnostic_child']))+list(generated_receipt_refs(C,inspection)))
                    summary['diagnostic_report_validated']=True
                except BaseException as error:primary=dict(error=repr(error),traceback=traceback.format_exc());C.write(root/'FIRST-FAULT.json',primary)
                finally:
                    if ctl is not None:
                        if ctl.cid and not getattr(ctl,'_fia_closed',False):
                            ctl.primary=primary
                            try:summary['failure_release']=ctl.cleanup()
                            except BaseException as error:joint.secondary.append(repr(error))
                        joint.secondary.extend(ctl.secondary)
            profile_restored=True
        namespace_restored=True
    except BaseException as error:
        failure=dict(error=repr(error),traceback=traceback.format_exc())
        if primary is None:primary=failure
        elif joint is not None:joint.secondary.append('namespace/profile-finally '+repr(error))
        if root.is_dir()and not(root/'FIRST-FAULT.json').exists():C.write(root/'FIRST-FAULT.json',failure)
    if joint is None:raise ValueError('pre-admission failure; no owned controller/result authority: '+repr(primary))
    try:
        for r in all_refs.values():C.checked(r);after[r['path']]=r['sha256']
    except BaseException as error:joint.secondary.append('immutable-input-after '+repr(error))
    if time.monotonic()>joint.deadline or time.time()>=C.obj(y['authority'])['cutoff_epoch']:joint.secondary.append('original whole3600/fixed cutoff expired')
    if joint.cleanup_used>180:joint.secondary.append('original joint cleanup180 exceeded')
    completed=primary is None and not joint.secondary and bool(before)and before==after and profile_restored and namespace_restored and summary.get('diagnostic_report_validated')is True and 'diagnostic_release'in summary
    result=C.write(root/'RESULT.json',dict(schema='bole.native-ar-map-identity-finite-owner/v1',owner_inputs=tr,original_fia_inputs=ir,diagnostic_inputs=dr,original_AR_source=y['AR_source'],resource_admission_source_ref=ir,
        resource_bootstrap_root=str(Path(t['original_owner_ref']['path']).parent),summary=summary,primary=primary,secondary=joint.secondary,source_before=before,source_after=after,MAIN_lock=lock,actual_host_argv=argv,
        entry_clock_before_source_replay=True,phase_remaining_at_admission=remaining,phase_seconds=3600,cleanup_seconds=180,elapsed=time.monotonic()-entry_start,cleanup_spent=joint.cleanup_used,
        private_namespace_restored_by_identity=namespace_restored,singleton_profile_restored_by_identity=profile_restored,original025_resource_methods_preserved=True,original_model_manifest_validation_preserved=True,diagnostic_completed=completed,
        original_metadata_run_replayed=False,all128_two_filler_control_pending=True,NPU_stage_requested=False,physical=[],logical=[],guest_cpus=[0],original_G1_math_rerun=False,model_reexecuted=False,
        original_native_numerical_pass=False,native_FA_math_qualified=False,mapped_file_identity_qualified=False,common_effects_pass=False,performance_ready=False,formal_success=False))
    print(json.dumps(dict(result=result,diagnostic_completed=completed,formal_success=False)),flush=True);return 0 if completed else 3
if __name__=='__main__':raise SystemExit(main())
