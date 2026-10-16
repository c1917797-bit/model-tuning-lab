"""Source-only bounded capture of three released phases; no container mutation."""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061');OUT=ROOT/'seal-evidence069-MAIN-002';MAX=50*1024**2
AGENT=Path('/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006')
OWNERS=[(1357,'649feda29cd60da14dc2c133be4ebcee4b8119177f0cd84d54ee43503a344f45'),(1620,'7261c6673bf6a8771119bfd2b3260a02a8480f0da10d568a40602cc104132f26'),(1345,'99a69829fee6dbbe04aa96301e7ebd18e93c70c988840aacb049b4812306c67e')]
CIDS=[['1839e5c3eb2e109c7032ccbe231451c7dfc346636dae745d481a1ffeb30fb5f9'],['6440959c940af9b89c2b3f41e04457b7f4fbac4e76aa1a29cf6f425d0aca3aae','af6a464cdf395e64506b3b0f4180ba0197b4dd69d84d1f27ecc4fc2f1d931541'],['5f4cc2ad306f24d048a18c9cc9bdf1bd5758010751c80a02e10e43f9f3211751']]
AUTH=dict(path=str(AGENT/'DL061_STORAGE_AUTHORITY_20261016.json'),bytes=1213,sha256='3b58d42555147db06874fa4db36ada8b95474af4f3153fc89b73e4b7779d6f6c')
def need(x,m):
 if not x:raise ValueError(m)
def ref(p):
 p=Path(p);h=hashlib.sha256();size=0
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b);size+=len(b)
 return dict(path=str(p),bytes=size,sha256=h.hexdigest())
def load(r,name):
 p=Path(r['path']);need(all(not x.is_symlink()for x in(p,*p.parents))and ref(p)==r,'actual reviewed helper Ref');sys.path.insert(0,str(p.parent));v=importlib.util.module_from_spec(s:=importlib.util.spec_from_file_location(name,p));sys.modules[name]=v;s.loader.exec_module(v);return v
def inspect(cid):
 argv=['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker','inspect','--',cid];r=subprocess.run(argv,capture_output=True,timeout=20);need(r.returncode==0 and len(r.stdout)<=2*1024**2 and len(r.stderr)<=65536,'bounded actual read-only inspect')
 rows=json.loads(r.stdout);need(len(rows)==1 and rows[0]['Id']==cid and rows[0]['Image']=='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1','exact source-created CID/same660, not foreign inspect')
 row=rows[0];state=row['State'];need(not row.get('ExecIDs')and state['Running']is False and state['Pid']==0 and state['ExitCode']==0 and state.get('OOMKilled',False)is False and state['Status']=='exited','actual terminal noExec noOOM')
 return dict(Id=row['Id'],State=state,ExecIDs=row.get('ExecIDs'))
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--phase',choices=('preflight','capture'),required=True);p.add_argument('--helper-ref',required=True);p.add_argument('--storage-ref',required=True);a=p.parse_args()
 if not a.execute:print('disabled');return 0
 need(time.time()<1792220533-90,'fixed NEW24H cutoff incl cleanup');S=load(json.loads(a.helper_ref),'_actual_sealed_storage069');G=load(json.loads(a.storage_ref),'_actual_storage069')
 need(OUT.parent==ROOT and not OUT.exists(),'exact new exclusive evidence leaf');S.exact_ref(AUTH);G.authority(AUTH,S.read);before=G.check(ROOT);need(before['committed_bytes']+MAX<=80*1024**3 and shutil.disk_usage(ROOT).free>=100*1024**3+MAX,'capture50MiB charged to existing80/100 limits')
 ledgers=S.generations(ROOT);need(ledgers and ledgers[-1].name=='STORAGE_LEDGER061.3.json','actual latest expected completed3 phase ledger');baseline=ref(ledgers[-1]);ledger=S.read(baseline);need(len(ledger['reservations'])==3,'no unreviewed active/new reservation')
 S.no_old_commands();phases=[];staged=[]
 for i,name in enumerate(S.EXPECTED):
  leaf=ROOT/name;owner=ref(leaf/'RESULT.json');need(owner['bytes']==OWNERS[i][0]and owner['sha256']==OWNERS[i][1],'exact actual finished owner')
  stages=('numeric','native')if i==1 else('native',);cleanup=[ref(leaf/stage/'cleanup-verdict.json')for stage in stages];states=[]
  for j,stage in enumerate(stages):
   creation=json.loads((leaf/stage/'create-receipt.json').read_bytes());cid=creation['stdout'].strip();need(cid==CIDS[i][j],'exact original MAIN-observed created CID, not foreign inspect');states.append(inspect(cid))
  terminal=None if i==0 else ref(AGENT/('DL061_NUMERIC16_OPERATION_TERMINAL_20261016.json'if i==1 else'DL066_CPU_OPERATION_TERMINAL_20261016.json'))
  row=dict(leaf=str(leaf),owner_ref=owner,cleanup_refs=cleanup,container_state_refs=[],operation_terminal_ref=terminal)
  phases.append(row);staged.append(states)
 if a.phase=='preflight':
  print(json.dumps(dict(actual_preflight=True,baseline_ledger_ref=baseline,owners=[x['owner_ref']for x in phases],closed_phase_count=3,actual_container_count=sum(len(x)for x in staged),no_phase_commands=True,output_not_created=True,seal_or_qualification=False)));return 0
 OUT.mkdir();written=0
 def write(name,value):
  nonlocal written
  data=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode();need(written+len(data)<=MAX,'actual entire evidence payload<=50MiB')
  target=OUT/name
  with target.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
  written+=len(data);return ref(target)
 for i,row in enumerate(phases):
  row['container_state_refs']=[write('phase-%d-container-inspect.json'%i,staged[i])]
  S.verify_terminal(row)
  files=S.tree(row['leaf'],True);need(S.tree(row['leaf'],False)==[{k:v for k,v in x.items()if k!='sha256'}for x in files],'fullhash then independent stat snapshot stable')
  row['frozen_bytes']=sum(x['bytes']for x in files);row['tree_ref']=write('phase-%d-full-tree.json'%i,dict(root=row['leaf'],files=files))
  S.verify_closed(row,True)
 need(ref(S.generations(ROOT)[-1])==baseline,'ledger not advanced during capture');S.no_old_commands()
 proof=write('EVIDENCE069.json',dict(schema='deltalog.closed-phase-storage-evidence/v069',root=str(ROOT),authority_ref=AUTH,baseline_ledger_ref=baseline,phases=phases,capture_source_ref=ref(__file__),reviewed_helper_ref=json.loads(a.helper_ref),read_only_closed_phases=True,declared_no_further_writes_by_MAIN=True,cached_terminal_observations_not_fresh_tool_snapshots=True))
 S.validate_evidence(proof,ROOT,AUTH,full=True);need(G.check(ROOT)['committed_bytes']<=80*1024**3,'actual capture remains within original ledger budget');fd=os.open(OUT,os.O_RDONLY);os.fsync(fd);os.close(fd)
 print(json.dumps(dict(actual_capture=True,evidence_ref=proof,actual_written_bytes=written,max_bytes=MAX,source_ref=ref(__file__),no_ledger_mutation=True,qualification=False)));return 0
if __name__=='__main__':raise SystemExit(main())
