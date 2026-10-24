"""Single source-profile disk ledger; no math or increased outer resources."""
from pathlib import Path
import copy,os
import input_resource_profile as P
MIB=2**20
CHECKPOINT=128*MIB
METADATA=64*MIB
ARGS=dict(input_tokens=32768,output_tokens=8,native_pages=264,conv_slot_bytes=56320,
 other_capture_bound=256*MIB,oracle_temporary_bound=256*MIB,serializer_temporary_bound=256*MIB)
def need(v,s):
 if not v:raise ValueError(s)
TEMPLATE_DISK_CAP=P.plan(**ARGS)['per_rank_disk_cap']
def template_disk_cap():return TEMPLATE_DISK_CAP
class _State:
 def __init__(self,c,profile):
  self.c=c;self.C=c['C'];self.m=c['m'];self.source=copy.deepcopy(c['source']);self.profile=copy.deepcopy(profile);self.pid=os.getpid()
def state(c):
 C,m=c['C'],c['m'];s=c.get('_profile_disk_state')
 if s is None:
  C.need(C.ref(__file__)==m['files']['disk_ledger.py']and C.ref(P.__file__)==m['files']['input_resource_profile.py'],'same source-owned disk ledger/profile')
  s=_State(c,P.validate(m['input_resource_profile32k']));c['_profile_disk_state']=s
 C.need(type(s)is _State and s.c is c and s.C is C and s.m is m and s.pid==os.getpid()and
        s.source==c['source']and s.profile==m['input_resource_profile32k'],'same process/context/source unchanged disk profile, not external cached PASS')
 return s
def limit(c):
 C,m=c['C'],c['m'];p=state(c).profile
 C.need(p['input_tokens']==32768 and p['output_tokens']in(8,160)and
        p['checkpoint']==CHECKPOINT and p['metadata']==METADATA and
        p['per_rank_disk_cap']==template_disk_cap()and
        p['all_rank_disk_cap']==4*p['per_rank_disk_cap']and
        p['reserves']['output_cap']==32*2**30 and p['reserves']['model_cgroup']==48*2**30,
        'exact reviewed32K disk derivation and unchanged outer guards')
 C.need(type(c['used'])is int and c['used']>=0 and type(c['metadata_bytes'])is int and
        0<=c['metadata_bytes']<=METADATA,'actual shared FA/retained-current PT and metadata counters')
 return p['per_rank_disk_cap']
def archive_before(c,n,*,metadata):
 cap=limit(c);need(type(n)is int and n>=0 and type(metadata)is bool,'strict proposed immutable bytes')
 need(c['used']+(0 if metadata else n)+CHECKPOINT+METADATA<=cap,
      'shared archive/retained-current PT within profile disk and reserved checkpoint/metadata')
 if metadata:need(c['metadata_bytes']+n<=METADATA,'all complete FA/qualification JSON inside metadata reserve')
 return cap
def metadata_before(c,n):return archive_before(c,n,metadata=True)
def wire_total(c,first,n):
 cap=limit(c)
 need(type(first)is int and first>=0 and type(n)is int and n>=0,'strict actual first/current wire operands')
 need(first+n+CHECKPOINT+METADATA<=cap,'actual shared FA/first/current wire inside profile disk')
 return first+n+CHECKPOINT+METADATA
def wire_room(c):
 cap=limit(c);return cap-c['used']-CHECKPOINT-METADATA
def pt_before(c,n):return wire_total(c,c['used'],n)
def rank_terminal(c,*,rank,source,total,json_bytes):
 cap=limit(c)
 need(type(rank)is int and 0<=rank<4 and type(total)is int and total>=0 and
      type(json_bytes)is int and 0<=json_bytes<=min(total,METADATA),
      'strict actual rank complete disk and JSON byte census')
 # JSON is already in total; reserve only its unspent part, never charge it twice.
 need(total+CHECKPOINT+(METADATA-json_bytes)<=cap,'full rank leaves plus unspent reserves inside profile disk')
 return dict(rank=rank,source=source,actual_total_bytes=total,actual_JSON_bytes=json_bytes,
  disk_cap=cap,checkpoint_reserve=CHECKPOINT,unspent_metadata_reserve=METADATA-json_bytes)
def all_terminal(C,m,source,rows,*,shared):
 need(type(rows)is list and len(rows)==4 and all(type(x)is dict for x in rows),'exact four rank disk reports')
 need([x['rank']for x in rows]==list(range(4))and all(type(x['rank'])is int for x in rows),
      'no missing duplicate reordered or bool rank')
 p=P.validate(m['input_resource_profile32k'])
 for x in rows:
  need(x['source']==source and x['disk_cap']==p['per_rank_disk_cap']and
       type(x['actual_total_bytes'])is int and type(x['actual_JSON_bytes'])is int and
       0<=x['actual_JSON_bytes']<=min(x['actual_total_bytes'],METADATA)and
       x['checkpoint_reserve']==CHECKPOINT and
       x['unspent_metadata_reserve']==METADATA-x['actual_JSON_bytes']and
       x['actual_total_bytes']+CHECKPOINT+x['unspent_metadata_reserve']<=p['per_rank_disk_cap'],
       'same exact source/profile and complete rank census, not caller PASS')
 refs=shared['references'];need(type(refs)is list and len({r['path']for r in refs})==len(refs),'exact shared evidence readset once')
 for r in refs:C.checked(r)
 shared_bytes=sum(r['bytes']for r in refs)
 need(type(shared['bytes'])is int and shared['bytes']==shared_bytes and all(x['actual_total_bytes']>=shared_bytes for x in rows),'actual reopened shared bytes included in each conservative rank view')
 total=sum(x['actual_total_bytes']for x in rows)-3*shared_bytes
 reserved=sum(x['checkpoint_reserve']+x['unspent_metadata_reserve']for x in rows)
 need(total+reserved<=p['all_rank_disk_cap']and total<=p['reserves']['output_cap'],
      'actual four-rank disk sum inside unchanged allrank/global limits')
 return dict(actual_total_bytes=total,shared_bytes_counted_once=shared_bytes,unspent_reserves=reserved,all_rank_disk_cap=p['all_rank_disk_cap'],
  output_cap=p['reserves']['output_cap'],numerical_qualified=False)
