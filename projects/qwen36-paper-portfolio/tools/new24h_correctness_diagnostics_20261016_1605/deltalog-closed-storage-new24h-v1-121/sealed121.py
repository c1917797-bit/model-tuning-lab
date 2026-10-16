"""Close exact R4 CPU + interrupted numeric phases; storage, never numerics."""
import argparse,ast,hashlib,importlib.util,inspect,json,os,time,types
from pathlib import Path
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061');G=2**30
PRIOR=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-closed-storage-new24h-v1-119/SOURCE_MANIFEST.json',bytes=937,sha256='aa574e91699c6b5bca8cfac66abab893a00a03bb5ef4eb87f851d73bc15faed6')
TARGET_TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair4/SOURCE_TEMPLATE.json',bytes=61165,sha256='4df881560dcb8fbb978da5d893315e5f48223ad7eab832de4decea286fc14a70')
LEAVES=tuple(ROOT/('run-'+s+'-MAIN-20261016-NEW24H-088-repair4-001')for s in('cpu','numeric16'))
def need(v,s):
 if not v:raise ValueError(s)
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and all(not x.is_symlink()for x in(p,*p.parents)),'ordinary actual file');a=p.stat();h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns),'stable exact reference');return dict(path=str(p),bytes=z.st_size,sha256=h.hexdigest())
def read(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and ref(r['path'])==r and r['bytes']<16*2**20,'exact bounded metadata');return json.loads(Path(r['path']).read_bytes())
def load(r,n):
 need(ref(r['path'])==r,'exact executable');s=importlib.util.spec_from_file_location(n,r['path']);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
def write(p,v):
 b=(json.dumps(v,sort_keys=True,allow_nan=False)+'\n').encode('utf-8')
 if ROOT in Path(p).parents:
  S=prior();need(len(b)<=50*2**20 and sum(x['bytes']for x in S.tree(ROOT,False))+len(b)<=80*G and os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize>=100*G+len(b),'all new plan/evidence/ledger bytes charged80/free100')
 with Path(p).open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(p)
def prior():
 m=read(PRIOR);need(m['schema']=='deltalog.closed-storage-source/v119','exact reviewed119');return load(m['files']['sealed119.py'],'_storage121_canonical119')
def generations():return sorted(ROOT.glob('STORAGE_LEDGER061.*.json'),key=lambda p:int(p.name.split('.')[1]))
def observed():
 v=json.loads((Path(__file__).parent/'ACTUAL_CLOSURE_INPUT.json').read_bytes());need(len(v['phase_refs'])==10,'exact actual ten original phase refs');return v
def receipt_rows(sr):
 actual=observed();need(sr==actual['phase_refs'][0]['projection']['source'],'exact observed bound088R4 source')
 for v in actual['phase_refs']:need(ref(v['ref']['path'])==v['ref'],'all original owner/create/inspect/cleanup bytes preserved')
 rows=[]
 for i,leaf in enumerate(LEAVES):
  owner=ref(leaf/'RESULT.json');o=read(owner)
  need(o['schema']=='deltalog.diagnostic-owned-host/v035'and o['source']==o['target_source']==sr and o['stage']==('cpu'if i==0 else'numeric')and o['steps']==16 and o['stopped_retained']is True,'exact R4 stage source and terminal owner')
  need((o['primary']is None and o['secondary']==[])if i==0 else(o['primary']=="ValueError('foreign physical4..7 process/cgroup')"and o['independent_consumer']is None),'preserve CPU success / actual failed numeric, no promotion')
  stage=leaf/('native'if i==0 else'numeric');cr=ref(stage/'create-receipt.json');cid=read(cr)['stdout'].strip();need(len(cid)==64 and all(c in'0123456789abcdef'for c in cid),'actual created CID')
  cl=ref(stage/'cleanup-verdict.json');c=read(cl);need(c['cid']==cid and c['stopped']is True and c['retained']is True and c['unresolved_active_cid']is None,'own stopped CID, not global cleanup success')
  rows.append(dict(leaf=str(leaf),owner_ref=owner,create_ref=cr,cleanup_ref=cl,original_inspect_refs=[v['ref']for v in actual['phase_refs']if v['phase']==('cpu'if i==0 else'numeric16')and v['relative_path'].endswith('inspect.json')],cid=cid,original_primary=o['primary'],original_secondary=o['secondary'],original_cleanup=c))
 return rows
def scoped(S,plan):
 # Byte-identical canonical functions; only explicit observation targets differ.
 ns=dict(S.__dict__,SOURCE=plan['target_source_ref'],leaf=lambda i:LEAVES[i],CIDS=tuple((p['cid'],)for p in plan['phases']))
 raw=inspect.getsource(S.no_writers);need(raw.count('range(3)')==1,'exact canonical119 three-phase anchor');changed=raw.replace('range(3)','range(2)');need(changed.replace('range(2)','range(3)')==raw,'exact phase-count inverse');ast.parse(changed);local={};exec(compile(changed,'sealed121.py:canonical119-two-phase','exec'),ns,local)
 return types.SimpleNamespace(no_writers=local['no_writers'],inspect_all=types.FunctionType(S.inspect_all.__code__,ns),tree=S.tree)
def states_check(states,plan):
 need(len(states)==2 and {x['Id']for x in states}=={p['cid']for p in plan['phases']},'all and only actual source-created CIDs')
 for x in states:
  i=next(i for i,p in enumerate(plan['phases'])if p['cid']==x['Id']);s=x['State']
  need(s['Status']=='exited'and s['Running']is False and s['Pid']==0 and not s.get('OOMKilled')and not x.get('ExecIDs')and s['ExitCode']==(0 if i==0 else 137),'exact CPU0 / interrupted137 quiescence, no numerical success claim')
def verify_plan(pr):
 p=read(pr);need(p['schema']=='deltalog.closed-storage-plan/v121'and p['prior_source_ref']==PRIOR and p['target_template_ref']==TARGET_TEMPLATE and p['baseline_ledger_ref']==observed()['latest_ledger']['ref'],'typed actual plan and actual highest14 predecessor')
 s=read(p['target_source_ref']);t=read(TARGET_TEMPLATE)
 need(s['prepared_only']is False and s['prepared_template']==TARGET_TEMPLATE and s['files']==t['files']and s['root']==t['root'],'exact current R4 bound source')
 need(receipt_rows(p['target_source_ref'])==p['phases'],'original failure and cleanup flags byte-preserved');S=prior();e,b,closed=S.validate(p['prior_evidence_ref'],PRIOR)
 need(s['storage_seal_evidence_ref']==p['prior_evidence_ref']and s['storage_authority_ref']==e['authority_ref'],'same actual119 evidence/authority')
 before=S.BASE;v=read(before)
 for q in generations():
  if int(q.name.split('.')[1])<=11:continue
  r=ref(q);n=read(r)
  if r==p.get('published_generation_ref'):break
  need(n['previous_ledger_ref']==before and n['sealed_evidence_ref']==p['prior_evidence_ref']and n['storage069_template_ref']==PRIOR and n['reservations'][:len(v['reservations'])]==v['reservations'],'actual append-only prior119 ledger chain');before=r;v=n
  if before==p['baseline_ledger_ref']:break
 need(before==p['baseline_ledger_ref'],'exact latest-bound baseline exists')
 need([r for r in v['reservations']if r['leaf']in map(str,LEAVES)]==[dict(leaf=str(LEAVES[0]),stage='cpu',budget_bytes=G),dict(leaf=str(LEAVES[1]),stage='numeric',budget_bytes=33*G)],'both unchanged current reservations')
 return p,S,v,closed
def bind(sr,out):
 s=read(sr);S=prior();rows=receipt_rows(sr);latest=ref(generations()[-1]);need(latest==observed()['latest_ledger']['ref'],'actual highest14 unchanged before binding');p=dict(schema='deltalog.closed-storage-plan/v121',target_source_ref=sr,target_template_ref=TARGET_TEMPLATE,prior_source_ref=PRIOR,prior_evidence_ref=s['storage_seal_evidence_ref'],baseline_ledger_ref=latest,phases=rows,numerical_qualification=False)
 # Existing119 validates the preceding9closed phases; no old failure rewritten.
 rr=write(out,p);verify_plan(rr);return rr
def capture(pr,sr,out):
 p,S,base,closed=verify_plan(pr);need(ref(generations()[-1])==p['baseline_ledger_ref'],'latest baseline stable before capture');Q=scoped(S,p)
 need(out.parent==ROOT and out.name=='seal-evidence121-MAIN-001'and not out.exists(),'unique authorized evidence leaf')
 need(sum(x['bytes']for x in S.tree(ROOT,False))+50*2**20<=80*G and os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize>=100*G+50*2**20,'80total/100free including evidence')
 before=Q.no_writers();a=Q.inspect_all();states_check(a,p);out.mkdir();phases=[]
 for row in p['phases']:
  x=S.tree(row['leaf'],True);y=S.tree(row['leaf'],True);need(x==y,'two full stable retained-tree hashes');tr=write(out/(Path(row['leaf']).name+'.tree.json'),dict(root=row['leaf'],files=x));phases.append(dict(row,tree_ref=tr,frozen_bytes=sum(v['bytes']for v in x)))
 b=Q.inspect_all();states_check(b,p);need(a==b,'stable independent double inspect');after=Q.no_writers();need(ref(generations()[-1])==p['baseline_ledger_ref'],'no ledger writer during capture')
 return write(out/'EVIDENCE121.json',dict(schema='deltalog.closed-phase-storage-evidence/v121',source_manifest_ref=sr,plan_ref=pr,baseline_ledger_ref=p['baseline_ledger_ref'],prior_source_ref=PRIOR,prior_evidence_ref=p['prior_evidence_ref'],phases=phases,states_before=a,states_after=b,no_writer_before=before,no_writer_after=after,numerical_qualification=False,old_failure_flags_preserved=True))
def validate(er,sr):
 e=read(er);need(e['schema']=='deltalog.closed-phase-storage-evidence/v121'and e['source_manifest_ref']==sr and e['prior_source_ref']==PRIOR and e['numerical_qualification']is False,'exact storage-only evidence');p,S,base,closed=verify_plan(e['plan_ref']);Q=scoped(S,p)
 need(e['baseline_ledger_ref']==p['baseline_ledger_ref']and e['prior_evidence_ref']==p['prior_evidence_ref']and len(e['phases'])==2,'same baseline/old evidence/two phases')
 for original,row in zip(p['phases'],e['phases']):
  need(all(row[k]==v for k,v in original.items()),'exact original flags and receipts');t=read(row['tree_ref']);need(t['root']==row['leaf']and S.tree(row['leaf'],True)==t['files']and row['frozen_bytes']==sum(v['bytes']for v in t['files']),'full retained phase unchanged')
 a=Q.inspect_all();states_check(a,p);need(a==e['states_before']==e['states_after'],'fresh independently exited same CIDs');Q.no_writers();return e,base,closed+e['phases']
def seal(er,sr):
 import fcntl,shutil
 fd=os.open(ROOT/'.storage061.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 try:
  fcntl.flock(fd,fcntl.LOCK_EX);e,base,closed=validate(er,sr);need(ref(generations()[-1])==e['baseline_ledger_ref'],'no unknown reservation or concurrent ledger writer');S=prior();need(sum(x['bytes']for x in S.tree(ROOT,False))+65536<=80*G and shutil.disk_usage(ROOT).free>=100*G+65536,'80hard/100free unchanged')
  v=dict(base,previous_ledger_ref=e['baseline_ledger_ref'],sealed_evidence_ref=er,storage069_template_ref=sr);n=int(Path(e['baseline_ledger_ref']['path']).name.split('.')[1])+1;r=write(ROOT/('STORAGE_LEDGER061.%d.json'%n),v);d=os.open(ROOT,os.O_RDONLY);os.fsync(d);os.close(d);return r
 finally:os.close(fd)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--mode',choices=['bind','capture','validate','seal']);p.add_argument('--source-ref');p.add_argument('--target-source-ref');p.add_argument('--plan-ref');p.add_argument('--evidence-ref');p.add_argument('--output',type=Path);a=p.parse_args()
 if not a.execute:print('{"enabled":false,"numeric_qualification":false}');return
 need(1792134133<=time.time()<1792220533,'fixed unchanged24h');sr=json.loads(a.source_ref);m=read(sr);need(m['schema']=='deltalog.closed-storage-source/v121'and m['root']==str(Path(__file__).parent)and m['files']['sealed121.py']==ref(__file__),'own exactsource')
 for r in m['files'].values():need(ref(r['path'])==r,'own exact complete source closure')
 if a.mode=='bind':
  need(a.output.parent==ROOT and a.output.name=='PLAN_STORAGE121_MAIN_001.json','exact unique plan');r=bind(json.loads(a.target_source_ref),a.output)
 elif a.mode=='capture':r=capture(json.loads(a.plan_ref),sr,ROOT/'seal-evidence121-MAIN-001')
 elif a.mode=='validate':e,b,c=validate(json.loads(a.evidence_ref),sr);r=dict(closed_phase_count=len(c),numeric_qualification=False)
 else:r=seal(json.loads(a.evidence_ref),sr)
 print(json.dumps(r))
if __name__=='__main__':main()
