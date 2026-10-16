"""Bounded actual output-tree accounting; no guessed zero, no device operations."""
import ast,errno,hashlib,inspect,json,os,stat
from pathlib import Path
LIMIT=12*1024**3
IPC_SOURCE={"network_source":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-adakv029-format-output-v4-execution-20261010-001/IPC_NETWORK_UTILS.py","bytes":11487,"sha256":"83b24f1e0026d1737e036a5abedc2f34ae234df5ccd7f1addab801c3cba55de9"},"environment_source_sha256":"b776fb6b1bae4a4f1d6c53792e65e15bd6cde7e70d5c17ef08dfeec54cd59603","original_source":{"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/MAIN-adakv029-format-output-v4-execution-20261010-001/IPC_SOURCE_011E_ORIGINAL.json","bytes":5140,"sha256":"7ca87f70be47327f8d6dceb45134fa9e0dec406d7f3715c13a2c80d268d135b0"}}
def need(value,why):
 if not value:raise ValueError(why)
def key(value):return (value.st_dev,value.st_ino,stat.S_IFMT(value.st_mode))

def socket_descriptor(value):
 return dict(device=value.st_dev,inode=value.st_ino,mode=value.st_mode,
  size_bytes=value.st_size,allocated_bytes=value.st_blocks*512,
  uid=value.st_uid,gid=value.st_gid,nlink=value.st_nlink,
  rdev=value.st_rdev,mtime_ns=value.st_mtime_ns,ctime_ns=value.st_ctime_ns)
def socket_scope(root,parent):
 root=Path(root);parent=Path(parent)
 need(parent.parent==root and
  parent.resolve()==parent and not parent.is_symlink(),"exact owned IPC output stage")
 return parent
def socket_name(name):
 import uuid
 try:value=uuid.UUID(name)
 except(ValueError,AttributeError):raise ValueError("native IPC basename must be canonical UUID4")
 need(str(value)==name and value.version==4 and value.variant==uuid.RFC_4122,
  "native IPC basename must be canonical UUID4")
 return name

def detail(error,path,operation):
 return dict(path=str(path),operation=operation,type=type(error).__name__,errno=error.errno,
  filename=error.filename,filename2=getattr(error,"filename2",None),str=str(error))
class Scan:
 def __init__(self,root,hook=None,socket_parent=None,ipc_source=None):
  self.root=Path(root);self.hook=hook;self.retired=[];self.entries=0;self.directories=0;self.sockets=[]
  self.socket_parents=[socket_scope(self.root,p)for p in (socket_parent if type(socket_parent)is list else [socket_parent])]if socket_parent is not None else []
  self.ipc_source=ipc_source
  need(self.root.is_absolute()and ".."not in self.root.parts and self.root.resolve()==self.root and
   not self.root.is_symlink(),"ordinary exact output accounting root")
  self.fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  self.identity=key(os.fstat(self.fd))
  try:self.root_guard()
  except BaseException:os.close(self.fd);raise
 def root_guard(self):
  actual=os.stat(self.root,follow_symlinks=False)
  need(key(actual)==self.identity==key(os.fstat(self.fd))and stat.S_ISDIR(actual.st_mode)and
   self.root.resolve()==self.root,"output root dev/inode/type identity changed")
 def strict_absent(self,parent,name,path,known,chain,first):
  need(type(first) is FileNotFoundError and first.errno==errno.ENOENT,"only exact child ENOENT may retire")
  self.root_guard()
  # Every still-visible ancestor is held open and checked by its original
  # actual parent fd. A disappearing ancestor retires that entire subtree.
  for fd,pfd,entry,identity,rel in chain:
   need(key(os.fstat(fd))==identity,"held output directory identity drift")
   try:actual=os.stat(entry,dir_fd=pfd,follow_symlinks=False)
   except FileNotFoundError as error:
    self.strict_absent(pfd,entry,rel,identity,chain[:chain.index((fd,pfd,entry,identity,rel))],error)
    return True
   need(key(actual)==identity,"output ancestor replacement/reuse")
  probes=[]
  for _ in range(2):
   if not self.fence(chain):return True
   self.root_guard()
   try:actual=os.stat(name,dir_fd=parent,follow_symlinks=False)
   except FileNotFoundError as error:
    need(error.errno==errno.ENOENT,"not strict child absence");probes.append(detail(error,path,"child.lstat"))
   else:raise ValueError("disappeared output child reappeared/reused")
  if not self.fence(chain):return True
  self.root_guard()
  self.retired.append(dict(path=str(path),known_identity=list(known)if known else None,
   first=detail(first,path,"enumerated-child"),strict_absence_probes=probes,
   stable_root_identity=list(self.identity),enumeration_retired=True,
   reason="strict ENOENT twice under stable held parent/root; not zero bytes for live unreadable child"))
  need(len(self.retired)<=8192,"bounded output retirement evidence")
  return True
 def fence(self,chain):
  self.root_guard()
  for i,(fd,pfd,name,identity,path)in enumerate(chain):
   need(key(os.fstat(fd))==identity,"output held directory identity")
   try:actual=os.stat(name,dir_fd=pfd,follow_symlinks=False)
   except FileNotFoundError as error:
    self.strict_absent(pfd,name,path,identity,chain[:i],error);return False
   need(key(actual)==identity and stat.S_ISDIR(actual.st_mode),"output directory replacement/reuse/type drift")
  return True
 def socket(self,fd,name,path,value,chain):
  need(self.socket_parents and self.ipc_source==IPC_SOURCE,
   "Unix socket requires source-qualified owned IPC scope")
  parent=(self.root/path).parent
  need(parent in self.socket_parents,"Unix socket outside actual TMPDIR-owned stage")
  socket_name(name)
  before=socket_descriptor(value)
  need(stat.S_ISSOCK(before["mode"])and before["size_bytes"]>=0 and before["allocated_bytes"]>=0 and
   before["nlink"]==1 and before["rdev"]==0,"actual IPC socket filesystem metadata")
  if self.hook:self.hook("socket-observed",self.root/path)
  probes=[]
  for _ in range(2):
   if not self.fence(chain):return 0
   try:actual=os.stat(name,dir_fd=fd,follow_symlinks=False)
   except FileNotFoundError as error:
    prior=len(self.retired);self.strict_absent(fd,name,path,key(value),chain,error)
    if len(self.retired)>prior:self.retired[-1]["known_socket_metadata"]=before
    return 0
   need(socket_descriptor(actual)==before and stat.S_ISSOCK(actual.st_mode),
    "IPC socket replacement/reuse/type or metadata drift")
   probes.append(socket_descriptor(actual))
  self.root_guard()
  row=dict(path=str(path),kind="unix_socket",metadata=before,stable_metadata_probes=probes,
   held_parent_identity=list(key(os.fstat(fd))),stable_root_identity=list(self.identity),
   ipc_source=self.ipc_source,tmpdir_alias="/adakv-results",
   actual_socket_parent=str(parent),opened=False,connected=False,
   charged_size_bytes=before["size_bytes"])
  self.sockets.append(row);need(len(self.sockets)<=8192,"bounded IPC socket metadata evidence")
  return row["charged_size_bytes"]
 def walk(self,fd,relative,chain):
  if not self.fence(chain):return 0
  self.directories+=1;need(self.directories<=131072,"bounded actual output directories")
  total=0
  # fd enumeration does not resolve arbitrary symlink targets. A deleted
  # directory can keep a valid fd: its visible path is separately fenced.
  with os.scandir(fd)as iterator:
   for entry in iterator:
    name=entry.name;need(name not in(".","..")and "/"not in name,"ordinary output child component")
    path=relative/name;self.entries+=1;need(self.entries<=1048576,"bounded actual output entries")
    if self.hook:self.hook("enumerated",self.root/path)
    try:value=os.stat(name,dir_fd=fd,follow_symlinks=False)
    except FileNotFoundError as error:
     self.strict_absent(fd,name,path,None,chain,error);continue
    need(not stat.S_ISLNK(value.st_mode),"output symlink is unsupported, not outside-root accounting")
    identity=key(value)
    if stat.S_ISREG(value.st_mode):
     total+=value.st_size
    elif stat.S_ISDIR(value.st_mode):
     try:child=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
     except FileNotFoundError as error:
      self.strict_absent(fd,name,path,identity,chain,error);continue
     try:
      need(key(os.fstat(child))==identity,"output child replaced between stat/open")
      total+=self.walk(child,path,chain+[(child,fd,name,identity,path)])
     finally:os.close(child)
    elif stat.S_ISSOCK(value.st_mode):total+=self.socket(fd,name,path,value,chain)
    else:raise ValueError("output nonregular/nondirectory child unsupported: "+str(path)+" mode="+oct(value.st_mode))
    need(total<=LIMIT,"joint whole packet32GiB output cap unchanged")
  if not self.fence(chain):return 0
  return total
 def run(self):
  try:
   used=self.walk(self.fd,Path("."),[]);self.root_guard()
   need(0<=used<=LIMIT,"whole output32GiB unchanged")
   return dict(schema="adakv.actual-output-budget-observation/v1",root=str(self.root),
    root_identity=list(self.identity),output_bytes=used,limit_bytes=LIMIT,
    sockets=self.sockets,socket_count=len(self.sockets),socket_charged_size_bytes=sum(r["charged_size_bytes"]for r in self.sockets),
    socket_policy=dict(parents=[str(p)for p in self.socket_parents],ipc_source=self.ipc_source),
    retired=self.retired,entries=self.entries,directories=self.directories,
    live_unreadable_rejected=True,snapshot_not_peak_claim=True)
  finally:os.close(self.fd)
def scan(root,hook=None,socket_parent=None,ipc_source=None):return Scan(root,hook,socket_parent,ipc_source).run()
def consume(value,root):
 need(type(value)is dict and value.get("schema")=="adakv.actual-output-budget-observation/v1"and
  value.get("root")==str(Path(root))and value.get("limit_bytes")==LIMIT,"exact observed output source schema/root/cap")
 need(type(value.get("output_bytes"))is int and 0<=value["output_bytes"]<=LIMIT,"actual output bytes32GiB")
 ident=value.get("root_identity");need(type(ident)is list and len(ident)==3 and all(type(n)is int for n in ident),"actual output root identity")
 need(type(value.get("retired"))is list and len(value["retired"])<=8192,"bounded actual retirement rows")
 for row in value["retired"]:
  need(type(row)is dict and row["stable_root_identity"]==ident and row["enumeration_retired"]is True and len(row["strict_absence_probes"])==2 and
   row["first"]["errno"]==errno.ENOENT and all(p["errno"]==errno.ENOENT for p in row["strict_absence_probes"]),"every child retirement has original+double absence/root fences")

 sockets=value.get("sockets");need(type(sockets)is list and len(sockets)<=8192 and
  value.get("socket_count")==len(sockets),"complete bounded IPC metadata list")
 policy=value.get("socket_policy");need(type(policy)is dict and type(policy.get("parents"))is list and
  len(policy["parents"])==len(set(policy["parents"]))<=8,"IPC socket policy")
 charged=0;paths=set()
 for row in sockets:
  need(type(row)is dict and row.get("kind")=="unix_socket"and row.get("opened")is False and
   row.get("connected")is False and row.get("tmpdir_alias")=="/adakv-results","socket never opened/communicated")
  path=Path(row["path"]);need(not path.is_absolute()and ".."not in path.parts and path not in paths,"unique relative IPC socket path");paths.add(path)
  parent=socket_scope(Path(root),row["actual_socket_parent"])
  need((Path(root)/path).parent==parent and str(parent)in policy["parents"],"actual owned stage socket scope")
  socket_name(path.name)
  meta=row["metadata"];fields={"device","inode","mode","size_bytes","allocated_bytes","uid","gid","nlink","rdev","mtime_ns","ctime_ns"}
  need(type(meta)is dict and set(meta)==fields and all(type(x)is int and x>=0 for x in meta.values())and
   stat.S_ISSOCK(meta["mode"])and meta["nlink"]==1 and meta["rdev"]==0,"actual Unix socket stat metadata")
  need(row["stable_metadata_probes"]==[meta,meta]and row["stable_root_identity"]==ident and
   type(row["held_parent_identity"])is list and len(row["held_parent_identity"])==3 and
   row["held_parent_identity"][2]==stat.S_IFDIR,"socket held-parent and double identity fences")
  need(row["ipc_source"]==policy["ipc_source"]==IPC_SOURCE,"actual source-qualified IPC policy")
  need(type(row["charged_size_bytes"])is int and row["charged_size_bytes"]==meta["size_bytes"],
   "IPC filesystem size charged exactly, not regular file/open or guessed kernel allocation")
  charged+=row["charged_size_bytes"]
 need(type(value.get("socket_charged_size_bytes"))is int and value["socket_charged_size_bytes"]==charged and
  charged<=value["output_bytes"],"complete IPC socket accounting contributes to unchanged32GiB")

 if "source"in value:
  scopes=value.get("actual_controller_IPC_mount_scopes")
  need(type(scopes)is list and len(scopes)<=8 and {r["parent"]for r in scopes}==set(policy["parents"]),
   "all source-qualified Controller stage mounts retained")
  for scope in scopes:
   need(scope["mount"]==[scope["parent"],True]or scope["mount"]==(scope["parent"],True),
    "exact actual RW TMPDIR controller mapping")
   need(type(scope["cid"])is str and len(scope["cid"])==64 and all(x in "0123456789abcdef"for x in scope["cid"])and
    type(scope["parent_identity"])is list and len(scope["parent_identity"])==3 and scope["parent_identity"][2]==stat.S_IFDIR,
    "actual stage CID and directory identity")
   for row in sockets:
    if row["actual_socket_parent"]==scope["parent"]:
     need(row["held_parent_identity"]==scope["parent_identity"],"socket held parent equals registered stage identity")
 return value["output_bytes"]
def install(S,source_ref,expected_safety_sha,writer,opt_in=False):
 need(opt_in is True,"explicit private output observation opt-in")
 path=Path(inspect.getfile(S.Controller));need(hashlib.sha256(path.read_bytes()).hexdigest()==expected_safety_sha,"exact original025 Controller source")
 original=S.Controller;fn=inspect.getsource(original.resources)
 old='used=sum(p.stat().st_size for p in self.out.parent.rglob("*") if p.is_file())'
 need(fn.count(old)==1,"one source-bound original resources expression")
 fn=fn.replace(old,"used=_actual_output_budget(self)")
 # Only the single accounting expression changes. The exact old RAM, CPU,
 # disk-free/reserve/workspace and RSS/admission/engine predicates remain.
 namespace=dict(S.__dict__);scopes={}
 def actual(ctl):
  try:
   ipc=json.loads(Path(source_ref["path"]).read_bytes())["ipc_policy"]
   need(ipc["tmpdir_alias"]==S.environment(ctl.out.name=="cpu-preflight")["TMPDIR"]=="/adakv-results"and
    ipc["basename"]=="canonical_UUID4"and ipc["source"]==IPC_SOURCE and "VLLM_RPC_BASE_PATH"not in S.environment(ctl.out.name=="cpu-preflight"),"source-qualified deployed IPC generation and exact existing TMPDIR")
   root=ctl.out.parent;known=scopes.setdefault(str(root),{})
   expected=getattr(ctl,"expected",None)
   if type(expected)is dict and type(expected.get("cid"))is str and len(expected["cid"])==64 and all(x in "0123456789abcdef"for x in expected["cid"]):
    need(expected["mounts"]["/adakv-results"] in((str(ctl.out),True),[str(ctl.out),True]),
     "actual controller owned RW TMPDIR mount before socket acceptance")
    parent=socket_scope(root,ctl.out);view=dict(parent=str(parent),mount=expected["mounts"]["/adakv-results"],cid=expected["cid"],
     parent_identity=list(key(os.stat(parent,follow_symlinks=False))))
    need(str(parent)not in known or known[str(parent)]==view,"IPC output stage directory/CID identity reused")
    known[str(parent)]=view
    need(len(known)<=8,"bounded exact controller stage mount scopes")
   value=scan(root,socket_parent=[Path(p)for p in known],ipc_source=ipc["source"])
   value["actual_controller_IPC_mount_scopes"]=list(known.values())
  except BaseException as error:
   try:writer(ctl.out/("OUTPUT-BUDGET-FIRST-%d.json"%S.time.time_ns()),dict(source=source_ref,root=str(ctl.out.parent),
    first_exception=repr(error),errno=getattr(error,"errno",None),filename=getattr(error,"filename",None),ready=False))
   except BaseException as secondary:ctl.secondary.append("output budget first-fault capture "+repr(secondary))
   raise
  value["source"]=source_ref
  receipt=writer(ctl.out/("OUTPUT-BUDGET-%d.json"%S.time.time_ns()),value)
  ctl._actual_output_budget_ref=receipt
  return consume(value,ctl.out.parent)
 namespace["_actual_output_budget"]=actual
 import textwrap
 exec(compile(ast.parse(textwrap.dedent(fn)),str(path),"exec"),namespace)
 class Observed(original):pass
 compiled_resources=namespace["resources"]
 def resources(self,initial=False):
  result=compiled_resources(self,initial)
  result["actual_output_budget_ref"]=self._actual_output_budget_ref
  result["actual_output_budget_source"]=source_ref
  return result
 Observed.resources=resources
 Observed._output_budget_source=source_ref
 S.Controller=Observed
 return original

