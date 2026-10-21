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


ACK_WIRE_SCHEMA='bole.actual-independent-frame-ACK-wire/v3'
ACK_FIELDS=('schema','source','consumer_source','channel_ref','nonce','rank','sequence','kind',
    'raw','logical_tensor_bytes','previous_ack','complete_frame_consumed','passed','coverage',
    'oracle_report_sha256','oracle_report','gates','consumer_identity','model_ready','formal_success')
ACK_REF_FIELDS=('source','consumer_source','channel_ref','raw','previous_ack','oracle_report')


def _ack_ref(value):
    need(type(value)is dict and set(value)=={'path','bytes','sha256'}and
         type(value['path'])is str and Path(value['path']).is_absolute()and
         type(value['bytes'])is int and value['bytes']>=0 and
         type(value['sha256'])is str and len(value['sha256'])==64 and
         all(c in '0123456789abcdef'for c in value['sha256']),
         'whole typed original ACK Ref3, no shortened hash or unknown key')
    return [value['path'],value['bytes'],value['sha256']]


def _ack_types(value):
    integer=lambda v: type(v)is int and v>=0
    hexadecimal=lambda v: type(v)is str and len(v)==64 and all(c in '0123456789abcdef'for c in v)
    need(type(value['rank'])is int and 0<=value['rank']<4 and integer(value['sequence'])and
         value['sequence']<G2.SCOPE['request_count']*(G2.SCOPE['max_steps_per_request']+2)+1,
         'actual bounded rank/sequence integers, never bool-as-int')
    need(type(value['kind'])is str and value['kind']in('open','step','retire','close','failure')and
         hexadecimal(value['nonce'])and hexadecimal(value['oracle_report_sha256'])and
         integer(value['logical_tensor_bytes'])and value['logical_tensor_bytes']<=G2.FRAME_LOGICAL_CAP,
         'original typed kind/nonce/oracle hash/logical frame count')
    need(all(type(value[k])is bool for k in('complete_frame_consumed','passed','model_ready','formal_success')),
         'actual ACK booleans, never truth-valued integers')
    identity=value['consumer_identity']
    need(type(identity)is dict and set(identity)=={'pid','start_ticks','cgroup'}and
         type(identity['pid'])is int and identity['pid']>0 and integer(identity['start_ticks'])and
         type(identity['cgroup'])is str and bool(identity['cgroup']),
         'full original typed PID/start/cgroup identity retained')
    cov=value['coverage'];kind=value['kind']
    need(type(cov)is dict,'complete original coverage object')
    keys={'open':{'generation','request'},'step':{'generation','request','ordinal','length','emitted_tokens','processed_nodes'},
          'retire':{'generation','request','steps','output_tokens'},'close':{'request_count','output_budget'}}
    if kind in keys:
        need(set(cov)==keys[kind],'complete original coverage fields, no dropped/extra coverage')
    if kind in('open','step','retire'):
        need(type(cov['generation'])is int and 1<=cov['generation']<=G2.SCOPE['request_count']and
             type(cov['request'])is str and bool(cov['request']),'actual request/generation types')
    if kind=='step':
        need(integer(cov['ordinal'])and cov['ordinal']<G2.SCOPE['max_steps_per_request']and
             integer(cov['length'])and
             type(cov['emitted_tokens'])is list and 1<=len(cov['emitted_tokens'])<=2 and
             all(integer(v)and v<248320 for v in cov['emitted_tokens'])and
             type(cov['processed_nodes'])is list and 1<=len(cov['processed_nodes'])<=2 and
             all(integer(v)and v<3 for v in cov['processed_nodes']),
             'full typed step coverage and token/node integers, no bool-as-int')
    if kind=='retire':need(integer(cov['steps'])and integer(cov['output_tokens']),'typed full retirement coverage')
    if kind=='close':need(integer(cov['request_count'])and integer(cov['output_budget']),'typed full close coverage')
    gates=value['gates']
    if kind=='step'and value['passed']:
        integers={'layers','GDN','FA'}
        booleans={'all_three_rows','original112_bounds','original_conv_bounds','original_FA_bounds',
                  'selected_state','whole_actual_arenas','previous_postimage_join','genuine_native_MTP','all4_native_vocabulary'}
        need(type(gates)is dict and set(gates)==integers|booleans and
             all(integer(gates[k])for k in integers)and all(type(gates[k])is bool for k in booleans),
             'every original typed STEP gate retained before unchanged validator')
    else:need(type(gates)is dict and gates==dict(kind=kind),'full original nonstep/failure gate')


def _ack_wire(value):
    need(type(value)is dict and set(value)==set(ACK_FIELDS)and
         value['schema']=='bole.actual-independent-frame-ACK/v2',
         'all twenty original semantic ACK fields retained, none missing or extra')
    _ack_types(value)
    values=[]
    for key in ACK_FIELDS:
        v=value[key]
        if key in ACK_REF_FIELDS:
            v=None if key=='previous_ack'and v is None else _ack_ref(v)
        values.append(v)
    return dict(schema=ACK_WIRE_SCHEMA,values=values)


def ack_bytes(value):
    data=(json.dumps(_ack_wire(value),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    need(len(data)<=3072,'bounded complete per-frame oracle ACK wire; original3072 unchanged')
    return data


def decode_ack(data):
    need(type(data)is bytes and len(data)<=3072,'actual ACK wire within original3072 before decode')
    def pairs(rows):
        value={}
        for key,item in rows:
            need(key not in value,'unique ACK wire JSON keys');value[key]=item
        return value
    wire=json.loads(data,object_pairs_hook=pairs,
        parse_constant=lambda s:(_ for _ in()).throw(ValueError('finite ACK JSON '+s)))
    need(type(wire)is dict and set(wire)=={'schema','values'}and
         wire['schema']==ACK_WIRE_SCHEMA and type(wire['values'])is list and
         len(wire['values'])==len(ACK_FIELDS),'exact source-owned v3 wire mapping and all original field positions')
    value=dict(zip(ACK_FIELDS,wire['values']))
    for key in ACK_REF_FIELDS:
        v=value[key]
        if key=='previous_ack'and v is None:continue
        need(type(v)is list and len(v)==3,'full original ACK Ref3 positional triple')
        value[key]=dict(path=v[0],bytes=v[1],sha256=v[2]);_ack_ref(value[key])
    need(ack_bytes(value)==data,'canonical lossless complete ACK wire, no ambiguous/hidden bytes')
    return value


def load(reference):
    data=checked(reference).read_bytes();value=json.loads(data)
    need(not(type(value)is dict and value.get('schema')=='bole.actual-independent-frame-ACK/v2'),
         'this source requires explicit canonical v3 ACK wire; no legacy size-cap bypass')
    return decode_ack(data)if type(value)is dict and value.get('schema')==ACK_WIRE_SCHEMA else value


def write(path, value):
    data=ack_bytes(value)if type(value)is dict and value.get('schema')=='bole.actual-independent-frame-ACK/v2'else(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
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
        import g3_budget
        C=self.C;m=C.obj(self.source)
        return g3_budget.actual(C,m,self.rank)['bytes']

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
        need(rr['bytes']<=G2.FRAME_WIRE_CAP and rr['bytes']+payload['logical_tensor_bytes']+G2.CHECKPOINT_CAP+self.metadata_bytes()<=G2.RAW_CAP,
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
        need(rr['bytes']<=G2.FRAME_WIRE_CAP and rr['bytes']+payload['logical_tensor_bytes']+G2.CHECKPOINT_CAP+self.metadata_bytes()<=G2.RAW_CAP,
             'complete failed logical plus serialized raw plus all retained evidence under original1GiB')
        write(self.root/('FRAME-'+stem+'.json'),dict(schema='bole.actual-stream-frame/v2',
            source=self.source,channel_ref=self.channel_ref,nonce=self.value['nonce'],rank=self.rank,
            sequence=self.sequence,kind='failure',coverage=coverage,raw=rr,
            logical_tensor_bytes=payload['logical_tensor_bytes'],previous_ack=self.previous_ack,
            successful_raw_replay_available=False,failed_available_raw_retained=True))
        return rr
