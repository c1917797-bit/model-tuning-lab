"""Bind already-admitted model/Devices[] controllers before the G2 HTTP client.

Creation, source/window/resource admission and cleanup remain in MAIN's exact
025 controller. This function never creates/stops a container or signals PIDs.
"""
import inspect
import json
from pathlib import Path
import secrets
import g2_contract as G2
import g2_channel as CH


def bind(C,c,S,*,source_ref,model_ctl,cpu_ctl,worker_rows,worker_bindings,
         model_owner_ref,consumer_owner_ref):
    m=C.obj(source_ref)
    C.need(C.ref(__file__)==m['files']['g2_stream_owner.py']and
        m['service_experiment']==G2.SCOPE,'exact new stream owner/scope')
    import identity_owner
    C.need(C.ref(identity_owner.__file__)==m['files']['identity_owner.py'],
           'unchanged actual namespace/executable lifetime verifier')
    model,mi=model_ctl.inspect();cpu,ci=cpu_ctl.inspect()
    C.need(model['Id']==model_ctl.cid and cpu['Id']==cpu_ctl.cid and model_ctl.cid!=cpu_ctl.cid and
        model['State']['Running']and cpu['State']['Running']and
        cpu['HostConfig']['Devices']in(None,[])and cpu['HostConfig']['CpusetCpus']=='145',
        'distinct actual live model and Devices[] CPU145 containers')
    model_view=S.H.cpu_view(model['State']['Pid'])
    C.need(model_view['effective_capacity']==3 and model_view['effective_cpus']==[0,1,2],
           'actual untimed model3 cgroup for all four TP ranks, original reserve2 retained')
    worker_cpu_views=[S.H.cpu_view(b['host']['pid'])for b in worker_bindings]
    C.need(all(v['effective_capacity']<=3 and set(v['effective_cpus'])<= {0,1,2}for v in worker_cpu_views),
           'all4 actual NPU workers remain in exact model3 CPU boundary')
    view=S.H.cpu_view(cpu['State']['Pid'])
    C.need(view['effective_capacity']==1 and view['effective_cpus']==[145],
           'actual effective independent CPU145 cgroup capacity')
    actual_mounts={x['Destination']:(x['Source'],x['RW'])for x in cpu['Mounts']}
    C.need(actual_mounts==cpu_ctl.expected['mounts']and
           actual_mounts[str(Path(m['root']))]==(m['root'],False)and
           actual_mounts[m['stream_channel_root']]==(m['stream_channel_root'],True)and
           actual_mounts[m['model_receipt_root']]==(m['model_receipt_root'],False),
           'complete exact CPU source/channel/calibration mount read/write closure')
    C.need(len(worker_rows)==len(worker_bindings)==4 and
        {x['host']['physical']for x in worker_bindings}=={4,5,6,7},
        'actual all4 original owned worker host/NSpid bindings')
    identities=[]
    for rank in range(4):
        wr=C.obj(C.ref(Path(m['stream_channel_root'])/('STREAM_WORKER_BOOT-RANK-%d.json'%rank)))
        C.need(wr['schema']=='bole.actual-stream-worker-BOOT/v2'and wr['source']==source_ref and
            wr['rank']==rank and wr['TP_world_size']==4 and wr['scope']==G2.SCOPE,
            'actual source-bound native TP4 rank BOOT, not filesystem order inference')
        identity=wr['identity']
        matches=[row for row in worker_rows if row['pid']==identity['pid']]
        C.need(len(matches)==1,'one actual owned source/namespace snapshot per native rank')
        row=matches[0];stat=row['proc_stat'];rest=stat[stat.rfind(')')+2:].split()
        C.need(identity==dict(pid=row['pid'],start_ticks=int(rest[19]),cgroup=row['cgroup'])and
            row['source_ref']==source_ref and row['allow_hf32']is False and
            sum(b['guest']==row for b in worker_bindings)==1,'actual source/precision worker lifetime join')
        identities.append(identity)
    boot_ref=C.ref(Path(m['stream_channel_root'])/'STREAM_CONSUMER_BOOT.json');boot=C.obj(boot_ref)
    C.need(boot['schema']=='bole.actual-stream-consumer-BOOT/v2'and boot['source']==source_ref and
        boot['Devices']==[]and boot['Torch_imported']is False and boot['source_before']==m['files'],
        'actual source-bound consumer BOOT before Torch/device/model construction')
    argv=boot['argv']
    C.need(argv[1:3]==['-I','-B']and argv[3]==str(Path(m['root'])/'g2_consumer.py')and
        set(argv[4:])>= {'--execute','--bootstrap','--source-ref'}and
        json.loads(argv[argv.index('--source-ref')+1])==source_ref,
        'actual exact-source independent consumer commandline')
    # This unchanged function performs a generic positive NSpid/PID/start/
    # cgroup/executable join. It grants no frontend or HTTP assignment authority.
    lifetime=identity_owner.frontend(c,S,cpu_ctl,dict(identity=boot['identity']))
    C.need(lifetime['guest']==boot['identity']and lifetime['owned_cid']==cpu_ctl.cid and
        lifetime['host']['argv']==argv,'same actual live CPU consumer namespace/executable/argv')
    for r in (model_owner_ref,consumer_owner_ref):C.checked(r)
    value=dict(schema='bole.owned-independent-stream-channel/v2',source=source_ref,scope=G2.SCOPE,
        consumer_source=m['stream_consumer_source'],root=m['stream_channel_root'],nonce=secrets.token_hex(32),
        consumer_Devices=[],consumer_container_independent=True,host_ownership_audited=True,
        actual_worker_identities=identities,actual_consumer_identity=boot['identity'],
        model_owner_ref=model_owner_ref,consumer_owner_ref=consumer_owner_ref,
        model_inspect=mi,consumer_inspect=ci,consumer_lifetime=lifetime,consumer_cpu_view=view,
        consumer_BOOT=boot_ref,model_cpu_view=model_view,worker_cpu_views=worker_cpu_views,limits=dict(raw_cap=G2.RAW_CAP,metadata_cap=G2.METADATA_CAP,
            frame_logical_cap=G2.FRAME_LOGICAL_CAP,frame_wire_cap=G2.FRAME_WIRE_CAP,
            checkpoint_cap=G2.CHECKPOINT_CAP))
    return C.write(Path(m['stream_channel_contract_path']),value)
