"""Reviewed collector delta: fresh inspect/full tree; never mutates containers."""
import argparse,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import sealed_storage093 as S
OUT=S.ROOT/'seal-evidence093-MAIN-001';MAX=50*1024**2
AUTH=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/DL061_STORAGE_AUTHORITY_20261016.json',bytes=1213,sha256='3b58d42555147db06874fa4db36ada8b95474af4f3153fc89b73e4b7779d6f6c')
CURRENT=dict(path='/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/NEW24H_AUTHORITY_20261016.json',bytes=3481,sha256='e8c373b6664a4bdd80012428b686227a6f15c0535b3c57a7654fb7996c02cf28')
def current_budget(base):
 r=S.read(S.SOURCE)['files']['storage061.py'];S.need(r['bytes']==5543 and r['sha256']=='ca8c1ee593cb94825736dca93f28834c720bb8baccaa3c65adcfa3f4c956161c','exact original storage061 budget implementation');S.need(S.ref(r['path'])==r,'original storage file closure');g=importlib.util.module_from_spec(spec:=importlib.util.spec_from_file_location('_storage093_original061',r['path']));sys.modules[spec.name]=g;spec.loader.exec_module(g);S.old().install(g,base['sealed_evidence_ref'],AUTH,base['storage069_template_ref']);return g.check(S.ROOT)
def write_scan(proc=Path('/proc'),leaves=None):
 """Complete current-writer check; races only permit vanished processes/FDs."""
 leaves=[S.ROOT/n for n in S.NAMES]if leaves is None else list(leaves);count=0;fds=0
 def inside(raw):
  p=Path(raw.removesuffix(' (deleted)'));return p.is_absolute()and any(p==r or p.is_relative_to(r)for r in leaves)
 for p in proc.iterdir():
  if not p.name.isdigit():continue
  count+=1;S.need(count<=16384,'bounded complete process writer scan')
  try:
   items=list((p/'fd').iterdir())
   for f in items:
    fds+=1;S.need(fds<=262144,'bounded complete FD scan')
    try:
     target=os.readlink(f)
     if not inside(target):continue
     text=(p/'fdinfo'/f.name).read_text();flags=[x.split(':',1)[1].strip()for x in text.splitlines()if x.startswith('flags:')];S.need(len(flags)==1 and int(flags[0],8)&3==0,'live write FD in closed phase')
    except FileNotFoundError:continue
   with(p/'maps').open('r')as mf:
    for j,line in enumerate(mf):
     S.need(j<262144,'bounded map scan');v=line.rstrip('\n').split(None,5)
     if len(v)==6 and inside(v[5]):S.need(not('w'in v[1]and's'in v[1]),'live shared writable map in closed phase')
  except FileNotFoundError:continue
 return dict(processes=count,file_descriptors=fds,no_open_write_fds_or_shared_writable_maps=True)
def inspect(cid,code):
 argv=['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker','inspect','--',cid];r=subprocess.run(argv,capture_output=True,timeout=20);S.need(r.returncode==0 and len(r.stdout)<=2*1024**2 and len(r.stderr)<=65536,'bounded readonly Docker inspect')
 vv=json.loads(r.stdout);S.need(len(vv)==1,'single inspect');v=vv[0];s=v['State'];S.need(v['Id']==cid and v['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1'and not v.get('ExecIDs')and s['Status']=='exited'and s['Running']is False and s['Pid']==0 and s['ExitCode']==code and s.get('OOMKilled',False)is False,'exact fresh stopped source-created CID, preserved consumer exit1')
 S.need(v['Config']['Labels']['deltalog-fresh-bridge.owner-source-sha256']==S.SOURCE['sha256'],'actual container source label');return dict(Id=v['Id'],State=s,ExecIDs=v.get('ExecIDs'))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--phase',choices=('preflight','capture','seal'));p.add_argument('--plan-ref');p.add_argument('--template-ref');p.add_argument('--evidence-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return 0
 S.need(1792134133<=time.time()<1792220533-90,'fixed window incl90 cleanup');sr=json.loads(a.template_ref);m=S.read(sr);S.need(m['schema']=='deltalog.closed-storage-source/v093'and m['files']['capture093.py']==S.ref(__file__)and m['files']['sealed_storage093.py']==S.ref(P/'sealed_storage093.py'),'source-bound actual collector/helper')
 for r in m['files'].values():S.need(S.ref(r['path'])==r,'complete source readset')
 for r in m['dependencies']:S.need(S.ref(r['path'])==r,'reviewed external readset')
 au=S.read(AUTH);window=S.read(CURRENT);S.need(au['schema']=='ascend.paper-experiment.storage-authority/v1'and au['output_root']==S.ROOT.as_posix()and au['max_total_bytes']==80*S.GIB and au['min_free_bytes']==100*S.GIB and au['current_authority_ref']==CURRENT and window['start_epoch']==1792134133 and window['cutoff_epoch']==1792220533,'same explicit storage/window authorization')
 if a.phase=='seal':print(json.dumps(dict(seal_ref=S.seal_generation(json.loads(a.evidence_ref),S.ROOT,AUTH,sr),qualification=False)));return 0
 plan=S.read(json.loads(a.plan_ref));S.need(plan['schema']=='deltalog.storage-terminal-plan/v093'and plan['source']==sr and plan['operation_terminal_refs']==[None,None,None]and plan['historical_operation_receipt_unavailable']is True and plan['operation_unavailable_ref']==m['files']['evidence/operation-notfound-observed.json'],'reviewed actual not_found observations, no fabricated historical terminal');S.unavailable(plan['operation_unavailable_ref'])
 base=S.read(S.BASE);S.need(S.ref(S.old().generations(S.ROOT)[-1])==S.BASE,'fresh exact ledger7');S.prefix_chain(base);S.no_writers();S.read(AUTH);budget=current_budget(base);S.need(budget['committed_bytes']+MAX<=80*S.GIB and not OUT.exists()and shutil.disk_usage(S.ROOT).free>=100*S.GIB+MAX,'capture50MiB charged on original committed budget, new exclusive leaf/free100')
 staged=[];phases=[]
 for i,name in enumerate(S.NAMES):
  leaf=S.ROOT/name;stages=('native',)if i==0 else('native','numeric');states=[];creates=[]
  for j,stage in enumerate(stages):
   r=S.ref(leaf/stage/'create-receipt.json');S.need(S.read(r)['stdout'].strip()==S.CIDS[i][j],'original exact created CID');creates.append(r);states.append(inspect(S.CIDS[i][j],S.EXITS[i][j]))
  phases.append(dict(leaf=str(leaf),owner_ref=S.ref(leaf/'RESULT.json'),create_refs=creates,cleanup_refs=[S.ref(leaf/stage/'cleanup-verdict.json')for stage in stages],container_state_refs=[],operation_terminal_ref=plan['operation_terminal_refs'][i]));staged.append(states)
 # Terminal validation needs persisted fresh inspect Ref; preflight checks exact originals
 # and cached terminal presence without manufacturing one. Full verify precedes seal.
 for i,row in enumerate(phases):
  S.need((row['owner_ref']['bytes'],row['owner_ref']['sha256'])==S.OWNER_PINS[i],'observed exact owner')
 if a.phase=='preflight':print(json.dumps(dict(source=sr,baseline=S.BASE,phase_count=3,actual_fresh_CIDs=5,output_not_created=True,qualification=False)));return 0
 S.need(a.phase=='capture','explicit phase');used=sum(x['bytes']for x in S.old().tree(S.ROOT,False));S.need(used+MAX<=80*S.GIB,'full capture50MiB counted80');OUT.mkdir(mode=0o700);written=0
 def write(name,v):
  nonlocal written
  b=(json.dumps(v,sort_keys=True,indent=2)+'\n').encode();S.need(written+len(b)<=MAX,'whole evidence50MiB hardcap');p=OUT/name
  with p.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
  written+=len(b);return S.ref(p)
 for i,row in enumerate(phases):
  row['container_state_refs']=[write('phase-%d-inspect.json'%i,staged[i])];S.no_writers();scan1=write_scan();files=S.old().tree(row['leaf'],True);first=write('phase-%d-tree.json'%i,dict(root=row['leaf'],files=files));S.no_writers();scan2=write_scan();second=write('phase-%d-tree-second.json'%i,dict(root=row['leaf'],files=S.old().tree(row['leaf'],True)));S.need(S.read(first)==S.read(second),'two complete full hashes/mtimes stable');row['frozen_bytes']=sum(x['bytes']for x in files);row['tree_ref']=first;row['quiescent_ref']=write('phase-%d-quiescent.json'%i,dict(schema='deltalog.actual-quiescent-closure/v093',source=S.SOURCE,leaf=row['leaf'],owner_ref=row['owner_ref'],historical_operation_receipt_unavailable=True,historical_operation_exit_claimed=False,operation_unavailable_ref=plan['operation_unavailable_ref'],unavailable_operation_id=S.OPERATIONS[i],no_original_commands=True,no_open_write_fds_or_shared_writable_maps=True,writer_scans=[scan1,scan2],two_full_hashes_equal=True,first_tree_ref=first,second_tree_ref=second));S.verify_terminal(row,i);S.old().verify_closed(row,True)
 S.need(S.ref(S.old().generations(S.ROOT)[-1])==S.BASE,'ledger not advanced');S.no_writers();er=write('EVIDENCE093.json',dict(schema='deltalog.closed-phase-storage-evidence/v093',source_manifest_ref=sr,root=str(S.ROOT),authority_ref=AUTH,baseline_ledger_ref=S.BASE,prior_evidence_ref=base['sealed_evidence_ref'],phases=phases,collector_source=S.ref(__file__),plan_ref=json.loads(a.plan_ref),old_failures_unchanged=True,numerical_qualification=False));S.validate(er,AUTH,True);fd=os.open(OUT,os.O_RDONLY);os.fsync(fd);os.close(fd);print(json.dumps(dict(evidence_ref=er,bytes_written=written,no_ledger_mutation=True,qualification=False)));return 0
if __name__=='__main__':raise SystemExit(main())
