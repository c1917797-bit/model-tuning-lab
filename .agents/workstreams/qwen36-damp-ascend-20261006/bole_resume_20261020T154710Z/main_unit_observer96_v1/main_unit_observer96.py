"""Default-OFF complete read-only unit observer. Never starts/stops/resets units."""
import argparse,hashlib,json,math,os,re,selectors,stat,subprocess,sys,time
from pathlib import Path
COLD=time.monotonic();MAX_UNITS=96;DISCOVERY_CAP=1<<20;AGGREGATE_CAP=4<<20;FINAL_RESERVE=256<<10;REF_CAP=8<<20;PHASE=300.;CALL_SECONDS=10.
SYSTEMCTL='/usr/bin/systemctl';DISCOVERY_ARGV=[SYSTEMCTL,'list-units','--all','--type=service','--plain','--no-legend','bole-*']
PROPERTIES=('Id','LoadState','ActiveState','SubState','MainPID','ControlPID','Job','ControlGroup','ExecStart','FragmentPath','RemainAfterExit','TasksCurrent','Result','ExecMainPID','ExecMainCode','ExecMainStatus','ExecMainStartTimestampMonotonic','ExecMainExitTimestampMonotonic','StateChangeTimestampMonotonic','ActiveEnterTimestampMonotonic','InactiveEnterTimestampMonotonic')
UNIT=re.compile(r'bole-[A-Za-z0-9_.@:-]+\.service\Z');REF_SHA=re.compile(r'[0-9a-f]{64}\Z')
BASE_HISTORY=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/MAIN_COMPLETE_UNIT_PRE_AR_V2.json',bytes=57779,sha256='916897188ca4400eff0a14822b9de919370d63b8722e5069b2c526c9175ba9b6')
KNOWN_CURRENT=('bole-native-ar-fia-20261020t154710z-v2.service','bole-g2-v13-cpu-20261020t154710z.service','bole-g2-v13-model-20261020t154710z.service')
SCHEMA='bole.readonly-complete-MAIN-unit-observation/v1'
OBS_KEYS=set(('schema observed_epoch observed_monotonic actual_pid actual_start_ticks source_ref history_refs known_units history_unit_names discovery_receipt_ref discovered_unit_names unit_names unit_count rows history_missing_from_discovery source_input_before source_input_after all_remaining_PIDs_zero all_units_quiescent observation_complete actual_entry_sources_complete source_input_equal resource_admitted submission_execution_proven historical_submission_role whole_MAIN_lock_proven limits unit_observation_semantics').split())
def need(ok,message):
 if not ok:raise ValueError(message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()+b'\n'
def parse_json(raw):
 def pairs(items):
  result={}
  for key,value in items:need(key not in result,'duplicate JSON key');result[key]=value
  return result
 def bad(value):raise ValueError('nonfinite JSON: '+value)
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def unit_name(value):need(type(value)is str and UNIT.fullmatch(value),'exact nonwildcard bole service');return value
def name_set(values):
 need(type(values)is list,'complete explicit unit list');result=[unit_name(v)for v in values];need(len(result)==len(set(result)),'duplicate unit');need(len(result)<=MAX_UNITS,'more than96 units; never truncate or expand');return set(result)
def ordinary_directory(path):
 p=Path(path);need(p.is_absolute()and '..'not in p.parts,'ordinary absolute directory');fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in p.parts[1:]:nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
  return fd
 except BaseException:os.close(fd);raise
def whole_file(path,cap=REF_CAP,body=False):
 p=Path(path);need(p.is_absolute()and '..'not in p.parts and p.name,'ordinary exact file');parent=ordinary_directory(p.parent);fd=None
 try:
  fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent);before=os.fstat(fd);need(stat.S_ISREG(before.st_mode)and 0<=before.st_size<=cap,'bounded regular whole file, no symlink');digest=hashlib.sha256();pieces=[];count=0
  while True:
   part=os.read(fd,min(1<<20,cap+1-count))
   if not part:break
   count+=len(part);need(count<=cap,'whole file exceeds fixed capacity');digest.update(part)
   if body:pieces.append(part)
  after=os.fstat(fd);named=os.stat(p.name,dir_fd=parent,follow_symlinks=False)
  def identity(v):return(v.st_dev,v.st_ino,v.st_size,v.st_mtime_ns,v.st_ctime_ns)
  need(identity(before)==identity(after)==identity(named)and count==after.st_size,'stable whole file identity')
  return dict(path=str(p),bytes=count,sha256=digest.hexdigest()),b''.join(pieces)if body else None
 finally:
  if fd is not None:os.close(fd)
  os.close(parent)
def strict_ref(reference):
 need(type(reference)is dict and set(reference)=={'path','bytes','sha256'}and type(reference['bytes'])is int and reference['bytes']>=0 and type(reference['sha256'])is str and REF_SHA.fullmatch(reference['sha256']),'complete exact Ref3');return reference
def checked(reference,*,body=False,cap=REF_CAP):
 strict_ref(reference);actual,raw=whole_file(reference['path'],cap=cap,body=body);need(actual==reference,'whole Ref3 mismatch');return raw
def discovery_names(text):
 need(type(text)is str and len(text.encode())<=DISCOVERY_CAP,'complete discovery within1MiB');names=[]
 for line in text.splitlines():
  if not line.strip():continue
  fields=line.split(None,4);need(len(fields)>=4,'complete list-units row, no legend/sampling');names.append(unit_name(fields[0]))
 return name_set(names)
def properties(text,unit):
 result={}
 for line in text.splitlines():
  need('='in line,'complete systemctl property line');key,value=line.split('=',1);need(key in PROPERTIES and key not in result,'only unique requested properties');result[key]=value
 need(set(result)==set(PROPERTIES)and result['Id']==unit,'all exact requested properties and actual Id');return result
def state(props):
 for key in('MainPID','ControlPID'):need(re.fullmatch(r'[0-9]+',props[key]),'actual numeric '+key)
 main=int(props['MainPID']);control=int(props['ControlPID']);inactive=props['ActiveState']in{'inactive','failed'}and props['SubState']in{'dead','failed'};exited=props['ActiveState']=='active'and props['SubState']=='exited'and props['RemainAfterExit']=='yes'
 absent_tasks=props['TasksCurrent']in{'[not set]','18446744073709551615','infinity',''}and not props['ControlGroup']
 quiet=props['LoadState']in{'loaded','not-found'}and(inactive or exited)and main==0 and control==0 and props['Job']in{'','0'}and(props['TasksCurrent']=='0'or absent_tasks)
 if props['LoadState']=='not-found':quiet=quiet and props['ActiveState']=='inactive'and props['SubState']=='dead'
 return dict(MainPID=main,ControlPID=control,LoadState=props['LoadState'],ActiveState=props['ActiveState'],SubState=props['SubState'],Job=props['Job'],TasksCurrent=props['TasksCurrent'],ControlGroup=props['ControlGroup'],RemainAfterExit=props['RemainAfterExit'],quiescent=bool(quiet))
def entry_path(execstart):
 need(type(execstart)is str and execstart.count('argv[]=')==1,'one actual ExecStart argv display; ambiguous entry rejected');display=execstart.split('argv[]=',1)[1];end=display.find(' ; ignore_errors=')
 if end<0:end=display.find('; ignore_errors=')
 need(end>=0,'exact systemd argv-display boundary');display=display[:end];candidates=re.findall(r'''(?<!\S)(/[^\s;{}'"\\]+\.py)(?=\s|$)''',display);need(len(candidates)==1,'one ordinary absolute Python entry token, no basename guess');return candidates[0],hashlib.sha256(display.encode()).hexdigest()
class Output:
 def __init__(self,path):
  self.path=Path(path);need(self.path.is_absolute()and self.path.name and '..'not in self.path.parts,'new absolute exclusive output leaf');parent=ordinary_directory(self.path.parent)
  try:os.mkdir(self.path.name,0o700,dir_fd=parent);self.fd=os.open(self.path.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent);os.fsync(parent)
  finally:os.close(parent)
  self.used=0;self.refs=[]
 def remaining(self,final=False):return(AGGREGATE_CAP if final else AGGREGATE_CAP-FINAL_RESERVE)-self.used
 def write(self,name,value,final=False):
  need('/'not in name and name not in{'','.','..'},'explicit output filename');raw=canonical(value);need(len(raw)<=self.remaining(final),'fixed4MiB aggregate evidence capacity');self.used+=len(raw);fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
  try:
   view=memoryview(raw)
   while view:count=os.write(fd,view);need(count>0,'complete exclusive evidence write');view=view[count:]
   os.fsync(fd)
  finally:os.close(fd)
  os.fsync(self.fd);reference=dict(path=str(self.path/name),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());self.refs.append(reference);return reference
 def close(self):os.close(self.fd)
def capture(argv,cap):
 left=COLD+PHASE-time.monotonic();need(left>0 and cap>0,'fixed cold300second observer/evidence budget');start=time.monotonic();epoch=time.time()
 proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd='/',env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','SYSTEMD_PAGER':'cat','SYSTEMD_COLORS':'0'},close_fds=True);selector=selectors.DefaultSelector();parts={'stdout':[],'stderr':[]};size=0;deadline=min(COLD+PHASE,start+CALL_SECONDS)
 try:
  for key,stream in(('stdout',proc.stdout),('stderr',proc.stderr)):os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,key)
  while selector.get_map():
   left=deadline-time.monotonic();need(left>0,'read-only systemctl timeout; no unit action/retry');events=selector.select(min(left,.1))
   for entry,_ in events:
    data=os.read(entry.fileobj.fileno(),min(65536,cap+1-size))
    if not data:selector.unregister(entry.fileobj);continue
    size+=len(data);need(size<=cap,'complete stdout/stderr exceeds fixed capacity; no sampling');parts[entry.data].append(data)
  left=deadline-time.monotonic();need(left>0,'same finite systemctl deadline includes wait');code=proc.wait(timeout=left)
  return dict(schema='bole.readonly-systemctl-receipt/v1',requested_argv=argv,subprocess_pid=proc.pid,observed_epoch=epoch,elapsed_seconds=time.monotonic()-start,exit_code=code,stdout=b''.join(parts['stdout']).decode('utf8'),stderr=b''.join(parts['stderr']).decode('utf8'),complete=True)
 except BaseException:
  if proc.poll()is None:proc.kill()
  try:proc.wait(timeout=2)
  except subprocess.TimeoutExpired:raise RuntimeError('owned read-only systemctl child did not retire')
  raise
 finally:selector.close();proc.stdout.close();proc.stderr.close()
def start_ticks(text):
 end=text.rfind(')');need(end>0,'complete Linux process stat');fields=text[end+2:].split();need(len(fields)>19,'complete process stat fields');return int(fields[19])
def proc_observation(pid):
 need(type(pid)is int and pid>0,'only an actually reported live PID');base=Path('/proc')/str(pid)
 def read(name,cap=65536):
  with(base/name).open('rb')as stream:raw=stream.read(cap+1)
  need(len(raw)<=cap,'bounded complete proc field');return raw.decode('utf8')
 try:
  before=read('stat');status=read('status');group=read('cgroup');after=read('stat');keys={'Name','State','Tgid','Pid','PPid','Uid','Gid','NSpid','Threads','CapInh','CapPrm','CapEff','CapBnd','CapAmb','NoNewPrivs','Seccomp'};filtered={}
  for line in status.splitlines():
   key,sep,value=line.partition(':')
   if sep and key in keys:need(key not in filtered,'unique actual proc status key');filtered[key]=value.strip()
  need(filtered.get('Pid')==str(pid),'actual proc PID identity');return dict(pid=pid,start_ticks=start_ticks(before),stable_lifetime=start_ticks(before)==start_ticks(after),status=filtered,cgroup=group,error=None)
 except(OSError,ValueError)as error:return dict(pid=pid,stable_lifetime=False,error=type(error).__name__+': '+str(error)[:512])
def legacy_history(value):
 expected={'all_remaining_PIDs_zero','discovery_stdout','observed_epoch','schema','show_stdout','unit_count'};need(set(value)==expected and value['schema']=='bole.actual-complete-unit-quiescence/v2','exact actual legacy history schema; unknown layout rejected')
 need(type(value['unit_count'])is int and 0<value['unit_count']<=MAX_UNITS and type(value['all_remaining_PIDs_zero'])is bool and type(value['observed_epoch'])in(int,float)and math.isfinite(value['observed_epoch']),'actual legacy history types')
 discovered=discovery_names(value['discovery_stdout']);need(type(value['show_stdout'])is str,'whole historical show output');blocks=[];current={}
 for line in value['show_stdout'].splitlines()+['']:
  if not line.strip():
   if current:blocks.append(current);current={}
   continue
  need('='in line,'complete historical key/value line');key,val=line.split('=',1);need(key not in current,'duplicate historical property');current[key]=val
 required={'MainPID','ControlPID','Result','ExecMainStatus','Id','ActiveState','SubState'};ids=[]
 for block in blocks:
  need(set(block)==required,'strict7field actual history block')
  for key in('MainPID','ControlPID','ExecMainStatus'):need(re.fullmatch(r'[0-9]+',block[key]),'actual numeric historical property')
  ids.append(unit_name(block['Id']))
 names=name_set(ids);need(len(blocks)==value['unit_count']==len(discovered)and names==discovered,'all78 history Id blocks equal complete discovery, never infer from flag');return names
def observe(args,output):
 source_ref=strict_ref(parse_json(args.source_ref));need(Path(source_ref['path'])==Path(os.path.abspath(__file__)),'actual source-owned observer path');checked(source_ref);before={source_ref['path']:source_ref};active=set();cache={}
 def remember(reference,*,body=False,cap=REF_CAP):
  raw=checked(reference,body=body,cap=cap);path=reference['path'];need(path not in before or before[path]==reference,'no conflicting exact input path');before[path]=reference;return raw
 def history(reference,depth=0):
  strict_ref(reference);need(depth<=16,'finite explicit prior-observation chain');key=(reference['path'],reference['sha256'])
  if key in cache:return cache[key]
  need(key not in active,'no cyclic history Ref chain');active.add(key);value=parse_json(remember(reference,body=True))
  if value.get('schema')=='bole.actual-complete-unit-quiescence/v2':names=legacy_history(value)
  elif value.get('schema')==SCHEMA:
   need(set(value)==OBS_KEYS,'exact prior observer output schema');names=name_set(value['unit_names']);need(value['unit_count']==len(names),'whole prior unit count');prior=set();need(type(value['history_refs'])is list and len(value['history_refs'])<=16,'finite prior history roots')
   for child in value['history_refs']:prior|=history(child,depth+1)
   receipt=parse_json(remember(value['discovery_receipt_ref'],body=True));need(receipt['schema']=='bole.readonly-systemctl-receipt/v1'and receipt['requested_argv']==DISCOVERY_ARGV and receipt['exit_code']==0 and receipt['complete']is True,'actual complete prior discovery receipt');found=discovery_names(receipt['stdout']);known=name_set(value['known_units'])
   need(names==prior|known|found and value['history_unit_names']==sorted(prior)and value['discovered_unit_names']==sorted(found),'retain every prior discovered unit without list replacement');remember(value['source_ref'])
  else:raise ValueError('unsupported history layout; no guessed keys')
  active.remove(key);cache[key]=names;return names
 roots=[BASE_HISTORY];roots.extend(strict_ref(parse_json(raw))for raw in args.history_ref);unique={}
 for reference in roots:need(reference['path']not in unique or unique[reference['path']]==reference,'no conflicting history root');unique[reference['path']]=reference
 roots=list(unique.values());need(len(roots)<=16,'finite explicit history roots');historical=set()
 for reference in roots:historical|=history(reference)
 known=name_set(list(KNOWN_CURRENT)+args.known_unit);need(len(historical|known)<=MAX_UNITS,'history/known union exceeds96; never discard');own_pid=os.getpid();own_start=start_ticks(Path('/proc/self/stat').read_text())
 output.write('SOURCE.json',dict(source_ref=source_ref,actual_pid=own_pid,actual_start_ticks=own_start,actual_argv=sys.argv,python_executable=sys.executable,python_version=sys.version,limits=dict(units=MAX_UNITS,discovery_bytes=DISCOVERY_CAP,aggregate_output_bytes=AGGREGATE_CAP,phase_seconds=PHASE,per_readonly_call_seconds=CALL_SECONDS)))
 output.write('HISTORY.json',dict(history_refs=roots,history_unit_names=sorted(historical),known_units=sorted(known),historical_PIDs_or_success_flags_reused_for_current=False,historical_submission_role='not provided by legacy history; not inferred or treated as corruption'))
 discovery=capture(DISCOVERY_ARGV,min(DISCOVERY_CAP,output.remaining()));dr=output.write('000-DISCOVERY.json',discovery);need(discovery['exit_code']==0 and discovery['complete']is True,'actual complete successful discovery command');found=discovery_names(discovery['stdout']);names=historical|known|found;need(len(names)<=MAX_UNITS,'complete discovered/history union exceeds96; no first96 sample');missing=(historical|known)-found;rows=[]
 for index,unit in enumerate(sorted(names),1):
  argv=[SYSTEMCTL,'show','--all','--no-pager',*[('--property='+key)for key in PROPERTIES],unit];receipt=capture(argv,min(DISCOVERY_CAP,output.remaining()));rr=output.write('%03d-SHOW.json'%index,receipt)
  row=dict(unit=unit,receipt_ref=rr,property_receipt_complete=False,actual_state=None,actual_entry_ref=None,entry_projection=None,actual_exec_argv_display_sha256=None,current_PID_proc_refs=[],historical_submission_ref=None,submission_execution_proven=False,error=None);props=None
  try:
   need(receipt['exit_code']==0 and receipt['complete']is True,'actual successful complete show receipt');props=properties(receipt['stdout'],unit);row['actual_state']=state(props);row['property_receipt_complete']=True;row['actual_result']=props['Result'];row['actual_ExecMainStatus']=props['ExecMainStatus'];row['actual_ExecMainPID']=props['ExecMainPID']
  except(ValueError,OSError)as error:row['error']=type(error).__name__+': '+str(error)[:512]
  if row['property_receipt_complete']:
   pids={row['actual_state']['MainPID'],row['actual_state']['ControlPID']}-{0}
   for pid in sorted(pids):pr=output.write('%03d-PROC-%d.json'%(index,pid),proc_observation(pid));row['current_PID_proc_refs'].append(pr)
   try:
    path,argv_digest=entry_path(props['ExecStart']);actual,_=whole_file(path);remember(actual);row['actual_entry_ref']=actual;row['actual_exec_argv_display_sha256']=argv_digest;row['entry_projection']='unique absolute .py token in actual systemd argv display; not a full submission argv proof'
   except(ValueError,OSError)as error:row['error']=type(error).__name__+': '+str(error)[:512]
  rows.append(row)
 need(len(rows)==len(names),'every union unit actually attempted once');after={};after_errors=[]
 for path,reference in before.items():
  try:actual,_=whole_file(path);after[path]=actual
  except(OSError,ValueError)as error:after_errors.append(dict(path=path,error=type(error).__name__+': '+str(error)[:512]))
 equal=before==after and not after_errors;complete=len(rows)==len(names)and all(row['property_receipt_complete']for row in rows);zero=complete and all(row['actual_state']['MainPID']==0 and row['actual_state']['ControlPID']==0 for row in rows);quiet=complete and not missing and equal and all(row['actual_state']['quiescent']for row in rows);entries=all(row['actual_entry_ref']is not None and row['error']is None for row in rows)
 need(time.monotonic()-COLD<=PHASE,'whole cold observer300seconds, never restarted')
 result=dict(schema=SCHEMA,observed_epoch=time.time(),observed_monotonic=time.monotonic(),actual_pid=own_pid,actual_start_ticks=own_start,source_ref=source_ref,history_refs=roots,known_units=sorted(known),history_unit_names=sorted(historical),discovery_receipt_ref=dr,discovered_unit_names=sorted(found),unit_names=sorted(names),unit_count=len(names),rows=rows,history_missing_from_discovery=sorted(missing),source_input_before=before,source_input_after=after,all_remaining_PIDs_zero=bool(zero),all_units_quiescent=bool(quiet),observation_complete=bool(complete),actual_entry_sources_complete=bool(entries),source_input_equal=bool(equal),resource_admitted=False,submission_execution_proven=False,historical_submission_role='legacy history contains no controller_refs; unknown submission unproven, never inferred corrupt from different entry path',whole_MAIN_lock_proven=False,limits=dict(units=MAX_UNITS,discovery_bytes=DISCOVERY_CAP,aggregate_output_bytes=AGGREGATE_CAP,final_metadata_reserve=FINAL_RESERVE,phase_seconds=PHASE,per_readonly_call_seconds=CALL_SECONDS),unit_observation_semantics=dict(single_actual_show_per_union_unit=True,interval_observations_not_atomic=True,historical_PID_flags_reused=False,subset_sampling=False,automatic_expansion=False,fixed_properties=list(PROPERTIES),Environment_read=False,after_check_errors=after_errors,output_file_refs=list(output.refs)))
 need(set(result)==OBS_KEYS,'exact own output/history schema');return result
def main():
 parser=argparse.ArgumentParser(allow_abbrev=False,description=__doc__);parser.add_argument('--execute',action='store_true');parser.add_argument('--source-ref');parser.add_argument('--history-ref',action='append',default=[]);parser.add_argument('--known-unit',action='append',default=[]);parser.add_argument('--output',type=Path);args=parser.parse_args()
 if not args.execute:print(json.dumps(dict(enabled=False,observed=False,resource_admitted=False)));return 0
 need(args.source_ref and args.output,'explicit whole source Ref3 and new output leaf');output=None
 try:
  output=Output(args.output);result=observe(args,output);reference=output.write('OBSERVATION.json',result,final=True);passed=result['all_units_quiescent']and result['actual_entry_sources_complete']and result['source_input_equal'];print(json.dumps(dict(observation_ref=reference,observation_checks_pass=bool(passed),resource_admitted=False,aggregate_evidence_bytes=output.used,unit_count=result['unit_count'])));return 0 if passed else 3
 except BaseException as error:
  fault=dict(schema='bole.readonly-unit-observer-fault/v1',error=type(error).__name__+': '+str(error)[:2048],observation_complete=False,observation_checks_pass=False,resource_admitted=False,partial_output_refs=[]if output is None else list(output.refs),units_never_started_stopped_or_reset=True,note='No successful observation from partial/capped/timed-out evidence.');reference=None
  if output is not None:
   try:reference=output.write('FIRST-FAULT.json',fault,final=True)
   except BaseException as second:fault['fault_write_error']=type(second).__name__+': '+str(second)[:512]
  print(json.dumps(dict(fault_ref=reference,failure=fault,observation_checks_pass=False,resource_admitted=False)));return 3
 finally:
  if output is not None:output.close()
if __name__=='__main__':raise SystemExit(main())
