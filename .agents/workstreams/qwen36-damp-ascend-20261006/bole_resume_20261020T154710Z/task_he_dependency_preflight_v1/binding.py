"""Exact host observation; no caller or resource policy widening."""
import os
from pathlib import Path
import owner_common as C
import main_quiescence as Q

def memory_view(H,pid,expected):
    version,group,mount,chain=H.hierarchy(pid,'memory');rows=[];finite=[]
    for path in chain:
        name='memory.max'if version==2 else'memory.limit_in_bytes';file=path/name
        if not file.is_file():C.need(path==Path(mount),'actual ancestor memory control missing');continue
        text=file.read_text().strip();limit=None if text=='max'else int(text)
        if limit is not None:finite.append(limit)
        usage_file=path/('memory.current'if version==2 else'memory.usage_in_bytes')
        swap=path/('memory.swap.max'if version==2 else'memory.memsw.limit_in_bytes')
        rows.append(dict(path=str(path),limit=text,usage_bytes=int(usage_file.read_text())if usage_file.is_file()else None,
            swap_limit=swap.read_text().strip()if swap.is_file()else None))
    C.need(finite and min(finite)==expected,'actual guest plus all ancestors admit exact finite memory cap')
    return dict(version=version,cgroup=group,ancestors=rows,effective_bytes=min(finite))

def host_binding(S,ctl,pid,uid,namespace_module,*,guest=None,HE=False):
    proc=Path('/proc')/str(pid);status=(proc/'status').read_text();stat=(proc/'stat').read_text();fields=stat[stat.rfind(')')+2:].split()
    cg=(proc/'cgroup').read_text();nspid=[int(v)for line in status.splitlines()if line.startswith('NSpid:')for v in line.split()[1:]]
    uids=[int(v)for line in status.splitlines()if line.startswith('Uid:')for v in line.split()[1:]]
    C.need(ctl.cid in cg and nspid and uids==[uid]*4 and fields[0]!='Z','actual exact live owned cgroup/namespace/uid')
    if guest is not None:C.need(nspid[-1]==guest['pid']and int(fields[19])==guest['start_ticks'],'actual child strong lifetime namespace mapping')
    argv=[v.decode()for v in(proc/'cmdline').read_bytes().split(b'\0')if v]
    if HE:
        # env-i resolves python3 using the frozen PATH. Compare the actual loaded
        # binary with the first executable in that PATH inside the same pinned root.
        F=namespace_module;namespaces=F.namespace_id(proc)
        rootfd=os.open(proc/'root',os.O_RDONLY|os.O_DIRECTORY);expected_fd=actual_fd=None
        C.need(F.identity(os.fstat(rootfd))==namespaces['root'],'pinned actual HE namespace root FD')
        expected=None
        try:
            for directory in('/usr/local/python3.12.13/bin','/usr/local/sbin','/usr/local/bin','/usr/sbin','/usr/bin','/sbin','/bin'):
                try:fd,canonical=F.root_open(rootfd,directory+'/python3')
                except FileNotFoundError:continue
                try:proof=F.file_proof(fd)
                except ValueError:os.close(fd);continue
                expected_fd=fd;expected=canonical;break
            C.need(expected_fd is not None,'actual frozen PATH resolves a real Python executable')
            actual_fd=os.open(proc/'exe',os.O_RDONLY)
            actual=F.file_proof(actual_fd);C.need(actual==F.file_proof(expected_fd),'actual HE loaded executable matches whole namespace PATH binary')
            C.need(expected=='/usr/local/python3.12.13/bin/python3.12' and actual['bytes']==10696 and actual['sha256']=='5d137e6378d886d6ee0390e126011e9e8af81290032e3fefa13a81f72651fda0','exact actual same-image Python312 whole binary')
            C.need(F.namespace_id(proc)==namespaces,'same actual HE namespaces/root throughout binary probe')
            program=dict(expected_namespace_executable=expected,actual_namespace_executable=os.readlink(proc/'exe'),executable=actual,namespaces=namespaces)
        finally:
            for fd in(actual_fd,expected_fd,rootfd):
                if fd is not None:os.close(fd)
        C.need(argv==['python3','-I','-B','/source/he_worker.py','--preflight','--capsule-sha256',ctl.stage['capsule_ref']['sha256']],
               'actual fixed HE controls process, no task execution entry')
    else:
        program=namespace_module.verify(proc,Path('/proc')/str(ctl.inspect()[0]['State']['Pid']),'/usr/local/python3.12.13/bin/python3')
        C.need(len(argv)>4 and argv[1:3]==['-I','-B']and argv[3]==str(P/'cpu_steps.py'),'actual private owned CPU child executable/entry')
    cpu=S.H.cpu_view(pid);C.need(cpu['effective_cpus']==[145]and cpu['effective_capacity']==1,'actual CPU145/oneCPU guest and ancestor quotas')
    memory=memory_view(S.H,pid,2*C.GIB if HE else 8*C.GIB)
    C.need((proc/'stat').read_text().split(')')[-1].split()[19]==fields[19]and(proc/'cgroup').read_text()==cg,'same live owned process across full host probe')
    return C.write(ctl.out/'PROCESS-BINDING.json',dict(container_id=ctl.cid,host_pid=pid,guest_pid=nspid[-1],
        nspid=nspid,start_ticks=int(fields[19]),uid=uid,status=status,cgroup=cg,argv=argv,
        program=program,cpu=cpu,memory=memory,guest_start=guest,Devices=[]))

def observe_cpu(ctl,label,initial=False):
    # Original025 actual NPU/HBM/FD/protected/resource guards always run first.
    r=ctl.observe(label,initial=initial)
    return Q.observe(ctl,r,ctl._main_quiescence_ref)
