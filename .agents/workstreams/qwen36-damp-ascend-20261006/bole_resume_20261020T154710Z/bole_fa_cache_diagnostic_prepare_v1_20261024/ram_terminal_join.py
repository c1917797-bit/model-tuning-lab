"""Strict saved-stage RAM receipts; no live /proc substitute or numerical PASS."""
from pathlib import Path
import fa_cache_advisory as CACHE

SCHEMA='bole.worker-diagnostic-RAM-reservation/v2'
STAGES=('pre_export','pre_save','post_wire','pre_reload','post_consume','ACK','sink_returned')
GIB=2**30
IDENTITY=('source','rank','pid','start_ticks','cid','owned','cgroup','cgroup_membership','limit')
KEYS={'schema','stage','source','rank','pid','start_ticks','cid','owned','cgroup','cgroup_membership','limit','usage',
      'VmRSS','VmHWM','reserved_total','per_rank_limit','model_limit','CPU_copies_reserved',
      'generation','ordinal','enter_RSS','enter_HWM','current_RSS_increment','new_HWM_increment',
      'cgroup_usage_includes_reclaimable_filecache','admission_classification',
      'exact_instantaneous_peak_proven','numerical_qualified','memory_stat'}


def need(v,s):
    if not v:raise ValueError(s)


def shared(C,m,source):
    need(C.ref(__file__)==m['files']['ram_terminal_join.py'],'actual source-owned RAM terminal consumer')
    receipt=Path(m['model_receipt_root']);base=receipt.parent
    owned_ref=C.ref(base/'OWNED.json');owned=C.obj(owned_ref)
    cid=owned['cid']
    need(type(cid)is str and len(cid)==64 and all(x in '0123456789abcdef'for x in cid)and
         owned['source']==source and owned['arm']==base.name=='dense'and
         owned['mounts'].get(str(base))==[str(base),True],
         'same actual completed owned source/CID/output')
    root=receipt/'RUNTIME-JOINT-RAM-v2'
    need(root.is_dir()and not any(p.is_symlink()for p in(root,*root.parents))and
         {p.name for p in root.iterdir()}=={'RESERVATIONS.json','RESERVATIONS.lock'}and
         all(p.is_file()and not p.is_symlink()for p in root.iterdir()),
         'all and only two durable shared RAM files, no unfinished pending')
    refs=[C.ref(root/n)for n in('RESERVATIONS.json','RESERVATIONS.lock')]
    need(refs[0]['bytes']<=65536 and refs[1]['bytes']==0,'bounded complete reservation state and empty ordinary lock')
    value=C.obj(refs[0])
    need(type(value)is dict and set(value)=={'schema','source','cid','failed','slots'}and
         value['schema']==SCHEMA and value['source']==source and value['cid']==cid and
         value['failed']is None and type(value['slots'])is dict and not value['slots'],
         'all actual diagnostic reservations released with no shared failure')
    return dict(owned=owned_ref,cid=cid,references=refs,bytes=sum(r['bytes']for r in refs))


def frame(C,m,source,rank,generation,ordinal,root,expected,identities,shared_state):
    need(type(rank)is int and rank in range(4)and type(generation)is int and generation in(1,2)and
         type(ordinal)is int and ordinal>=0,'strict actual terminal frame key')
    refs=[];first=None
    for stage in STAGES:
        name='G%d-O%d-RAM-%s.json'%(generation,ordinal,stage)
        expected.add(name);r=C.ref(Path(root)/name);v=C.obj(r)
        need(r['bytes']<=16384 and type(v)is dict and set(v)==KEYS,'complete bounded exact RAM stage fields')
        CACHE.validate_memory_stat(v['memory_stat'])
        need(v['schema']==SCHEMA and v['stage']==stage and v['source']==source and
             type(v['rank'])is int and v['rank']==rank and
             type(v['generation'])is int and v['generation']==generation and
             type(v['ordinal'])is int and v['ordinal']==ordinal,'same saved RAM source/rank/generation/ordinal/stage')
        for k in('pid','start_ticks','limit','usage','VmRSS','VmHWM','reserved_total','per_rank_limit',
                  'model_limit','CPU_copies_reserved','enter_RSS','enter_HWM','current_RSS_increment','new_HWM_increment'):
            need(type(v[k])is int and v[k]>=0,'strict nonnegative RAM counter '+k)
        need(v['pid']>0 and v['start_ticks']>0 and v['cid']==shared_state['cid']and
             v['owned']==shared_state['owned']and type(v['cgroup'])is str and
             Path(v['cgroup']).is_absolute()and '..'not in Path(v['cgroup']).parts and
             type(v['cgroup_membership'])is str and Path(v['cgroup_membership']).is_absolute()and
             '..'not in Path(v['cgroup_membership']).parts and
             Path(v['cgroup_membership']).name==v['cid'],
             'actual saved worker lifetime/CID/cgroup and independently reopened OWNED')
        need(v['limit']==v['model_limit']==48*GIB and v['per_rank_limit']==8455716864 and
             v['CPU_copies_reserved']==2 and v['reserved_total']%(8455716864)==0 and
             v['reserved_total']<=33822867456 and v['usage']+v['reserved_total']<=48*GIB and
             (v['reserved_total']>=8455716864 if stage!='sink_returned'else v['reserved_total']<=25367150592),
             'unchanged real32GiB model /2GiB per rank and conservative reservation admission')
        need(v['VmRSS']<=v['VmHWM']and v['enter_RSS']<=v['enter_HWM']and
             v['current_RSS_increment']==max(0,v['VmRSS']-v['enter_RSS'])and
             v['new_HWM_increment']==max(0,v['VmHWM']-v['enter_HWM'])and
             v['current_RSS_increment']<=8455716864 and v['new_HWM_increment']<=8455716864 and
             v['cgroup_usage_includes_reclaimable_filecache']is True and
             v['admission_classification']=='conservative resource admission, not algorithm memory verdict'and
             v['exact_instantaneous_peak_proven']is False and v['numerical_qualified']is False,
             'original baseline/delta meanings; no instantaneous peak or numerical promotion')
        identity={k:v[k]for k in IDENTITY}
        if first is None:
            first=dict(identity,enter_RSS=v['enter_RSS'],enter_HWM=v['enter_HWM'])
            need(stage=='pre_export'and v['VmRSS']==v['enter_RSS']and v['VmHWM']==v['enter_HWM'],
                 'actual frame starts at saved entry baselines')
        else:need(first==dict(identity,enter_RSS=v['enter_RSS'],enter_HWM=v['enter_HWM']),
                  'same seven-stage actual frame identity/baselines')
        if rank in identities:need(identities[rank]==identity,'same worker lifetime across all frames/generations')
        else:identities[rank]=identity
        refs.append(r)
    return refs


def complete(identities):
    need(set(identities)==set(range(4))and len({(r['pid'],r['start_ticks'])for r in identities.values()})==4,
         'all four distinct actual worker lifetimes in saved successful receipts')
    need(len({(r['cid'],r['cgroup'],r['cgroup_membership'])for r in identities.values()})==1,
         'one exact source-owned model cgroup')
