"""Read Linux proc magic links as namespace references, never host paths.

Only the explicitly named /proc/PID/{root,exe} magic links are opened. All
ordinary executable path components are resolved relative to a pinned root FD;
absolute symlinks restart at that root, not the host root. No process mutation.
"""
import hashlib,os,stat
from pathlib import Path,PurePosixPath

PY='/usr/local/python3.12.13/bin/python3' # exact original025 model_contract.PY
MAX_BINARY=64*2**20

def need(v,message):
 if not v:raise ValueError(message)

def identity(s):
 return (s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_nlink)

def guest_parts(path):
 need(type(path)is str and path.startswith('/')and not path.startswith('//')and
      '\\'not in path and '\x00'not in path and '(deleted)'not in path,'ordinary absolute namespace executable, not deleted/host fallback')
 p=PurePosixPath(path)
 need('..'not in p.parts and str(p)==path,'canonical absolute namespace spelling')
 return list(p.parts[1:])

def symlink_parts(target):
 need(type(target)is str and target and '\x00'not in target and '\\'not in target and
      '(deleted)'not in target,'ordinary nondeleted namespace symlink target')
 # Do not lexical-normalize foo/..: foo can itself be a symlink. This narrow
 # exact-interpreter resolver refuses that domain instead of guessing kernel
 # traversal semantics. Known plain python3 -> python3.12 remains supported.
 need('..'not in target.split('/'),'parent components in interpreter symlink require separate source proof')
 return [p for p in target.split('/')if p not in('','.')]

def root_open(rootfd,path):
 """Bounded openat component walk, safely following namespace symlinks."""
 pending=guest_parts(path);resolved=[];links=0;directory=os.dup(rootfd)
 try:
  while pending:
   part=pending.pop(0)
   need(part not in ('','.'),'nonempty executable component')
   need(part!='..','no parent traversal in namespace executable lookup')
   before=os.stat(part,dir_fd=directory,follow_symlinks=False)
   if stat.S_ISLNK(before.st_mode):
    links+=1;need(links<=40,'bounded namespace symlink resolution')
    target=os.readlink(part,dir_fd=directory)
    after=os.stat(part,dir_fd=directory,follow_symlinks=False)
    need(identity(before)==identity(after),'stable namespace symlink inode')
    pieces=symlink_parts(target)
    # Normalize against the already-open namespace parent, never Path.resolve.
    base=[]if target.startswith('/')else list(resolved)
    base+=pieces
    pending=base+pending;resolved=[];os.close(directory);directory=os.dup(rootfd);continue
   flags=os.O_RDONLY|os.O_NOFOLLOW
   if pending:flags|=os.O_DIRECTORY
   fd=os.open(part,flags,dir_fd=directory)
   opened=os.fstat(fd)
   if identity(opened)!=identity(before):os.close(fd);raise ValueError('namespace component changed during open')
   if pending:
    if not stat.S_ISDIR(opened.st_mode):os.close(fd);raise ValueError('ordinary namespace parent directory')
    os.close(directory);directory=fd;resolved.append(part)
   else:
    if not(stat.S_ISREG(opened.st_mode)and opened.st_mode&0o111 and opened.st_nlink>0):os.close(fd);raise ValueError('ordinary linked executable file')
    return fd,'/'+('/'.join(resolved+[part]))
  raise ValueError('namespace executable cannot be root')
 finally:os.close(directory)

def file_proof(fd):
 before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and before.st_mode&0o111 and before.st_nlink>0 and
                         0<before.st_size<=MAX_BINARY,'bounded ordinary live executable file')
 os.lseek(fd,0,os.SEEK_SET);h=hashlib.sha256();size=0
 while True:
  b=os.read(fd,65536)
  if not b:break
  size+=len(b);need(size<=MAX_BINARY,'bounded executable stream');h.update(b)
 after=os.fstat(fd);need(identity(before)==identity(after)and size==before.st_size,'stable entire executable bytes and inode')
 return dict(bytes=size,sha256=h.hexdigest(),stat=identity(after))

def namespace_id(proc):
 return dict(pid=os.readlink(proc/'ns/pid'),mnt=os.readlink(proc/'ns/mnt'),root=identity(os.stat(proc/'root')))

def verify(proc,init_proc,expected):
 need(os.name=='posix'and hasattr(os,'O_NOFOLLOW')and expected==PY,'Linux exact source-bound original025 interpreter')
 proc=Path(proc);init_proc=Path(init_proc)
 before=namespace_id(proc);initial=namespace_id(init_proc)
 need(before==initial,'frontend shares actual inspected init PID/mount namespace and root inode')
 target=os.readlink(proc/'exe');guest_parts(target)
 rootfd=os.open(proc/'root',os.O_RDONLY|os.O_DIRECTORY)
 executable=expectedfd=targetfd=None
 try:
  need(identity(os.fstat(rootfd))==before['root'],'pinned actual frontend container root FD')
  executable=os.open(proc/'exe',os.O_RDONLY) # intentional kernel executable magic link
  expectedfd,canonical_expected=root_open(rootfd,expected)
  targetfd,canonical_target=root_open(rootfd,target)
  actual=file_proof(executable);want=file_proof(expectedfd);named=file_proof(targetfd)
  need(actual==want==named,'actual loaded binary equals exact namespace interpreter path and complete hash/inode, not basename')
  # Rewalk after streaming to reject rename/path replacement, not just changed FD.
  again,resolved=root_open(rootfd,expected)
  try:need(file_proof(again)==actual and resolved==canonical_expected,'expected namespace path remains the same live executable')
  finally:os.close(again)
  need(os.readlink(proc/'exe')==target and namespace_id(proc)==before and namespace_id(init_proc)==initial,
       'same executable magic link/namespace/root throughout identity probe')
  return dict(namespace_executable=target,expected_interpreter=expected,canonical_expected=canonical_expected,
              canonical_target=canonical_target,executable=actual,namespaces=before,
              observed_binary_digest=True,pre_registered_binary_digest=False)
 finally:
  for fd in (executable,expectedfd,targetfd,rootfd):
   if fd is not None:os.close(fd)
