"""Source-bound actual fsum/copy prerequisites for private FIA diagnostic replay."""
import importlib.util
import base64
import csv
import json
from pathlib import Path
import re

LOCK='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_ADMISSION.lock'
FILES=('ar_owner_common.py','ar_saved_namespace.py','replay_common.py','prepare_replay_owner.py','replay_cpu_owner.py',
    'metadata_cpu.py','replay_fia.py','consume_replay.py','singleton_profile.py','arena_layout.py','library_maps.py',
    'ACTUAL_FSUM_REFS.json','INSTALLED_PROVENANCE_REFS.json','INSTALLED_DISPATCH_REFS.json','INSTALLED_LINKED_REFS.json','namespace_repair_gate.py','ACTUAL_FIA_V1_REFS.json','ACTUAL_NAMESPACE_PROBE_REFS.json','namespace_compile_probe.py','prepare_profile_repair_v2.py')


def common():
    import hashlib
    p=Path(__file__).parent/'ar_owner_common.py';b=p.read_bytes()
    if(len(b),hashlib.sha256(b).hexdigest())!=(19055,'5d0b9034706b9a942a4d7dd10870139959b22dfaab2cebbdddf25ba962e456a4'):
        raise ValueError('exact original AR025 common')
    s=importlib.util.spec_from_file_location('_fia_original_common',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def inspection(C,r):
    value=C.obj(r)
    if type(value)is dict and 'stdout'in value:
        C.need(value['exit_code']==0 and type(value['stdout'])is str,'actual successful inspect wrapper')
        value=json.loads(value['stdout'])
    if type(value)is list:
        C.need(len(value)==1,'one actual inspect');value=value[0]
    C.need(type(value)is dict and 'Id'in value and 'State'in value,'complete actual Docker inspect')
    return value


def successful_fsum(C):
    refs=C.obj(C.ref(Path(__file__).parent/'ACTUAL_FSUM_REFS.json'))
    values={n:C.obj(r)for n,r in refs.items()if n.endswith('.json')}
    for r in refs.values():C.checked(r)
    owner=values['RESULT.json'];old=values['INPUTS.json'];report=values['cpu-consumer/FSUM-ORACLE.json'];release=values['cpu-consumer/cleanup.json']
    owned=values['cpu-consumer/OWNED.json'];child=values['cpu-consumer/FSUM-ORACLE-CHILD.json'];unit=values['UNIT_TERMINAL.json']
    C.need(owner['schema']=='bole.native-ar-fsum-oracle-finite-owner/v1'and owner['primary']is None and owner['secondary']==[]and
        owner['inputs']==report['inputs']==refs['INPUTS.json']and owner['source_before']==owner['source_after']and len(owner['source_before'])==913 and
        owner['entry_clock_before_source_replay']is True and owner['independent_oracle_control_completed']is True and
        owner['mathematics_recomputed']is True and owner['Devices']==[]and owner['guest_CPU']==0,
        'actual source-equal completed independent all128 fsum control')
    C.need(report['all128_independent_oracle_join_pass']is True and report['frame_count']==128 and report['rank_count']==4 and
        report['independent_failure_frame_count']==16 and report['independent_violation_count']==32 and
        report['scalar_product_terms']==51904512 and report['exp_terms']==101376 and
        all(owner[k]is False and report[k]is False for k in('NPU','native_FA_math_qualified','native_AR_numeric_pass','common_effects_pass',
            'model_ready','performance_ready','formal_success')),'independent arithmetic agrees; original numerical failure remains')
    C.need(release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[]and
        release['container']==owned['cid']and owned['image']==C.IMAGE and owned['guest_cpus']==[0]and
        child['exit_code']==0 and child['child_termination_observed']is True and child['requested_argv'][:3]==['/usr/bin/docker','exec',owned['cid']],
        'actual original fsum child and exact stopped-retained CPU owner')
    after=inspection(C,release['after_inspect'])
    C.need(after['Id']==owned['cid']and after['Image']==C.IMAGE and after['State']['Running']is False and after['State']['Pid']==0 and
        not after.get('ExecIDs'),'real release wrapper/second-layer inspect shows no pending owner execution')
    properties=unit['properties']
    C.need(unit['schema']=='bole.actual-finite-unit-terminal/v1'and unit['unit']=='bole-native-ar-fsum-20261020t154710z-v1.service'and
        all(properties[k]==v for k,v in dict(Id=unit['unit'],MainPID='0',ControlPID='0',Result='success',ExecMainStatus='0',
            ActiveState='active',SubState='exited',Type='exec',Restart='no').items()),'actual full owner namespace-finally exited0')
    r=old['files']['fsum_common.py']
    C.need((r['bytes'],r['sha256'])==(7125,'29dc17e3e4570fd9bc94743663e74d071a9f44ac7c9199e65e1473e1dccb9c5d'),'exact successful fsum helper before import')
    F=C.load(r,'_fia_successful_fsum_common');F.source(C,refs['INPUTS.json'])
    return refs,values,owner,old,F


def held_main_lock(C):
    *_,F=successful_fsum(C);return F.held_main_lock(C)


def source(C,ir):
    y=C.obj(ir)
    C.need(y['schema']=='bole.native-ar-FIA-replay-inputs/v1'and y['files']['replay_common.py']==C.ref(__file__)and
        y['MAIN_lock']==LOCK and y['default_enabled']is False and y['prepared_only']is True,'new exact defaultOFF FIA replay source')
    for r in y['files'].values():C.checked(r)
    p=Path(y['output_root'])
    C.need(p.parent==Path('/opt/host/vnf/austinov')and re.fullmatch('run-bole-native-ar-fia-[a-z0-9-]{1,15}',p.name)is not None,
        'new bounded native AR singleton replay leaf')
    C.need(y['phase_seconds']==3600 and y['cleanup_seconds']==180 and y['metadata_cap_seconds']==600 and
        y['replay_cap_seconds']==y['consumer_cap_seconds']==900 and y['physical']==[4]and y['logical']==[0]and
        y['frames']==128 and y['actual_operator_calls_required']==256 and
        y['preregistered_fillers']==['all_zero','finite_alternating']and y['unused_arena_reconstruction']is True and
        y['precision_change']is False and y['original_numerical_failure_preserved']is True,'fixed source-bound all128×2 protocol and unchanged limits')
    namespace_repair_values(C,y)
    return y


def copy_records(C,y):
    refs={}
    for name in('INSTALLED_PROVENANCE_REFS.json','INSTALLED_DISPATCH_REFS.json','INSTALLED_LINKED_REFS.json'):
        refs.update(C.obj(C.ref(Path(__file__).parent/name)))
    receipts=[]
    for name,r in refs.items():
        if name.endswith('COPY.json'):receipts.append(r)
    receipts.extend(y['extra_copy_refs'])
    objects=[];mapping={};wheel_libraries={}
    for r in receipts:
        value=C.obj(r);objects.extend([r,value]);C.need(value['image']==C.IMAGE and value.get('resources_admitted')is False and value.get('NPU')is False,
            'actual stopped same-image metadata copy, not a live/process library proof')
        before=inspection(C,value['before']);after=inspection(C,value['after'])
        C.need(before['Id']==after['Id']==value['cid']and before['Image']==after['Image']==C.IMAGE and
            before['State']['Running']is after['State']['Running']is False and before['State']['Pid']==after['State']['Pid']==0,
            'ordinary file copy from same exact stopped image, never stopped exec')
        if value['schema']=='bole.stopped-image-wheel-record/v1':
            record=value['record'];C.checked(record['copy'])
            with Path(record['copy']['path']).open(newline='')as stream:rows=list(csv.reader(stream))
            root=Path(record['requested_path']).parent.parent
            for selected in value['selected_library_rows']:
                C.need(rows.count(selected)==1 and len(selected)==3 and selected[1].startswith('sha256='),
                    'exact selected installed library row in actual complete wheel RECORD')
                relative=Path(selected[0]);C.need(not relative.is_absolute()and '..'not in relative.parts and relative.parts[0]=='torch_npu',
                    'explicit finite wheel library path; no path-prefix permission or traversal')
                digest=base64.urlsafe_b64decode(selected[1].split('=',1)[1]+'='*((-len(selected[1].split('=',1)[1]))%4)).hex()
                installed=dict(path=str(root/relative),bytes=int(selected[2]),sha256=digest)
                wheel_libraries[installed['path']]=dict(installed=installed,record=record['copy'],row=selected)
            copy_rows=[record]
        else:copy_rows=value['files']
        for row in copy_rows:
            if row['exit_code']!=0:continue
            host=row['copy'];C.checked(host);path=row['requested_path']
            installed=dict(path=path,bytes=host['bytes'],sha256=host['sha256'])
            C.need(Path(path).is_absolute()and path!=host['path'],'explicit installed alias differs from exact host-copy path')
            record=dict(installed=installed,host=host,copy_receipt=r)
            C.need(path not in mapping or mapping[path]['installed']==installed,'one exact installed alias content')
            mapping[path]=record
    C.need(mapping['/usr/local/python3.12.13/lib/python3.12/site-packages/torch_npu/lib/libtorch_npu.so']['installed']['sha256']==
        '83fb9a0eb249aef6bca7f8463047fcb4d3062cc4849f17ddf31a5e050c838842'and
        mapping['/usr/local/Ascend/ascend-toolkit/latest/lib64/libopapi.so']['installed']['sha256']==
        '3e10def2f7158482f3967b9db6ad2707cca8691198ddae8cc52bbbaf61bb2675','exact installed TorchNPU/opapi evidence bytes')
    for r in refs.values():C.checked(r)
    for path,row in wheel_libraries.items():
        if path in mapping:C.need(mapping[path]['installed']==row['installed'],'actual wheel RECORD agrees with independent whole binary copy')
    return mapping,[*objects,refs],wheel_libraries


def installed_alias(C,r):
    # The installed latest alias may be a symlink. It is permitted only by its
    # exact declared Ref3 above, then resolved and fully hashed independently.
    p=Path(r['path']);canonical=p.resolve(strict=True);actual=C.ref(canonical)
    C.need((actual['bytes'],actual['sha256'])==(r['bytes'],r['sha256']),'declared installed alias resolves to exact copied bytes')
    return actual


def readset(C,y,*,installed=False):
    refs,values,owner,old,F=successful_fsum(C)
    C.need(y['actual_fsum_refs']==refs and y['original_fsum_inputs']==refs['INPUTS.json'],'actual fsum source exact ticket')
    x,m,on,base,base_mapping=F.readset(C,old,installed=installed)
    current={r['path']:r['sha256']for r in(*base,refs['INPUTS.json'])}
    C.need(all(current.get(path)==sha for path,sha in owner['source_before'].items()),'all913 immutable successful fsum inputs reopened')
    C.need(y['AR_source']==x['AR_source']and y['authority']==x['authority'],'same original actual AR/authority')
    num=C.obj(old['original_NUMdiag_inputs']);original=C.obj(num['original_numeric_inputs'])
    B=C.load(original['files']['saved_common.py'],'_fia_original_saved_common')
    prior_mapping=base_mapping['original_NUMdiag_mapping']['original_numeric_mapping']['mapping']
    copies,objects,wheel=copy_records(C,y)
    projection={r['installed']['path']:r for r in prior_mapping}
    for path,row in copies.items():
        C.need(path not in projection or projection[path]['installed']==row['installed'],'one exact source installed projection')
        projection[path]=row
        if installed:installed_alias(C,row['installed'])
    if installed:
        for row in wheel.values():installed_alias(C,row['installed'])
    extra,_=B.collect(C,[values,refs,y['files'],objects,namespace_repair_values(C,y)['objects']],projection,installed=installed)
    unique={}
    for r in(*base,*extra,refs['INPUTS.json']):
        C.need(r['path']not in unique or unique[r['path']]==r,'one exact FIA replay immutable input');unique[r['path']]=r
    for path,sha in namespace_repair_values(C,y)['source_before'].items():
        r=unique.get(path)
        if r is None:r=C.ref(path);unique[path]=r
        C.need(r['sha256']==sha,'all1010 exact immutable failed-v1 source paths reopened; no prefix exemption')
    return x,m,on,list(unique.values()),dict(base=base_mapping,installed_copies=copies,wheel_libraries=wheel,
        actual_CPU_profile=base_mapping['actual_CPU_profile'],original913_sources_reopened=True,
        original_G1_math_rerun=False,original_native_numerical_pass=False,loaded_libraries_proven=False,NPU=False)


def math_sources(C,y):
    old=C.obj(y['original_fsum_inputs']);num=C.obj(old['original_NUMdiag_inputs']);original=C.obj(num['original_numeric_inputs'])
    return original,num


def metadata_gate(C,y,ir,hr):
    h=C.obj(hr);C.need(h['schema']=='bole.native-AR-FIA-actual-CPU-handoff/v1'and h['inputs']==ir,'actual source-bound CPU handoff')
    value=C.obj(h['report']);child=C.obj(h['child']);owned=C.obj(h['owned']);release=C.obj(h['release'])
    C.need(value['schema']=='bole.native-AR-FIA-Devices0-metadata/v1'and value['inputs']==ir and value['source']==y['AR_source']and
        value['metadata_preflight_pass']is True and value['frame_count']==128 and value['rank_count']==4 and len(value['rows'])==128 and
        value['NPU']is False and value['Devices']==[]and value['native_operator_called']is False and value['weights_only_load']is True and
        value['actual_export_packet_identity']is True and value['original_native_numerical_pass']is False and
        sum(r['native_numerical_failure_preserved']for r in value['rows'])==16,'actual complete CPU metadata; no native pass')
    C.need(owned['image']==C.IMAGE and owned['source']==ir and owned['arm']=='cpu-preflight'and owned['guest_cpus']==[0]and
        child['exit_code']==0 and child['child_termination_observed']is True and
        child['requested_argv'][:3]==['/usr/bin/docker','exec',owned['cid']]and
        child['requested_argv'].count(y['files']['metadata_cpu.py']['path'])==1 and
        release['container']==owned['cid']and release['stopped']is True and release['retained']is True and release['errors']==[],
        'real metadata child/source/owned image and released CPU owner')
    after=inspection(C,release['after_inspect'])
    C.need(after['Id']==owned['cid']and after['Image']==C.IMAGE and after['State']['Running']is False and after['State']['Pid']==0 and
        not(after['HostConfig'].get('Devices')or[])and not after.get('ExecIDs'),'actual stopped Devices[] metadata producer')
    libs=value['allowed_executable_libraries'];C.need(0<len(libs)<=2048,'finite exact CPU/fixed executable catalog')
    for path,row in libs.items():
        r=row['ref'];C.need(set(r)=={'path','bytes','sha256'}and r['path']==path and Path(path).is_absolute()and
            type(r['bytes'])is int and r['bytes']>0 and re.fullmatch('[0-9a-f]{64}',r['sha256'])is not None and
            row['ELF']['ELF']is True,'explicit complete ELF/wholeSHA catalog; no basename or prefix approval')
    copies,_,wheel=copy_records(C,y);expected={p:r['installed']for p,r in copies.items()}
    expected.update({p:r['installed']for p,r in wheel.items()});observed={}
    for row in value['static_installed_aliases']:
        r=row['installed_alias'];canonical=row['canonical']
        C.need(expected.get(r['path'])==r and set(canonical)=={'path','bytes','sha256'}and Path(canonical['path']).is_absolute()and
            (r['bytes'],r['sha256'])==(canonical['bytes'],canonical['sha256']),'exact static alias↔actual CPU canonical bytes, no guessed path')
        observed[r['path']]=r
    C.need(observed==expected,'complete declared installed copy/wheel set checked in actual CPU image')
    return h,value


def metadata_readset(C,y,ir,hr):
    """Host checks ordinary handoff files; declared actual CPU-installed refs remain distinct.

    The exact inventory came from the successful source/image-bound Devices[]
    child above. Host enumeration cannot pretend those image files are host
    copies. Future NPU bind reopens/hash-checks every full canonical Ref again.
    """
    h,value=metadata_gate(C,y,ir,hr);installed=[]
    for row in value['allowed_executable_libraries'].values():installed.append(row['ref'])
    for row in value['static_installed_aliases']:installed.extend([row['installed_alias'],row['canonical']])
    unique={}
    def walk(v):
        if type(v)is dict:
            if set(v)in({'path','bytes','sha256'},{'path','sha256'}):
                if any(v==r for r in installed):return
                full=C.ref(v['path']);C.need(full['sha256']==v['sha256']and('bytes'not in v or full['bytes']==v['bytes']),
                    'ordinary handoff source/receipt bytes; unknown refs fail')
                C.need(full['path']not in unique or unique[full['path']]==full,'one ordinary handoff path identity');unique[full['path']]=full
            else:
                for child in v.values():walk(child)
        elif type(v)is list:
            for child in v:walk(child)
    walk([hr,h,value,C.obj(h['child']),C.obj(h['owned']),C.obj(h['release'])])
    return list(unique.values()),dict(actual_CPU_inventory_ref=h['report'],explicit_installed_Ref_count=len(installed),
        exact_full_Ref_projection_only=True,host_claims_installed_file_hash=False,NPU_reopen_fullSHA_buildID_required=True)


def admission_gate(C,y,ir,hr,ar):
    h,_=metadata_gate(C,y,ir,hr);a=C.obj(ar);o=C.obj(a['owned']);v=inspection(C,a['live_inspect'])
    C.need(a['schema']=='bole.native-AR-FIA-actual-singleton-admission/v1'and a['inputs']==ir and
        a['metadata_handoff']==hr and a['owned_CID']==o['cid']==v['Id']and o['image']==v['Image']==C.IMAGE and
        o['source']==ir and o['arm']=='dense'and v['State']['Running']is True and v['State']['Pid']>0 and
        not v['State'].get('OOMKilled')and not v.get('ExecIDs')and len(o['guest_cpus'])==4,
        'actual MAIN-owned source/image/live singleton admission after real CPU metadata release')
    hcfg=v['HostConfig'];cfg=v['Config'];devices=hcfg.get('Devices')or[]
    expected={'/dev/davinci4':'/dev/davinci0',**{'/dev/'+n:'/dev/'+n for n in('davinci_manager','devmm_svm','hisi_hdc')}}
    C.need(len(devices)==4 and {d['PathOnHost']:d['PathInContainer']for d in devices}==expected and
        all(d['CgroupPermissions']=='rwm'for d in devices)and hcfg['Memory']==hcfg['MemorySwap']==32*2**30 and
        hcfg['NanoCpus']==4*10**9 and hcfg['CpusetCpus']==','.join(map(str,o['guest_cpus']))and
        hcfg['Privileged']is False and hcfg['NetworkMode']=='none'and hcfg['ReadonlyRootfs']is True and
        set(hcfg['CapDrop'])=={'ALL'}and set(hcfg['SecurityOpt'])=={'no-new-privileges'}and
        not hcfg.get('DeviceRequests')and not hcfg.get('DeviceCgroupRules'),
        'actual singleton4→0/three aux, cap32/sevenCPU isolation and readonly root, protected0..3 absent')
    C.need(v['Name']=='/'+o['name']and cfg['Labels']['model-tuning-lab.source-manifest-sha256']==ir['sha256']and
        cfg['Labels']['model-tuning-lab.controller-sha256']==o['host_sha256']and cfg['Labels']['model-tuning-lab.run']==o['name']and
        cfg['Labels']['model-tuning-lab.arm']=='dense'and cfg['Env'].count('ASCEND_RT_VISIBLE_DEVICES=0')==1 and
        cfg['Env'].count('TORCH_DEVICE_BACKEND_AUTOLOAD=0')==1,'real original controller/source/run labels and logical0 environment')
    mounts={m['Destination']:(m['Source'],m['RW'])for m in v['Mounts']}
    C.need(len(mounts)==len(v['Mounts'])==len(o['mounts'])and mounts=={p:tuple(q)for p,q in o['mounts'].items()}and
        {d:(p,rw)for d,(p,rw)in mounts.items()if rw}=={str(Path(y['output_root'])/'dense'):(str(Path(y['output_root'])/'dense'),True),
            '/adakv-results':(str(Path(y['output_root'])/'dense'),True)},'exact all readonly mounts and sole private replay RW leaf')
    profile=C.obj(a['singleton_profile'])
    C.need(profile['adapter']==y['files']['singleton_profile.py']and profile['physical']==[4]and profile['logical']==[0]and
        profile['whole_singleton_inverse']is True and profile['original_Controller_and_resource_methods_unchanged']is True and
        profile['cap32_and_seven_CPU_budget_unchanged']is True and profile['resource_PHYSICAL_unchanged']==[4,5,6,7]and
        profile['original_FD_HBM_idle_scope_preserved']is True and a['phase_clock_not_renewed']is True,
        'explicit exact original025 singleton-only adapter source/whole inverse ledger')
    return dict(a,reference=ar)


def replay_gate(C,y,ir,hr,rr):
    h=C.obj(rr);C.need(h['schema']=='bole.native-AR-FIA-actual-replay-handoff/v1'and h['inputs']==ir and h['metadata_handoff']==hr,
        'exact source-bound actual replay/release handoff')
    v=C.obj(h['report']);owned=C.obj(h['owned']);child=C.obj(h['child']);release=C.obj(h['release'])
    admission=admission_gate(C,y,ir,hr,h['admission'])
    C.need(v['schema']=='bole.native-AR-FIA-all128-two-filler-replay/v1'and v['inputs']==ir and v['source']==y['AR_source']and
        v['metadata_handoff']==hr and v['admission']==h['admission']and v['rank_count']==4 and v['frame_count']==128 and
        v['actual_operator_calls']==256 and len(v['ranks'])==4 and v['fillers']==y['preregistered_fillers']and
        v['same_operator_replay_completed']is True and v['all13_kwargs_unchanged']is True and
        v['all_input_bits_unchanged']is True and v['maps_checked_before_after_each_call']is True and
        v['whole_SHA_buildIDs_joined_start_end']is True and v['whole_SHA_buildIDs_recomputed_each_call_before_after']is True and v['HF32']is False and v['precision_changed']is False and
        v['unused_arena_reconstruction']is True and v['original_failure_frame_count']==16 and
        all(v[k]is False for k in('original_native_numerical_pass','native_FA_math_qualified','common_effects_pass','formal_success')),
        'all256 same-operator diagnostic outputs and unchanged original failure; never numerical promotion')
    C.need(owned==C.obj(admission['owned'])and owned['cid']==admission['owned_CID']and child['exit_code']==0 and
        child['child_termination_observed']is True and child['requested_argv'][:3]==['/usr/bin/docker','exec',owned['cid']]and
        child['requested_argv'].count(y['files']['replay_fia.py']['path'])==1 and release['container']==owned['cid']and
        release['stopped']is True and release['retained']is True and release['deleted']is False and release['errors']==[],
        'actual original-owned replay child0 and exact fullCID stopped-retained before independent CPU consume')
    after=inspection(C,release['after_inspect'])
    C.need(after['Id']==owned['cid']and after['Image']==C.IMAGE and after['State']['Running']is False and
        after['State']['Pid']==0 and not after.get('ExecIDs'),'actual NPU owned stopped and no pending executions')
    _,metadata=metadata_gate(C,y,ir,hr)
    C.need(v['allowed_executable_libraries']==metadata['allowed_executable_libraries'],'actual predeclared full CPU/static catalog unchanged')
    join=C.obj(h['process_join']);guest=v['process']
    C.need(join['schema']=='bole.native-AR-FIA-live-process-join/v1'and join['inputs']==ir and
        join['owned_CID']==owned['cid']and join['guest']==guest and join['original_controller_observe_unmodified']is True and
        join['actual_compute']and join['observations']and len({(p['pid'],p['start_ticks'])for p in join['actual_compute']})==1,
        'actual original host controller observed one precise replay compute lifetime')
    observations=[C.obj(r)for r in join['observations']]
    actual=[p for o in observations for p in o['actual_compute']]
    C.need(all(p in actual and p['physical']==4 and p['chip']==0 and owned['cid']in p['cgroup']and
        p['namespace_pids'][-1]==guest['pid']and p['start_ticks']==guest['start_ticks']and
        p['argv'].count(y['files']['replay_fia.py']['path'])==1 for p in join['actual_compute']),
        'original actual physical4 host NSpid/start/cgroup joins exact registered replay guest process; no synthetic admission')
    return h,v


def replay_readset(C,y,ir,hr,rr):
    h,v=replay_gate(C,y,ir,hr,rr);_,metadata=metadata_gate(C,y,ir,hr)
    declared=[row['ref']for row in metadata['allowed_executable_libraries'].values()]
    ordinary={}
    def walk(value):
        if type(value)is dict:
            if set(value)in({'path','bytes','sha256'},{'path','sha256'}):
                if any(value==r for r in declared):return
                r=C.ref(value['path']);C.need(r['sha256']==value['sha256']and('bytes'not in value or r['bytes']==value['bytes']),
                    'ordinary whole replay evidence; unknown Ref never exempt')
                C.need(r['path']not in ordinary or ordinary[r['path']]==r,'one exact replay path identity');ordinary[r['path']]=r
            else:
                for x in value.values():walk(x)
        elif type(value)is list:
            for x in value:walk(x)
    walk([rr,h,v,C.obj(h['child']),C.obj(h['owned']),C.obj(h['release']),C.obj(h['admission']),C.obj(h['process_join'])])
    for rank in v['ranks']:walk(C.obj(rank['report']))
    return list(ordinary.values()),dict(exact_CPU_catalog_only=True,unknown_ordinary_Ref_rejected=True,
        host_installed_hash_claim=False,replay_handoff=rr,actual_maps_fullSHA_joined_by_source_bound_child=True)


def namespace_repair_values(C,y):
    gate=C.load(y['files']['namespace_repair_gate.py'],'_fia_namespace_repair_v2_gate')
    return gate.verify(C,y)
