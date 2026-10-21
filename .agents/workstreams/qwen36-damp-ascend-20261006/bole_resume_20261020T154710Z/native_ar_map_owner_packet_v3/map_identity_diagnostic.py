"""Default-OFF complete CPU mapping observation; never numerical qualification."""
import argparse,hashlib,importlib,importlib.util,json,os,re,stat,sys,time,traceback
from pathlib import Path
SCHEMA='bole.native-ar-map-identity-diagnostic-inputs/v1';REPORT='bole.native-ar-map-identity-diagnostic/v1'
MIB=2**20;RAW_CAP=4*MIB;TOTAL_CAP=64*MIB;RESERVE=MIB;MAP_CAP=1024
OPTIN='BOLE_NATIVE_AR_MAP_DIAGNOSTIC_ENABLE';PROC_READS=[]
class DiagnosticError(Exception):pass
def need(ok,text):
 if not ok:raise DiagnosticError(text)
def no_duplicates(pairs):
 out={}
 for key,value in pairs:need(key not in out,'duplicate JSON key: '+str(key));out[key]=value
 return out
def decode_json(data):return json.loads(data,object_pairs_hook=no_duplicates)
def encoded(value):return(json.dumps(value,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':'))+'\n').encode('ascii')
def ref3(value):
 need(type(value)is dict and set(value)=={'path','bytes','sha256'},'exact Ref3')
 need(type(value['path'])is str and value['path'].startswith('/')and '\x00'not in value['path'],'absolute Ref3 path')
 need(type(value['bytes'])is int and value['bytes']>=0,'Ref3 byte count')
 need(type(value['sha256'])is str and re.fullmatch('[0-9a-f]{64}',value['sha256'])is not None,'Ref3 whole SHA256');return value
def stat_value(s):
 return dict(device=s.st_dev,major=os.major(s.st_dev),minor=os.minor(s.st_dev),inode=s.st_ino,mode=s.st_mode,size=s.st_size,nlink=s.st_nlink,uid=s.st_uid,gid=s.st_gid,rdev=s.st_rdev,atime_ns=s.st_atime_ns,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,blocks=getattr(s,'st_blocks',None),blksize=getattr(s,'st_blksize',None))
def stable_value(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def exception_value(exc):
 return dict(type=type(exc).__module__+'.'+type(exc).__qualname__,message=str(exc),repr=repr(exc),errno=getattr(exc,'errno',None),strerror=getattr(exc,'strerror',None),filename=getattr(exc,'filename',None),filename2=getattr(exc,'filename2',None),traceback=traceback.format_exc())
def observe(fn):
 began=time.monotonic()
 try:return dict(completed=True,value=fn(),seconds=time.monotonic()-began)
 except Exception as exc:return dict(completed=False,error=exception_value(exc),seconds=time.monotonic()-began)
class Budget:
 def __init__(self,start):self.start=start
 def check(self):need(time.monotonic()-self.start<600,'600-second child cold deadline')
class Journal:
 def __init__(self,root,budget):
  self.root=Path(root);need(self.root.is_absolute()and not self.root.exists(),'new diagnostic output leaf must be absent');need(self.root.parent.is_dir(),'original owned RW parent exists')
  for p in(self.root.parent,)+tuple(self.root.parent.parents):need(not p.is_symlink(),'ordinary diagnostic output parents')
  self.root.mkdir(mode=0o700);self.budget=budget;self.total=0;self.refs={};self.stream=None;self.stream_hash=hashlib.sha256();self.stream_bytes=0
 def charge(self,n,final=False):
  if not final:self.budget.check()
  limit=TOTAL_CAP if final else TOTAL_CAP-RESERVE;need(self.total+n<=limit,'64-MiB complete-metadata cap; no sampling');self.total+=n
 def save(self,name,data,final=False):
  need('/'not in name and name not in self.refs,'unique output filename');self.charge(len(data),final=final);path=self.root/name
  with path.open('xb')as f:f.write(data)
  result=dict(path=str(path),bytes=len(data),sha256=hashlib.sha256(data).hexdigest());self.refs[name]=result;return result
 def obj(self,name,value,final=False):return self.save(name,encoded(value),final=final)
 def begin_maps(self):self.stream=(self.root/'EXECUTABLE-MAPPINGS.jsonl').open('xb')
 def map_row(self,value):
  data=encoded(value);self.charge(len(data));self.stream.write(data);self.stream_hash.update(data);self.stream_bytes+=len(data);self.stream.flush()
 def end_maps(self):
  if self.stream is not None:
   self.stream.close();self.stream=None;self.refs['EXECUTABLE-MAPPINGS.jsonl']=dict(path=str(self.root/'EXECUTABLE-MAPPINGS.jsonl'),bytes=self.stream_bytes,sha256=self.stream_hash.hexdigest())
def hash_file(path,budget):
 budget.check();p=Path(path);before=p.stat();need(stat.S_ISREG(before.st_mode),'regular source/reference file: '+str(p));digest=hashlib.sha256();size=0
 with p.open('rb')as f:
  opened=os.fstat(f.fileno());need(stable_value(opened)==stable_value(before),'opened source identity')
  while True:
   budget.check();data=f.read(MIB)
   if not data:break
   digest.update(data);size+=len(data)
  finished=os.fstat(f.fileno())
 after=p.stat();need(stable_value(before)==stable_value(finished)==stable_value(after)and size==after.st_size,'whole source stable while hashing: '+str(p))
 return dict(path=str(p),bytes=size,sha256=digest.hexdigest())
def checked(ref,budget):
 ref3(ref);actual=hash_file(ref['path'],budget);need(actual==ref,'exact Ref3 before use: '+ref['path']);return actual
def read_ref_json(ref,budget):
 checked(ref,budget);need(ref['bytes']<=RAW_CAP,'bounded diagnostic binding JSON');data=Path(ref['path']).read_bytes();need(len(data)==ref['bytes']and hashlib.sha256(data).hexdigest()==ref['sha256'],'binding re-open exact bytes');return decode_json(data)
def raw_file(path,budget):
 budget.check();fd=os.open(path,os.O_RDONLY|os.O_CLOEXEC);chunks=[];lengths=[];size=0;began=time.monotonic()
 try:
  while True:
   budget.check();data=os.read(fd,RAW_CAP-size+1);lengths.append(len(data))
   if not data:break
   size+=len(data);need(size<=RAW_CAP,'4-MiB complete raw proc cap: '+path);chunks.append(data)
 finally:
  os.close(fd);PROC_READS.append(dict(path=path,read_lengths=lengths,bytes_read=size,seconds=time.monotonic()-began,atomic_snapshot_claim=False))
 return b''.join(chunks)
def module_file(module):
 path=getattr(module,'__file__',None);need(type(path)is str,'module has exact file identity');return os.path.abspath(path)
def import_context(y,budget):
 records=[]
 for item in y['imports']:
  budget.check();need(type(item)is dict and set(item)=={'kind','name','ref'},'exact ordered import declaration');ref=ref3(item['ref']);name=item['name']
  need(type(name)is str and name and all(part.isidentifier()for part in name.split('.')),'declared import name');checked(ref,budget)
  if item['kind']=='module':module=importlib.import_module(name)
  else:
   need(item['kind']=='file'and name not in sys.modules,'new exact private source module name');spec=importlib.util.spec_from_file_location(name,ref['path']);need(spec is not None and spec.loader is not None,'exact source loader');module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
  need(module_file(module)==ref['path'],'import module full path identity: '+name);checked(ref,budget);records.append(dict(name=name,kind=item['kind'],ref=ref))
 need('torch'in sys.modules and 'torch_npu'in sys.modules,'actual Torch and TorchNPU imported in declared context')
 torch=sys.modules['torch'];torch.set_num_threads(1);torch.set_num_interop_threads(1);return records
def path_observation(path):return dict(path=path,lstat=observe(lambda:stat_value(os.lstat(path))),readlink=observe(lambda:os.readlink(path)),stat=observe(lambda:stat_value(os.stat(path))))
def observation_value(value):return value['value']if value.get('completed')is True else None
def identity_equal(parsed,observed):
 s=observation_value(observed)
 if parsed is None or s is None:return None
 return(parsed['major'],parsed['minor'],parsed['inode'])==(s['major'],s['minor'],s['inode'])
def parse_map(row):
 parts=row.split(maxsplit=5);need(len(parts)>=5,'complete observed proc maps row');need(re.fullmatch('[0-9a-f]+-[0-9a-f]+',parts[0])is not None,'observed proc range syntax')
 first,last=(int(x,16)for x in parts[0].split('-'));need(first<last and len(parts[1])==4,'observed mapping range/perms');major,minor=parts[3].split(':')
 return dict(range=parts[0],start=first,end=last,permissions=parts[1],offset=int(parts[2],16),major=int(major,16),minor=int(minor,16),inode=int(parts[4]),path=parts[5]if len(parts)==6 else None)
def diagnostic_row(row,index,L,budget):
 budget.check();parsed_result=observe(lambda:parse_map(row));result=dict(index=index,raw=row,parsed=parsed_result,pathname_hash_proves_mapped_identity=False,mapped_file_identity_qualified=False);parsed=observation_value(parsed_result)
 if parsed is None:result['unresolved_reason']='actual malformed maps row; full raw retained';return result
 map_file='/proc/self/map_files/'+parsed['range'];result['map_file']=path_observation(map_file);name=parsed['path'];result['original_special_skip']=name in('[vdso]','[vsyscall]');literal=type(name)is str and name.startswith('/')
 if literal:
  result['pathname']=path_observation(name);ordinary=not name.endswith(' (deleted)')and '\\'not in name;result['ordinary_literal_path']=ordinary
  if ordinary:
   canonical=observe(lambda:str(Path(name).resolve(strict=True)));result['canonical_resolution']=canonical;path=observation_value(canonical)
   if path is not None:
    result['canonical_path']=path_observation(path);budget.check();result['canonical_original_fingerprint']=observe(lambda:L.fingerprint(path));budget.check()
  else:result['canonical_not_attempted']='deleted/escaped literal retained without rewriting'
 else:result['pathname_not_attempted']='anonymous or special mapping retained without inventing a path'
 result['maps_equals_map_file_stat']=identity_equal(parsed,result['map_file']['stat'])
 if 'pathname'in result:result['maps_equals_literal_path_stat']=identity_equal(parsed,result['pathname']['stat'])
 if 'canonical_path'in result:
  result['maps_equals_canonical_path_stat']=identity_equal(parsed,result['canonical_path']['stat']);first=observation_value(result['canonical_path']['stat']);second=observation_value(result['map_file']['stat'])
  result['canonical_equals_map_file_stat_identity']=None if first is None or second is None else(first['device'],first['inode'])==(second['device'],second['inode'])
 return result
def collect_refs(y,inputs_ref):
 values=[inputs_ref]+list(y['files'].values())+list(y['source_refs']);values+=[item['ref']for item in y['imports']]
 for item in y['known_files']:
  need(type(item)is dict and set(item)=={'alias_ref','canonical_ref','ELF'},'exact known file declaration');values.append(item['alias_ref'])
  if item['canonical_ref']is not None:values.append(item['canonical_ref'])
 refs={}
 for value in values:
  ref3(value);need(value['path']not in refs or refs[value['path']]==value,'one exact Ref3 per declared path');refs[value['path']]=value
 need(len(refs)<=16384,'bounded declared source/reference readset');return refs
def validate_binding(y):
 keys={'schema','default_enabled','diagnostic_seconds','files','imports','library_name','sys_path','source_refs','known_files','output_dir'}
 need(type(y)is dict and set(y)==keys,'exact diagnostic binding fields');need(y['schema']==SCHEMA and y['default_enabled']is False and type(y['diagnostic_seconds'])is int and y['diagnostic_seconds']==600,'explicit default-OFF finite diagnostic binding')
 need(type(y['files'])is dict and set(y['files'])=={'diagnostic','library_maps','metadata_cpu'},'exact original sources and diagnostic identity')
 need(type(y['imports'])is list and 2<=len(y['imports'])<=256,'bounded actual metadata import sequence')
 need(type(y['source_refs'])is list and type(y['known_files'])is list and len(y['known_files'])<=16384,'declared full source/reference lists')
 need(type(y['sys_path'])is list and len(y['sys_path'])<=32 and all(type(p)is str and Path(p).is_absolute()and Path(p).is_dir()for p in y['sys_path']),'exact declared metadata import roots')
 need(type(y['library_name'])is str,'declared original library_maps module name');names=[item.get('name')for item in y['imports']if type(item)is dict]
 need(len(names)==len(y['imports'])and len(set(names))==len(names),'one declaration per imported context module')
 need('torch'in names and 'torch_npu'in names and names.index('torch')<names.index('torch_npu'),'source-bound Torch then TorchNPU import order')
 library_items=[item for item in y['imports']if item['name']==y['library_name']]
 need(len(library_items)==1 and library_items[0]['ref']==y['files']['library_maps'],'original library_maps exact module/ref join')
def collect(y,inputs_ref,budget,journal,summary):
 refs=collect_refs(y,inputs_ref);summary['source_before']={path:checked(ref,budget)for path,ref in refs.items()}
 need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')=='','CPU child empty Ascend visibility');need(os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0','original CPU import autoload guard');need(os.sched_getaffinity(0)=={0},'actual original025 CPU0 affinity');need(not list(Path('/dev').glob('davinci[0-9]*')),'no numbered NPU device in this child')
 sys.path[:0]=y['sys_path'];imports=import_context(y,budget)
 journal.obj('IMPORT-CONTEXT.json',dict(imports=imports,sys_path=list(sys.path),metadata_cpu_source=y['files']['metadata_cpu'],metadata_cpu_run_called=False,original_128_math_replayed=False,original_owner_admission_replaced=False,source_declared_import_context_only=True))
 L=sys.modules[y['library_name']];need(module_file(L)==y['files']['library_maps']['path'],'actual original L source path')
 functions={name:value for name,value in vars(L).items()if getattr(value,'__code__',None)is not None and value.__globals__ is vars(L)}
 need(all(name in functions for name in('executable_paths','inventory','fingerprint')),'unchanged original mapping functions available')
 journal.obj('PROCESS.json',dict(pid=os.getpid(),ppid=os.getppid(),uname=list(os.uname()),affinity=sorted(os.sched_getaffinity(0)),namespace_links={name:observe(lambda name=name:os.readlink('/proc/self/ns/'+name))for name in('mnt','user','pid')},qualification=False,actual_npu_operator_called=False))
 for path,output in(('/proc/version','PROC-VERSION.txt'),('/proc/self/status','PROC-STATUS.txt'),('/proc/self/cgroup','PROC-CGROUP.txt')):journal.save(output,raw_file(path,budget))
 maps=raw_file('/proc/self/maps',budget);journal.save('PROC-MAPS-BEFORE.txt',maps);journal.save('PROC-MOUNTINFO-BEFORE.txt',raw_file('/proc/self/mountinfo',budget));text=maps.decode('utf-8',errors='surrogateescape')
 budget.check();original_paths=observe(lambda:L.executable_paths(text));budget.check();journal.obj('ORIGINAL-EXECUTABLE-PATHS.json',original_paths)
 original_inventory=observe(lambda:L.inventory());budget.check();journal.obj('ORIGINAL-INVENTORY.json',original_inventory)
 summary['original_executable_paths_completed']=original_paths['completed'];summary['original_inventory_completed']=original_inventory['completed'];summary['original_exception_is_not_a_pass']=True
 executable=[];malformed=[]
 for index,row in enumerate(text.splitlines()):
  parts=row.split(maxsplit=5)
  if len(parts)<5:malformed.append(dict(index=index,raw=row,error='malformed row cannot be classified safely'))
  elif 'x'in parts[1]:executable.append((index,row))
 summary['raw_maps_rows']=len(text.splitlines());summary['executable_rows_observed']=len(executable);journal.obj('MALFORMED-ROWS.json',malformed)
 need(not malformed,'all raw maps rows classified; malformed rows retained');need(0<len(executable)<=MAP_CAP,'all executable mappings bounded to1024; no sampling');journal.begin_maps();summary['executable_rows_processed']=0
 for index,row in executable:
  result=diagnostic_row(row,index,L,budget);journal.map_row(result);summary['executable_rows_processed']+=1
 journal.end_maps();known=[]
 for item in y['known_files']:
  budget.check();alias=item['alias_ref'];actual_alias=checked(alias,budget);resolved=observe(lambda alias=alias:str(Path(alias['path']).resolve(strict=True)))
  entry=dict(alias_ref=alias,actual_alias_ref=actual_alias,resolution=resolved,static_installation_evidence_only=True,mapped_file_identity_qualified=False);canonical=observation_value(resolved)
  if canonical is not None:
   fingerprint=observe(lambda canonical=canonical:L.fingerprint(canonical));entry['original_fingerprint']=fingerprint;actual=observation_value(fingerprint)
   if actual is not None:
    expected=item['canonical_ref'];entry['canonical_ref_equal']=None if expected is None else actual['ref']==expected;entry['ELF_equal']=None if item['ELF']is None else actual['ELF']==item['ELF']
    need(expected is None or actual['ref']==expected,'declared canonical full Ref3 changed: '+canonical);need(item['ELF']is None or actual['ELF']==item['ELF'],'declared ELF/buildID changed: '+canonical)
  known.append(entry)
 journal.obj('KNOWN-SOURCE-CANONICAL-JOIN.json',known);journal.save('PROC-MAPS-AFTER.txt',raw_file('/proc/self/maps',budget));journal.save('PROC-MOUNTINFO-AFTER.txt',raw_file('/proc/self/mountinfo',budget))
 need(all(vars(L).get(name)is fn and fn.__globals__ is vars(L)for name,fn in functions.items()),'all original L function objects/globals unchanged')
 summary['original_function_objects_unchanged']=True;summary['source_after']={path:checked(ref,budget)for path,ref in refs.items()};need(summary['source_before']==summary['source_after'],'complete declared source before/after equal')
 summary['source_unchanged']=True;summary['diagnostic_completed']=True;summary['complete_requested_mapping_observation_attempts']=summary['executable_rows_processed']==summary['executable_rows_observed']
def main():
 start=time.monotonic();parser=argparse.ArgumentParser(description=__doc__,allow_abbrev=False);parser.add_argument('--diagnose',action='store_true');parser.add_argument('--inputs-ref');args=parser.parse_args()
 if not args.diagnose:print(json.dumps(dict(schema=REPORT,enabled=False,executed=False)));return 0
 journal=None;budget=Budget(start);summary=dict(schema=REPORT,diagnostic_completed=False,original_owner_admission_replaced=False,original_metadata_run_replayed=False,original_128_math_replayed=False,actual_npu_operator_called=False,mapped_file_identity_qualified=False,native_FA_math_pass=False,model_qualified=False,common_plugin_effects_pass=False,formal_performance_pass=False,atomic_proc_snapshot_claim=False,sampled_or_filtered_mapping_set=False,old_failure_reclassified_as_numerical=False);code=3
 try:
  need(os.environ.get(OPTIN)=='1','explicit CPU diagnostic opt-in');need(args.inputs_ref is not None,'exact diagnostic binding Ref3 required');inputs_ref=ref3(decode_json(args.inputs_ref));y=read_ref_json(inputs_ref,budget);validate_binding(y)
  need(y['files']['diagnostic']['path']==os.path.abspath(__file__),'executed diagnostic full source path identity');checked(y['files']['diagnostic'],budget);journal=Journal(y['output_dir'],budget);summary['inputs_ref']=inputs_ref;collect(y,inputs_ref,budget,journal,summary);code=0
 except Exception as exc:summary['failure']=exception_value(exc)
 finally:
  summary['elapsed_seconds']=time.monotonic()-start;summary['proc_read_observations']=list(PROC_READS)
  if journal is not None:
   journal.end_maps();summary['artifacts']=dict(journal.refs);summary['artifact_bytes_before_report']=journal.total
   try:
    report_ref=journal.obj('MAP-IDENTITY-DIAGNOSTIC.json',summary,final=True);print(json.dumps(dict(schema=REPORT,report_ref=report_ref,diagnostic_completed=summary['diagnostic_completed'],qualification=False),sort_keys=True))
   except Exception as exc:print(json.dumps(dict(schema=REPORT,diagnostic_completed=False,qualification=False,final_write_error=exception_value(exc)),ensure_ascii=True,sort_keys=True),file=sys.stderr);code=3
  else:print(json.dumps(summary,ensure_ascii=True,sort_keys=True),file=sys.stderr)
 return code
if __name__=='__main__':raise SystemExit(main())
