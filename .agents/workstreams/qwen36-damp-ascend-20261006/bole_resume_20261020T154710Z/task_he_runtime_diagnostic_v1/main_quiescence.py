"""Read-only explicit MAIN lifecycle checks; foreign declarations stay metadata.
No discovery, stop, signal, lock acquisition, model import or device operation.
"""
import json
from pathlib import Path
import re
import time
import owner_common as C

SCHEMA='bole.MAIN-NPU-quiescence-policy/v2'
REGISTRY_SCHEMA='bole.explicit-MAIN-CPU3-owned-registry/v1'
SYSTEMCTL='/usr/bin/systemctl'
DOCKER='/usr/bin/docker'
PROPERTIES=('Id','LoadState','ActiveState','SubState','MainPID','ControlPID','Job','ControlGroup','ExecStart','FragmentPath','RemainAfterExit','TasksCurrent')

# Fixed approved partition; authorization is explicit actual Ref3 registry membership.
CPU3_PROFILE={'TP_world_size': 4, 'consumer': [145], 'consumer_budget': 1, 'formal_timing': False, 'host': [166], 'host_budget': 1, 'model': [0, 1, 2], 'model_budget': 3, 'reserve': [3, 144], 'reserve_budget': 2, 'schema': 'bole.untimed-stream-CPU-budget/v1', 'total_budget': 7}


def strict_ref3(reference):
    C.need(type(reference)is dict and set(reference)=={'path','bytes','sha256'}
           and type(reference['bytes'])is int and reference['bytes']>=0
           and type(reference['sha256'])is str and re.fullmatch('[0-9a-f]{64}',reference['sha256']),
           'explicit complete CPU3 registry Ref3')
    C.checked(reference)
    return reference


def registry(reference,*,authority_ref):
    strict_ref3(reference);v=C.obj(reference)
    C.need(type(v)is dict and set(v)=={'schema','authority_ref','entries'}and v['schema']==REGISTRY_SCHEMA
           and v['authority_ref']==authority_ref,'same exact CPU3 registry authority/schema')
    C.checked(v['authority_ref']);rows=v['entries']
    C.need(type(rows)is list and len(rows)<=64,'bounded explicit CPU3 entry inventory')
    paths=[];cids=[]
    for row in rows:
        C.need(type(row)is dict and set(row)=={'owned_ref','source_ref','cid','profile'},'complete exact CPU3 entry keys')
        strict_ref3(row['owned_ref']);strict_ref3(row['source_ref'])
        C.need(type(row['cid'])is str and re.fullmatch('[0-9a-f]{64}',row['cid'])
               and C.canonical(row['profile'])==C.canonical(CPU3_PROFILE),'exact CPU3 full CID and unchanged sevenCPU partition')
        e=C.obj(row['owned_ref']);source=C.obj(row['source_ref'])
        C.need(e.get('cid')==row['cid']and type(e.get('guest_cpus'))is list
               and all(type(n)is int for n in e['guest_cpus'])and e['guest_cpus']==CPU3_PROFILE['model']
               and C.ref(C.checked(e['source']))==row['source_ref'],
               'registry full owned/source/CID/declared model3 identity join')
        C.need(C.canonical(source.get('stream_resource_profile'))==C.canonical(CPU3_PROFILE),
               'actual whole source exact model3/consumer1/host1/reserve2 total7 profile')
        paths.append(row['owned_ref']['path']);cids.append(row['cid'])
    C.need(len(paths)==len(set(paths))and len(cids)==len(set(cids)),'no duplicate registered CPU3 owned paths or CIDs')
    return v


def policy(reference,*,authority_ref=None):
    v=C.obj(reference)
    C.need(type(v)is dict and set(v)=={'schema','authority_ref','declared_complete_MAIN_NPU_inventory','units','owned_refs','serial_schedule','CPU3_registry_ref'}
           and v['schema']==SCHEMA and v['declared_complete_MAIN_NPU_inventory']is True,'explicit complete MAIN-only lifecycle inventory')
    C.checked(v['authority_ref'])
    if authority_ref is not None:C.need(v['authority_ref']==authority_ref,'same new CPU authority')
    reg=registry(v['CPU3_registry_ref'],authority_ref=v['authority_ref'])
    units=v['units'];owned=v['owned_refs'];s=v['serial_schedule']
    C.need(type(units)is list and 1<=len(units)<=64 and type(owned)is list and 1<=len(owned)<=64,'bounded nonempty known MAIN controller/container inventory')
    names=[]
    for u in units:
        C.need(type(u)is dict and set(u)=={'unit','controller_ref'}and type(u['unit'])is str
               and re.fullmatch(r'bole-[A-Za-z0-9_.@:-]+\.service',u['unit']),'explicit exact MAIN NPU unit; no wildcard/foreign inventory')
        names.append(u['unit']);C.checked(u['controller_ref'])
    C.need(len(set(names))==len(names),'no duplicate unit')
    actual_owned=[C.ref(C.checked(r))for r in owned]
    C.need(all(row['owned_ref']in actual_owned for row in reg['entries']),'every registered CPU3 entry belongs to explicit MAIN owned_refs')
    cids=[]
    for r in owned:cids.append(owned_identity(r,CPU3_registry_ref=v['CPU3_registry_ref'],authority_ref=v['authority_ref'])['cid'])
    C.need(len(set(cids))==len(cids),'no duplicate MAIN CID')
    C.need(type(s)is dict and set(s)=={'no_MAIN_NPU_start_during_CPU_owner','external_lock_path','external_lock_argv_prefix','lock_lifetime','lock_verification_owner'}
           and s['no_MAIN_NPU_start_during_CPU_owner']is True and s['lock_lifetime']=='entire-owner'
           and s['lock_verification_owner']=='MAIN-submitter','MAIN serial scheduling and external lifetime lock declaration')
    lock=Path(s['external_lock_path'])
    C.need(lock.is_absolute()and lock.name=='MAIN_ADMISSION.lock'and '..'not in lock.parts
           and not any(p.is_symlink()for p in(lock,*lock.parents)),'ordinary explicit MAIN shared lock path')
    C.need(s['external_lock_argv_prefix']==['/usr/bin/flock','--nonblock','--no-fork',str(lock)],'exact external nonblocking whole-owner lock prefix')
    return v


def owned_identity(reference,*,CPU3_registry_ref=None,authority_ref=None):
    e=C.obj(reference)
    C.need(re.fullmatch('[0-9a-f]{64}',e.get('cid',''))is not None and e.get('image')==C.IMAGE
           and type(e.get('name'))is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',e['name'])
           and type(e.get('arm'))is str and e['arm']!='cpu-preflight'
           and type(e.get('guest_cpus'))is list,
           'actual prior full-CID same-image MAIN model OWNED receipt')
    if len(e['guest_cpus'])==4:
        C.need(len(set(e['guest_cpus']))==4 and all(type(n)is int and n>=0 for n in e['guest_cpus']),
               'original prior MAIN fourCPU declaration')
    else:
        C.need(len(e['guest_cpus'])==3 and CPU3_registry_ref is not None and authority_ref is not None,
               'only explicit registered threeCPU identity; unsupported CPU counts rejected')
        reg=registry(CPU3_registry_ref,authority_ref=authority_ref);actual=C.ref(C.checked(reference))
        matches=[row for row in reg['entries']if row['owned_ref']==actual]
        C.need(len(matches)==1 and matches[0]['cid']==e['cid']and C.ref(C.checked(e['source']))==matches[0]['source_ref'],
               'exact full OWNED/source/CID must be explicitly registered for CPU3')
    C.checked(e['source'])
    C.need(re.fullmatch('[0-9a-f]{64}',e.get('host_sha256',''))is not None,'exact original ownership controller SHA')
    create=C.obj(e['create_receipt'])
    C.need(create['exit_code']==0 and create['stdout'].strip()==e['cid']
           and create['requested_argv'][:2]==[DOCKER,'create'],'original successful actual creation receipt reopens same CID')
    create_owner(e)
    return e


def create_owner(e):
    create=C.obj(e['create_receipt']);argv=create['requested_argv']
    C.need(type(argv)is list and all(type(x)is str for x in argv),'original complete creation argv')
    labels={};names=[]
    for n,token in enumerate(argv):
        if token=='--name':
            C.need(n+1<len(argv),'original create name value');names.append(argv[n+1])
        if token=='--label':
            C.need(n+1<len(argv)and '='in argv[n+1],'original separate complete label value')
            k,v=argv[n+1].split('=',1);C.need(k not in labels and k and v,'unique nonempty original create labels');labels[k]=v
        C.need(not token.startswith('--label=')and not token.startswith('--name='),'exact original separate label/name argv')
    want={'model-tuning-lab.run':e['name'],'model-tuning-lab.arm':e['arm'],
          'model-tuning-lab.source-manifest-sha256':e['source']['sha256'],'model-tuning-lab.controller-sha256':e['host_sha256']}
    C.need(names==[e['name']]and argv.count(e['image'])==1
           and all(labels.get(k)==v for k,v in want.items())and labels.get('model-tuning-lab.owner'),
           'same immutable create receipt joins exact name/image/source/controller/arm and unique owner')
    return labels['model-tuning-lab.owner']


def readset(reference,*,authority_ref=None):
    p=policy(reference,authority_ref=authority_ref);refs=[reference,p['authority_ref'],p['CPU3_registry_ref']]
    refs.extend(u['controller_ref']for u in p['units'])
    for r in p['owned_refs']:
        e=owned_identity(r,CPU3_registry_ref=p['CPU3_registry_ref'],authority_ref=p['authority_ref']);refs.extend((r,e['source'],e['create_receipt']))
    return list({r['path']:C.ref(C.checked(r))for r in refs}.values())


def unit_state(text,unit):
    C.need(type(text)is str and len(text.encode())<=2**20,'bounded actual systemctl show result')
    rows={}
    for line in text.splitlines():
        C.need('='in line,'complete key/value systemctl show')
        k,v=line.split('=',1);C.need(k in PROPERTIES and k not in rows,'only unique requested unit properties');rows[k]=v
    C.need(set(rows)==set(PROPERTIES)and rows['Id']==unit,'exact actual unit identity/properties')
    inactive=(rows['ActiveState']in{'inactive','failed'}and rows['SubState']in{'dead','failed'})
    exited=(rows['ActiveState']=='active'and rows['SubState']=='exited'and rows['RemainAfterExit']=='yes')
    absent_tasks=rows['TasksCurrent']in{'[not set]','18446744073709551615','infinity',''}and not rows['ControlGroup']
    C.need(rows['LoadState']in{'loaded','not-found'}and(inactive or exited)
           and rows['MainPID']=='0'and rows['ControlPID']=='0'and rows['Job']in{'','0'}
           and(rows['TasksCurrent']=='0'or absent_tasks),
           'known MAIN NPU controller exited/inactive with no main/control/job/task lifecycle')
    if rows['LoadState']=='not-found':C.need(rows['ActiveState']=='inactive'and rows['SubState']=='dead','collected absent unit has no active lifecycle')
    return rows


def stopped_owned(rows,e):
    C.need(type(rows)is list and len(rows)==1,'one actual explicit full-CID inspect')
    x=rows[0];cfg=x['Config'];h=x['HostConfig'];s=x['State'];labels=cfg.get('Labels')or{}
    want={'model-tuning-lab.owner':create_owner(e),'model-tuning-lab.run':e['name'],'model-tuning-lab.arm':e['arm'],
          'model-tuning-lab.source-manifest-sha256':e['source']['sha256'],'model-tuning-lab.controller-sha256':e['host_sha256']}
    C.need(x['Id']==e['cid']and x['Name']=='/'+e['name']and x['Image']==cfg['Image']==e['image']
           and all(labels.get(k)==v for k,v in want.items()),'exact actual MAIN owned CID/image/name/source/controller labels')
    C.need(s['Running']is False and s['Pid']==0 and s.get('Restarting',False)is False and not x.get('ExecIDs')
           and h['RestartPolicy']['Name']=='no','MAIN owned model init and all exec lifecycles stopped; no auto restart')
    return dict(cid=e['cid'],name=e['name'],image=e['image'],source=e['source'],host_sha256=e['host_sha256'],
                State=s,ExecIDs=x.get('ExecIDs'),restart_policy=h['RestartPolicy'])


def observe(ctl,original_observation,reference):
    # Caller has ALREADY executed unmodified original025 actual NPU/resource guard.
    v=policy(reference);original=C.obj(original_observation)
    units=[];containers=[]
    for n,u in enumerate(v['units']):
        argv=[SYSTEMCTL,'show','--no-pager',*[('--property='+k)for k in PROPERTIES],u['unit']]
        raw,r=ctl.call('MAIN-unit-'+str(n),argv,cap=10)
        units.append(dict(unit=u['unit'],controller_ref=u['controller_ref'],receipt_ref=r,
                          actual=unit_state(raw['stdout'],u['unit'])))
    for n,r in enumerate(v['owned_refs']):
        e=owned_identity(r,CPU3_registry_ref=v['CPU3_registry_ref'],authority_ref=v['authority_ref']);raw,ir=ctl.call('MAIN-owned-'+str(n),[DOCKER,'inspect',e['cid']],cap=10)
        containers.append(dict(owned_ref=r,inspect_ref=ir,actual=stopped_owned(json.loads(raw['stdout']),e)))
    out=C.write(ctl.out/('MAIN-QUIESCENCE-'+str(time.time_ns())+'.json'),dict(
        schema='bole.actual-MAIN-NPU-quiescence-observation/v2',policy_ref=reference,CPU3_registry_ref=v['CPU3_registry_ref'],
        original025_observation_ref=original_observation,units=units,containers=containers,
        foreign_static_device_declarations=original['declared_only_containers'],
        declaration_is_actual_compute_evidence=False,known_MAIN_lifecycles_quiescent=True,
        serial_schedule_declaration=v['serial_schedule'],external_lock_verified_by_this_reader=False,
        original_actual_resource_guards_executed=True,NPU_dispatch=False))
    if not hasattr(ctl,'_main_quiescence_observations'):ctl._main_quiescence_observations=[]
    ctl._main_quiescence_observations.append(out)
    return out
