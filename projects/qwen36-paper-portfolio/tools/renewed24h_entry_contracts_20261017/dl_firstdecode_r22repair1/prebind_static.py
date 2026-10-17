"""Cheap source/ticket closure only. Never reads dependencies or closed raw."""
import hashlib,importlib.util,json,os,stat
from pathlib import Path,PurePosixPath

MARK='__R21_REVIEWED_TEMPLATE_SHA256__'
DECLARATION=dict(schema='deltalog.bound-only-own-file/v021',file='COMMANDS_FINAL.json',spec_file='COMMANDS_SPEC.json',phase='before-closed-input-bind')

def need(v,msg):
 if not v:raise ValueError(msg)

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)

def obj(raw):
 def pairs(values):
  result={}
  for k,v in values:
   need(k not in result,'duplicate JSON key');result[k]=v
  return result
 def constant(value):raise ValueError('nonfinite JSON constant '+value)
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)

def fingerprint(path):
 p=Path(path);before=p.lstat()
 need(stat.S_ISREG(before.st_mode)and not any(x.is_symlink()for x in(p,*p.parents)),'ordinary exact own file')
 h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(131072),b''):h.update(b);size+=len(b)
 after=p.lstat()
 fields=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 need(fields(before)==fields(after)and size==after.st_size,'stable complete own file')
 return dict(bytes=size,sha256=h.hexdigest())

def own_files(m,root):
 root=Path(root);logical=m['root'];need(logical.startswith('/')and '\\'not in logical,'exact POSIX source identity')
 for name,r in m['files'].items():
  n=PurePosixPath(name);need(name==str(n)and not n.is_absolute()and '..'not in n.parts,'ordinary own relative leaf')
  need(set(r)=={'path','bytes','sha256'}and r['path']==logical+'/'+name and fingerprint(root/name)=={k:r[k]for k in('bytes','sha256')},'source-hashed declared own leaf '+name)

def expected_ticket(m,tr,root):
 need(m['command_ticket_declaration']==DECLARATION,'explicit bound-only ticket phase, no guard exception')
 need(tr==dict(path=m['root']+'/SOURCE_TEMPLATE.json',**fingerprint(Path(root)/'SOURCE_TEMPLATE.json')),'exact reviewed template Ref, no self-reference')
 need('COMMANDS_FINAL.json'not in m['files'],'prepared template must not self-pin derived final ticket')
 spec=obj((Path(root)/'COMMANDS_SPEC.json').read_bytes())
 need(set(spec)=={'schema','skeleton'}and spec['schema']=='deltalog.command-ticket-spec/v021','source-owned command spec')
 result=spec['skeleton']
 need(result['template']=={'$reviewed_template_ref':True}and result['bind']['argv'][6]==MARK and result['cheap_prebind']['argv'][6]==MARK,'exact reviewed template substitution seams')
 result['template']=tr;result['bind']['argv'][6]=tr['sha256'];result['cheap_prebind']['argv'][6]=tr['sha256']
 return result

def prepare(m,tr,root,*,runtime):
 root=Path(root)
 need(type(runtime)is bool and m['prepared_only']is True,'prepared phase only; no qualification cache')
 if runtime:need(str(root)==m['root'],'actual binder exact deployed root, no replay alias')
 need(canonical(m)==canonical(obj((root/'SOURCE_TEMPLATE.json').read_bytes())),'actual unchanged template object, not caller-injected declarations')
 own_files(m,root)
 expected=expected_ticket(m,tr,root)
 path=root/'COMMANDS_FINAL.json';before=fingerprint(path);actual=obj(path.read_bytes())
 need(canonical(actual)==canonical(expected),'whole actual final command ticket equals reviewed source spec/template')
 need(fingerprint(path)==before,'same command ticket through parse and whole comparison')
 ticket=dict(path=m['root']+'/COMMANDS_FINAL.json',**before)
 bound=dict(m);bound['files']=dict(m['files']);bound['files']['COMMANDS_FINAL.json']=ticket
 # Load the original guard from its authenticated file, unchanged. No new
 # allowed filename, ignored read or weaker AST resolution rule is introduced.
 p=root/'readset_guard101r8.py';s=importlib.util.spec_from_file_location('_r21_actual_readset_guard',p);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
 guard=g.check(bound,root)
 need(fingerprint(path)==before,'exact final command bytes remain after guard')
 return bound,dict(schema='deltalog.cheap-prebind-own-closure/v021',ticket=ticket,template=tr,own_files=len(bound['files']),guard=guard,physical_source_root=str(root),source_root_alias_is_preparation_only=str(root)!=m['root'],external_dependency_reads=False,closed_raw_reads=False,NPU=False,resources_admitted=False,qualified=False)

def bind(O,m,tr,root):
 bound,report=prepare(m,tr,root,runtime=True)
 O.obj_file(report['ticket'])
 m['files']=bound['files'];m['command_ticket_binding']=report
 return report
