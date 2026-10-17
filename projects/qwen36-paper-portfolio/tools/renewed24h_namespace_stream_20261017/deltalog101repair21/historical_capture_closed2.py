"""Two retained R6 leaves only. No core ledger write, deletion or math grant."""
import argparse,hashlib,importlib.util,json,os,re,sys,time,types,stat,ast
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=Path('/opt/varlib/kubelet/mst-deltalog-new24h-20261016-061');G=2**30
OUT=ROOT/'seal-evidence-R6-N16-N160-model-snapshots-MAIN-R2-001'
BASE=dict(path=(ROOT/'STORAGE_LEDGER061.23.json').as_posix(),bytes=4169,sha256='7bacf26df76b47d53963fc054c91b38384716c7d9901938087f329dc288c23d0')
SOURCE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair6-repair2/SOURCE_MANIFEST.json',bytes=67429,sha256='871c8e32831ee3eebacd43a084e4416bb14d6d06cd9f5ee08017ba459f287cd8')
LEAVES=tuple(ROOT/('run-numeric'+str(n)+'-MAIN-20261016-NEW24H-088-repair6-repair2-001')for n in(16,160))
OWNERS=((1667,'7b10472808da9c409dca97e4f36ff577cf4d090db95c90b556d0bf680f4d25fe'),(1511,'c336a6b4b9f071e349147fe71037651fd628388246dd973d7be342381a45f908'))
# Original CIDs freshly read with all ten exact owner/create/cleanup Ref3s.
CIDS=(('12cd8ce564f540b096eb3023e1fd4c9db2b5ffb07cdd43423a6bbef5ab6d1103','d7e316abd86de078c2dcde86bc524f7c784166b235f41eb9239e3394d2e46fee'),('04b83ff30be859ad047756173355633c01cf430a6a35ed00824aea6a7a6e6155','3457a8dd4e431927148bbd2e06f715d350ac2f353d99461cdc5f6863cff4fae2'))
SCHEMA='deltalog.closed-R6-numeric16-160-overlay/v1'
def walk_error(error):raise error
def failclosed_tree(text):
 pairs=[('paths=[str(leaf(i))for i in range(3)]','paths=[str(leaf(i))for i in range(len(PHASES))]'),
 ('p=Path(p);dev=p.stat().st_dev;rows=[]','p=Path(p);_root=p.lstat();need(stat.S_ISDIR(_root.st_mode)and all(not x.is_symlink()for x in(p,*p.parents)),"ordinary tree root");dev=_root.st_dev;rows=[]'),
 ('os.walk(p,followlinks=False)','os.walk(p,followlinks=False,onerror=_closed_walk_error)'),
 ("return sorted(rows,key=lambda r:r['relative_path'])","need(_root_identity(_root)==_root_identity(p.lstat()),'tree root identity stable');return sorted(rows,key=lambda r:r['relative_path'])")]
 return derive(text,pairs)
def derive(text,pairs):
 out=text
 for a,b in pairs:need(out.count(a)==1,'exact source-derived walker delta');out=out.replace(a,b)
 inv=out
 for a,b in reversed(pairs):need(inv.count(b)==1,'unique walker inverse');inv=inv.replace(b,a)
 need(inv==text,'whole original walker inverse');return out
def root_identity(s):return(s.st_dev,s.st_ino,s.st_mode,s.st_mtime_ns,s.st_ctime_ns)
def failclosed_scan(S,raw):
 pairs=[('os.walk(root,followlinks=False)','os.walk(root,followlinks=False,onerror=_closed_walk_error)'),
 ('dev=root.stat().st_dev;total=0;amounts=','_root=root.lstat();dev=_root.st_dev;total=0;amounts='),
 (' return total,amounts'," need(_root_identity(_root)==_root_identity(root.lstat()),'scan root identity stable');return total,amounts")]
 body=derive(raw.decode(),pairs);tree=ast.parse(body);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='scan'];need(len(nodes)==1,'only source scan function')
 S._closed_walk_error=walk_error;S._root_identity=root_identity
 exec(compile(ast.Module(body=nodes,type_ignores=[]),S.__file__+'#failclosed-scan','exec'),S.__dict__)
def inventory(root,exclude=None):
 root=Path(root);before=root.lstat();need(stat.S_ISDIR(before.st_mode)and all(not p.is_symlink()for p in(root,*root.parents)),'ordinary complete inventory root')
 digest=hashlib.sha256();total=0;count=0
 for parent,dirs,files in os.walk(root,followlinks=False,onerror=walk_error):
  dirs.sort()
  for name in sorted(dirs+files):
   q=Path(parent)/name;s=q.lstat();need(s.st_dev==before.st_dev and not stat.S_ISLNK(s.st_mode)and(stat.S_ISREG(s.st_mode)or stat.S_ISDIR(s.st_mode)),'complete ordinary sameFS inventory')
   if exclude is not None and(q==exclude or exclude in q.parents):continue
   row=(q.relative_to(root).as_posix(),s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
   digest.update((json.dumps(row,separators=(',',':'))+'\n').encode());count+=1
   if stat.S_ISREG(s.st_mode):total+=s.st_size
 need(root_identity(before)==root_identity(root.lstat()),'inventory root stable during complete traversal')
 return dict(bytes=total,entries=count,metadata_sha256=digest.hexdigest(),root_identity=(before.st_dev,before.st_ino,before.st_mode))
def need(v,m):
 if not v:raise ValueError(m)
def canonical(sr):
 m=json.loads(Path(sr['path']).read_bytes());r=m['files']['canonical119.py'];b=(P/'canonical119.py').read_bytes()
 need((len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'exact reviewed canonical119 source')
 changed=failclosed_tree(b.decode())
 K=types.ModuleType('_closed2_actual119');K.__file__=str(P/'canonical119.py');exec(compile(changed,K.__file__+'#two-leaves', 'exec'),K.__dict__)
 K._closed_walk_error=walk_error;K._root_identity=root_identity
 K.need(K.ref(sr['path'])==sr,'exact own source Ref');K.SOURCE=SOURCE;K.PHASES=('numeric16','numeric160');K.CIDS=CIDS;K.leaf=lambda i:LEAVES[i]
 K.need(m['schema']=='deltalog.closed-two-R6-source/v1'and m['root']==str(P)and m['baseline_ledger_ref']==BASE and m['original_source_ref']==SOURCE,'exact reviewed two-leaf source identity')
 for name,r in m['files'].items():K.need(K.ref(P/name)==r,'complete declared source closure '+name)
 return K,m
def policy_context(K,io):
 # Preserve stronger canonical ordinary-parent/stable Ref checks, while
 # executing the REAL original bridge_io.load(r,name) implementation.
 def checked(r):
  K.need(type(r)is dict and set(r)=={'path','bytes','sha256'}and K.ref(r['path'])==r,'exact policy input')
  return Path(r['path'])
 def load_ref(r,name):
  checked(r)
  return io.load(r,name)
 return types.SimpleNamespace(need=K.need,obj=K.read,checked=checked,ref=K.ref,load=load_ref)

def prior_policy(K):
 m=K.read(SOURCE);root=Path(SOURCE['path']).parent;sys.path.insert(0,str(root))
 def load(name):
  r=m['files'][name+'.py'];K.need(K.ref(r['path'])==r,'source-bound actual policy '+name)
  spec=importlib.util.spec_from_file_location(name,r['path']);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
 io=load('bridge_io');C=policy_context(K,io)
 S=load('storage061');failclosed_scan(S,Path(S.__file__).read_bytes());B=load('storage_bridge088r6');B.install(C,m,S)
 for name in('storage_bridge121','closed_overlay088r6'):
  module=sys.modules[name];K.need(K.ref(module.__file__)==m['files'][name+'.py'],'no ambient policy module')
 proof=S.check();K.need(proof['max_total_bytes']==80*G and proof['min_free_bytes']==100*G,'unchanged80/100 prior13 policy')
 return S,proof
def receipts(K):
 need(all(type(cid)is str and re.fullmatch('[0-9a-f]{64}',cid)for row in CIDS for cid in row),'exact original N16 CIDs pending')
 expected=json.loads((P/'ACTUAL_RECEIPT_REFS.json').read_bytes())['refs'];expected={r['path']:r for r in expected};rows=[]
 for i,leaf in enumerate(LEAVES):
  owner=dict(path=(leaf/'RESULT.json').as_posix(),bytes=OWNERS[i][0],sha256=OWNERS[i][1]);o=K.read(owner)
  need(o['source']==o['target_source']==SOURCE and o['schema']=='deltalog.diagnostic-owned-host/v035'and o['steps']==(16,160)[i]and o['stopped_retained']is True and o['secondary']==[],'exact original source/owner retained, not rewritten')
  need((o['primary']is None)if i==0 else(o['primary']=="independent consumer ValueError('actual GE child failed; preserved logs/raw')"and o['independent_consumer']is None),'original N16 pass and N160 failed timeout preserved separately')
  rr=[]
  for j,stage in enumerate(('numeric','native')):
   cr=expected[(leaf/stage/'create-receipt.json').as_posix()];created=K.read(cr);need(created['stdout'].strip()==CIDS[i][j],'exact originally created CID')
   cl=expected[(leaf/stage/'cleanup-verdict.json').as_posix()];c=K.read(cl);need(c['cid']==CIDS[i][j]and c['stopped']is c['retained']is True and c['unresolved_active_cid']is None,'original stopped/retained receipt; flags unmodified')
   rr.append(dict(create_ref=cr,cleanup_ref=cl,cid=CIDS[i][j]))
  rows.append(dict(leaf=leaf.as_posix(),owner_ref=owner,receipts=rr,old_owner_primary=o['primary'],old_owner_secondary=o['secondary']))
 return rows
def locked():
 import fcntl
 fd=os.open(ROOT/'.storage061.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BaseException:os.close(fd);raise
 return fd
def latest(K):
 files=list(ROOT.glob('STORAGE_LEDGER061.*.json'));need(files,'actual old ledger exists')
 return K.ref(max(files,key=lambda p:int(p.name.split('.')[1])))
def evidence_admission(proof):
 need(proof['used_bytes']+50*2**20<=80*G and proof['committed_bytes']+50*2**20<=80*G and proof['filesystem_free_bytes']>=100*G+50*2**20,'evidence50MiB charged actual and commitment80/free100')
def read_tree(K,r):
 # Only this declared full-tree container may exceed canonical small-JSON16MiB.
 # The entire new evidence directory remains below50MiB, including both trees.
 need(Path(r['path']).parent==OUT and 0<r['bytes']<49*2**20 and K.ref(r['path'])==r,'bounded exact full-tree evidence container')
 value=json.loads(Path(r['path']).read_bytes());need(set(value)=={'root','files'}and type(value['files'])is list,'typed tree evidence only');return value
def write_evidence(K,path,value):
 need(Path(path).parent==OUT,'only one exact new evidence leaf')
 body=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode();used=sum(r['bytes']for r in K.tree(OUT,False))
 cap=(49 if Path(path).name.startswith('tree-')else 50)*2**20
 need(used+len(body)<cap,'combined evidence50MiB before any write; trees reserve1MiB metadata')
 with Path(path).open('xb')as f:f.write(body);f.flush();os.fsync(f.fileno())
 return K.ref(path)
def capture(sr):
 K,m=canonical(sr);fd=locked()
 try:
  need(latest(K)==BASE and not OUT.exists(),'exact highest23 and unique evidence output')
  inv1=inventory(ROOT);S,proof=prior_policy(K);inv2=inventory(ROOT);need(inv1==inv2 and inv1['bytes']==proof['used_bytes'],'fresh complete fullP inventory agrees original policy bytes')
  original=receipts(K);base=K.read(BASE)
  evidence_admission(proof)
  OUT.mkdir(mode=0o700);before=K.no_writers();states1=K.inspect_all();phases=[]
  for i,leaf in enumerate(LEAVES):
   matches=[r for r in base['reservations']if r['leaf']==str(leaf)]
   need(len(matches)==1 and matches[0]['stage']=='numeric'and matches[0]['budget_bytes']==33*G,'exact two original33GiB rows')
   a=K.tree(leaf,True);b=K.tree(leaf,True);need(a==b,'two complete independent full streamed tree hashes stable')
   tr=write_evidence(K,OUT/('tree-'+str((16,160)[i])+'.json'),dict(root=str(leaf),files=a));phases.append(dict(original[i],tree_ref=tr,frozen_bytes=sum(x['bytes']for x in a)))
  states2=K.inspect_all();need(states1==states2,'two fresh stopped/noExec/noOOM inspections stable');after=K.no_writers();need(latest(K)==BASE,'old ledger not changed')
  inv3=inventory(ROOT,OUT);need(inv3==inv1,'all old P metadata stable; only new evidence leaf excluded')
  need(sum(x['bytes']for x in K.tree(OUT,False))<49*2**20,'whole evidence bounded50MiB')
  need(time.time()<1792220533,'capture must complete inside original cutoff')
  return write_evidence(K,OUT/'EVIDENCE.json',dict(schema=SCHEMA,source_manifest_ref=sr,root=str(ROOT),baseline_ledger_ref=BASE,original_source_ref=SOURCE,prior_sealed_evidence_ref=base['sealed_evidence_ref'],authority_ref=base['authority_ref'],phases=phases,states_before=states1,states_after=states2,no_writer_before=before,no_writer_after=after,global_inventory_before=inv1,global_inventory_after=inv3,original_policy_proof=proof,old_flags_preserved=True,core_ledger_written=False,numeric_qualified=False))
 finally:os.close(fd)
def validate(er,sr):
 K,m=canonical(sr);e=K.read(er);need(e['schema']==SCHEMA and e['source_manifest_ref']==sr and e['baseline_ledger_ref']==BASE and e['original_source_ref']==SOURCE and e['core_ledger_written']is e['numeric_qualified']is False,'exact new overlay source, no promotion')
 need(latest(K)==BASE,'legacy ledger prefix unchanged');inv1=inventory(ROOT,OUT);S,proof=prior_policy(K);original=receipts(K);base=K.read(BASE)
 need(e['global_inventory_before']==e['global_inventory_after'],'capture complete fullP inventory stable')
 need(inv1['bytes']+sum(r['bytes']for r in K.tree(OUT,False))==proof['used_bytes'],'fresh fullP complete bytes joins original policy proof')
 need(e['root']==str(ROOT)and e['authority_ref']==base['authority_ref']and e['prior_sealed_evidence_ref']==base['sealed_evidence_ref']and e['old_flags_preserved']is True,'exact original authority/13closed seal/failure flags')
 need(len(e['phases'])==2,'exactly two leaves, no scope expansion')
 for i,row in enumerate(e['phases']):
  need(all(row[k]==v for k,v in original[i].items()),'original failure/cleanup/create immutable')
  t=read_tree(K,row['tree_ref']);need(t['root']==str(LEAVES[i])and K.tree(LEAVES[i],True)==t['files']and row['frozen_bytes']==sum(v['bytes']for v in t['files']),'full frozen tree unchanged')
 need(K.inspect_all()==e['states_before']==e['states_after'],'fresh exactCID independently stopped');K.no_writers();need(inventory(ROOT,OUT)==inv1,'fresh complete fullP stable throughout validation');need(latest(K)==BASE and time.time()<1792220533,'ledger/cutoff stable through final verification');return e,proof
def readset(er,sr):
 # Explicit original typed readset, never recursive provenance discovery.
 e,proof=validate(er,sr);K,m=canonical(sr);bound=K.read(SOURCE)
 B=sys.modules['storage_bridge088r6'];C=policy_context(K,sys.modules['bridge_io'])
 refs=B.readset(C,bound)
 prior=B.original.api(C,bound)
 unused,base,closed=prior.validate(B.original.ACTUAL_EVIDENCE,B.original.SOURCE121)
 extra=sys.modules['closed_overlay088r6'].validate(C,bound,bound['storage088r6_append_evidence_ref'])
 closed=closed+extra['phases']+e['phases'];need(len(closed)==15,'exact original13 plus two closed leaves')
 refs += [sr,er,BASE,SOURCE]+list(m['files'].values())
 for row in e['phases']:
  refs += [row['owner_ref'],row['tree_ref']]
  for receipt in row['receipts']:refs += [receipt['create_ref'],receipt['cleanup_ref']]
 out={}
 for r in refs:
  need(type(r)is dict and set(r)=={'path','bytes','sha256'}and K.ref(r['path'])==r,'exact explicit readonly dependency')
  need(r['path']not in out or out[r['path']]==r,'no conflicting dependency identity');out[r['path']]=r
 return dict(refs=list(out.values()),retained_tree_roots=[r['leaf']for r in closed],proof=proof,closed_count=15,numeric_qualified=False)
def main():
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true');p.add_argument('--mode',choices=('preflight','capture','validate'));p.add_argument('--source-ref');p.add_argument('--evidence-ref');a=p.parse_args()
 if not a.execute:print('{"enabled":false,"NPU":false}');return
 need(1792134133<=time.time()<1792220533,'unchanged actual cutoff');sr=json.loads(a.source_ref);K,m=canonical(sr)
 if a.mode=='preflight':
  need(latest(K)==BASE,'actual highest23');receipts(K);S,proof=prior_policy(K);evidence_admission(proof)
  need(not OUT.exists()and latest(K)==BASE,'full original loader/policy preflight does not create output or ledger')
  result=dict(preflight=True,full_prior_policy_checked=True,original_policy_proof=proof,NPU=False,numeric_qualified=False)
 elif a.mode=='capture':result=capture(sr)
 else:e,proof=validate(json.loads(a.evidence_ref),sr);result=dict(valid=True,closed2=e['phases'],original_policy_proof=proof,numeric_qualified=False)
 print(json.dumps(result))
if __name__=='__main__':main()
