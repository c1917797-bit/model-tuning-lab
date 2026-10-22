"""Read-only historical transport -> current CPU decoder bridge. No launch/approval."""
import ast
from contextlib import contextmanager
import copy,hashlib,importlib.util,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
_ACTIVE=None
SCHEMA='bole.transport-current-decoder-source/v1'
def need(v,s):
 if not v:raise ValueError(s)
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def ref(p):
 p=Path(p);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'ordinary exact bridge source')
 before=p.stat();raw=p.read_bytes();after=p.stat()
 need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'stable whole bridge bytes')
 return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def checked(r):
 need(type(r)is dict and set(r)=={'path','bytes','sha256'}and type(r['bytes'])is int and 0<=r['bytes']<=128*2**20,'bounded full bridge Ref3')
 need(ref(r['path'])==r,'whole bridge Ref');return Path(r['path'])
def obj(r):return json.loads(checked(r).read_bytes())
def load_module(r,name):
 raw=checked(r).read_bytes();s=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(s)
 sys.modules[name]=m
 exec(compile(raw,r['path'],'exec'),m.__dict__);checked(r);return m
@contextmanager
def isolated(names):
 missing=object();snapshot=dict(sys.modules);old={n:sys.modules.get(n,missing)for n in names};paths=list(sys.path)
 try:yield
 finally:
  sys.path[:]=paths
  for n,v in old.items():
   if v is missing:sys.modules.pop(n,None)
   else:sys.modules[n]=v
  # Both unchanged CPU14 proof readers load this exact source-owned helper prefix.
  # Restore these dynamic helper identities too, without deleting unrelated imports.
  for n in set(snapshot)|set(sys.modules):
   if n.startswith('_HTTPv3_pure_HE_guard_'):
    if n in snapshot:sys.modules[n]=snapshot[n]
    else:sys.modules.pop(n,None)
def historical_verifier(original_module,observed_epoch):
 """Original authority body, with explicit recorded historical-time operand only."""
 original=checked(ref(original_module.__file__)).read_text();tree=ast.parse(original)
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='authority')
 need(ast.get_source_segment(original,node)=="""def authority(r,seconds=0):
    v=obj(r);need(v['start_epoch']<=time.time()and time.time()+seconds<v['cutoff_epoch'],'current new authority including finite full budget');return v""",'exact retained historical authority verifier')
 node=copy.deepcopy(node);node.name='verify_recorded_generation_authority'
 class HistoricalTime(ast.NodeTransformer):
  count=0
  def visit_Call(self,n):
   if ast.unparse(n.func)=='time.time'and not n.args and not n.keywords:
    self.count+=1;return ast.copy_location(ast.Name(id='OBSERVED_GENERATION_EPOCH',ctx=ast.Load()),n)
   return self.generic_visit(n)
 transform=HistoricalTime();node=transform.visit(node);need(transform.count==2,'exact two historical clock operands')
 ast.fix_missing_locations(node)
 env=dict(original_module.__dict__,OBSERVED_GENERATION_EPOCH=observed_epoch)
 exec(compile(ast.Module(body=[node],type_ignores=[]),'explicit-recorded-generation-authority-verifier','exec'),env)
 return env[node.name]
def current():
 need(_ACTIVE is not None,'explicit current CPU replay context required; no direct HTTP/consumer bypass')
 _ACTIVE['R'].validate_current(_ACTIVE['m'],_ACTIVE['binding_ref'])
 return _ACTIVE
class CommonProxy:
 def __getattr__(self,name):return getattr(current()['C'],name)
COMMON_PROXY=CommonProxy()
def historical_authority(reference,seconds=0):
 c=current();g=c['generation']
 need(seconds==0 and reference==g['authority_ref']==c['HTTP_m']['authority_ref'],
      'historical read-only generation authority only, never a new HTTP budget or foreign ticket')
 # Actual generation times were reconstructed by R.verify_generation from retained
 # host operations, not passed by this caller. Current execution remains separately checked.
 for epoch in(g['started_epoch'],g['finished_epoch']):
  historical_verifier(c['C'],epoch)(reference,0)
 return c['C'].obj(reference)
def decode_grades(plan,client):
 c=current();R=c['R'];b=c['binding']
 need(plan==c['plan']and client==R.obj(c['generation']['client_ref'])and client['raw_ref']==b['raw_ref'],
      'same generation plan/client/raw as independently admitted current decoder')
 raw=R.envelope(c['raw'],c['decoder_source_ref'])
 need(R.inverse_envelope(raw,b['historical_task_source_ref'])==c['raw'],'whole reversible decoder envelope')
 leaf=c['output']/'REPLAY_ENVELOPE.json'
 fd=os.open(leaf,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(canonical(raw)+b'\n');f.flush();os.fsync(f.fileno())
 grades=c['modules']['score_tokens'].replay(c['decoder_source_ref'],R.ref(leaf),full_provenance=False)
 need(grades['human_eval_code_executed']is False,'pure unchanged decoder/scorer; no generated HumanEval execution')
 current();return grades
def packet(source_ref,decoder_source_ref,binding_ref):
 q=obj(source_ref);m=obj(decoder_source_ref);b=obj(binding_ref)
 for n,size,sha in [('decoder_replay_contract.py',15365,'a1e5055fe1a0181c82d5aa6435f2466ea67d9ee734fa8fc72eb9d62e56766103'),
                    ('replay_entry.py',4928,'4ce29c200d2da63992fbf2dc64bb8e49cf5699ede3ebf2ec762b91881838ae21')]:
  need((m['files'][n]['bytes'],m['files'][n]['sha256'])==(size,sha),'exact reviewed decoder helper before executable import '+n)
  checked(m['files'][n])
 need(q['schema']==SCHEMA and q['prepared_only']is True and q['default_enabled']is False
      and q['root']==str(P)and b['transport_decoder_binding_ref']==source_ref
      and q['decoder_source_ref']==decoder_source_ref,'explicit current CPU ticket binds exact additional transport bridge')
 need(set(q['files'])=={'transport_decoder_bridge.py','transport_decoder_entry.py','consume_lifecycle_replay.py'},'complete executable bridge closure')
 for name,r in q['files'].items():need(checked(r)==P/name,'exact source-owned bridge file')
 need(q['files']['transport_decoder_bridge.py']==ref(__file__),'actual current bridge helper')
 need(str(P)in b['required_readonly_mounts'],'MAIN actual CPU inspect must cover this additional read-only bridge')
 need(q['HTTP_source_ref']==obj(b['generation_ref'])['HTTP_source_ref'],'same historical HTTP source, not current execution ticket')
 historical=obj(q['HTTP_source_ref'])
 need(q['original_consumer_ref']==historical['files']['consume_lifecycle.py']and
      q['original_consumer_ref']['sha256']=='bffd5f6cd195ca2af835cde6f37b011c1afa2c6887947882c086b217d4339708','same exact original full transport consumer')
 original=checked(q['original_consumer_ref']).read_bytes()
 text=checked(q['files']['consume_lifecycle_replay.py']).read_text()
 seams=[('import http_common as C','import transport_decoder_bridge as B\nC=B.COMMON_PROXY'),
        ("    tm=C.obj(plan['source_ref']);sys.path.insert(0,tm['root'])\n    S=C.load(tm['files']['score_tokens.py'],'_task_http_exact_frozen_component_scorer')\n    grades=S.replay(plan['source_ref'],client['raw_ref'],full_provenance=False)",
         "    grades=B.decode_grades(plan,client)")]
 for old,new in reversed(seams):
  need(text.count(new)==1,'one precise read-only consumer inverse seam');text=text.replace(new,old,1)
 need(text.encode()==original,'complete unchanged stop/owner/native-role/worker/HTTP consumer, not a subset')
 return q,m,b
@contextmanager
def transport_context(q,R,m,binding_ref,decoder_source_ref,modules,output):
 global _ACTIVE
 need(_ACTIVE is None and R._ACTIVE is not None,'no nested/global transport view; current R.execution must already be active')
 b=R._ACTIVE['binding'];g=R.obj(b['generation_ref']);hm=R.obj(q['HTTP_source_ref'])
 need(hm['plan_ref']==b['plan_ref']and hm['authority_ref']==g['authority_ref'],'same exact historical generation manifest')
 original_ref=hm['files']['http_common.py']
 need((original_ref['bytes'],original_ref['sha256'])==(24368,'6d24a14c2a49499bd9caf63e0a405a9d5b4c91d79284c4acdc81f9b5b1bf5646')and
      (hm['files']['cohort_contract.py']['bytes'],hm['files']['cohort_contract.py']['sha256'])==(4040,'09c614efc9a17cccf938ad581dd787ccef6eefa77ebd700f014534fac12ed31a'),
      'exact reviewed original transport helpers before executable import')
 names=('_historical_transport_common','cohort_contract')
 with isolated(names):
  need((hm['files']['cohort_contract.py']['bytes'],hm['files']['cohort_contract.py']['sha256'])==
       (m['files']['cohort_contract.py']['bytes'],m['files']['cohort_contract.py']['sha256']),'same original official cohort helper')
  load_module(hm['files']['cohort_contract.py'],'cohort_contract')
  C=load_module(original_ref,names[0]);original_authority=C.authority
  c=dict(R=R,m=m,binding=b,binding_ref=binding_ref,decoder_source_ref=decoder_source_ref,
         modules=modules,output=output,C=C,generation=g,HTTP_m=hm,
         plan=R.obj(b['plan_ref']),raw=R.obj(b['raw_ref']))
  _ACTIVE=c;C.authority=historical_authority
  try:
   # Original complete source verifier still reopens all original transport files,
   # native stopped-image snapshots, cohort policy and generation config.
   need(C.source(q['HTTP_source_ref'],native_runtime=False)==hm,'whole unchanged historical transport source')
   yield c
  finally:C.authority=original_authority;_ACTIVE=None
