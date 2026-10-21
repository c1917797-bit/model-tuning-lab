"""Bounded read-only network facts. No socket, ioctl, setns or safety verdict."""
import os
from pathlib import Path
import re
import stat
import owner_common as C

ATTRIBUTES=('flags','operstate','type','carrier','ifindex','iflink')
ROUTES=('route','ipv6_route','if_inet6')


def validate_read(value,limit):
    C.need(type(value)is dict and set(value)=={'ok','text','error'}and type(value['ok'])is bool,'exact read-only file receipt')
    if value['ok']:
        C.need(type(value['text'])is str and len(value['text'].encode('ascii'))<=limit and value['error']is None,
            'bounded actual raw ASCII network file; no interpretation')
    else:
        error=value['error']
        C.need(value['text']is None and type(error)is dict and set(error)=={'type','errno'}
            and type(error['type'])is str and re.fullmatch('[A-Za-z]+Error',error['type'])is not None
            and type(error['errno'])is int and error['errno']>0,'retained exact OS read failure, never a fabricated value')


def validate_details(value,names):
    C.need(value['schema']=='bole.actual-HE-readonly-network-details/v1'and value['interpretation_performed']is False
        and value['network_safety_accepted']is False,'actual network details only; no inferred semantics/safety')
    rows=value['sys_entries'];C.need(type(rows)is list and [row['name']for row in rows]==names,
        'each and every actual sys network entry, in the independently recorded inventory')
    for row in rows:
        C.need(set(row)=={'name','lstat','is_symlink','is_dir','symlink_target','attributes'}
            and type(row['name'])is str and 0<len(row['name'])<=256 and '/'not in row['name']
            and row['name']not in('.','..'),'ordinary actual sys entry identity')
        s=row['lstat'];C.need(type(s)is dict and set(s)=={'mode','device','inode'}
            and all(type(v)is int and v>=0 for v in s.values())and s['inode']>0,'actual lstat mode/device/inode')
        C.need(type(row['is_symlink'])is bool and type(row['is_dir'])is bool
            and row['is_symlink']==stat.S_ISLNK(s['mode']),'actual lstat/symlink fields agree')
        if row['is_symlink']:
            C.need(type(row['symlink_target'])is str and 0<len(row['symlink_target'])<=4096,'bounded raw sys symlink target')
        else:
            C.need(row['symlink_target']is None and row['is_dir']==stat.S_ISDIR(s['mode']),'actual non-symlink file/directory fields agree')
        C.need(set(row['attributes'])==set(ATTRIBUTES),'all six requested interface file attempts')
        for result in row['attributes'].values():validate_read(result,4096)
    C.need(set(value['proc_routes'])==set(ROUTES),'all three exact proc route/address files')
    for result in value['proc_routes'].values():validate_read(result,65536)
    process=value['guest_process'];C.need(set(process)=={'pid','start_ticks'}
        and all(type(v)is int and v>0 for v in process.values()),'actual guest process lifetime for namespace join')
    return value


def process_ticks(proc):
    text=(proc/'stat').read_text();fields=text[text.rfind(')')+2:].split()
    C.need(len(fields)>19 and fields[0]!='Z','live process for read-only net namespace proof')
    return int(fields[19])


def file_identity(s):return dict(device=s.st_dev,inode=s.st_ino)


def capture_namespaces(binding):
    guest=Path('/proc')/str(binding['host_pid']);owner=Path('/proc')/str(os.getpid());init=Path('/proc/1')
    C.need(process_ticks(guest)==binding['start_ticks']and(guest/'cgroup').read_text()==binding['cgroup'],
        'same actual bound guest lifetime/cgroup before net namespace observation')
    rows={};opened=[]
    try:
        for role,proc in(('owner',owner),('host_init',init),('guest',guest)):
            ticks=process_ticks(proc);path=proc/'ns/net';before=os.readlink(path)
            fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC);opened.append((role,proc,fd,ticks,before))
            identity=file_identity(os.fstat(fd))
            C.need(re.fullmatch(r'net:\[[0-9]+\]',before)is not None and int(before[5:-1])==identity['inode'],
                'actual opened netns inode agrees with live namespace link')
            rows[role]=dict(pid=int(proc.name),start_ticks=ticks,link=before,file_identity=identity)
        for role,proc,fd,ticks,link in opened:
            C.need(process_ticks(proc)==ticks and os.readlink(proc/'ns/net')==link
                and file_identity(os.fstat(fd))==rows[role]['file_identity'],
                'same process lifetime and pinned read-only namespace FD throughout capture')
        C.need((guest/'cgroup').read_text()==binding['cgroup'],'same owned guest cgroup after namespace observation')
    finally:
        for _,_,fd,_,_ in opened:os.close(fd)
    identities={k:row['file_identity']for k,row in rows.items()}
    return dict(schema='bole.actual-HE-host-guest-netns-observation/v1',container_id=binding['container_id'],
        bound_guest_host_pid=binding['host_pid'],bound_guest_start_ticks=binding['start_ticks'],namespaces=rows,
        comparisons=dict(owner_equals_host_init=identities['owner']==identities['host_init'],
            guest_equals_host_init=identities['guest']==identities['host_init'],guest_equals_owner=identities['guest']==identities['owner']),
        setns_performed=False,sockets_or_ioctls_performed=False,network_safety_accepted=False)


def validate_namespaces(value,binding,observation,owner_pid,owner_ticks):
    C.need(value['schema']=='bole.actual-HE-host-guest-netns-observation/v1'and value['container_id']==binding['container_id']
        and value['bound_guest_host_pid']==binding['host_pid']and value['bound_guest_start_ticks']==binding['start_ticks'],
        'actual fullCID/live guest process and namespace observation join')
    rows=value['namespaces'];C.need(set(rows)=={'owner','host_init','guest'},'exact owner/init/live guest namespace roles')
    for row in rows.values():
        C.need(set(row)=={'pid','start_ticks','link','file_identity'}and type(row['pid'])is int and row['pid']>0
            and type(row['start_ticks'])is int and row['start_ticks']>0
            and type(row['link'])is str and re.fullmatch(r'net:\[[0-9]+\]',row['link'])is not None
            and set(row['file_identity'])=={'device','inode'}
            and all(type(v)is int and v>=0 for v in row['file_identity'].values())
            and row['file_identity']['inode']==int(row['link'][5:-1]),'actual process and nsfs identity/link consistency')
    C.need(rows['owner']['pid']==owner_pid and rows['owner']['start_ticks']==owner_ticks
        and rows['host_init']['pid']==1 and rows['guest']['pid']==binding['host_pid']
        and rows['guest']['start_ticks']==binding['start_ticks']and rows['guest']['link']==observation['net_namespace_link']
        and observation['network_details']['guest_process']==dict(pid=binding['guest_pid'],start_ticks=binding['start_ticks']),
        'guest-internal and live host netns observations belong to the exact same bound process')
    i={k:row['file_identity']for k,row in rows.items()}
    expected=dict(owner_equals_host_init=i['owner']==i['host_init'],guest_equals_host_init=i['guest']==i['host_init'],guest_equals_owner=i['guest']==i['owner'])
    C.need(value['comparisons']==expected and all(type(v)is bool for v in value['comparisons'].values())
        and all(value[k]is False for k in('setns_performed','sockets_or_ioctls_performed','network_safety_accepted')),
        'independent namespace identity comparisons, never a safety verdict')
    return value
