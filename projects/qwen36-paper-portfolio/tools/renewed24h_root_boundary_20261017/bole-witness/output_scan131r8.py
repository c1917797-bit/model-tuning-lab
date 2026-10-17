"""Complete original output accounting with bounded whole-tree ENOENT retry.

This is a sampled complete traversal, NOT an atomic filesystem snapshot.
No missing path is skipped; a retry discards the entire partial sum.
"""
import ast,errno,hashlib,json,os,stat,time,traceback
from pathlib import Path
ORIGINAL=(22338,'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30')
EXPRESSION='sum(p.stat().st_size for p in self.out.parent.rglob("*") if p.is_file())'
REPLACEMENT='_SCAN_BUDGET.used(self)'

def need(v,message):
 if not v:raise ValueError(message)

def derive(raw):
 need((len(raw),hashlib.sha256(raw).hexdigest())==ORIGINAL,'exact original025 safety source')
 text=raw.decode('utf8');need(text.count(EXPRESSION)==1,'unique original full output sum')
 result=text.replace(EXPRESSION,REPLACEMENT)
 need(result.count(REPLACEMENT)==1 and result.replace(REPLACEMENT,EXPRESSION)==text,'whole safety inverse, only output scan expression')
 return result

def root_identity(root):
 s=root.lstat();need(stat.S_ISDIR(s.st_mode)and not any(p.is_symlink()for p in(root,*root.parents)),'ordinary exact output root')
 return (s.st_dev,s.st_ino)

class Scanner:
 def __init__(self,root):
  self.root=Path(root);need(self.root.is_absolute(),'exact absolute registered output root')
  # host load() precedes its original exclusive output mkdir. Never touch or create it here.
  self.identity=None
 def full_tree(self,end):
  total=0;files=0;pending=[self.root]
  while pending:
   need(time.monotonic()<end,'whole scan <=1s within original remaining')
   with os.scandir(pending.pop())as entries:
    for entry in entries:
     need(time.monotonic()<end,'whole scan <=1s within original remaining')
     info=entry.stat(follow_symlinks=False) # Unlike is_file(), ENOENT is never swallowed.
     if stat.S_ISDIR(info.st_mode):pending.append(Path(entry.path))
     elif stat.S_ISREG(info.st_mode):total+=info.st_size;files+=1
     elif stat.S_ISLNK(info.st_mode):
      target=entry.stat(follow_symlinks=True)
      # Preserve original rglob static-tree semantics: count file links, do not descend directory links.
      if stat.S_ISREG(target.st_mode):total+=target.st_size;files+=1
  return total,files
 def journal(self,ctl,row):
  path=ctl.out/'OUTPUT-SCAN-RACES.jsonl';payload=(json.dumps(row,sort_keys=True,allow_nan=False)+'\n').encode()
  prior=getattr(ctl,'_output_scan_journal_bytes',0);need(prior+len(payload)<=65536,'bounded64KiB race journal; never truncate evidence')
  flags=os.O_WRONLY|os.O_APPEND|os.O_CREAT|getattr(os,'O_NOFOLLOW',0)
  if prior==0:flags|=os.O_EXCL
  else:need(path.is_file()and not path.is_symlink()and path.stat().st_size==prior,'unchanged exact journal')
  fd=os.open(path,flags,0o600)
  try:
   actual=os.fstat(fd);identity=(actual.st_dev,actual.st_ino)
   need(stat.S_ISREG(actual.st_mode)and actual.st_size==prior and actual.st_nlink==1,'exact ordinary append-only journal descriptor')
   need(prior==0 or identity==ctl._output_scan_journal_identity,'same journal inode')
   with os.fdopen(fd,'ab',closefd=False)as f:f.write(payload);f.flush();os.fsync(f.fileno())
  finally:os.close(fd)
  if prior==0:
   directory=os.open(ctl.out,os.O_RDONLY)
   try:os.fsync(directory)
   finally:os.close(directory)
  ctl._output_scan_journal_bytes=prior+len(payload);ctl._output_scan_journal_identity=identity
 def used(self,ctl):
  started=time.monotonic();end=started+min(1.,ctl.remaining(cap=1.));races=[]
  need(ctl.out.parent==self.root,'exact registered output root')
  actual=root_identity(self.root)
  if self.identity is None:self.identity=actual # First real used() after the original fresh-root mkdir.
  need(actual==self.identity,'first-pinned ordinary output root unchanged')
  for attempt in range(1,4):
   need(time.monotonic()<end and root_identity(self.root)==self.identity,'bounded scan deadline/root identity')
   try:
    total,files=self.full_tree(end)
   except FileNotFoundError as error:
    missing=Path(error.filename)if isinstance(error.filename,str)else None
    need(error.errno==errno.ENOENT and missing is not None and missing.is_absolute()and missing!=self.root and missing.is_relative_to(self.root)and '..'not in missing.parts and root_identity(self.root)==self.identity,'only exact inside-root ENOENT may restart full scan')
    row=dict(schema='bole.output-scan-race/v131r8',root=str(self.root),root_identity=list(self.identity),attempt=attempt,error_type=type(error).__name__,error=repr(error),traceback=traceback.format_exc(),errno=error.errno,filename=error.filename,elapsed=time.monotonic()-started,partial_sum_discarded=True,atomic_snapshot=False)
    self.journal(ctl,row);races.append(row)
    if attempt==3 or time.monotonic()>=end:raise
    continue
   need(root_identity(self.root)==self.identity and time.monotonic()<=end,'complete scan within bound and same root')
   ctl._output_scan_last=dict(schema='bole.complete-output-scan/v131r8',root=str(self.root),attempts=attempt,files=files,output_bytes=total,elapsed=time.monotonic()-started,atomic_snapshot=False,complete_entry_stat_traversal=True,races=len(races))
   return total
  raise AssertionError('unreachable scan termination')

def install(c,S,root):
 raw=Path(S.__file__).read_bytes();text=derive(raw)
 original=S.Controller.resources
 need(original.__globals__ is S.__dict__ and original.__code__.co_filename==str(S.__file__)and original.__name__=='resources','only actual unwrapped025 resources')
 tree=ast.parse(text);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller');nodes=[n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='resources'];need(len(nodes)==1,'one original resources method')
 S._SCAN_BUDGET=Scanner(root);scope=S.__dict__;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(S.__file__)+'#output-scan131r8','exec'),scope);patched=scope.pop('resources')
 def resources(self,initial=False):
  value=patched(self,initial);return dict(value,output_scan=self._output_scan_last)
 S.Controller.resources=resources
 return dict(original_safety_ref=dict(path=str(S.__file__),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),full_tree_retry_attempts=3,total_seconds=1,original_time_and_output_limits_unchanged=True,atomic_snapshot=False)
