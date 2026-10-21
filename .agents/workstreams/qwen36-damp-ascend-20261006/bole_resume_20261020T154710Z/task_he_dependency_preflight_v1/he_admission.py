"""Source-owned pre-executor host namespace admission, no network operations."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import owner_common as C
import network_evidence as V


def ready(text,G,source_sha,capsule_sha,binding,namespace):
    C.need(type(text)is str and len(text.encode())<=2**20,'bounded pre-executor actual HE logs')
    lines=[line[len(G.READY_MARKER):]for line in text.splitlines()if line.startswith(G.READY_MARKER)]
    C.need(len(lines)==1,'one actual source-bound network READY')
    r=json.loads(lines[0]);facts=r['facts'];predicate=G.validate(facts)
    C.need(r['schema']=='bole.actual-HE-network-ready/v1'and len(r['nonce'])==64
        and all(v in'0123456789abcdef'for v in r['nonce'])and r['predicate']==predicate
        and r['root_source_sha256']==source_sha and r['capsule_sha256']==capsule_sha
        and facts['guest']==dict(pid=binding['guest_pid'],start_ticks=binding['start_ticks'])
        and facts['net_namespace']==dict(link=namespace['namespaces']['guest']['link'],**namespace['namespaces']['guest']['file_identity']),
        'actual READY exact nonce/source/capsule/bound guest lifetime/netns')
    C.need(namespace['container_id']==binding['container_id']and namespace['bound_guest_host_pid']==binding['host_pid']
        and namespace['bound_guest_start_ticks']==binding['start_ticks']
        and namespace['comparisons']==dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False),
        'before executor, actual owner is host-init netns and actual bound guest is private/distinct')
    return r


def publish(ctl,binding,namespace,F,ack,G):
    proc=Path('/proc')/str(binding['host_pid']);before=F.namespace_id(proc)
    C.need(C.canonical(before)==C.canonical(binding['program']['namespaces'])and V.process_ticks(proc)==binding['start_ticks']
        and(proc/'cgroup').read_text()==binding['cgroup'],'same exact bound owned process before private tmpfs ACK')
    rootfd=os.open(proc/'root',os.O_RDONLY|os.O_DIRECTORY);tmpfd=fd=None;temporary='.HE-ACK-'+ack['nonce']+'.tmp';linked=False
    data=C.canonical(ack)+b'\n'
    try:
        C.need(F.identity(os.fstat(rootfd))==before['root'],'pinned actual namespace root directory FD')
        tmpfd=os.open('tmp',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=rootfd);tmp_identity=V.file_identity(os.fstat(tmpfd))
        lines=(proc/'mountinfo').read_text().splitlines();mounts=[]
        for line in lines:
            fields=line.split();separator=fields.index('-')
            if fields[4]=='/tmp':mounts.append((fields,separator))
        C.need(len(mounts)==1,'one actual private tmpfs mount')
        fields,separator=mounts[0];major,minor=map(int,fields[2].split(':'))
        C.need(fields[3]=='/'and fields[separator+1]=='tmpfs'and{'rw','nosuid','nodev','noexec'}<=set(fields[5].split(','))
            and(major,minor)==(os.major(tmp_identity['device']),os.minor(tmp_identity['device'])),
            'same pinned writable private tmpfs device; no symlink or host directory write')
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o400,dir_fd=tmpfd)
        C.need(os.geteuid()==0 and os.fstat(fd).st_uid==0,'only actual host root can issue admission ACK')
        offset=0
        while offset<len(data):offset+=os.write(fd,data[offset:])
        os.fsync(fd);os.fchmod(fd,0o444);proof=os.fstat(fd)
        C.need(stat.S_ISREG(proof.st_mode)and proof.st_uid==0 and stat.S_IMODE(proof.st_mode)==0o444
            and proof.st_nlink==1 and proof.st_size==len(data),'complete root-owned immutable ACK before atomic publish')
        C.need(F.namespace_id(proc)==before and V.process_ticks(proc)==binding['start_ticks']
            and(proc/'cgroup').read_text()==binding['cgroup'],'same actual pinned mount and guest lifetime immediately before ACK')
        # link publishes complete data atomically and fails if ACK already exists.
        # At the instant before unlink, the legitimate complete ACK has two links.
        os.link(temporary,G.ACK_NAME,src_dir_fd=tmpfd,dst_dir_fd=tmpfd,follow_symlinks=False);linked=True
        os.unlink(temporary,dir_fd=tmpfd);os.fsync(tmpfd)
        after=os.stat(G.ACK_NAME,dir_fd=tmpfd,follow_symlinks=False)
        C.need((after.st_dev,after.st_ino)==(proof.st_dev,proof.st_ino)and after.st_nlink==1
            and V.file_identity(os.fstat(tmpfd))==tmp_identity,'same atomic ACK inode and pinned private mount after publish')
        value=dict(schema='bole.actual-HE-private-tmpfs-ACK-publication/v1',container_id=ctl.cid,
            owned_host_pid=binding['host_pid'],owned_start_ticks=binding['start_ticks'],namespace_before=before,
            tmp_identity=tmp_identity,tmp_mountinfo=' '.join(fields),ack_file_identity=V.file_identity(after),
            ack_uid=after.st_uid,ack_mode=stat.S_IMODE(after.st_mode),ack_bytes=len(data),ack_sha256=hashlib.sha256(data).hexdigest(),
            directory_nofollow=True,new_file_exclusive=True,complete_data_before_atomic_link=True,
            no_added_mounts=True,no_sockets_or_ioctls_or_setns=True)
        return C.write(ctl.out/'ACK-PUBLICATION.json',value)
    finally:
        if fd is not None:os.close(fd)
        if tmpfd is not None:
            if not linked:
                try:os.unlink(temporary,dir_fd=tmpfd)
                except FileNotFoundError:pass
            os.close(tmpfd)
        os.close(rootfd)


def admit(ctl,binding_ref,F,G,source_sha,capsule_sha,HE_deadline):
    binding=C.obj(binding_ref);namespace=V.capture_namespaces(binding)
    C.need(namespace['comparisons']==dict(owner_equals_host_init=True,guest_equals_host_init=False,guest_equals_owner=False),
        'actual distinct private network namespace is mandatory before executor')
    namespace_ref=C.write(ctl.out/'HE-NET-NAMESPACE.json',namespace)
    until=min(time.monotonic()+10,HE_deadline);r=None
    while r is None:
        raw,_=ctl.call('HE-network-READY',[ctl._task_DOCKER,'logs',ctl.cid],cap=5)
        text=raw['stdout']+raw['stderr']
        C.need(len(text.encode())<=2**20,'bounded source-only READY logs')
        if any(line.startswith(G.READY_MARKER)for line in text.splitlines()):r=ready(text,G,source_sha,capsule_sha,binding,namespace)
        else:
            actual,_=ctl.inspect();C.need(actual['State']['Running']and time.monotonic()<until,'finite actual pre-executor READY')
            ctl.remaining(cap=10);time.sleep(.05)
    ready_ref=C.write(ctl.out/'HE-NET-READY.json',r)
    ack=dict(schema='bole.actual-HE-host-network-admission-ack/v1',nonce=r['nonce'],root_source_sha256=source_sha,
        capsule_sha256=capsule_sha,container_id=ctl.cid,owned_host_pid=binding['host_pid'],owned_start_ticks=binding['start_ticks'],
        guest=r['facts']['guest'],guest_net_namespace=r['facts']['net_namespace'],
        host_namespaces={role:namespace['namespaces'][role]for role in('owner','host_init')})
    G.validate_ack(ack,r);ack_ref=C.write(ctl.out/'HE-NET-ACK.json',ack)
    C.need(time.monotonic()<HE_deadline,'pre-executor ACK fits original HE whole90second budget')
    publication_ref=publish(ctl,binding,namespace,F,ack,G)
    return C.write(ctl.out/'HE-NET-ADMISSION.json',dict(schema='bole.actual-HE-host-pre-executor-network-admission/v1',
        binding_ref=binding_ref,namespace_ref=namespace_ref,ready_ref=ready_ref,ack_ref=ack_ref,publication_ref=publication_ref,
        original_profile='runc/networknone/uid65534/Devices[]/three-public-RO/private-tmpfs',before_executor_ack_issued=True))
