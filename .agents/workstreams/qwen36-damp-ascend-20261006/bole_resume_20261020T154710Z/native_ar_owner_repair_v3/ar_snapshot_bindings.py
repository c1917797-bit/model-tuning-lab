"""Read existing AR load snapshots and join fresh actual compute; NEVER signal."""
from pathlib import Path


def proc(pid):
    p=Path('/proc')/str(pid);stat=(p/'stat').read_text();fields=stat[stat.rfind(')')+2:].split()
    status=(p/'status').read_text();ns=[int(x)for line in status.splitlines()if line.startswith('NSpid:')for x in line.split()[1:]]
    return dict(pid=pid,start_ticks=int(fields[19]),state=fields[0],cgroup=(p/'cgroup').read_text(),
                NSpid=ns,stat=stat)


def bind(C,c,ctl,source_ref,root):
    observation=ctl.observe('native-ar-existing-load-snapshots')
    rows=c.obj(observation)['actual_compute'];snapshots=[];refs=[];bindings=[]
    for rank in range(4):
        rr=C.ref(root/('NATIVE-AR-SNAPSHOT-RANK-%d.json'%rank));snapshot=C.obj(rr)
        C.need(snapshot['source_ref']==source_ref and snapshot['rank']==rank and snapshot['allow_hf32']is False and
               snapshot['actual_allow_hf32']is False and snapshot['speculative_config']is None and
               snapshot['registry']['counts']==dict(gdn=48,fa=16),'actual AR load snapshot/source/registry/HF32')
        fields=snapshot['proc_stat'][snapshot['proc_stat'].rfind(')')+2:].split()
        C.need(int(snapshot['proc_stat'].split(' ',1)[0])==snapshot['pid'],'actual guest stat PID')
        choices={row['pid']:row for row in rows if row['physical']==rank+4}
        C.need(len(choices)==1,'one actual compute PID on each physical4..7')
        host=next(iter(choices.values()));before=proc(host['pid'])
        C.need(before['start_ticks']==host['start_ticks']==int(fields[19]) and before['state']not in('Z','X') and
               ctl.cid in before['cgroup'] and before['cgroup']==host['cgroup'] and before['NSpid'] and
               before['NSpid'][-1]==snapshot['pid'],'fresh actual SMI/PID/start/cgroup/NSpid load join')
        after=proc(host['pid'])
        C.need(after['pid']==before['pid'] and after['start_ticks']==before['start_ticks'] and
               after['cgroup']==before['cgroup'] and after['NSpid']==before['NSpid'] and after['state']not in('Z','X'),
               'same live worker lifetime across binding read')
        snapshots.append(snapshot);refs.append(rr)
        bindings.append(dict(host=host,guest=snapshot,NSpid=before['NSpid'],owned_cid=ctl.cid,
                             actual_observation=observation,signal_sent=False))
    C.need(len({b['host']['pid']for b in bindings})==4,'four distinct real owned AR workers')
    return snapshots,refs,bindings
