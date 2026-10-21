"""Narrow none-network profile, with a host-owned pre-executor namespace ACK."""
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import time

CONSTANTS=dict(IFF_UP=1,IFF_LOOPBACK=8,IFF_RUNNING=64,IFF_LOWER_UP=65536,IFF_DORMANT=131072,
    ARPHRD_LOOPBACK=772,RTF_UP=1,RTF_REJECT=512,RTF_NONEXTHOP=2097152)
ATTRIBUTES=('flags','operstate','type','carrier','ifindex','iflink')
READY_MARKER='BOLE_HE_NETWORK_READY_V1 '
ACK_NAME='BOLE_HE_NETWORK_ACK.json'


def need(value,message):
    if not value:raise ValueError(message)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def read(path,limit):
    with Path(path).open('rb')as stream:value=stream.read(limit+1)
    need(len(value)<=limit,'bounded actual isolation file');return value.decode('ascii')


def detail(path,limit=4096):
    try:return dict(ok=True,text=read(path,limit),error=None)
    except OSError as e:return dict(ok=False,text=None,error=dict(type=type(e).__name__,errno=e.errno))


def ticks(text):return int(text[text.rfind(')')+2:].split()[19])


def collect():
    root=Path('/sys/class/net');names=sorted(p.name for p in root.iterdir());need(0<len(names)<=64,'bounded actual sys network inventory')
    rows=[]
    for name in names:
        p=root/name;s=p.lstat()
        rows.append(dict(name=name,lstat=dict(mode=s.st_mode,device=s.st_dev,inode=s.st_ino),is_symlink=p.is_symlink(),
            is_dir=p.is_dir(),symlink_target=os.readlink(p)if stat.S_ISLNK(s.st_mode)else None,
            attributes={key:detail(p/key)for key in ATTRIBUTES}))
        after=p.lstat();need((s.st_mode,s.st_dev,s.st_ino)==(after.st_mode,after.st_dev,after.st_ino),'stable actual sys entry identity')
    need(sorted(p.name for p in root.iterdir())==names,'stable actual sys network inventory')
    ns=Path('/proc/self/ns/net');identity=ns.stat();link=os.readlink(ns)
    status=read('/proc/self/status',65536);keys={'Uid','NoNewPrivs','CapInh','CapPrm','CapEff','CapBnd','CapAmb'}
    privilege={line.split(':',1)[0]:line.split(':',1)[1].strip()for line in status.splitlines()if line.split(':',1)[0]in keys}
    value=dict(schema='bole.actual-HE-network-guard-facts/v1',sys_entries=rows,
        proc_files={name:read('/proc/self/net/'+name,65536)for name in('dev','route','ipv6_route','if_inet6')},
        guest=dict(pid=os.getpid(),start_ticks=ticks(read('/proc/self/stat',65536))),privilege=privilege,
        net_namespace=dict(link=link,device=identity.st_dev,inode=identity.st_ino))
    need(len(canonical(value))<=131072,'complete bounded128KiB network facts, within original1MiB logs');return value


def decimal(text):
    need(re.fullmatch('[0-9]+\n?',text)is not None,'exact unsigned decimal sys attribute');return int(text)


def attr(row,name):
    v=row['attributes'][name]
    need(set(v)=={'ok','text','error'}and v['ok']is True and v['error']is None
        and type(v['text'])is str and len(v['text'].encode('ascii'))<=4096,'actual readable required sys attribute '+name)
    return v['text']


def validate(facts):
    need(facts['schema']=='bole.actual-HE-network-guard-facts/v1'and len(canonical(facts))<=131072,'exact bounded actual isolation facts')
    rows=facts['sys_entries'];need(type(rows)is list and 0<len(rows)<=64,'bounded complete sys entries')
    names=[r['name']for r in rows];need(names==sorted(set(names)),'complete ordered unique actual entries')
    loopback=[];down=[];files=[];indices=[]
    for r in rows:
        name=r['name'];s=r['lstat'];need(type(name)is str and re.fullmatch('[A-Za-z0-9_.:-]{1,256}',name)is not None,'ordinary kernel interface/sys filename')
        need(set(s)=={'mode','device','inode'}and all(type(v)is int and v>=0 for v in s.values())and s['inode']>0,
            'actual sysfs lstat identity')
        need(type(r['is_symlink'])is bool and type(r['is_dir'])is bool and r['is_symlink']==stat.S_ISLNK(s['mode'])
            and set(r['attributes'])==set(ATTRIBUTES),'actual sys entry kind and all attribute attempts')
        if stat.S_ISREG(s['mode']):
            need(r['is_symlink']is False and r['is_dir']is False and r['symlink_target']is None,'ordinary sys metadata file, not an interface')
            for v in r['attributes'].values():
                need(v==dict(ok=False,text=None,error=dict(type='NotADirectoryError',errno=errno.ENOTDIR)),
                    'regular metadata file has no child interface attributes')
            files.append(name);continue
        need(r['is_symlink']is True and r['is_dir']is True and r['symlink_target']=='../../devices/virtual/net/'+name,
            'only actual virtual interface symlinks; physical/unrecognized entries rejected')
        text=attr(r,'flags');need(re.fullmatch('0x[0-9a-fA-F]+\n?',text)is not None,'actual hexadecimal interface flags')
        flags=int(text,16);hardware=decimal(attr(r,'type'));index=decimal(attr(r,'ifindex'));link=decimal(attr(r,'iflink'))
        need(index>0 and index not in indices,'actual distinct positive interface index');indices.append(index)
        if flags&CONSTANTS['IFF_LOOPBACK']:
            need(hardware==CONSTANTS['ARPHRD_LOOPBACK']and flags==(CONSTANTS['IFF_UP']|CONSTANTS['IFF_LOOPBACK'])
                and index==link and attr(r,'operstate')in('unknown\n','up\n')and attr(r,'carrier')=='1\n',
                'single actual local loopback type/flags/link, never an interface-name exemption')
            loopback.append(name)
        else:
            active=sum(CONSTANTS[k]for k in('IFF_UP','IFF_RUNNING','IFF_LOWER_UP','IFF_DORMANT'))
            need(hardware!=CONSTANTS['ARPHRD_LOOPBACK']and flags&active==0 and attr(r,'operstate')=='down\n'and link==0,
                'nonloopback must be administratively/operationally down and have no link peer')
            carrier=r['attributes']['carrier']
            need(carrier==dict(ok=True,text='0\n',error=None)or carrier==dict(ok=False,text=None,error=dict(type='OSError',errno=errno.EINVAL)),
                'retain known carrier EINVAL as unavailable, never interpret it as carrier0; reject carrier1/unknown errors')
            down.append(name)
    need(len(loopback)==1,'exactly one semantically identified loopback interface')
    proc=facts['proc_files'];need(set(proc)=={'dev','route','ipv6_route','if_inet6'}
        and all(type(v)is str and len(v.encode('ascii'))<=65536 for v in proc.values()),'bounded complete raw proc network files')
    lines=proc['route'].splitlines()
    need(len(lines)==1 and lines[0].split()==['Iface','Destination','Gateway','Flags','RefCnt','Use','Metric','Mask','MTU','Window','IRTT'],
        'IPv4 main route table must contain header only; no claim to enumerate all IPv4 addresses')
    need(proc['if_inet6'].strip()=='','no configured IPv6 addresses')
    rejected=[]
    for line in proc['ipv6_route'].splitlines():
        p=line.split();need(len(p)==10 and all(re.fullmatch('[0-9a-fA-F]{'+str(n)+'}',p[i])is not None
            for i,n in enumerate((32,2,32,2,32,8,8,8,8))), 'exact IPv6 proc route columns')
        need(p[0]=='0'*32 and p[1]=='00'and p[2]=='0'*32 and p[3]=='00'and p[4]=='0'*32
            and int(p[5],16)==0xffffffff
            and int(p[8],16)==(CONSTANTS['RTF_REJECT']|CONSTANTS['RTF_NONEXTHOP'])and p[9]in loopback,
            'only unusable zero-address reject/no-nexthop entries; every usable/unknown route rejected')
        rejected.append(p)
    dev=proc['dev'].splitlines();need(len(dev)>=3 and dev[0].split()[0]=='Inter-|'and dev[1].split()[0]=='face', 'actual proc dev header')
    seen=[]
    for line in dev[2:]:
        pair=line.rsplit(':',1);need(len(pair)==2,'actual proc dev row')
        name=pair[0].strip();values=pair[1].split();need(name in loopback+down and name not in seen
            and len(values)==16 and all(re.fullmatch('[0-9]+',v)is not None for v in values),'actual unique complete interface counters')
        need(name in loopback or all(int(v)==0 for v in values),'no observed prior nonloopback traffic in isolated profile');seen.append(name)
    need(set(seen)==set(loopback+down),'proc and sys interface inventories must agree')
    privileges=facts['privilege'];need(set(privileges)=={'Uid','NoNewPrivs','CapInh','CapPrm','CapEff','CapBnd','CapAmb'}
        and privileges['Uid'].split()==['65534']*4 and privileges['NoNewPrivs']=='1'
        and all(privileges[k]=='0000000000000000'for k in privileges if k.startswith('Cap')),
        'actual uid65534/no-new-privileges and all capability sets empty')
    ns=facts['net_namespace'];need(set(ns)=={'link','device','inode'}and re.fullmatch(r'net:\[[0-9]+\]',ns['link'])is not None
        and type(ns['device'])is int and ns['device']>=0 and type(ns['inode'])is int and ns['inode']==int(ns['link'][5:-1]),'actual self netns identity')
    guest=facts['guest'];need(set(guest)=={'pid','start_ticks'}and all(type(v)is int and v>0 for v in guest.values()),'actual guest process lifetime')
    return dict(schema='bole.HE-network-local-predicate/v1',loopback_interfaces=loopback,down_virtual_interfaces=down,
        regular_metadata_files=files,ipv4_main_routes=0,ipv6_addresses=0,unusable_ipv6_reject_rows=len(rejected),
        facts_sha256=hashlib.sha256(canonical(facts)).hexdigest(),local_predicate_passed=True,
        host_namespace_join_still_required=True,standalone_network_safety_accepted=False)


def verify_protocol(root):
    value=json.loads(read(root/'HE_NETWORK_PROTOCOL.json',65536))
    need(value['schema']=='bole.HE-isolated-down-virtual-networks/v1'and value['constants']==CONSTANTS
        and value['qualified']is False and value['iface_name_whitelist']is False,'frozen prospective network protocol/constant source')
    for name,row in value['header_files'].items():
        raw=(root/'network_uapi'/name).read_bytes()
        need((len(raw),hashlib.sha256(raw).hexdigest())==(row['bytes'],row['sha256']),'exact copied same-image public UAPI header')
    return value


def validate_ack(ack,ready):
    need(ack['schema']=='bole.actual-HE-host-network-admission-ack/v1'and ack['nonce']==ready['nonce']
        and ack['root_source_sha256']==ready['root_source_sha256']and ack['capsule_sha256']==ready['capsule_sha256']
        and ack['guest']==ready['facts']['guest']and ack['guest_net_namespace']==ready['facts']['net_namespace'],
        'host ACK exact nonce/source/capsule/guest lifetime/netns join')
    need(type(ack['owned_host_pid'])is int and ack['owned_host_pid']>0 and ack['owned_start_ticks']==ready['facts']['guest']['start_ticks']
        and re.fullmatch('[0-9a-f]{64}',ack['container_id'])is not None,'ACK actual owned host lifetime/fullCID')
    host=ack['host_namespaces'];need(set(host)=={'owner','host_init'}and host['owner']['file_identity']==host['host_init']['file_identity']
        and host['owner']['file_identity']!=dict(device=ready['facts']['net_namespace']['device'],inode=ready['facts']['net_namespace']['inode'])
        and host['host_init']['pid']==1 and type(host['owner']['pid'])is int and host['owner']['pid']>0,
        'host confirms distinct private guest netns from actual owner/host init')
    for row in host.values():
        need(set(row)=={'pid','start_ticks','link','file_identity'}and type(row['pid'])is int and row['pid']>0
            and type(row['start_ticks'])is int and row['start_ticks']>0
            and set(row['file_identity'])=={'device','inode'}
            and all(type(v)is int and v>=0 for v in row['file_identity'].values())
            and type(row['link'])is str and re.fullmatch(r'net:\[[0-9]+\]',row['link'])is not None
            and int(row['link'][5:-1])==row['file_identity']['inode'],'ACK actual host process and namespace FD identities')
    return ack


def await_ack(facts,root_sha,capsule_sha,authority):
    validate(facts);path=Path('/tmp')/ACK_NAME;need(not path.exists(),'new private tmpfs ACK leaf, never reused')
    ready=dict(schema='bole.actual-HE-network-ready/v1',nonce=secrets.token_hex(32),root_source_sha256=root_sha,
        capsule_sha256=capsule_sha,facts=facts,predicate=validate(facts))
    print(READY_MARKER+canonical(ready).decode(),flush=True)
    deadline=time.monotonic()+10;need(time.time()+10<authority['cutoff_epoch'],'ACK wait fits current finite authority')
    while not path.exists():
        need(time.monotonic()<deadline,'finite10second pre-executor host namespace ACK, never fallback');time.sleep(.05)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and before.st_uid==0 and stat.S_IMODE(before.st_mode)==0o444
            and before.st_nlink in(1,2)and 0<before.st_size<=65536,'root-owned complete atomically published readonly ACK')
        data=os.read(fd,65537);after=os.fstat(fd)
        need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
            and len(data)==before.st_size,'stable complete actual ACK bytes')
    finally:os.close(fd)
    ack=validate_ack(json.loads(data),ready)
    current=collect();validate(current)
    need(current['guest']==facts['guest']and current['net_namespace']==facts['net_namespace'],'same actual guest lifetime and netns after host ACK')
    return dict(ready=ready,ack=ack,ack_sha256=hashlib.sha256(data).hexdigest(),after_ack_facts=current,
        before_executor_host_ack_verified=True)
