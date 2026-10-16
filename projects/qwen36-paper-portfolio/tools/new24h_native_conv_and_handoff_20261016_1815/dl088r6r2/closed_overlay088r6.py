"""Source-bound read-only R5 closure. No ledger reset, no numeric promotion."""
import ast,inspect,json,shutil,types
from pathlib import Path
import storage_bridge121 as B
ROOT=B.ROOT;G=2**30
BASE=dict(path=ROOT.as_posix()+'/STORAGE_LEDGER061.17.json',bytes=3122,sha256='cb5015767ddab938149b0419796ffec11d09bd54be2e6d578e3fefbbd8ec2119')
SIXTEEN=dict(path=ROOT.as_posix()+'/STORAGE_LEDGER061.16.json',bytes=2956,sha256='947e78764a9dbadcd30dae585d11bbe784d4d3ebea37e71c583d8dbfb7d6f257')
R5_TEMPLATE=dict(path='/cache/cch/qwen36-paper-preparation-20261007/lowbit/deltalog-sameinitial-native-contract-new24h-v1-088-repair5/SOURCE_TEMPLATE.json',bytes=62770,sha256='f3f12ddc4e3f0b255b5f38f7e8f731bc3f29d8b161d9f96db8a1c923e5b390e8')
LEAVES=tuple(ROOT/('run-'+n+'-MAIN-20261016-NEW24H-088-repair5-001')for n in('cpu','numeric16'))
CIDS=('0cd45684514c83e61d0b83b820def60b6343a11f9150b6c859d4ec8a037517d5','37e67dce799bcdc5367f7642189cdac83309c4b52c0a185d1c86e1a55b7eb1bd')
OWNERS=((1402,'b9be0111cd757e1fc0540ebc2af9e91e4d4ae28078ad40994277079ffed5ad74'),(1233,'28bf2e88ea97eb23b7d9f1ef481087a482e1a7c801d0721a212f790d8183c3c5'))
CLEANUPS=((246,'82310e3e348e77ea208178a085f76b651d6a3957fac28da9a4b631fb21721235'),(246,'f40ed2d81d3bfa8e3fcb4f2607ad8826f40282a0e41403c054e866b85b2471b9'))
PRIMARY="ValueError('active true CID and actual ARM proof retained')"
def expected(path,pair):return dict(path=path.as_posix(),bytes=pair[0],sha256=pair[1])
def history(C,template=None,overlay=None):
 prev=B.ACTUAL_GENERATION;v=C.obj(prev)
 for path in B.generations():
  n=int(path.name.split('.')[1])
  if n<=15:continue
  C.need(n==int(Path(prev['path']).name.split('.')[1])+1,'no missing continuation generation');r=C.ref(path);w=C.obj(r);context=(B.SOURCE121,B.ACTUAL_EVIDENCE)if n<=17 else(template,overlay)
  C.need(None not in context and w['previous_ledger_ref']==prev and w['storage069_template_ref']==context[0]and w['sealed_evidence_ref']==context[1],'exact historical121 / newR6 append chain')
  C.need(w['root']==v['root']and w['authority_ref']==v['authority_ref']and w['reservations'][:len(v['reservations'])]==v['reservations']and len(w['reservations'])==len(v['reservations'])+1,'immutable prefix, one new reservation')
  if n in(16,17):
   i=n-16;C.need(r==(SIXTEEN if i==0 else BASE)and w['reservations'][-1]==dict(leaf=LEAVES[i].as_posix(),stage='cpu'if i==0 else'numeric',budget_bytes=(1 if i==0 else 33)*G),'actual R5 spent16/17')
  prev=r;v=w
 C.need(int(Path(prev['path']).name.split('.')[1])>=17,'actual spent17 exists');return prev,v
def receipts(C):
 rows=[];source=None
 for i,leaf in enumerate(LEAVES):
  rr=expected(leaf/'RESULT.json',OWNERS[i]);o=C.obj(rr)
  C.need(o['schema']=='deltalog.diagnostic-owned-host/v035'and o['source']==o['target_source']and o['steps']==16 and o['stage']==('cpu'if i==0 else'numeric')and o['stopped_retained']is True and o['secondary']==[]and o['primary']==(None if i==0 else PRIMARY),'actual R5 terminal, immutable failure')
  if source is None:source=o['source']
  C.need(o['source']==source,'both R5 stages same source');s=C.obj(source);t=C.obj(R5_TEMPLATE);C.need(s['prepared_only']is False and s['prepared_template']==R5_TEMPLATE and s['files']==t['files']and s['root']==t['root'],'actual R5 source/template')
  stage=leaf/('native'if i==0 else'numeric');cr=C.ref(stage/'create-receipt.json');C.need(C.obj(cr)['stdout'].strip()==CIDS[i],'source-created exact CID');cl=expected(stage/'cleanup-verdict.json',CLEANUPS[i]);c=C.obj(cl)
  C.need(c['cid']==CIDS[i]and c['stopped']is c['retained']is c['resource_release_verified']is True and c['errors']==[]and c['unresolved_active_cid']is None,'actual independently released cleanup')
  rows.append(dict(leaf=leaf.as_posix(),cid=CIDS[i],owner_ref=rr,create_ref=cr,cleanup_ref=cl,original_primary=o['primary'],original_secondary=o['secondary']))
 return source,rows
def observer(S,source):
 K=S.prior();ns=dict(K.__dict__,SOURCE=source,leaf=lambda i:LEAVES[i],CIDS=tuple((c,)for c in CIDS));raw=inspect.getsource(K.no_writers);assert raw.count('range(3)')==1
 changed=raw.replace('range(3)','range(2)');assert changed.replace('range(2)','range(3)')==raw;ast.parse(changed);local={};exec(compile(changed,'closed_overlay088r6.py#canonical119-twoR5','exec'),ns,local)
 return types.SimpleNamespace(no_writers=local['no_writers'],inspect_all=types.FunctionType(K.inspect_all.__code__,ns),tree=K.tree)
def states(C,values):
 C.need(len(values)==2 and {x['Id']for x in values}==set(CIDS),'both and only actual R5 CIDs')
 for x in values:
  s=x['State'];C.need(not x.get('ExecIDs')and s['Pid']==0 and s['Running']is False and s['Status']=='exited'and s['OOMKilled']is False and s['ExitCode']==(0 if x['Id']==CIDS[0]else 1),'actual CPU0 / ARMfailure1 stopped, not success relabel')
def capture(C,m,tr,out):
 C.need(C.obj(tr)==m and m['prepared_only']is True,'actual R6 template');S=B.api(C,m);S.validate(B.ACTUAL_EVIDENCE,B.SOURCE121);latest,_=history(C);C.need(latest==BASE,'capture only actual17')
 src,rows=receipts(C);Q=observer(S,src);C.need(out==ROOT/'seal-evidence088R6repair2-MAIN-001'and not out.exists(),'exact fresh overlay leaf');C.need(sum(x['bytes']for x in Q.tree(ROOT,False))+50*2**20<=80*G and shutil.disk_usage(ROOT).free>=100*G+50*2**20,'80total/100free incl evidence')
 before=Q.no_writers();a=Q.inspect_all();states(C,a);out.mkdir();phases=[]
 for i,row in enumerate(rows):
  x=Q.tree(row['leaf'],True);y=Q.tree(row['leaf'],True);C.need(x==y,'two complete stable tree hashes');p=out/('tree-'+str(i)+'.json');C.write(p,dict(root=row['leaf'],files=x));phases.append(dict(row,tree_ref=C.ref(p),frozen_bytes=sum(v['bytes']for v in x)))
 b=Q.inspect_all();states(C,b);C.need(a==b,'fresh double inspect unchanged');after=Q.no_writers();C.need(C.ref(B.generations()[-1])==BASE,'ledger17 unchanged')
 p=out/'OVERLAY088R6.json';C.write(p,dict(schema='deltalog.closed-R5-storage-overlay/v088-repair6',source_template_ref=tr,baseline_ledger_ref=BASE,r5_source_ref=src,prior_evidence_ref=B.ACTUAL_EVIDENCE,phases=phases,states_before=a,states_after=b,no_writer_before=before,no_writer_after=after,numerical_qualification=False));return C.ref(p)
def validate(C,m,r,full=True,fresh=True):
 C.need(type(r)is dict,'actual R5 overlay Ref3 mandatory');e=C.obj(r);tr=m.get('prepared_template')or C.ref(Path(__file__).parent/'SOURCE_TEMPLATE.json')
 C.need(e['schema']=='deltalog.closed-R5-storage-overlay/v088-repair6'and e['source_template_ref']==tr and e['baseline_ledger_ref']==BASE and e['prior_evidence_ref']==B.ACTUAL_EVIDENCE and e['numerical_qualification']is False,'exact actual17 own source/storage-only overlay')
 src,rows=receipts(C);C.need(e['r5_source_ref']==src and len(e['phases'])==2,'actual R5 source/two phases');S=B.api(C,m);Q=observer(S,src)
 for original,row in zip(rows,e['phases']):
  C.need(all(row[k]==v for k,v in original.items()),'old flags/receipts exact');t=C.obj(row['tree_ref']);actual=Q.tree(row['leaf'],full);expected=t['files']if full else[{k:v for k,v in x.items()if k!='sha256'}for x in t['files']];C.need(t['root']==row['leaf']and actual==expected and row['frozen_bytes']==sum(x['bytes']for x in expected),'closed R5 hash/stat unchanged')
 states(C,e['states_before']);states(C,e['states_after']);C.need(e['states_before']==e['states_after'],'stable captured inspect')
 for name in('no_writer_before','no_writer_after'):
  v=e[name];C.need(set(v)=={'processes_examined','no_original_commands','no_open_write_FDs_or_shared_writable_maps'}and type(v['processes_examined'])is int and 0<v['processes_examined']<=16384 and v['no_original_commands']is v['no_open_write_FDs_or_shared_writable_maps']is True,'typed complete original no-writer proof')
 if fresh:C.need(Q.inspect_all()==e['states_before'],'fresh same stopped proof');Q.no_writers()
 return e
