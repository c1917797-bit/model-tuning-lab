"""Owned Devices[] every-frame independent consumer. Default OFF.

Successful raw frames are not replayable after their durable audited ACK and
release. Failed or unacknowledged raw frames are retained by the sender.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))


STEP_GATES=dict(layers=64,GDN=48,FA=16,all_three_rows=True,original112_bounds=True,
    original_conv_bounds=True,original_FA_bounds=True,selected_state=True,
    whole_actual_arenas=True,previous_postimage_join=True,genuine_native_MTP=True,
    all4_native_vocabulary=True)


def main():
    p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
    p.add_argument('--source-ref');p.add_argument('--channel-ref');p.add_argument('--bootstrap',action='store_true');a=p.parse_args()
    if not a.execute:print('{"enabled":false,"NPU":false}');return 0
    import sourceio as C,g2_contract as G2,g2_channel as CH
    sr=json.loads(a.source_ref);m=C.obj(sr)
    C.need(os.environ.get(G2.FLAG)=='1'and m['service_experiment']==G2.SCOPE and
        C.ref(__file__)==m['stream_consumer_source']==m['files']['g2_consumer.py'],
        'explicit exact independently reviewed G2 consumer/scope')
    C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='' and
        os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and
        not list(Path('/dev').glob('davinci[0-9]*')),'actual Devices[] CPU consumer before Torch import')
    for r in (*m['files'].values(),*m['runtime_sources'].values()):C.checked(r)
    import identity_capture
    root=Path(m['stream_channel_root'])
    if a.bootstrap:
        C.need(a.channel_ref is None,'host binds actual consumer lifetime after BOOT, not caller-selected ref')
        CH.write(root/'STREAM_CONSUMER_BOOT.json',dict(schema='bole.actual-stream-consumer-BOOT/v2',
            source=sr,identity=identity_capture.process_identity(),
            argv=[v.decode()for v in Path('/proc/self/cmdline').read_bytes().split(b'\0')if v],
            Devices=[],Torch_imported=False,source_before=dict(m['files'])))
        deadline=time.monotonic()+G2.BOOT_TIMEOUT_SECONDS
        path=Path(m['stream_channel_contract_path'])
        while not path.is_file():
            C.need(time.monotonic()<deadline,'bounded actual host ownership/channel bind')
            time.sleep(G2.POLL_SECONDS)
        cr=C.ref(path)
    else:cr=json.loads(a.channel_ref)
    channel=CH.contract(C,sr,cr)
    C.need(C.ref(identity_capture.__file__)==m['files']['identity_capture.py'] and
        identity_capture.process_identity()==channel['actual_consumer_identity'],
        'same independently owned actual consumer PID/start/cgroup')
    import torch as t
    import g2_state,g2_reports
    C.need(C.ref(g2_state.__file__)==m['files']['g2_state.py'],'exact independent stateful numeric consumer')
    consumer=g2_state.Consumer(t,C,sr,m,channel)
    sequence=0;previous=[None]*4;primary=None;acks=[];start=time.monotonic()
    try:
        while not consumer.closed:
            deadline=time.monotonic()+G2.ACK_TIMEOUT_SECONDS
            paths=[root/('FRAME-RANK-%d-%06d.json'%(rank,sequence))for rank in range(4)]
            while not all(path.is_file()for path in paths):
                C.need(time.monotonic()<deadline,'bounded complete TP4 frame arrival')
                time.sleep(G2.POLL_SECONDS)
            manifests=[CH.load(CH.ref(path))for path in paths]
            kind=manifests[0]['kind']
            C.need(all(v['schema']=='bole.actual-stream-frame/v2'and v['source']==sr and
                v['channel_ref']==cr and v['nonce']==channel['nonce']and v['rank']==rank and
                v['sequence']==sequence and v['kind']==kind and v['previous_ack']==previous[rank] and
                v['raw']['path']==str(root/('FRAME-RANK-%d-%06d.pt'%(rank,sequence)))and
                v['raw']['bytes']<=G2.FRAME_WIRE_CAP and
                v['logical_tensor_bytes']<=G2.FRAME_LOGICAL_CAP
                for rank,v in enumerate(manifests)),'all4 exact bounded source/channel/hash/ordinal chains')
            for r in (*m['files'].values(),*m['runtime_sources'].values()):C.checked(r)
            values=[]
            for v in manifests:
                exported=t.load(CH.checked(v['raw']),map_location='cpu',weights_only=False)
                C.need(exported['schema']=='bole.model-diagnostic-primitives/v1'and
                    exported['logical_tensor_bytes']==v['logical_tensor_bytes']==
                    g2_state.tensor_bytes(t,exported['payload']),
                    'independent complete logical frame charge, repeated tensors included')
                values.append(exported['payload'])
            for rank,v in enumerate(manifests):
                C.need(v['coverage']==consumer.coverage(kind,values[rank]),'source-bound coverage recomputed from complete actual frame')
            reports=None;error=None
            try:
                reports=consumer.consume_batch(kind,values)
            except BaseException as e:error=e
            for rank,v in enumerate(manifests):
                report=reports[rank]if reports is not None else dict(primary=repr(error))
                report_ref=CH.write(root/('REPORT-RANK-%d-%06d.json'%(rank,sequence)),
                    g2_reports.summarize(sr,v,report,error))
                digest=report_ref['sha256']
                ack=dict(schema='bole.actual-independent-frame-ACK/v2',source=sr,
                    consumer_source=m['stream_consumer_source'],channel_ref=cr,nonce=channel['nonce'],
                    rank=rank,sequence=sequence,kind=kind,raw=v['raw'],
                    logical_tensor_bytes=v['logical_tensor_bytes'],previous_ack=previous[rank],
                    complete_frame_consumed=error is None,passed=error is None,
                    coverage=v['coverage'],oracle_report_sha256=digest,oracle_report=report_ref,
                    gates=STEP_GATES if kind=='step'and error is None else dict(kind=kind),
                    consumer_identity=channel['actual_consumer_identity'],
                    model_ready=False,formal_success=False)
                C.need(len((json.dumps(ack,sort_keys=True)+'\n').encode())<=3072,'bounded complete per-frame oracle ACK')
                ar=CH.write(root/('ACK-RANK-%d-%06d.json'%(rank,sequence)),ack)
                previous[rank]=ar;acks.append(ar)
            if error is not None:raise error
            values.clear();sequence+=1
    except BaseException as e:primary=repr(e);trace=traceback.format_exc()
    else:trace=None
    after=True
    try:
        for r in (*m['files'].values(),*m['runtime_sources'].values()):C.checked(r)
    except BaseException as e:after=False;primary=primary or repr(e)
    value=dict(schema='bole.actual-stream-consumer-exit/v2',source=sr,consumer_source=m['stream_consumer_source'],
        channel_ref=cr,identity=channel['actual_consumer_identity'],primary=primary,traceback=trace,
        completed=consumer.closed and primary is None,source_unchanged=after,
        actual_frame_batches=sequence,requests=consumer.completed,ACKs=acks,
        elapsed=time.monotonic()-start,successful_raw_replay_available=False,
        timing_is_formal=False,model_ready=False,task_ready=False,performance_ready=False,formal_success=False)
    CH.write(root/'STREAM_CONSUMER_EXIT.json',value)
    return 3 if primary is not None else 0


if __name__=='__main__':raise SystemExit(main())
