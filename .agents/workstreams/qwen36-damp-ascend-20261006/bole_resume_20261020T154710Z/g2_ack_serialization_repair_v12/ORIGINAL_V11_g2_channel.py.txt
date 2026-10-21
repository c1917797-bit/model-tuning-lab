"""Owned file channel: retain every unacknowledged/failed raw frame.

Only an exact source-bound independent consumer ACK permits successful-frame
release. This protocol deliberately cannot replay released successful raw data.
The host must create/audit the shared leaf and independent Devices[] consumer.
"""
import hashlib
import json
import os
from pathlib import Path
import time
import g2_contract as G2


def need(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path)
    h = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while block := stream.read(2**20):
            size += len(block)
            h.update(block)
    return dict(path=str(path), bytes=size, sha256=h.hexdigest())


def checked(reference):
    need(ref(reference['path'])==reference, 'exact actual frame/ACK Ref3')
    return Path(reference['path'])


def load(reference):
    return json.loads(checked(reference).read_bytes())


def write(path, value):
    data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
    temporary=path.with_suffix(path.suffix+'.pending')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    need(not path.exists(), 'exclusive actual channel event')
    os.rename(temporary,path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return ref(path)


def contract(C, source_ref, reference):
    m=C.obj(source_ref);v=C.obj(reference)
    need(v['schema']=='bole.owned-independent-stream-channel/v2' and
         v['source']==source_ref and v['scope']==G2.SCOPE and
         v['consumer_source']==m['stream_consumer_source'] and
         v['consumer_Devices']==[] and v['consumer_container_independent'] is True and
         v['host_ownership_audited'] is True and
         len(v['actual_worker_identities'])==4 and
         len({x['pid'] for x in v['actual_worker_identities']})==4,
         'actual independently owned Devices[] consumer and distinct bound worker lifetimes')
    for r in (v['consumer_source'],v['consumer_owner_ref'],v['model_owner_ref']):C.checked(r)
    from g2_handoff import verify as verify_metadata
    verify_metadata(C,source_ref,v)
    root=Path(v['root'])
    need(root.is_absolute() and root.is_dir() and not any(p.is_symlink()for p in(root,*root.parents)) and
         str(root)==m['stream_channel_root'] and type(v['nonce'])is str and len(v['nonce'])==64,
         'exact precreated owned channel leaf and fresh host capability')
    need(v['limits']==dict(raw_cap=G2.RAW_CAP,metadata_cap=G2.METADATA_CAP,
         frame_logical_cap=G2.FRAME_LOGICAL_CAP,frame_wire_cap=G2.FRAME_WIRE_CAP,
         checkpoint_cap=G2.CHECKPOINT_CAP), 'source-frozen bounded stream resources')
    return v


def validate_ack(ack, manifest, *, consumer_source, channel_ref, previous_ack):
    need(ack['schema']=='bole.actual-independent-frame-ACK/v2' and
         ack['source']==manifest['source'] and ack['consumer_source']==consumer_source and
         ack['channel_ref']==channel_ref and ack['nonce']==manifest['nonce'] and
         ack['rank']==manifest['rank'] and ack['sequence']==manifest['sequence'] and
         ack['kind']==manifest['kind'] and ack['raw']==manifest['raw'] and
         ack['logical_tensor_bytes']==manifest['logical_tensor_bytes'] and
         ack['previous_ack']==previous_ack and
         ack['complete_frame_consumed'] is True and ack['passed'] is True and
         ack['model_ready'] is False and ack['formal_success'] is False,
         'exact successful complete-frame independent ACK before release/progression')
    need(type(ack['oracle_report_sha256'])is str and len(ack['oracle_report_sha256'])==64 and
         ack['coverage']==manifest['coverage'] and
         ack['oracle_report']['sha256']==ack['oracle_report_sha256'] and
         ack['oracle_report']['bytes']<=G2.REPORT_CAP, 'actual source-bound oracle report hash and exact coverage')
    report=load(ack['oracle_report'])
    need(report['source']==manifest['source'] and report['raw']==manifest['raw'] and
         report['coverage']==manifest['coverage'] and report['passed'] is True,
         'actual durable source-bound independent oracle report')
    if manifest['kind']=='step':
        need(ack['gates']==dict(layers=64,GDN=48,FA=16,all_three_rows=True,
             original112_bounds=True,original_conv_bounds=True,original_FA_bounds=True,
             selected_state=True,whole_actual_arenas=True,previous_postimage_join=True,
             genuine_native_MTP=True,all4_native_vocabulary=True),
             'every actual target step independently consumed with original bounds')
    return True


class Sender:
    def __init__(self,C,source_ref,channel_ref,rank,identity):
        self.C=C;self.source=source_ref;self.channel_ref=channel_ref
        self.value=contract(C,source_ref,channel_ref);self.rank=rank
        need(type(rank)is int and rank in range(4) and
             self.value['actual_worker_identities'][rank]==identity,
             'same actual rank worker PID/start/cgroup as owned channel')
        self.root=Path(self.value['root']);self.sequence=0;self.previous_ack=None
        self.events=[];self.active=None

    def metadata_bytes(self):
        m=self.C.obj(self.source);base=Path(m['model_receipt_root'])
        paths=set(self.root.glob('*RANK-%d-*.json'%self.rank))
        paths.update(self.root.glob('*RANK-%d.json'%self.rank))
        paths.update(p for p in self.root.glob('*.json')if 'RANK-'not in p.name)
        paths.update(base.glob('*RANK-%d.json'%self.rank))
        paths.update(base.glob('IDENTITY-rank%d-*.json'%self.rank))
        cal=base/('CONV-MODEL-CALIBRATION-RANK-%d'%self.rank)
        if cal.is_dir():paths.update(cal.iterdir())
        return sum(p.stat().st_size for p in paths if p.is_file())

    def send(self,t,payload,*,kind,coverage):
        need(self.active is None and kind in('open','step','retire','close'),
             'one actual frame in flight per rank')
        need(payload['logical_tensor_bytes']<=G2.FRAME_LOGICAL_CAP,
             'complete frame bounded before actual serialization')
        n=self.sequence;stem='RANK-%d-%06d'%(self.rank,n)
        raw=self.root/('FRAME-'+stem+'.pt')
        fd=os.open(raw,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb')as stream:
            t.save(payload,stream);stream.flush();os.fsync(stream.fileno())
        self.active=raw
        rr=ref(raw)
        need(rr['bytes']<=G2.FRAME_WIRE_CAP and rr['bytes']+payload['logical_tensor_bytes']+self.metadata_bytes()<=G2.RAW_CAP,
             'one actual serialized frame plus all retained rank evidence under1GiB')
        manifest=dict(schema='bole.actual-stream-frame/v2',source=self.source,
            channel_ref=self.channel_ref,nonce=self.value['nonce'],rank=self.rank,
            sequence=n,kind=kind,coverage=coverage,raw=rr,
            logical_tensor_bytes=payload['logical_tensor_bytes'],previous_ack=self.previous_ack,
            successful_raw_replay_available=False)
        need(len((json.dumps(manifest,sort_keys=True)+'\n').encode())<=2048,'bounded complete frame manifest')
        need(self.metadata_bytes()+8192<=G2.METADATA_CAP,'all retained calibration/metadata/journal budget before frame publication')
        mr=write(self.root/('FRAME-'+stem+'.json'),manifest)
        path=self.root/('ACK-'+stem+'.json');deadline=time.monotonic()+G2.ACK_TIMEOUT_SECONDS
        while not path.exists():
            need(time.monotonic()<deadline,'bounded independent CPU ACK timeout; full raw retained')
            time.sleep(G2.POLL_SECONDS)
        ar=ref(path);ack=load(ar)
        validate_ack(ack,manifest,consumer_source=self.value['consumer_source'],
            channel_ref=self.channel_ref,previous_ack=self.previous_ack)
        checked(rr)
        need(self.metadata_bytes()+8192<=G2.METADATA_CAP,'all retained rank metadata within64MiB')
        # ACK is durable first; failures before this exact point retain the raw.
        raw.unlink()
        release=write(self.root/('RELEASE-'+stem+'.json'),dict(
            schema='bole.actual-stream-frame-release/v2',source=self.source,rank=self.rank,
            sequence=n,manifest=mr,ack=ar,raw=rr,released_after_successful_ACK=True,
            successful_raw_replay_available=False))
        need(release['bytes']<=G2.RELEASE_CAP,'source-frozen retained release receipt cap')
        self.events.append(dict(sequence=n,kind=kind,coverage=coverage,manifest=mr,ack=ar,release=release))
        self.previous_ack=ar;self.sequence+=1;self.active=None
        return self.events[-1]

    def retain_failure(self,t,payload,coverage):
        if self.active is not None:
            return ref(self.active)
        need(payload['logical_tensor_bytes']<=G2.FRAME_LOGICAL_CAP,'bounded complete available failed frame')
        stem='RANK-%d-%06d'%(self.rank,self.sequence)
        raw=self.root/('FRAME-'+stem+'.pt')
        fd=os.open(raw,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb')as stream:t.save(payload,stream);stream.flush();os.fsync(stream.fileno())
        self.active=raw;rr=ref(raw)
        need(rr['bytes']<=G2.FRAME_WIRE_CAP and rr['bytes']+payload['logical_tensor_bytes']+self.metadata_bytes()<=G2.RAW_CAP,
             'complete failed logical plus serialized raw plus all retained evidence under original1GiB')
        write(self.root/('FRAME-'+stem+'.json'),dict(schema='bole.actual-stream-frame/v2',
            source=self.source,channel_ref=self.channel_ref,nonce=self.value['nonce'],rank=self.rank,
            sequence=self.sequence,kind='failure',coverage=coverage,raw=rr,
            logical_tensor_bytes=payload['logical_tensor_bytes'],previous_ack=self.previous_ack,
            successful_raw_replay_available=False,failed_available_raw_retained=True))
        return rr
