"""Read-only explicit MAIN lifecycle checks; foreign declarations stay metadata.
No discovery, stop, signal, lock acquisition, model import or device operation.
"""
import json
from pathlib import Path
import re
import time
import owner_common as C

SCHEMA='bole.MAIN-NPU-quiescence-policy/v1'
OWNER='adakv-all-request-tp4-model-once-v1'
SYSTEMCTL='/usr/bin/systemctl'
DOCKER='/usr/bin/docker'
PROPERTIES=('Id','LoadState','ActiveState','SubState','MainPID','ControlPID','Job','ControlGroup','ExecStart','FragmentPath','RemainAfterExit','TasksCurrent')


def policy(reference,*,authority_ref=None):
    v=C.obj(reference)
    C.need(type(v)is dict and set(v)=={'schema','authority_ref','declared_complete_MAIN_NPU_inventory','units','owned_refs','serial_schedule'}
           and v['schema']==SCHEMA and v['declared_complete_MAIN_NPU_inventory']is True,'explicit complete MAIN-only lifecycle inventory')
    C.checked(v['authority_ref'])
    if authority_ref is not None:C.need(v['authority_ref']==authority_ref,'same new CPU authority')
    units=v['units'];owned=v['owned_refs'];s=v['serial_schedule']
    C.need(type(units)is list and 1<=len(units)<=64 and type(owned)is list and 1<=len(owned)<=64,'bounded nonempty known MAIN controller/container inventory')
    names=[]
    for u in units:
        C.need(type(u)is dict and set(u)=={'unit','controller_ref'}and type(u['unit'])is str
               and re.fullmatch(r'bole-[A-Za-z0-9_.@:-]+\.service',u['unit']),'explicit exact MAIN NPU unit; no wildcard/foreign inventory')
        names.append(u['unit']);C.checked(u['controller_ref'])
    C.need(len(set(names))==len(names),'no duplicate unit')
    cids=[]
    for r in owned:cids.append(owned_identity(r)['cid'])
    C.need(len(set(cids))==len(cids),'no duplicate MAIN CID')
    C.need(type(s)is dict and set(s)=={'no_MAIN_NPU_start_during_CPU_owner','external_lock_path','external_lock_argv_prefix','lock_lifetime','lock_verification_owner'}
           and s['no_MAIN_NPU_start_during_CPU_owner']is True and s['lock_lifetime']=='entire-owner'
           and s['lock_verification_owner']=='MAIN-submitter','MAIN serial scheduling and external lifetime lock declaration')
    lock=Path(s['external_lock_path'])
    C.need(lock.is_absolute()and lock.name=='MAIN_ADMISSION.lock'and '..'not in lock.parts
           and not any(p.is_symlink()for p in(lock,*lock.parents)),'ordinary explicit MAIN shared lock path')
    C.need(s['external_lock_argv_prefix']==['/usr/bin/flock','--nonblock','--no-fork',str(lock)],'exact external nonblocking whole-owner lock prefix')
    return v


def owned_identity(reference):
    e=C.obj(reference)
    C.need(re.fullmatch('[0-9a-f]{64}',e.get('cid',''))is not None and e.get('image')==C.IMAGE
           and type(e.get('name'))is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}',e['name'])
           and type(e.get('arm'))is str and e['arm']!='cpu-preflight'
           and type(e.get('guest_cpus'))is list and len(e['guest_cpus'])==4
           and len(set(e['guest_cpus']))==4 and all(type(n)is int and n>=0 for n in e['guest_cpus']),
           'actual prior full-CID same-image MAIN fourCPU model OWNED receipt')
    C.checked(e['source'])
    C.need(re.fullmatch('[0-9a-f]{64}',e.get('host_sha256',''))is not None,'exact original ownership controller SHA')
    create=C.obj(e['create_receipt'])
    C.need(create['exit_code']==0 and create['stdout'].strip()==e['cid']
           and create['requested_argv'][:2]==[DOCKER,'create'],'original successful actual creation receipt reopens same CID')
    return e


def readset(reference,*,authority_ref=None):
    p=policy(reference,authority_ref=authority_ref);refs=[reference,p['authority_ref']]
    refs.extend(u['controller_ref']for u in p['units'])
    for r in p['owned_refs']:
        e=owned_identity(r);refs.extend((r,e['source'],e['create_receipt']))
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
    want={'model-tuning-lab.owner':OWNER,'model-tuning-lab.run':e['name'],'model-tuning-lab.arm':e['arm'],
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
        e=owned_identity(r);raw,ir=ctl.call('MAIN-owned-'+str(n),[DOCKER,'inspect',e['cid']],cap=10)
        containers.append(dict(owned_ref=r,inspect_ref=ir,actual=stopped_owned(json.loads(raw['stdout']),e)))
    out=C.write(ctl.out/('MAIN-QUIESCENCE-'+str(time.time_ns())+'.json'),dict(
        schema='bole.actual-MAIN-NPU-quiescence-observation/v1',policy_ref=reference,
        original025_observation_ref=original_observation,units=units,containers=containers,
        foreign_static_device_declarations=original['declared_only_containers'],
        declaration_is_actual_compute_evidence=False,known_MAIN_lifecycles_quiescent=True,
        serial_schedule_declaration=v['serial_schedule'],external_lock_verified_by_this_reader=False,
        original_actual_resource_guards_executed=True,NPU_dispatch=False))
    if not hasattr(ctl,'_main_quiescence_observations'):ctl._main_quiescence_observations=[]
    ctl._main_quiescence_observations.append(out)
    return out
