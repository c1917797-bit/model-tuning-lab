"""Read only the inherited MAIN lock. Never opens/acquires/releases the lock."""
import hashlib
import os
from pathlib import Path
import re
import stat
import time
import owner_common as C

SCHEMA='bole.actual-inherited-MAIN-lock-observation/v1'
BOUND=2**20


def bounded(path):
    with Path(path).open('rb')as f:data=f.read(BOUND+1)
    C.need(len(data)<=BOUND,'bounded proc lock observation')
    return data.decode()


def identity(value):
    return dict(device_major=os.major(value.st_dev),device_minor=os.minor(value.st_dev),inode=value.st_ino)


def start_ticks(text):
    fields=text[text.rfind(')')+2:].split()
    C.need(len(fields)>19 and fields[0]!='Z','actual living lock owner process')
    return int(fields[19])


def parse_lock(line):
    # /proc/locks and fdinfo lock rows share the same kernel text format.
    fields=line.split()
    if len(fields)!=8 or not re.fullmatch(r'[0-9]+:',fields[0]):return None
    if fields[1:4]!=['FLOCK','ADVISORY','WRITE']or fields[6:]!=['0','EOF']:return None
    device=fields[5].split(':')
    if len(device)!=3:return None
    try:
        return dict(pid=int(fields[4]),device_major=int(device[0],16),device_minor=int(device[1],16),inode=int(device[2]))
    except ValueError:return None


def matching(line,pid,file_identity):
    return parse_lock(line)==dict(pid=pid,**file_identity)


def validate(value,policy_ref,lock_path):
    C.need(value['schema']==SCHEMA and value['policy_ref']==policy_ref and value['lock_path']==lock_path,
        'source-bound exact inherited MAIN lock policy/path')
    pid=value['owner_pid'];file_identity=value['file_identity']
    C.need(type(pid)is int and pid>0 and type(value['owner_start_ticks'])is int and value['owner_start_ticks']>0
        and set(file_identity)=={'device_major','device_minor','inode'}
        and all(type(v)is int and v>=0 for v in file_identity.values())and file_identity['inode']>0,
        'actual owner lifetime and exact filesystem lock identity')
    lines=value['proc_locks_matching_lines']
    C.need(type(lines)is list and len(lines)==1 and matching(lines[0],pid,file_identity),
        'one actual held whole-file exclusive FLOCK for current owner and inode')
    C.need(type(value['proc_locks_bytes'])is int and 0<value['proc_locks_bytes']<=BOUND
        and re.fullmatch('[0-9a-f]{64}',value['proc_locks_sha256'])is not None,
        'bounded whole proc locks observation digest')
    fds=value['inherited_fds'];C.need(type(fds)is list and 1<=len(fds)<=64,'actual pre-existing inherited lock FD')
    seen=set()
    for row in fds:
        fd=row['fd'];C.need(type(fd)is int and fd>=0 and fd not in seen,'distinct actual inherited FD');seen.add(fd)
        C.need(row['link']==lock_path and row['file_identity']==file_identity and row['regular_file']is True,
            'held FD exact path and regular file identity')
        text=row['fdinfo'];C.need(type(text)is str and len(text.encode())<=BOUND,'bounded actual fdinfo')
        held=[line.split(':',1)[1].strip()for line in text.splitlines()if line.startswith('lock:')]
        C.need(any(matching(line,pid,file_identity)for line in held),'inherited FD itself owns exact exclusive kernel lock')
    C.need(value['acquired_or_released_lock']is False and value['capture_phase']=='before-sandbox-create'
        and type(value['captured_monotonic'])in(int,float)and value['captured_monotonic']>=0,
        'read-only pre-create observation, never a new lock operation')
    return value


def capture(policy_ref,lock_path):
    path=Path(lock_path)
    C.need(path.is_absolute()and path.name=='MAIN_ADMISSION.lock'
        and not any(p.is_symlink()for p in(path,*path.parents)),'ordinary exact MAIN admission lock')
    pid=os.getpid();before=bounded('/proc/self/stat');stamp=start_ticks(before)
    target=path.stat();C.need(stat.S_ISREG(target.st_mode),'existing regular MAIN lock file')
    target_identity=identity(target);fds=[]
    # Enumerate only existing self FDs. Reading proc files cannot obtain flock.
    numbers=[int(p.name)for p in Path('/proc/self/fd').iterdir()if p.name.isdecimal()]
    C.need(len(numbers)<=4096,'bounded owner FD enumeration')
    for fd in numbers:
        try:actual=os.fstat(fd)
        except OSError:continue
        if identity(actual)!=target_identity:continue
        row=dict(fd=fd,link=os.readlink('/proc/self/fd/'+str(fd)),file_identity=identity(actual),
            regular_file=stat.S_ISREG(actual.st_mode),fdinfo=bounded('/proc/self/fdinfo/'+str(fd)))
        fds.append(row)
    raw=bounded('/proc/locks');lines=[line for line in raw.splitlines()if matching(line,pid,target_identity)]
    C.need(start_ticks(bounded('/proc/self/stat'))==stamp and identity(path.stat())==target_identity,
        'same exact owner lifetime and lock file throughout observation')
    value=dict(schema=SCHEMA,policy_ref=policy_ref,lock_path=lock_path,owner_pid=pid,owner_start_ticks=stamp,
        file_identity=target_identity,inherited_fds=fds,proc_locks_matching_lines=lines,
        proc_locks_bytes=len(raw.encode()),proc_locks_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        acquired_or_released_lock=False,capture_phase='before-sandbox-create',captured_monotonic=time.monotonic())
    return validate(value,policy_ref,lock_path)
