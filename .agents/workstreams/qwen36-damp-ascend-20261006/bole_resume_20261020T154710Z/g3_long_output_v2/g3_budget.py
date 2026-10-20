"""Full fixed1024 evidence reservation; capture/oracle remain enabled every step."""
from pathlib import Path
import json,re
import sourceio as C
import g2_contract as G
MAX_EVENTS=(G.MAX_OUTPUT-1)+3
CAL=16*2**20
JOURNAL=8*2**20
OTHER=3*2**20
FINAL=16*2**20
EVENT_CAPS=dict(FRAME=2048,ACK=3072,RELEASE=1536,REPORT=4000)


def reservation():
    event=(MAX_EVENTS+1)*sum(EVENT_CAPS.values()) # Retain a terminal failure too.
    total=event+CAL+JOURNAL+OTHER+FINAL
    C.need(G.MAX_OUTPUT==1024 and total<=G.METADATA_CAP and
        G.FRAME_LOGICAL_CAP+G.FRAME_WIRE_CAP+G.CHECKPOINT_CAP+G.METADATA_CAP<=G.RAW_CAP,
        'all worst-case segments plus full calibration/identity/final evidence under64MiB and original1GiB')
    return dict(max_success_events=MAX_EVENTS,terminal_failure_events=1,
        event_reserved_bytes=event,calibration_bytes=CAL,identity_bytes=JOURNAL,
        other_rank_bytes=OTHER,final_global_and_summary_bytes=FINAL,
        maximum_metadata_bytes=total,cap_bytes=G.METADATA_CAP,
        logical_plus_serialized_plus_checkpoint_plus_metadata=G.FRAME_LOGICAL_CAP+G.FRAME_WIRE_CAP+G.CHECKPOINT_CAP+G.METADATA_CAP)


def actual(C_,m,rank,*,references=False):
    reservation();base=Path(m['model_receipt_root']);channel=Path(m['stream_channel_root'])
    caldir=base/('CONV-MODEL-CALIBRATION-RANK-%d'%rank)
    cal={p for p in caldir.iterdir()if p.is_file()}if caldir.is_dir()else set()
    journals=set(base.glob('IDENTITY-rank%d-*.json'%rank))
    events=set(channel.glob('*RANK-%d-*.json'%rank))
    events.update(channel.glob('*RANK-%d-*.json.pending'%rank))
    for p in events:
        key=p.name.split('-',1)[0]
        C_.need(key in EVENT_CAPS and p.stat().st_size<=EVENT_CAPS[key],
            'every retained event obeys its source-frozen metadata allocation')
    C_.need(len({p.name.rsplit('-',1)[-1]for p in events})<=MAX_EVENTS+1,'finite every-frame event count')
    finals={p for pattern in('*.json','*.json.pending')for p in channel.glob(pattern)if 'RANK-'not in p.name}
    finals.update(channel.glob('*RANK-%d.json'%rank))
    finals.update(base.glob('BOLE-TREE-RANK-%d.*'%rank))
    other=set(base.glob('*RANK-%d.json'%rank))-finals
    # Conservatively charge every same-owned model snapshot/load receipt to
    # each rank. No ownership is inferred from a partial PID filename match.
    other.update(base.glob('worker-*-snapshot-*.json'))
    other.update(base.glob('MTP-LOAD-*.json'))
    sets=dict(calibration=cal,identity=journals,events=events,other=other,final=finals)
    for p in set().union(*sets.values()):
        C_.need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),
            'actual ordinary complete retained evidence without symlink')
    values={key:sum(p.stat().st_size for p in paths)for key,paths in sets.items()}
    C_.need(values['calibration']<=CAL and values['identity']<=JOURNAL and values['other']<=OTHER and values['final']<=FINAL,
        'complete actual retained calibration/identity/observer/final files fit declared allocations')
    C_.need(values['events']<=(MAX_EVENTS+1)*sum(EVENT_CAPS.values())and sum(values.values())<=G.METADATA_CAP,
        'all actual retained long-output metadata inside original64MiB')
    return dict(charges=values,bytes=sum(values.values()),references=
        [C_.ref(p)for p in sorted(set().union(*sets.values()))]if references else None)
