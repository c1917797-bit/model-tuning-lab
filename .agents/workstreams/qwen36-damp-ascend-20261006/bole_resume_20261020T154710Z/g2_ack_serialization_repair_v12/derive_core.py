from pathlib import Path
import hashlib
P=Path(__file__).resolve().parent
OLD=Path('/opt/host/vnf/austinov/bole-g2-stream-smoke4-20261020T154710Z-v11')
for n in ('g2_channel.py','g2_consumer.py','g2_finalize.py'):
 (P/('ORIGINAL_V11_'+n+'.txt')).write_bytes((OLD/n).read_bytes())
CODEC='''ACK_WIRE_SCHEMA='bole.actual-independent-frame-ACK-wire/v3'
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
    data=(json.dumps(_ack_wire(value),sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n').encode()
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


'''
LOAD_OLD="def load(reference):\n    return json.loads(checked(reference).read_bytes())"
LOAD_NEW="""def load(reference):
    data=checked(reference).read_bytes();value=json.loads(data)
    need(not(type(value)is dict and value.get('schema')=='bole.actual-independent-frame-ACK/v2'),
         'this source requires explicit canonical v3 ACK wire; no legacy size-cap bypass')
    return decode_ack(data)if type(value)is dict and value.get('schema')==ACK_WIRE_SCHEMA else value"""
WRITE_OLD="    data=(json.dumps(value,sort_keys=True,allow_nan=False)+'\\n').encode()"
WRITE_NEW="    data=ack_bytes(value)if type(value)is dict and value.get('schema')=='bole.actual-independent-frame-ACK/v2'else(json.dumps(value,sort_keys=True,allow_nan=False)+'\\n').encode()"
s=(OLD/'g2_channel.py').read_text();assert s.count(LOAD_OLD)==s.count(WRITE_OLD)==1
s=s.replace(LOAD_OLD,CODEC+LOAD_NEW,1).replace(WRITE_OLD,WRITE_NEW,1);(P/'g2_channel.py').write_text(s)
s=(OLD/'g2_consumer.py').read_text();before="len((json.dumps(ack,sort_keys=True)+'\\n').encode())<=3072";assert s.count(before)==1
(P/'g2_consumer.py').write_text(s.replace(before,'len(CH.ack_bytes(ack))<=3072',1))
s=(OLD/'g2_finalize.py').read_text();before="manifest=C.obj(event['manifest']);ack=C.obj(event['ack']);release=C.obj(event['release'])";assert s.count(before)==1
(P/'g2_finalize.py').write_text(s.replace(before,"manifest=C.obj(event['manifest']);ack=CH.load(event['ack']);release=C.obj(event['release'])",1))
for n in ('sourceio.py','g1_contract.py','g2_contract.py','g2_cold_clock.py'):(P/n).write_bytes((OLD/n).read_bytes())
expected={'g2_channel.py':(16728,'f52484f64a63f4dd679c554006adba580b0edec341e35e0bceae039c4ac2e1af'),'g2_consumer.py':(7492,'3d66905a331165de4182c4885065935aaecab3774f35969c88160e67db00dc71'),'g2_finalize.py':(17504,'8d8b3a9af2c069792a3d923af0a43ff6ba7b8e4effba5681a17cdfb2bbcccfda')}
for n,(size,digest)in expected.items():
 b=(P/n).read_bytes();assert len(b)==size and hashlib.sha256(b).hexdigest()==digest,n
print('core three exact local checked whole SHA reproduced on MAIN')
